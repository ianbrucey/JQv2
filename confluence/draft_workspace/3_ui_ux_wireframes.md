## UI/UX Wireframes – Draft Workspace Tab

### Entry and layout
- Location: Conversation view → new tab "Drafts"
- Regions:
  - Top bar (inside tab): Draft switcher (dropdown), "Create Draft" button
  - Main area: Tabs for sections; editor + preview
  - Optional side panel: Sections outline or file browser (collapsible)

### Empty state (no drafts)
- Card with:
  - Draft Type dropdown (Complaint, Motion, Pleading, Demurrer, ...)
  - Draft Name input
  - Create button
- After create: stay on Drafts tab, load its sections, select first tab

### Draft selector
- Dropdown listing: name (type) • updated_at
- Actions menu: Rename, Delete (confirm)

### Section tabs
- Shown as horizontal tabs in order from manifest
- Tabs include add [+] menu to insert new section after current
- Tab context menu: Rename section, Delete section

### Editor + Preview
- Split view (stacked on narrow screens)
- Editor: markdown textarea with toolbar (bold, italic, heading, list, link)
- Preview: live markdown render (same renderer used elsewhere)
- Save: explicit Save button + Ctrl/Cmd+S with debounce
- Status: "Saved at HH:MM" or "Unsaved changes" indicator

### Error/edge cases
- Show non-blocking toasts for save errors
- Confirmations for delete operations
- Disabled actions when no draft selected

### Accessibility
- Keyboard focus order supports tabs and editor
- ARIA labels for controls and tabs

### Navigation details
- Route stays inside conversation: /conversations/{conversationId}/drafts
- Encode selected draft/section in query params (e.g., ?draft=...&section=...)
- Keep URL in sync on section tab switch for deep linking

