# Storage Implementation Details: Multi-Tenant Legal Case Management

This document clarifies storage location choices, AI access patterns, user isolation, and how the hybrid (PostgreSQL + file storage) architecture operates at runtime with OpenHands-style workspaces.

## 1) Storage Location Options and Recommendations

### A. Local File System on App Servers (Not authoritative)
- Use case: Short-lived, per-session workspace for AI agent read/write.
- Pros: Lowest latency, POSIX semantics, simple to mount into agent containers.
- Cons: Not durable, no cross-node visibility, poor for scale or HA.
- Recommendation: Use as an ephemeral cache only; not the source of truth.

### B. Network/Distributed File Systems (NFS, EFS, Azure Files, Filestore, CephFS)
- Use case: Simple POSIX mount that all app nodes can access; authoritative if you require POSIX everywhere.
- Pros: Drop-in POSIX, easy container mounts; simpler agent integration.
- Cons: Cost and throughput limits at scale; metadata-intensive ops can be slow; cross-region complexity.
- Recommendation: Viable in private/on-prem or single-cloud-region deployments. Consider CephFS/Isilon for high-end on-prem; EFS/Filestore/Azure Files for cloud-managed POSIX.

### C. Cloud Object Storage (S3/Azure Blob/GCS) — Recommended authoritative store
- Use case: System of record for all case documents.
- Pros: Virtually infinite scale, strong durability (versioning), lifecycle mgmt, geo-replication, cost-effective.
- Cons: Not POSIX; object-level semantics; small-file churn can be expensive if overused.
- Recommendation: Make object storage the authoritative layer; combine with local ephemeral workspace caches for agent operations.

Summary recommendation:
- Authoritative store = Cloud Object Storage (per-tenant prefixes)
- Performance layer = Local ephemeral workspace on compute (POSIX)
- Optional: DFS/NAS if regulatory/infra constraints require POSIX persistence

## 2) AI Agent Access: File Access Patterns

The OpenHands agent expects a POSIX-like workspace mounted into a container. We therefore materialize files into a local workspace cache when a case is opened and sync back to authoritative storage.

### Read Path
1. User opens case.
2. App resolves manifest for that case (from DB metadata) — folder tree + file list with content hashes and sizes.
3. Workspace Manager prepares a local workspace directory on the compute node.
4. It prefetches a configurable subset (hot set) of files:
   - recent docs, small Markdown files, folder indices, etc.
   - large PDFs/docs fetched lazily on first access.
5. Agent operates directly on the local POSIX workspace.

### Write Path
1. Agent edits files locally (POSIX operations inside container).
2. File Syncer detects changes via fs events or staged commits.
3. Changed files are uploaded to object storage as new versions; DB metadata is updated atomically (transaction) with content hash, size, modified time.
4. Conflicts handled via ETag/content-hash checks and optimistic concurrency (see below).

### Streaming vs Download for AI
- For read-only analysis of large files: support ranged GET or streaming readers direct from object storage to reduce full downloads (e.g., PDF metadata extraction).
- For edits or multi-pass analysis: download to local workspace to avoid repeated network reads.

### Performance Implications
- Small file reads/writes: local cache dominates; very fast.
- Large immutable reads (PDFs): stream initial pages; lazy fetch; optional background full download if agent keeps reading.
- Batch sync: upload deltas; parallelize uploads; use multipart transfers.

## 3) User Isolation and Scaling Strategy

### Tenant Isolation
- Object storage per-tenant prefix: `s3://legal-root/users/{user_id}/cases/{case_id}/...`
- IAM policies scoped to tenant prefixes; service role mediates access.
- Compute isolation at container boundary per user/session; no shared writeable mounts across tenants.

### Sharding and Physical Mapping
- Users sharded logically across storage domains (e.g., buckets or storage accounts) using a stable hash of `user_id`.
- App nodes are stateless; any node can serve any user; the workspace cache lives on the node handling the session.
- Example mapping (1000 users): 3 storage domains (A/B/C) where `domain = hash(user_id) % 3`.
- On-prem/DFS option: shard users across storage clusters or volumes (e.g., Ceph pools, Isilon tiers) using the same hash.

### Dedicated Instances?
- Not needed per user. Use shared multi-tenant app and storage services with strict isolation via prefixes, IAM, and container boundaries.
- Consider dedicated storage domains for large firms if needed for contractual isolation or throughput guarantees.

## 4) Hybrid Architecture Details (DB + Storage)

### Where do files live?
- System of record: Cloud object storage under tenant-prefixed paths (or DFS/NAS in regulated environments).
- Local compute: Ephemeral POSIX workspace (e.g., `/var/ai-workspaces/{session_id}`) mounted into agent containers.

### How does the app coordinate DB + storage?
- PostgreSQL holds:
  - Users, cases, permissions
  - File metadata (logical path, size, content hash, last_modified, version)
  - Manifests: a normalized tree of directories and files for fast listings
- Storage layer holds the actual file bytes.
- Workflow:
  1) On case open, app fetches case manifest from DB.
  2) Workspace Manager materializes a local folder tree from manifest.
  3) Lazy fetch file contents from storage as needed.
  4) On save, File Syncer writes bytes to storage, updates DB metadata in a transaction, and refreshes in-memory caches.

### File Serving to Frontend
- Small files: serve directly from app via streaming for simplicity (auth checked in app).
- Large files: issue time-limited signed URLs from object storage; frontend downloads/streams directly.
- Edits from web UI: go through app to ensure concurrency control and audit logging.

## 5) Caching Strategy (Multi-Tier)

### Tier 0: In-Memory Metadata Cache (Redis)
- Cache case manifests, directory listings, and file metadata records.
- TTL + cache invalidation on write transactions.
- Hot-path reads avoid DB hits for listings (< 100 ms typical).

### Tier 1: Local Disk Workspace Cache
- Per-session workspace on SSD.
- Implements read-through caching: first access pulls from object storage; subsequent access is local.
- Eviction policy: LRU at session end; optional background warm-up for recently accessed cases.

### Tier 2: CDN / Edge Cache (optional)
- For large, frequently viewed read-only assets (e.g., exhibits), use CDN with signed URLs.
- Bypass CDN for sensitive or frequently changing files.

## 6) Concurrency, Versioning, and Conflicts

- Object storage writes use conditional requests with ETag or `If-Match` preconditions to prevent overwrites.
- DB updates use transactions and version columns.
- On conflict: create a new version and flag a UI-side merge workflow; never silently overwrite legal documents.
- Manifest generation includes a version pointer so the workspace knows its baseline.

## 7) Security and Compliance Controls

- Encryption at rest: KMS-managed keys; per-tenant data keys if required.
- Encryption in transit: TLS everywhere; signed URLs with short expiry for storage access.
- Access control: RBAC in DB; IAM policies at object storage; container-level isolation at runtime.
- Audit trails: DB audit tables + append-only logs for file reads/writes (user, case, file, action, timestamp, IP, user-agent).
- Data residency: map `user_id`/`org_id` to storage region; route to region-local buckets.

## 8) Backup and DR Mechanics

- Enable storage versioning + lifecycle policies; retain prior versions for configured period.
- Periodic snapshots of DB (logical and physical); point-in-time recovery enabled.
- Cross-region replication for both storage and DB replicas where required.
- User-scoped or case-scoped restore flows:
  - Restore DB metadata to time T
  - Restore file versions (object storage) to time T for the affected prefix
  - Rebuild manifest caches

## 9) Integration with OpenHands Agent Runtime

OpenHands runs agents inside containers with a mounted workspace. We inject our workspace path and file sync hooks.

### Container Mounting
- Host path: `/var/ai-workspaces/{session_id}` (local SSD)
- Container mount: `/opt/workspace_base/{case_id}` (matching OpenHands config)

### Workspace Lifecycle
1. Case Opened → Create workspace → Prefetch hot files + skeleton dirs
2. Agent Runs → POSIX read/writes → Local SSD performance
3. Save/Sync → Changed files pushed to storage → DB metadata updated
4. Session Ends → Optionally purge workspace or retain for short TTL for quick resume

### Large File Handling
- On first access, stream initial chunks; if AI continues, switch to full download in background.
- For speculative tasks (OCR, NLP), schedule background prefetch jobs.

## 10) Example Access Flows

### A. Case Open Flow
- Input: user_id, case_id
- Steps:
  1) AuthZ: verify user has access to case
  2) Load manifest from DB (cache hit expected)
  3) Create local workspace; lay out directories
  4) Prefetch hot files; stub placeholders for large assets
  5) Launch container with workspace mount

### B. File Read Flow
- If file present locally → return immediately
- Else → range-read from storage into local file → return handle/bytes to agent

### C. File Write Flow
- Write to local file → enqueue sync job → upload to storage with ETag check → update DB metadata → invalidate caches

## 11) Physical Infrastructure Mapping

- Cloud-first:
  - Object storage: S3/Blob/GCS with per-tenant prefixes and versioning
  - DB: PostgreSQL primary + read replicas (managed service recommended)
  - Cache: Redis (managed)
  - Compute: stateless app servers + job workers; autoscaling groups
  - Optional: EFS/Filestore/Azure Files if POSIX persistence needed beyond ephemeral caches

- On-prem/hybrid:
  - DFS: CephFS/Isilon/GPFS; shard users across storage pools
  - DB: Postgres with Patroni/pgpool for HA
  - Cache: Redis cluster
  - Compute: K8s or VM autoscaling; local NVMe for workspaces

## 12) Sizing and SLAs

- Latency targets: < 2s case open (warm cache); < 5s cold open with prefetch
- Throughput: parallel prefetch up to 1 Gbps per node
- Capacity: size local SSD for 5–10 concurrent cases per node with headroom
- Eviction: LRU on workspace cache; global LRU across nodes optional

---

This implementation preserves legal-friendly folder semantics while delivering scale, security, and performance. It integrates cleanly with OpenHands by treating the compute workspace as a synchronized cache over an authoritative object store (or DFS/NAS where required).
