# Architecture and Design

## High-Level Design
- Introduce "Case" as a first-class resource; stored as directory (local) or prefix (S3) with `case.json`
- Add CaseStore abstraction with LocalCaseStore and S3CaseStore implementations
- Frontend adds Cases pages, create/select flows, sets active case_id
- Conversation creation/start receives case_id; conversation metadata records case_id
- Docker runtime receives per-session SANDBOX_VOLUMES mapping case path → `/workspace`
- Git features hidden via feature flag; repo-based microagents bypassed

## Data Model
- case.json
  - id, name, description, tags
  - storage: { type: "local"|"s3", path|bucket, prefix }
  - created_at, updated_at, last_opened_at
  - size_bytes (optional cached)

- conversation metadata (extended)
  - case_id (required)
  - case_name (denormalized)

## Sequence (Start Conversation)
1) Frontend POST /api/cases/{id}/conversations or POST /api/conversations with { case_id }
2) Backend validates case and derives host_case_path (local) or syncs from S3 to local temp path
3) Backend sets SANDBOX_VOLUMES to `${host_case_path}:/workspace:rw` for nested runtime
4) Runtime starts; agent operates within /workspace

## S3 Integration Strategies
- MVP: Sync approach (app container syncs S3→local on start; local→S3 on stop)
- Advanced: s3fs mount in nested runtime (additional dependencies/credentials)

## Feature Flags
- FEATURE_GIT (default false for case mode instances)
- FEATURE_S3 (enable S3 CaseStore)

## Error Handling
- Missing or inaccessible case path → 400/404 with guidance
- S3 sync failures → explicit errors/toasts; allow retry
- Switching case while a conversation active → confirmation dialog

