# Technical Implementation Plan

## Backend Tasks
1) CaseStore Abstraction
- Create `openhands/server/case_store/base.py` with interface: list(), get(id), create(name, desc, storage), update(id, ...)
- Implement `local.py` using os, read/write `case.json`
- Implement `s3.py` using existing S3 helpers; manage prefixes and `case.json`

2) API Endpoints
- `openhands/server/routes/cases.py`
  - GET /api/cases — list with pagination, filters
  - POST /api/cases — create case; returns metadata
  - GET /api/cases/{id} — fetch
  - PATCH /api/cases/{id} — update metadata
  - (Optional) DELETE /api/cases/{id}
  - POST /api/cases/{id}/conversations — create new conversation bound to case

3) Conversation Integration
- Extend existing POST /conversations to accept { case_id } or add dedicated route
- In `docker_nested_conversation_manager._create_runtime` derive `host_case_path` for case_id and set `SANDBOX_VOLUMES`
- For S3 (sync):
  - On start: sync S3 → local temp path
  - On stop: sync local → S3 (hook in session close)

4) Feature Flags
- Server config: `features.git_enabled=false`
- Guard repo/microagent bootstrap paths in `agent_session` and related modules

## Frontend Tasks
1) Routing & App Boot
- Add `/cases` route (landing)
- Redirect to `/cases` when no active case_id
- Store `last_case_id` in localStorage; preload if present

2) Pages & Components
- `pages/cases/index.tsx` — lists existing, create new CTA
- `components/cases/case-list.tsx` — search/sort/paginate
- `components/cases/case-card.tsx` — name, desc, modified, size, storage
- `components/cases/case-create-modal.tsx`

3) API Client
- Add Cases API to `frontend/src/api/open-hands.ts`
  - listCases, createCase, getCase, updateCase, openCase

4) Conversation Start
- On selecting a case: call POST /api/cases/{id}/conversations → navigate to `/conversations/{id}`
- Ensure conversation payload includes `case_id`

5) Hide Git
- Vite env: `VITE_FEATURE_GIT=false`
- Wrap Git/PR UI in feature flag checks

## DevOps/Config
- New env vars:
  - CASES_BASE_PATH (local)
  - FEATURE_GIT (bool)
  - FEATURE_S3 (bool), AWS_* for S3/MinIO
- Compose: ensure host case path accessible to app container (for sync) and to nested runtime via SANDBOX_VOLUMES

## Milestones
- M1: Local Case MVP (list/create/select; mount per-session)
- M2: S3 Sync (MinIO), test flows
- M3: Cleanup Git deps and polish UX
- M4: Advanced (s3fs mount option), performance tuning

