# Storage Architecture Decision Matrix

Comparison of storage options by deployment scenario. Scores: 1 (poor) to 5 (excellent). Comments justify tradeoffs.

## Legend
- POSIX: Native file system semantics (rename, atomic writes, symlinks)
- Latency: Typical perceived latency for common ops (listing, small file read)
- Scale: Ability to scale to 1000+ users / 20k+ cases / 100M+ objects

## Matrix

| Scenario | Option | POSIX | Latency | Scale | Durability | Cost | Complexity | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Cloud (single region) | S3/Blob/GCS + Local Workspace Cache | 2 | 4 | 5 | 5 | 4 | 3 | Recommended. Authoritative object store + ephemeral POSIX cache for AI. Versioning, lifecycle, signed URLs. |
| Cloud (single region) | Managed NAS (EFS/Filestore/Azure Files) | 5 | 3 | 3 | 4 | 3 | 2 | Simple POSIX semantics; can bottleneck on metadata and throughput; cost grows with IOPS. |
| Cloud (single region) | Hybrid (Object Store + NAS cache) | 4 | 4 | 5 | 5 | 3 | 4 | Object store as source of truth; NAS for hot set (shared). Increased ops complexity. |
| Cloud (multi‑region) | S3/Blob/GCS with CRR/Geo‑replication | 2 | 4 | 5 | 5 | 4 | 4 | Strong for DR and data residency; higher x‑region costs; needs region routing. |
| On‑prem (single site) | Enterprise NAS (Isilon/NetApp) | 5 | 4 | 4 | 4 | 2 | 2 | Fits strict POSIX+compliance; CapEx heavy; good throughput. |
| On‑prem (cluster) | CephFS/Gluster/GPFS | 5 | 4 | 4 | 4 | 3 | 4 | Open/commodity; requires strong ops; can scale horizontally. |
| Hybrid (cloud+onprem) | Object store authoritative, on‑prem NAS cache | 4 | 4 | 5 | 5 | 3 | 5 | Best of both; complex network + sync; clear runbooks needed. |
| Air‑gapped | DFS only + tape/archive | 5 | 3 | 3 | 5 | 2 | 4 | Meets isolation/compliance; low cloud dependency; slower collaboration. |

## Decision Guidance

- Prefer object storage as the authoritative layer wherever possible; pair with local ephemeral workspaces for agent performance.
- Choose NAS/DFS authoritative only where POSIX persistence is mandated or cloud is disallowed.
- Hybrid is ideal when cross‑site collaboration or DR is required but POSIX workloads remain heavy.

## Reference Paths and IAM

- Object storage (tenant‑scoped):
  - `s3://legal-root/users/{user_id}/cases/{case_id}/...`
  - Signed URL TTL: 5–60 minutes; refresh via API when expired
- NAS/DFS (tenant‑scoped mounts):
  - `/mnt/legal/users/{user_id}/cases/{case_id}/...`
  - Bind‑mount to container workspace

## Operational Considerations

- Monitoring: latency (P50/P95), error rates, throughput, queue backlogs
- Autoscaling: workspace nodes based on concurrent cases; prefetch workers by queue depth
- Cost controls: lifecycle rules (auto‑archive), compression for cold data, tiering (Glacier/Archive)
- Security: per‑tenant prefixes/mounts; KMS‑managed keys; audit logging for reads/writes

