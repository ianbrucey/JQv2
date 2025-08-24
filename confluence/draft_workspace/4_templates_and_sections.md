## Draft Types, Sections, and Templates

### Complaint
Default sections (templates/drafts/complaint/sections.yml):
- caption-and-title: Caption and Title
- introduction: Introduction
- factual-allegations: Factual Allegations
- parties: Parties
- causes-of-action: Causes of Action
- prayer-for-relief: Prayer for Relief
- verification: Verification (optional)
- signature: Signature

### Motion
Default sections (templates/drafts/motion/sections.yml):
- caption-and-title: Caption and Title
- introduction: Introduction
- legal-standard: Legal Standard
- argument: Argument
- conclusion: Conclusion
- proposed-order: Proposed Order (optional)

### Pleading (generic)
- caption-and-title
- introduction
- allegations
- claims-or-defenses
- relief-requested
- conclusion

### Demurrer
- caption-and-title
- introduction
- grounds-for-demurrer
- argument
- conclusion
- prayer-for-relief

### Templates structure
- OpenHands/draft_system/templates/drafts/{type}/
  - sections.yml (ordered canonical list)
  - stubs/
    - {id}.md (starter content)

### Starter content conventions
- Front matter (optional): title, section id, draft type
- H1 title mirrors display name
- Placeholder paragraphs guide the user

### Fallbacks
- If type template missing: use a minimal default set
- If stub missing: create empty file with H1 section title

