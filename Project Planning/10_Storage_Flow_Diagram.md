# Storage Flow Diagram: Multi‑Tenant Legal Case Management

Below is a mermaid diagram showing the end‑to‑end flow for uploads, metadata, caching, workspace preparation, AI access, and syncing to the authoritative store.

```mermaid
sequenceDiagram
  autonumber
  participant U as Browser (User)
  participant API as App API (FastAPI)
  participant R as Redis (Metadata Cache)
  participant DB as PostgreSQL (Metadata)
  participant OR as Object Storage (S3/Blob)
  participant WM as Workspace Manager (Compute Node)
  participant WS as Local SSD Workspace (/var/ai-workspaces)
  participant AG as OpenHands Agent (Container)

  Note over U,API: Case opened, user begins upload(s)
  U->>API: POST /api/cases/{caseId}/files (init upload)
  API->>DB: Begin txn: create pending file records
  API->>OR: Create pre‑signed upload URL(s)
  API-->>U: 200 + pre‑signed URL(s)

  U->>OR: PUT object(s) via pre‑signed URL (multipart ok)
  OR-->>U: 200 + ETag(s)
  U->>API: POST /api/cases/{caseId}/files/complete (ETag list)

  API->>OR: HEAD object(s) to verify size/hash
  API->>DB: Commit: mark files=uploaded, store content_hash/version
  API->>R: Invalidate cache: cache:manifest:{tenant}:{case}
  API-->>U: 201 Created (file records)

  Note over API,WM: Prepare workspace for AI
  API->>WM: Queue job: materialize case workspace
  WM->>DB: Read case manifest (+ file metadata)
  WM->>OR: Prefetch "hot" files (read‑through)
  WM->>WS: Create local tree + write files

  WM->>AG: Launch agent with mount
  AG->>WS: POSIX read/write during analysis

  Note over AG,WM: Conversion / derived artifacts
  AG->>WS: Create derived .md files
  WM->>OR: Sync new/changed files (If‑Match/ETag)
  WM->>DB: Txn: upsert file metadata (derived links)
  WM->>R: Invalidate cache: cache:manifest:{tenant}:{case}

  Note over U,API: User (or agent) requests file listing
  U->>API: GET /api/cases/{caseId}/files
  API->>R: GET cache:manifest:{tenant}:{case}
  R-->>API: Hit? manifest JSON (else miss)
  API->>DB: (on miss) query manifest
  API-->>U: JSON listing (logical tree)
```

Legend:
- Authoritative storage = Object Storage (versioned)
- Fast metadata = PostgreSQL + Redis cache
- AI execution = Local SSD workspace mounted into agent container
- Consistency = ETag/If‑Match + DB transactions + cache invalidation

