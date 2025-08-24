## Development Phases and Milestones – Draft Workspace

### Phase 0 – Planning and templates
- Finalize endpoint specs and manifest schema
- Define templates: templates/drafts/{type}/sections.yml + stubs/*.md
- Review compatibility with agent workflows and draft_system layout

### Phase 1 – Backend MVP (filesystem)
- Implement drafts routes: create/list/get/rename/delete; sections list/get/put; preview
- Filesystem operations within case draft_system/active_drafts
- Input validation and error responses
- Unit tests for creation/rename/delete & content IO

Milestones
- M1.1: Create/list drafts working
- M1.2: Sections read/write working
- M1.3: Preview returns rendered HTML

### Phase 2 – Frontend MVP
- New tab + empty state creation form
- Draft switcher + tabs for sections
- Markdown editor + preview with save

Milestones
- M2.1: Create first draft from UI
- M2.2: Edit and preview sections
- M2.3: Rename/delete flows with confirmations

### Phase 3 – Templates & UX polish
- Integrate type-specific stubs and previews
- Autosave + unsaved changes guard
- Loading/error states and toasts

### Phase 4 – Optional enhancements
- Section add/rename/delete in UI
- Attachments subfolder with uploads
- Search within draft sections
- Export to combined PDF/Word via existing generator

### Phase 5 – Agent enrichments (optional)
- Per-section “ask agent” actions (summarize/improve)
- Change tracking notes in manifest

### Risks & mitigations
- Name collisions → enforce slug + uniqueness
- Large files → lazy load, debounce saves
- Template drift → centralize templates and version them

