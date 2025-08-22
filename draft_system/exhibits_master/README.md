# Master Exhibits Folder

## Purpose
This folder contains exhibits and supporting documents that don't belong to a specific active draft but are relevant to the overall case.

## Exhibit Management System
Each exhibit follows a standardized three-file structure:

### Three-File System
For each exhibit (e.g., "Exhibit A"):
1. **Original File**: `exhibit_a_original.[ext]` - The original document (PDF, image, etc.)
2. **Parsed Text**: `exhibit_a_text.txt` - Extracted/parsed text version
3. **Summary**: `exhibit_a_summary.md` - Description and analysis

## Naming Convention
- Use lowercase letters for exhibit designations
- Format: `exhibit_[letter]_[description]_[type].[ext]`
- Examples:
  - `exhibit_a_contract_original.pdf`
  - `exhibit_a_contract_text.txt`
  - `exhibit_a_contract_summary.md`

## Document Processing Workflow
1. **Upload Original**: Place original document with `_original` suffix
2. **Extract Text**: Create `_text.txt` file with extracted content
3. **Create Summary**: Write `_summary.md` file with description and analysis

### Text Extraction Methods
- **Primary**: PDF-to-text extraction for text-based PDFs
- **Fallback**: Tesseract OCR for scanned documents or images
- **Manual**: Manual transcription for complex or poor-quality documents

## Summary File Template
Each `_summary.md` file should contain:
```markdown
# Exhibit [Letter] - [Description]

## Document Information
- **Original Filename**: [filename]
- **Document Type**: [type]
- **Date Created**: [date]
- **Source**: [where obtained]

## Content Summary
[Brief description of document contents]

## Legal Relevance
[How this exhibit relates to the case]

## Key Points
- [Important point 1]
- [Important point 2]
- [Important point 3]

## Cross-References
- Related to: [other exhibits or documents]
- Supports: [legal arguments or claims]
```

## Usage Instructions
1. Process all documents through the three-file system
2. Maintain consistent naming conventions
3. Update exhibit lists in case documentation
4. Cross-reference exhibits with legal arguments
5. Ensure all exhibits are properly authenticated for court use
