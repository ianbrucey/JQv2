# Storage Options Analysis and Recommendations

This document evaluates two storage strategies for a multi-tenant legal case management system built on OpenHands: (1) GitHub-based repositories and (2) Cloud object storage. It includes criteria-based scoring, security/compliance implications, integration details with the planned hybrid architecture (PostgreSQL + Redis + ephemeral workspaces), and a recommended path.

## Executive Summary

- Recommended primary: **Cloud Object Storage (S3/Azure Blob/GCS) as the authoritative store**, with:
  - PostgreSQL for metadata/manifests/permissions
  - Redis for metadata caching
  - Ephemeral local SSD workspaces mounted into agent containers
  - Transparent sync (ETag/If-Match) and versioning enabled
- Optional hybrid: **Selective Git mirrors** for text-first artifacts (Markdown, templates), or periodic Git snapshots for audit-friendly diffs—without forcing legal users to learn Git.
- Not recommended as primary: **GitHub-only per-case repositories** for all content. Git excels at diffs and collaboration for source code but strains on binary-heavy legal corpora (PDF/Word), LFS management, enterprise auth/compliance, and cost/ops at 20k+ repos.

## Criteria-Based Comparison

| Criterion | Option 1: GitHub Repos (per case) | Option 2: Object Storage (authoritative) |
|---|---|---|
| User Experience | 3/5 – Can abstract Git in UI, but edge cases (conflicts, LFS prompts) leak; auth UX can be confusing | 5/5 – Simple folder semantics; no Git concepts exposed |
| Security & Compliance | 3/5 – Strong controls, but attorney‑client privilege, BAA/PII constraints may require Enterprise + additional agreements; limited KMS control | 5/5 – Fine-grained IAM, KMS customer‑managed keys, data residency, strong server-side encryption, versioning |
| Scalability (1000+ users, 20k+ cases) | 3/5 – 20k private repos manageable but heavy on API rate limits, lifecycle ops, seat/license mgmt; LFS costs | 5/5 – Designed for billions of objects; cheap and easy horizontal scale |
| Cost | 3/5 – Org seats, Actions minutes, LFS and transfer costs accumulate; backups require extra infra | 4/5 – Storage + transfer + requests; lifecycle tiering reduces cost; predictable |
| Version Control | 5/5 – First-class history/diffs, PRs | 4/5 – Native object versioning + metadata; can layer Git snapshots for text diffs |
| Performance | 3/5 – git clone/pull on large binary repos is slow; shallow clones help; LFS latency | 5/5 – Read-through cache + range GET; parallel fetch; optimal for large binaries |
| Backup/Recovery | 3/5 – Mirrors/backup tooling needed; limited control over RPO/RTO | 5/5 – Built-in versioning, cross-region replication, lifecycle; precise PITR with DB |
| OpenHands Integration | 4/5 – Clone repo into workspace; push on save; needs Git creds + LFS | 5/5 – Materialize from object storage; POSIX workspace; simple sync on save |

## Option 1: Git Repository Workflow (GitHub-based)

### Architecture
- Each case → private repository under a GitHub Organization (preferred) or per-user account.
- Authentication via **GitHub App** (recommended) instead of PATs. App grants repo-scoped access; OAuth for user identity; fine-grained permissions; rotates tokens.
- Large files via **Git LFS**; still stored externally and billed separately.

### Operational Questions & Answers
- Accounts: Use **one organizational account** (your company org) with per-case private repositories. Add users via seats and team permissions; avoid per-user GitHub accounts for ownership/control.
- Auth & Access: Install your **GitHub App** on the org; app issues installation tokens per repo. Map internal user_id to GitHub user membership/teams for read/write.
- Cost: Org plan seats + private repos (unlimited) + **LFS storage/transfer** + API rate limits. At thousands of repos, administrative overhead and cost can spike. Budget for LFS on PDF/Word assets.
- Security/Compliance: GitHub Enterprise Cloud offers SSO, audit logs, IP allowlists. However, **HIPAA/BAA and strict attorney‑client privilege controls** may require contractual assurances; encryption key control is limited vs KMS in your cloud. Assess data residency requirements.

### Integration with OpenHands
- On case open: `git clone --depth=1` into the ephemeral workspace; fetch-on-demand for large paths; LFS pulls for binaries.
- On save: stage changes and commit in background; push to origin using app token. Conflict handling surfaced in UI; auto-rebase where safe.
- Metadata DB: Store case → repo mapping, branch, path filters; per-file logical paths; derived artifacts tracked as Git paths. Redis caches repo manifests (ls-files) and logical tree.

### Risks
- Binary-heavy workloads perform poorly with git diffs; clone/pull ops are expensive at scale.
- LFS introduces separate storage/transfer costs and operational complexity.
- Compliance and data residency may be harder to guarantee than with your own object storage and keys.

## Option 2: Cloud Object Storage (Authoritative)

### Architecture
- Authoritative bucket(s) with tenant prefixes:
  - `s3://legal-root/users/{user_id}/cases/{case_id}/...`
- PostgreSQL stores manifests, metadata, permissions, derived_from relations, hashes, versions.
- Redis caches manifests and directory listings.
- Ephemeral local SSD workspace is the POSIX working set; read‑through from object storage; sync on save with ETag/If‑Match.

### Sync Strategies
- Individual file sync on save (recommended): upload only changed files; cheap and fast; preserves object version history; optimistic concurrency via ETag.
- Batched folder sync: queue changes and flush periodically; good for burst edits; slightly higher conflict surface.
- Zip-based archive: maintain periodic full-case snapshots as versioned archives for compliance/exports; not for normal editing.

### Integration with OpenHands
- On case open: materialize skeleton + prefetch hot set into `/var/ai-workspaces/{session_id}/{user_id}/{case_id}`; mount into agent container.
- On save: upload changed files, update DB metadata in a transaction, invalidate Redis keys. Derived files (.md) are first-class objects alongside originals.

### Benefits
- Excellent scale/cost; native versioning; KMS and IAM for strong security; lifecycle tiering; easy DR/replication; clean fit to our hybrid architecture.

## Hybrid Approaches

1) **Object Storage (authoritative) + Git Snapshots (text-only)**
- Keep PDFs/Word in object storage. Periodically commit Markdown and config files to a per-case or per-user Git mirror for human-friendly diffs and audit trails.
- Automate snapshots via background jobs (e.g., on every N edits or nightly). Store the Git mirror in GitHub/Gitea; do not gate the live editing workflow on Git.

2) **Object Storage + Legal DMS Connector (future)**
- Integrate with legal DMS (iManage/NetDocuments) for firms that require it. Store a link/ID in PostgreSQL manifest; fetch through a connector layer into the ephemeral workspace when needed.

3) **Managed Git (Gitea/GitLab CE) for selective cases**
- Self-hosted Git for firms demanding Git history under your control. Still keep binaries in object storage and only mirror text.

## Security and Compliance Considerations

- Prefer **object storage with customer-managed KMS keys** and per-tenant prefixes. Enforce IAM least-privilege policies.
- Enable **bucket versioning**, lifecycle policies, and **replication** (multi-region if required). Pair with **DB PITR**.
- Full **audit logging**: DB audit tables + append-only file access logs (reads/writes, actor, timestamp, IP). Signed URLs for direct downloads.
- Data residency: route tenant/org to region-local buckets.

## Cost Notes (order-of-magnitude)

- GitHub: Org seats (per-user/month), LFS storage/egress (per GB), API/Actions usage, possible Enterprise tier for compliance. Thousands of repos add admin overhead.
- Object Storage: $/GB-month (standard + archival tiers), request costs, egress; overall more predictable and cheaper for binary-heavy legal data.

## Performance Notes

- Git: cloning/pulling large repos (with thousands of PDFs) is slow; LFS downloads on demand can still bottleneck.
- Object Storage: read-through cache + range GET for PDFs; parallel multipart uploads on save. Case open < 2–5s with prefetch; hot reads < 100ms from local cache.

## Integration with PostgreSQL + Redis + Ephemeral Workspace

- Both options still use **PostgreSQL** for case metadata/manifests/permissions and **Redis** for manifest caching.
- With Git primary: the manifest is derived from git ls-tree/ls-files periodically and cached; with object storage primary: manifest is a DB-first source updated on every write.
- The **ephemeral workspace** remains central for the agent; it’s populated either by `git clone` (Option 1) or by object fetch (Option 2). Sync-back semantics differ (git push vs object PUT + DB update).

## Implementation Recommendations

1) Adopt **Object Storage as the authoritative store** now; implement:
- Tenant-scoped prefixes; KMS; bucket versioning; lifecycle policies
- Presigned URL uploads; ETag/If-Match concurrency; content hashing
- Manifest table design in PostgreSQL (path, size, hash, version, derived_from, mime, timestamps)
- Redis cache keys: `cache:manifest:{tenant}:{case}`, `cache:filemeta:{tenant}:{case}:{path}`
- Workspace Manager + Syncer (as specified in 09_Storage_Implementation_Details.md)

2) Add optional **Git snapshot mirrors** (phase 2):
- Background job converts current Markdown/text trees to a bare git repo and pushes to an org-owned mirror (GitHub or self-hosted). No LFS; exclude binaries.
- Store mirror URL/commit SHA in DB for audit.

3) Preserve a **zip-archive export** feature:
- On-demand or scheduled zipped case snapshot for discovery/production and cold backups; store in archival tier; index in DB.

4) Defer **Git-as-primary** unless a customer mandates it:
- If required, use GitHub App auth; org-owned repos; enforce LFS only for select binary subtrees; aggressively shallow clone and sparse checkout; expect higher ops cost.

## Modifications to the Hybrid Architecture

- Confirm object storage authoritative; treat Git mirrors as optional sidecars.
- Extend metadata schema:
  - `files(path, size, hash, version, mime, derived_from, created_at, updated_at, owner_id, permissions)`
  - `snapshots(case_id, type=['git','zip'], location, commit_sha/version_id, created_at)`
- API endpoints:
  - POST /files (init presign) → PUT to object storage → POST /files/complete
  - POST /snapshots/git, GET /snapshots/git
  - POST /snapshots/zip, GET /snapshots/zip
- Background workers: prefetch, sync, snapshot, lifecycle tasks.

## Final Recommendation

- For non-technical legal users at the stated scale, choose **Object Storage primary** with the OpenHands-compatible **ephemeral POSIX workspace** and **DB/Redis** layers you’ve planned. Add **Git snapshots** narrowly for text diffs/audits where they provide clear value. Reserve **GitHub-per-case** as an opt-in integration for specific customers, not the core storage substrate.

