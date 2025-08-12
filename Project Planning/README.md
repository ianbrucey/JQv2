# Project Planning: Case Folder Selection Workflow

This folder contains planning documentation for adapting OpenHands to a one-customer-per-instance model that operates on filesystem-backed "cases" rather than GitHub repositories.

Contents:
- 01-vision-and-scope.md — Business context, goals, constraints
- 02-user-stories-and-ux.md — User stories, flows, UX wireframes (text)
- 03-architecture-and-design.md — System design, components, decisions
- 04-technical-implementation-plan.md — Backend and frontend plans broken into tasks
- 05-api-spec-cases.md — API design for /api/cases and related
- 06-storage-strategy.md — Local filesystem vs S3 (MinIO) strategy, sync
- 07-feature-flags-and-github-bypass.md — Strategy to disable Git features cleanly
- 08-test-environment-config.md — MinIO and local testing guidance
- 09-rollout-and-migration.md — Phased rollout and migration planning
- 10-risks-and-mitigations.md — Risks, assumptions, mitigations

Use these documents to guide planning and implementation. No code changes are included at this stage.

