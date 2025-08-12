# API Spec: Cases

Base: `/api`

## GET /cases
- Query: `q` (search), `page`, `page_size`, `storage` (local|s3)
- 200 OK: `{ items: Case[], total: number }`

Case
```
{
  id: string,
  name: string,
  description?: string,
  storage: { type: "local"|"s3", path?: string, bucket?: string, prefix?: string },
  created_at: string,
  updated_at: string,
  last_opened_at?: string,
  size_bytes?: number,
  tags?: string[]
}
```

## POST /cases
- Body: `{ name: string, description?: string, storage: { type: "local"|"s3", path?: string, bucket?: string, prefix?: string } }`
- 201 Created: `Case`

## GET /cases/{id}
- 200 OK: `Case`

## PATCH /cases/{id}
- Body: `{ name?, description?, tags? }`
- 200 OK: `Case`

## DELETE /cases/{id} (optional)
- 204 No Content

## POST /cases/{id}/conversations
- Creates a new conversation bound to case
- 201 Created: `{ conversation_id: string, status: "STARTING" }`

## Notes
- Security: single-tenant instance; all endpoints assume authenticated user
- Validation: ensure local path under CASES_BASE_PATH; S3 bucket/prefix exist
- Errors: 400 for invalid storage; 404 for missing case

