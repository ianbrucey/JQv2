# Legal Document Generation System

## Overview

This system provides a standardized, reliable method for generating consistently formatted legal documents using AI assistance. It separates content creation from document formatting, ensuring high-quality legal writing with perfect formatting every time.

## System Architecture

### Enhanced Multi-Path Workflow

The system now supports multiple workflow options for different use cases:

#### **Path A: HTML-First Workflow (NEW)**
**Phase 1: Content Generation**
- AI focuses exclusively on legal content quality
- Generates Markdown files for document sections
- No consideration of formatting or structure

**Phase 2: HTML Preview & Generation**
- AI or automated system populates HTML templates
- Instant browser preview for review and editing
- Direct HTML → PDF conversion for court filing

#### **Path B: YAML-First Workflow (EXISTING)**
**Phase 1: Content Generation**
- AI focuses exclusively on legal content quality
- Generates Markdown files for document sections

**Phase 2: Structural Transformation**
- AI populates pre-defined YAML templates
- Transfers approved content to structured format
- Python script converts YAML to formatted Word document

#### **Path C: Hybrid Preview Workflow (RECOMMENDED)**
**Phase 1: Content Generation**
- Create high-quality Markdown content

**Phase 2A: HTML Preview**
- Generate HTML preview for immediate review
- Validate formatting and cross-references
- Make content adjustments as needed

**Phase 2B: Final Generation**
- Use YAML system for Word documents
- Use HTML system for PDF documents
- Choose format based on court requirements

## Complete Workflow Process

### **PHASE 1: Content Creation (Markdown)**
**Objective**: Create high-quality legal content without formatting concerns

**User Request Format**:
```
"Let's work on Phase 1 - content creation for [document type].
Focus on the legal arguments without worrying about formatting."
```

**AI Actions**:
1. Generate separate Markdown files for each section
2. Follow Markdown standards from `.augment_guidelines`
3. Focus on legal substance and accuracy
4. Use proper header hierarchy and legal citations

**Output**: Multiple `.md` files following standardized naming (see Folder Structure section)

---

### **PHASE 2: YAML Population (Single Complete File)**
**Objective**: Transfer all content into one complete, structured YAML file

**User Request Format**:
```
"Now let's move to Phase 2. Please create a complete YAML file using
[template_name] and populate it with content from ALL our Markdown files."
```

**AI Actions**:
1. Read ALL existing Markdown files in the project
2. Select appropriate starter template (`complaint_starter.yml`, `motion_starter.yml`, etc.)
3. Populate ONE complete YAML file with all sections
4. Add proper cross-reference labels (`{{LABEL:name}}`)
5. Include all required sections: caption, body, prayer, signature, certificate

**Critical Requirements**:
- ✅ **Single File Output**: One complete YAML file, not separate section files
- ✅ **All Sections Included**: Every part of the document in one file
- ✅ **Cross-Reference Labels**: Proper `{{LABEL:start}}` and `{{REF_RANGE:start:end}}` syntax
- ✅ **Complete Metadata**: All caption, signature, and certificate information

**Output**: One complete `.yml` file ready for document generation

---

### **PHASE 3: Document Generation (Enhanced)**

#### **Option A: HTML → PDF Generation (NEW)**
**Objective**: Convert HTML preview to court-ready PDF

**User Actions**:
```bash
# Install dependencies (one-time setup)
pip install -r draft_system/requirements.txt

# Generate HTML preview from standardized folder
python scripts/complaint_processor.py active_drafts/complaint_case_name/

# Generate PDF from HTML
python scripts/html_to_pdf.py convert complaint_preview.html complaint.pdf
```

**Output**: Court-ready `.pdf` file with perfect formatting

#### **Option B: YAML → Word Generation (EXISTING)**
**Objective**: Convert YAML to professionally formatted Word document

**User Actions**:
```bash
# Generate document
cd draft_system/scripts
python generate_legal_document.py ../active_drafts/complaint_case_name/complaint.yml final_complaint.docx
```

**Output**: Court-ready `.docx` file

#### **Option C: HTML → Word Generation (FUTURE)**
**Objective**: Convert HTML templates to Word documents

**Planned Features**:
- HTML template → Word conversion
- Maintain all formatting standards
- Alternative to YAML-based generation

---

## Quality Assurance Checklist

### **Phase 1 Validation**
- [ ] All required sections have Markdown files
- [ ] Headers follow hierarchy standards (H1 → H2 → H3)
- [ ] Legal citations are properly formatted
- [ ] Content is substantively complete

### **Phase 2 Validation**
- [ ] Single complete YAML file created
- [ ] All Markdown content transferred
- [ ] Cross-reference labels added (`{{LABEL:name}}`)
- [ ] YAML syntax is valid
- [ ] All required sections present

### **Phase 3 Validation**
- [ ] Word document generates without errors
- [ ] Cross-references resolve correctly
- [ ] Formatting meets legal standards
- [ ] All sections appear in proper order
- [ ] Document is court-ready

---

## Error Prevention

### **Common Mistakes to Avoid**
1. **Multiple YAML Files**: Don't create separate YAML files for each section
2. **Missing Cross-References**: Ensure labels and references are properly added
3. **Incomplete Sections**: Include ALL document parts in the single YAML file
4. **YAML Syntax Errors**: Validate indentation and quotes
5. **Missing Dependencies**: Install required Python packages

### **Validation Commands**
```bash
# Test YAML syntax
python -c "import yaml; yaml.safe_load(open('active_drafts/complaint_case_name/complaint.yml'))"

# Test document generation
python generate_legal_document.py active_drafts/complaint_case_name/complaint.yml test_output.docx

# Test HTML preview generation
python scripts/complaint_processor.py active_drafts/complaint_case_name/
```

## YAML Syntax Guide

### Basic Content
```yaml
- type: 'paragraph'
  data: "This is a standard paragraph."
```

### Multi-line Paragraphs
```yaml
- type: 'paragraph'
  data: >
    This is a long paragraph that spans
    multiple lines but renders as a single
    paragraph in the final document.
```

### Lists
```yaml
- type: 'list'
  data:
    style: 'numbered'  # or 'bullet', 'lettered'
    items:
      - "First item"
      - "Second item"
      - "Third item"
```

### Formatting Within Text
```yaml
- type: 'paragraph'
  data: "Pursuant to **O.C.G.A. § 9-11-55(b)**, the *defendant* must respond."
```

### Cross-References
```yaml
# Create labels (invisible in final document)
- type: 'paragraph'
  data: '{{LABEL:facts_start}}This is the first fact paragraph.'

- type: 'paragraph'
  data: 'This is the last fact paragraph.{{LABEL:facts_end}}'

# Reference the labeled range
- type: 'paragraph'
  data: 'Plaintiff realleges paragraphs {{REF_RANGE:facts_start:facts_end}}.'
```

## Document Types

### Complaints/Pleadings
- Numbered paragraphs throughout
- Standard sections: Parties, Jurisdiction, Facts, Counts, Prayer
- Cross-references between sections

### Motions
- Unnumbered paragraphs (typically)
- Standard sections: Introduction, Facts, Legal Standard, Argument, Conclusion
- Lettered sub-arguments (A, B, C)

### Discovery Documents
- Numbered requests/interrogatories
- Standard sections: Instructions, Definitions, Requests
- Detailed definitions section

### Affidavits
- Numbered paragraphs
- Personal knowledge statements
- Notarization block

### Briefs
- Complex heading hierarchy (I, A, 1, a)
- Table of contents and authorities (auto-generated)
- Statement of issues, facts, argument, conclusion

## Best Practices

### Content Creation (Phase 1)
1. Focus solely on legal substance and arguments
2. Don't worry about paragraph numbers or formatting
3. Create comprehensive, well-researched content
4. Use clear, professional legal writing

### Structure Population (Phase 2)
1. Use the exact starter template structure
2. Don't modify template sections or hierarchy
3. Follow YAML syntax precisely
4. Include all required labels and references

### Quality Control
1. Validate YAML syntax before processing
2. Ensure all cross-references are properly labeled
3. Verify all required sections are populated
4. Check that formatting markup is correct

## Troubleshooting

### Common Issues
- **Invalid YAML**: Check indentation and syntax
- **Missing cross-references**: Ensure labels match references exactly
- **Formatting errors**: Verify Markdown syntax within YAML strings
- **Missing sections**: Check template requirements

### Validation
Each template includes validation rules:
```yaml
validation:
  required_sections:
    - "INTRODUCTION"
    - "LEGAL STANDARD"
  max_heading_levels: 3
```

## Standardized Folder Structure and Naming Conventions

### **Active Drafts Organization**

The `active_drafts/` folder contains all documents currently being worked on or planned for work, organized according to standardized conventions to ensure consistency, scalability, and multi-tenant compatibility.

#### **Document Folder Naming Convention**
```
Format: {document_type}_{document_name}
```

**Document Types:**
- `complaint` - Initial pleadings and complaints
- `response_to_complaint` - Answers, motions to dismiss, etc.
- `motion` - All types of motions (compel, summary judgment, etc.)
- `interrogatories` - Discovery interrogatories
- `requests_for_production` - Document production requests
- `requests_for_admission` - Admission requests
- `affidavit` - Sworn statements and affidavits
- `brief` - Legal briefs and memoranda
- `discovery` - General discovery documents
- `settlement` - Settlement agreements and negotiations
- `appeal` - Appellate documents

**Document Name Guidelines:**
- Use underscores or dashes to connect words
- Keep names descriptive but concise
- Include case-specific identifiers when helpful

**Examples:**
```
complaint_hilton_timeshare
motion_compel_discovery
interrogatories_first_set
brief_summary_judgment
affidavit_damages_expert
response_to_complaint_hilton
```

#### **Required Subfolder Structure**

Each document folder must contain the following standardized subfolders:

```
{document_type}_{document_name}/
├── draft_content/              # Primary markdown files for document generation
├── research/                   # Legal research and analysis
├── exhibits/                   # Document exhibits and supporting materials
├── reference_material/         # Additional reference documents
├── case_documents/            # Filed motions, orders, and docket documents
└── metadata.yml               # Document metadata and configuration
```

**Subfolder Purposes:**

- **`draft_content/`**: Contains the actual markdown files used for document generation
- **`research/`**: Legal research, case law analysis, statutory research
- **`exhibits/`**: Supporting documents, evidence, contracts, correspondence
- **`reference_material/`**: Background materials, similar cases, templates
- **`case_documents/`**: Filed documents, court orders, opposing party filings
- **`metadata.yml`**: Document configuration, court information, party details

#### **Draft Content Template Files**

The `draft_content/` folder contains standardized markdown files with consistent naming:

**For Complaints and Pleadings:**
```
01_caption_and_parties.md       # Court caption and party information
02_jurisdiction_and_venue.md    # Jurisdictional allegations
03_factual_allegations.md       # Statement of facts
04_count_i_[claim_type].md      # First cause of action
05_count_ii_[claim_type].md     # Second cause of action
06_count_iii_[claim_type].md    # Additional causes of action
07_prayer_for_relief.md         # Relief requested
08_jury_demand.md               # Jury trial demand (if applicable)
```

**For Motions:**
```
01_caption_and_title.md         # Court caption and motion title
02_introduction.md              # Motion introduction
03_statement_of_facts.md        # Factual background
04_legal_standard.md            # Applicable legal standard
05_argument.md                  # Legal argument
06_conclusion.md                # Conclusion and prayer for relief
```

**For Discovery Documents:**
```
01_caption_and_title.md         # Court caption and document title
02_instructions.md              # General instructions
03_definitions.md               # Definitions section
04_requests.md                  # Actual requests/interrogatories
```

**For Briefs:**
```
01_caption_and_title.md         # Court caption and brief title
02_table_of_contents.md         # Table of contents (auto-generated)
03_table_of_authorities.md      # Table of authorities (auto-generated)
04_statement_of_issues.md       # Issues presented
05_statement_of_facts.md        # Statement of facts
06_argument.md                  # Legal argument
07_conclusion.md                # Conclusion
```

### **Global Case Resources Structure**

Resources that apply to the entire case should be organized outside individual document folders:

```
case_resources/
├── court_rules/               # Local court rules and procedures
├── case_law/                  # Relevant case law and precedents
├── statutes/                  # Applicable statutes and regulations
├── expert_reports/            # Expert witness reports and materials
├── discovery_materials/       # Master discovery index and materials
├── settlement_communications/ # Settlement negotiations and offers
└── case_timeline.md          # Chronological case timeline
```

### **Clean File Structure**
```
draft_system/
├── .augment_guidelines          # AI behavior guidelines (unified standards)
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── active_drafts/              # All active document work
│   └── complaint_01/           # Example: Hilton timeshare complaint
│       ├── draft_content/      # Markdown files (01_, 02_, etc.)
│       ├── research/           # Legal research and analysis
│       ├── exhibits/           # Supporting documents and evidence
│       ├── reference_material/ # Background materials and templates
│       ├── case_documents/     # Filed documents and court orders
│       └── metadata.yml        # Document configuration
├── standards/                  # Unified formatting standards
│   ├── markdown_formatting_guide.md
│   ├── validation_rules.yml
│   └── document_type_specifications.yml
├── schema/
│   └── master_schema.yml       # Universal YAML schema
├── templates/
│   ├── yaml/                   # YAML templates for Word generation
│   │   ├── complaint_starter.yml
│   │   ├── motion_starter.yml
│   │   └── discovery_starter.yml
│   ├── html/                   # HTML templates for preview/PDF
│   │   ├── complaint.html
│   │   └── motion.html
│   └── Case_Summary_and_Timeline_Template.md  # Case tracking template
├── scripts/                    # Core processing tools
│   ├── universal_markdown_parser.py     # Unified parser for all documents
│   ├── universal_preview_generator.py   # Universal HTML preview generator
│   ├── generate_final_document.py       # Final PDF/Word document generator
│   ├── format_validator.py              # Validation against standards
│   ├── format_fixer.py                 # Automatic formatting fixes
│   ├── complaint_processor.py           # Complaint-specific HTML generator
│   ├── html_to_pdf.py                  # HTML to PDF conversion
│   └── generate_legal_document.py       # YAML to Word converter
├── html_preview/               # Standardized preview output
│   └── draft-preview.html      # Single preview file for all documents
├── final_documents/            # Generated final documents
│   ├── complaint_name_timestamp.pdf     # PDF documents with timestamps
│   └── complaint_name_timestamp.docx    # Word documents with timestamps
└── venv/                       # Python virtual environment
```

### **Case Management Structure**
For complete case management, organize each case with this structure:

```
case_name/
├── Intake/                     # Preliminary documents and user information
│   ├── initial_request.md      # User's initial description/request
│   ├── background_info.md      # Background information provided
│   ├── preliminary_docs/       # Any initial documents from user
│   └── intake_notes.md         # Notes from initial consultation
├── Case_Summary_and_Timeline.md # Living document tracking entire case
├── complaint_document_name/     # Individual document folders
├── motion_document_name/        # Individual document folders
└── discovery_document_name/     # Individual document folders
```

#### **Intake Folder Purpose**
The `Intake/` folder serves as the collection point for all preliminary case information:
- **Initial User Requests**: What the user wants to accomplish
- **Background Information**: Context and history provided by user
- **Preliminary Documents**: Any existing documents user provides
- **Intake Notes**: Questions, clarifications, and initial analysis

#### **Case Summary and Timeline**
The `Case_Summary_and_Timeline.md` file serves as the central reference point for the entire case:
- **Case Overview**: Basic case information and current status
- **Key Parties**: All parties and their contact information
- **Timeline**: Chronological record of all case events
- **Next Steps**: Current action items and deadlines
- **Legal Issues**: Summary of claims, defenses, and key legal questions
- **Agent Context**: Important notes for AI agents to understand case context

**Purpose**: Allows agents to quickly understand the entire case context without needing to pull information from multiple files.

### **Metadata Configuration**

Each document folder includes a `metadata.yml` file containing:

```yaml
document_info:
  type: "complaint"
  name: "hilton_timeshare"
  title: "Complaint for Damages"
  status: "draft"  # draft, review, final, filed
  created_date: "2024-12-01"
  last_modified: "2024-12-15"

court_info:
  court_name: "District Court of Clark County"
  jurisdiction: "State of Nevada"
  case_number: "[TO BE ASSIGNED]"
  judge: ""

parties:
  plaintiff:
    name: "Ian Bruce"
    role: "Pro Se"
    address: "7219 Laurel Creek Dr., Stockbridge, GA 30281"
    phone: "(404) 555-1212"
    email: "ib708090@gmail.com"
  defendants:
    - name: "Hilton Resorts Corporation"
      type: "corporation"
      state: "Delaware"
    - name: "Hilton Grand Vacations Inc."
      type: "corporation"
      state: "Delaware"

workflow:
  current_phase: "content_creation"  # content_creation, review, formatting, filing
  target_format: "pdf"  # html, pdf, word
  cross_references: true

generation_options:
  numbered_paragraphs: true
  double_spaced: true
  font_family: "Times New Roman"
  font_size: 14
  margins: "1 inch"
```

### **Organizational Rules and Best Practices**

#### **File Naming Conventions**

1. **Markdown Files**: Use numbered prefixes for proper ordering
   - Format: `##_descriptive_name.md`
   - Example: `01_caption_and_parties.md`

2. **Research Files**: Include date and topic
   - Format: `YYYY-MM-DD_topic.md`
   - Example: `2024-12-01_trid_violations.md`

3. **Exhibit Files**: Use exhibit numbers or letters
   - Format: `exhibit_[number]_description.pdf`
   - Example: `exhibit_a_purchase_agreement.pdf`

4. **Case Documents**: Include filing date and document type
   - Format: `YYYY-MM-DD_document_type.pdf`
   - Example: `2024-11-15_motion_to_dismiss.pdf`

#### **Version Control Guidelines**

1. **Draft Versions**: Use semantic versioning in metadata
   - `v1.0` - Initial draft
   - `v1.1` - Minor revisions
   - `v2.0` - Major restructuring

2. **Backup Strategy**: Maintain previous versions in `archive/` subfolder

3. **Change Tracking**: Document significant changes in `CHANGELOG.md`

#### **Multi-Tenant Considerations**

1. **Case Isolation**: Each case should have its own `draft_system/` instance
2. **Template Sharing**: Common templates can be shared across cases
3. **User Permissions**: Implement folder-level access controls
4. **Audit Trail**: Track document access and modifications

#### **Automation Rules**

1. **Auto-Generation**: New document folders should auto-create required subfolders
2. **Template Population**: Automatically populate metadata.yml with defaults
3. **Cross-Reference Validation**: Verify all references resolve correctly
4. **Format Consistency**: Enforce naming conventions through validation scripts

#### **Quality Assurance Standards**

1. **Required Files**: Each document must have complete draft_content files
2. **Metadata Validation**: Ensure all required metadata fields are populated
3. **Cross-Reference Integrity**: Verify all `{{LABEL:}}` and `{{REF:}}` tags resolve
4. **Format Compliance**: Ensure generated documents meet court formatting requirements

#### **Scalability Features**

1. **Modular Design**: Each document type has independent processing logic
2. **Template Extensibility**: Easy to add new document types and templates
3. **Plugin Architecture**: Support for custom processing modules
4. **Batch Processing**: Ability to process multiple documents simultaneously

## HTML-Based Document System (NEW)

### Quick Start with HTML System

#### 1. Generate Sample Preview
```bash
python demo_html_system.py
```
This creates a sample motion preview and opens it in your browser.

#### 2. Preview from Document Folder
```bash
python scripts/complaint_processor.py active_drafts/complaint_case_name/
```

#### 3. Generate PDF from Document Folder
```bash
# First generate HTML preview, then convert to PDF
python scripts/complaint_processor.py active_drafts/complaint_case_name/
python scripts/html_to_pdf.py convert complaint_preview.html case_complaint.pdf
```

### HTML System Benefits

1. **Instant Preview**: See formatted documents immediately in browser
2. **Perfect Formatting**: CSS ensures exact legal document standards
3. **Cross-Reference Compatibility**: Works with existing `{{LABEL:}}` system
4. **Multi-Format Output**: Generate HTML, PDF, and Word documents
5. **Print-Ready**: Browser print function produces court-ready documents
6. **Template-Based**: Easy to customize for different document types

### HTML Template Features

- **Legal Caption Structure**: Split table with proper court formatting
- **Professional Typography**: Times New Roman, 14pt, double-spaced
- **Exact Margins**: 1-inch margins enforced via CSS `@page` rules
- **Page Numbering**: Automatic page numbers for print/PDF
- **Cross-References**: Dynamic paragraph reference resolution
- **Signature Blocks**: Properly formatted signature and certificate sections

### Dependencies for HTML System

```bash
# Core HTML template engine
pip install jinja2

# PDF generation (choose one)
pip install weasyprint          # Recommended for legal documents
pip install playwright          # Alternative option

# Install all dependencies
pip install -r requirements.txt
```

### **Additional Recommendations for Framework Improvement**

#### **Security and Access Control**
1. **Document Encryption**: Sensitive case materials should be encrypted at rest
2. **Access Logging**: Track who accesses which documents and when
3. **Permission Levels**: Implement role-based access (attorney, paralegal, client)
4. **Secure Sharing**: Encrypted sharing mechanisms for external collaboration

#### **Integration Capabilities**
1. **Case Management Systems**: Integration with popular legal case management software
2. **Court Filing Systems**: Direct integration with electronic filing systems
3. **Document Management**: Integration with legal document management platforms
4. **Time Tracking**: Automatic time tracking for document work

#### **Advanced Features**
1. **AI-Powered Suggestions**: Intelligent content suggestions based on document type
2. **Citation Validation**: Automatic verification of legal citations
3. **Conflict Checking**: Automated conflict of interest checking
4. **Deadline Management**: Integration with court deadlines and calendar systems

#### **Collaboration Features**
1. **Real-Time Editing**: Multiple users editing documents simultaneously
2. **Comment System**: Inline comments and review workflows
3. **Approval Workflows**: Structured review and approval processes
4. **Version Comparison**: Visual diff tools for document versions

#### **Reporting and Analytics**
1. **Document Statistics**: Track document creation, modification, and filing metrics
2. **Workflow Analytics**: Identify bottlenecks in document preparation
3. **Quality Metrics**: Track formatting compliance and error rates
4. **Time Analysis**: Analyze time spent on different document types

#### **Mobile and Cloud Support**
1. **Mobile Access**: Responsive design for tablet and phone access
2. **Cloud Synchronization**: Automatic backup and synchronization
3. **Offline Capability**: Work on documents without internet connection
4. **Cross-Platform**: Support for Windows, Mac, and Linux environments

#### **Compliance and Standards**
1. **Court Rule Compliance**: Automatic checking against local court rules
2. **Accessibility Standards**: Ensure documents meet ADA compliance requirements
3. **Professional Standards**: Adherence to legal profession formatting standards
4. **Audit Trails**: Complete audit trails for regulatory compliance

#### **Performance and Scalability**
1. **Large Document Handling**: Efficient processing of complex, multi-hundred-page documents
2. **Batch Operations**: Process multiple documents simultaneously
3. **Caching Systems**: Intelligent caching for faster document generation
4. **Load Balancing**: Support for high-volume, multi-user environments

## Support

For issues or questions:
1. Check this README for syntax and workflow guidance
2. Run `python demo_html_system.py check` to verify dependencies
3. Review the html_integration_plan.md for technical details
4. Verify YAML syntax using online validators (for YAML workflow)
5. Review the .augment_guidelines for AI behavior rules

## Unified Standards Implementation

### **New Tools Available**

#### **Format Validation**
```bash
# Validate document formatting
python scripts/format_validator.py active_drafts/complaint_case_name/ standard

# Validation levels: strict, standard, lenient
python scripts/format_validator.py active_drafts/complaint_case_name/ strict
```

#### **Automatic Format Fixing**
```bash
# Fix common formatting issues automatically
python scripts/format_fixer.py active_drafts/complaint_case_name/

# Then validate to verify fixes
python scripts/format_validator.py active_drafts/complaint_case_name/ standard
```

#### **Universal Document Processing**
```bash
# Parse any document type with unified parser
python scripts/universal_markdown_parser.py active_drafts/complaint_case_name/ complaint

# Generate HTML preview (universal - works for any document type)
python scripts/universal_preview_generator.py active_drafts/complaint_case_name/

# Generate HTML preview (complaint-specific)
python scripts/complaint_processor.py active_drafts/complaint_case_name/
```

### **Standards Documentation**
- **Complete Guide**: `standards/markdown_formatting_guide.md`
- **Validation Rules**: `standards/validation_rules.yml`
- **Document Specifications**: `standards/document_type_specifications.yml`

### **Complete Document Workflow**
1. **Create Content**: Write markdown following unified standards
2. **Validate Format**: Run format validator to check compliance
3. **Auto-Fix Issues**: Use format fixer for common problems
4. **Generate Preview**: Create HTML preview for review
5. **Generate Final Documents**: Create PDF and/or Word documents

### **Standardized Preview System**
All HTML previews are generated to a single, standardized location for easy application integration:

**Preview Location**: `html_preview/draft-preview.html`

**Benefits**:
- **Simple Routing**: Applications can always point to the same file
- **Consistent Interface**: Single endpoint for all document types
- **Easy Integration**: No need to track different output files
- **Automatic Overwrite**: Each preview replaces the previous one

**Usage**:
```bash
# Any of these commands will output to html_preview/draft-preview.html
python scripts/universal_preview_generator.py active_drafts/complaint_case/
python scripts/universal_preview_generator.py active_drafts/motion_case/
python scripts/complaint_processor.py active_drafts/complaint_case/
```

**Application Integration**:
- Route: `/preview` → `html_preview/draft-preview.html`
- Always displays the most recently generated preview
- Works with any document type (complaint, motion, discovery, etc.)

### **Final Document Generation**
Generate court-ready PDF and Word documents with timestamps:

```bash
# Generate PDF only
python scripts/generate_final_document.py active_drafts/complaint_case_name/ pdf

# Generate Word document only
python scripts/generate_final_document.py active_drafts/complaint_case_name/ docx

# Generate both PDF and Word documents
python scripts/generate_final_document.py active_drafts/complaint_case_name/ both
```

**Output Location**: `final_documents/`
- **Timestamped Filenames**: `complaint_name_YYYYMMDD_HHMMSS.pdf`
- **No Overwriting**: Each generation creates new timestamped files
- **Both Formats**: Single command can generate PDF and Word simultaneously

**Features**:
- **Court-Ready Formatting**: 1-inch margins, Times New Roman, proper spacing
- **Professional Layout**: Legal document structure with proper headers
- **Cross-Platform**: Works on all operating systems
- **Consistent Output**: Same formatting as HTML preview

## Version History

- v1.0: Initial release with core document types and YAML schema
- v2.0: Added HTML-based preview and generation system
- v3.0: Implemented unified markdown formatting standards with validation and auto-fixing
