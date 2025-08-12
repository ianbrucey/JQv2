# Vision and Scope

## Vision
Transform OpenHands to operate on a per-customer, per-instance basis using "case folders" (filesystem directories or S3 prefixes) instead of GitHub repositories. Each conversation operates against exactly one selected case, improving data isolation, compliance, and operational simplicity.

## Goals
- Provide a clear case selection/creation workflow at first use and when switching cases
- Associate each conversation with a single case, mounted at /workspace
- Support local filesystem and S3-backed (MinIO) storage for cases
- Remove/bypass GitHub repo assumptions in UI and backend paths
- Keep changes modular, feature-flagged, and reversible

## Out of Scope (for MVP)
- Real-time multi-user collaboration inside a single case
- Git-backed PR workflows and repo-based microagents
- Advanced permissioning or case-level RBAC

## Constraints
- One-customer-per-instance
- Planning phase only: no code changes yet
- Prefer minimal invasive changes and feature flags

## Success Criteria
- Users can select or create a case on first login
- Conversations run with a mounted case folder as workspace
- UI hides Git/PR features cleanly
- Documentation sufficient to implement with low ambiguity

