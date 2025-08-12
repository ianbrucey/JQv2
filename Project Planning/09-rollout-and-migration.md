# Rollout and Migration Plan

## Phases
- Phase 1: Local Case MVP
  - Implement CaseStore (local), /api/cases, frontend cases UI
  - Integrate case_id with conversations and mounts
  - Hide Git features
- Phase 2: S3 Sync
  - Implement S3 CaseStore and sync logic
  - Configure MinIO and validate flows
- Phase 3: Hardening and UX polish
  - Error handling, retries, file browser improvements
- Phase 4: Optional s3fs mount, performance tuning

## Migration From Git-Repo Mode
- Default FEATURE_GIT=false for new instances
- For existing environments, leave Git code paths available but disabled
- Communicate deprecation of repo-centric flows in instance notes

## Backout Plan
- Re-enable Git flows by setting FEATURE_GIT=true
- Cases remain available; conversations can be tied to cases or repos if desired in hybrid modes (future)

