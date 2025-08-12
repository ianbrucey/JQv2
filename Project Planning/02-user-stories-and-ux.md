# User Stories and UX

## Primary Personas
- Case Worker: performs tasks within a case; starts/resumes conversations
- Admin/Operator: configures instance (storage, feature flags)

## User Stories
1. As a Case Worker, I need to select an existing case so I can resume work.
2. As a Case Worker, I need to create a new case so I can start work on new files.
3. As a Case Worker, when a case is selected, I want new conversations to use that case's files.
4. As an Admin, I want to disable Git features globally.
5. As a Case Worker, I want to view case details (last modified, size, description) to choose correctly.
6. As an Admin, I want to support S3-backed cases using MinIO.

## First Login Flow
- If no current case selected → redirect to Cases Landing
- "Select Existing" or "Create New"
- On selection/creation → start or resume conversation in that case

## Cases Landing Page (UX)
- Header: "Select a Case"
- Search + filters (storage type, tags)
- Sort by last modified desc
- List/Grid of Case Cards:
  - Name, description
  - Last modified
  - Size (cached)
  - Storage: Local path or S3 bucket/prefix
  - Actions: Open, Details

## Create Case Modal
- Fields: Name (required), Description (optional)
- Storage: Local (base path) or S3 (bucket/prefix)
- Initial Content: Empty | Upload files (optional for MVP)
- Submit → Create metadata and folder/prefix → Open case

## In-Case Experience
- Top bar shows current case; "Switch Case" button
- Files panel bound to /workspace
- "New Conversation" creates conversation tied to current case

## Wireframe (text)
- /cases: [Header][Search][Filters]
  - [Cards: Name | Description | Last Modified | Size | Storage | Open]
- Modal: [Name][Description][Storage: Local|S3][Create]
- Conversation: [Case Chip][Files panel][Chat]

