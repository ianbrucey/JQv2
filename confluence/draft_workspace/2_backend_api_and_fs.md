## Backend API and Filesystem Design – Draft Workspace

### Base
- Base path: /api/legal/cases/{case_id}/drafts
- All operations validated against the case’s workspace: /tmp/legal_workspace/cases/case-{case_id}/draft_system

### Endpoints
1) POST /create
- Body: { draft_type: string, name: string }
- Returns: { draft_id, name, type, sections: [{ id, name, file }] }
- Behavior: Creates active_drafts/{slug}/, writes manifest.json, seeds sections/* from templates

2) GET /
- List drafts
- Returns: [{ draft_id, name, type, updated_at }]

3) GET /{draft_id}
- Returns draft metadata + sections

4) POST /{draft_id}/rename
- Body: { name: string }
- Returns updated metadata
- Behavior: rename folder + update manifest

5) DELETE /{draft_id}
- Delete draft folder recursively

6) GET /{draft_id}/sections
- Returns ordered sections: [{ id, name, file }]

7) GET /{draft_id}/sections/{section_id}
- Returns: { content: string }

8) PUT /{draft_id}/sections/{section_id}
- Body: { content: string }
- Persist content, update manifest updated_at

9) POST /{draft_id}/sections
- Body: { name: string, after_section_id?: string }
- Creates new section, updates manifest

10) DELETE /{draft_id}/sections/{section_id}
- Removes file + manifest entry

11) GET /{draft_id}/preview
- Returns: { html: string }
- Server renders markdown → HTML (reuse preview generator)

### Filesystem layout
- draft_system/active_drafts/{draft-slug}/
  - manifest.json
  - sections/
    - 01_caption_and_title.md
    - 02_introduction.md
    - ...
    - attachments/ (optional)
  - preview.html (optional cached render)

manifest.json (example)
{
  "draft_id": "<uuid>",
  "name": "Complaint vs. XYZ",
  "type": "complaint",
  "created_at": "...",
  "updated_at": "...",
  "sections": [
    { "id": "caption-and-title", "name": "Caption and Title", "file": "sections/01_caption_and_title.md" },
    { "id": "introduction", "name": "Introduction", "file": "sections/02_introduction.md" }
  ]
}

### Templates by type
- Path: OpenHands/draft_system/templates/drafts/{type}/
  - sections.yml: ordered section names + ids
  - stubs/*.md: starter content for each section
- If template not found, fall back to a minimal generic set

### Validation + guards
- slugify draft name; enforce uniqueness within active_drafts/
- prevent path traversal; only operate within case draft_system
- return 400/404 with clear JSON details

### Errors
- 400: bad input (invalid type/name)
- 404: draft/section not found
- 409: name conflict on create/rename
- 500: unexpected IO errors (with safe messages)

