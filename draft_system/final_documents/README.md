# Final Documents Folder

## Purpose
This folder contains the final, court-ready PDF and Word documents generated from the draft system.

## File Naming Convention
All final documents use timestamped naming to prevent overwrites:
- **Format**: `{document_type}_{name}_{YYYYMMDD_HHMMSS}.{pdf,docx}`
- **Examples**:
  - `complaint_contract_dispute_20241215_143022.pdf`
  - `motion_summary_judgment_20241215_143022.docx`

## Document Types
- **PDF**: Browser-based generation for perfect formatting
- **Word**: Full caption, proper tables, Times New Roman, 1-inch margins
- **Consistent**: All formats match HTML preview exactly

## Generation Process
Use the final document generator:
```bash
# Generate both PDF and Word documents
python scripts/generate_final_document.py active_drafts/document_folder/ both

# Generate specific formats
python scripts/generate_final_document.py active_drafts/document_folder/ pdf
python scripts/generate_final_document.py active_drafts/document_folder/ docx
```

## Quality Standards
- **Professional Formatting**: Court-ready appearance
- **Legal Standards**: Proper margins, fonts, spacing
- **Cross-References**: All references resolve correctly
- **Validation**: Documents pass format validation
- **Consistency**: Output matches HTML preview exactly

## File Management
- **Timestamped**: Files never overwrite previous versions
- **Preserved**: All generated documents are kept for record
- **Organized**: Easy to identify latest versions by timestamp
- **Backup**: Maintains history of document revisions

## Court Readiness
All final documents meet standard court requirements:
- Times New Roman 14-point font
- 1-inch margins on all sides
- Double-spaced text
- Proper legal formatting
- Professional appearance
- Correct pagination

## Usage Instructions
1. Validate and fix document formatting first
2. Generate HTML preview for review
3. Generate final documents when ready
4. Use timestamped files for filing or service
5. Keep all versions for audit trail
