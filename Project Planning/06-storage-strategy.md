# Storage Strategy (Local vs S3)

## Local Filesystem (Default MVP)
- Config: `CASES_BASE_PATH` (e.g., `/data/cases` on host)
- Case path: `${CASES_BASE_PATH}/${case_id}` (or slug)
- Mounting: per-conversation set `SANDBOX_VOLUMES` to `${host_case_path}:/workspace:rw`
- Pros: Simple, fast, no extra deps
- Cons: Single node storage; backups external

## S3 via MinIO (Sync Approach)
- Rationale: portable, fewer runtime deps
- Flow:
  1) On conversation start: sync `s3://bucket/prefix` → `/opt/cases-cache/{case_id}/{sid}` inside app container (or host)
  2) Mount that local path via `SANDBOX_VOLUMES` to `/workspace`
  3) On stop: sync back local → S3, resolve conflicts with last-write-wins (MVP)
- Credentials: AWS_* envs; path-style endpoint, custom endpoint
- Pros: No kernel fs; clear boundary for credentials
- Cons: Sync overhead, conflict risk

## S3 via s3fs (Advanced)
- Mount s3 directly in nested runtime (requires s3fs/goofys)
- Provide scoped credentials via env
- Pros: Live streaming access
- Cons: More deps, security hardening

## Caching and Metadata
- Store `case.json` in case root (local) or prefix (S3)
- Cache size_bytes and updated_at on close; recalc asynchronously for large cases

## MinIO Test Config
```
AWS_BUCKET=herd-bucket
AWS_ACCESS_KEY_ID=herd
AWS_USE_PATH_STYLE_ENDPOINT=true
AWS_SECRET_ACCESS_KEY=secretkey
AWS_DEFAULT_REGION=us-east-1
AWS_URL=https://minio.herd.test/herd-bucket
AWS_ENDPOINT=https://minio.herd.test
```
- Use MinIO dashboard to create `herd-bucket` and optional prefixes
- Ensure app can reach MinIO host from Docker network; if using TLS, trust certs or disable verify for testing

