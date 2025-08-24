## Draft Workspace Tab – Overview and Technical Architecture

### Purpose and goals
- Provide a first‑class tab within the conversation view so users can talk to the agent and see draft updates live
- Keep full compatibility with existing agent workflows and draft_system folder layout
- Ensure drafts are file‑backed markdown artifacts living under each case’s draft_system/active_drafts

### Key user flows
- Empty state: Select draft type (Complaint, Motion, Pleading, Demurrer, etc.) + enter custom name → backend generates structure and stub content
- Ongoing editing: Tabbed sections for the draft, markdown editor with live preview, autosave
- Management: Switch drafts, rename, add/remove sections, delete with confirmation

### High‑level architecture
- Frontend (React/Vite):
  - New tab inside the conversation route (e.g., /conversations/{conversationId}/drafts)
  - Panels: Draft selector, creation form (empty state), tabbed section editor + preview
  - Live updates: subscribe to file changes or poll to reflect agent edits in near real-time
- Backend (FastAPI under /api/legal):
  - Drafts endpoints under /api/legal/cases/{case_id}/drafts (no change)
  - Conversation→case resolution via case metadata on the conversation (case_id lookup)
- Storage (filesystem):
  - Case workspace path: /tmp/legal_workspace/cases/case-{id}/draft_system
  - Drafts root: active_drafts/{draft-slug}/
  - manifest.json + sections/*.md
  - Type templates under OpenHands/draft_system/templates/drafts/{type}/

### Routing
- Drafts tab URL scheme (no separate page):
  - /conversations/{conversationId}/drafts → index
  - Optionally encode selected draft/section in query params
- Backend continues using /api/legal/cases/{case_id}/drafts endpoints

### Non-goals
- No DB is required for MVP (filesystem + manifest.json is source of truth)
- No AI required to generate the initial scaffold (pure templates + stubs)

### Compatibility principles
- Preserve draft_system structure and naming rules
- Draft content are plain .md files (agent scripts already handle these)
- No reliance on draft_agent; only draft_system

### Security and safety
- Sanitize names (slugify), prevent traversal
- Never write outside the case’s draft_system
- Confirm destructive operations (UI) and guard with server‑side checks

### Performance
- Tab-level code splitting (load editor only when Drafts tab is active)
- Lazy load draft sections; debounced autosave; batch writes

### Observability
- Structured logs: draft lifecycle (created, renamed, deleted), section save events
- Optional preview errors surfaced to UI

