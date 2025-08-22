# Draft System Setup Guide

## Quick Start for New Cases

This guide will help you set up the draft_system template for a new legal case.

### Step 1: Repository Setup

1. **Clone or Download** this template repository
2. **Rename** the folder to match your case (e.g., `smith_v_jones_case`)
3. **Initialize** as a new repository if using version control

### Step 2: Install Dependencies

#### Python Environment Setup
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

#### Additional System Requirements

**For Document Processing (OCR)**:
- **Windows**: Download Tesseract from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### Step 3: Customize Template Files

#### Replace Case Information
1. **Case_Summary_and_Timeline.md**
   - Replace `[Case Name]` with actual case name
   - Update all `[Placeholder]` fields with real information
   - Add actual parties, dates, and case details

2. **Intake Folder Files**
   - `initial_request.md` - Replace with actual client request
   - `background_info.md` - Add real case background
   - `intake_notes.md` - Include actual consultation notes

#### Update Metadata
3. **Court and Jurisdiction Information**
   - Update court names and jurisdictions throughout
   - Verify local court rules and requirements
   - Adjust formatting standards if needed

### Step 4: Test System Functionality

#### Verify Installation
```bash
# Test document processing
python scripts/document_processor.py --help

# Test exhibit management
python scripts/exhibit_manager.py list

# Test workflow management
python scripts/workflow_manager.py --help
```

#### Run Sample Generation
```bash
# Create a test document folder
python scripts/workflow_manager.py create-document complaint test_case

# Validate system components
python scripts/format_validator.py --check-system
```

### Step 5: Configure for Your Case

#### Set Up Active Drafts
1. Create document folders as needed:
   ```bash
   python scripts/workflow_manager.py create-document complaint [case_name]
   python scripts/workflow_manager.py create-document motion [motion_type]
   ```

2. Customize metadata.yml files in each document folder

#### Organize Case Resources
1. **Court Rules**: Add local court rules to `case_resources/court_rules/`
2. **Applicable Law**: Add relevant statutes to `case_resources/statutes/`
3. **Case Law**: Add precedents to `case_resources/case_law/`

#### Set Up Document Processing
1. **Upload Documents**: Place initial documents in `Intake/preliminary_docs/`
2. **Process Documents**: 
   ```bash
   python scripts/document_processor.py Intake/preliminary_docs/document.pdf
   ```
3. **Create Exhibits**:
   ```bash
   python scripts/exhibit_manager.py create path/to/document.pdf "Document Description"
   ```

### Step 6: Workflow Selection

#### Choose Your Mode
The system supports two workflow modes:

**Guided Mode** (Recommended for new users):
- Step-by-step guidance
- Educational explanations
- Automatic folder creation
- Quality checkpoints

**Freehand Mode** (For experienced users):
- Flexible, user-directed workflow
- Minimal explanations
- Quick task completion
- Expert-level efficiency

#### Mode Selection
When working with AI agents, specify your preferred mode:
- "I'd like to use Guided Mode for this case"
- "I prefer Freehand Mode for efficiency"

### Step 7: Quality Assurance Setup

#### Validation Configuration
1. Review `standards/validation_rules.yml`
2. Customize for your jurisdiction if needed
3. Test validation system:
   ```bash
   python scripts/format_validator.py active_drafts/document_folder/ standard
   ```

#### Preview System
1. HTML preview generation is now manual:
   ```
   AI Agent creates HTML previews using str-replace-editor tool
   Location: active_drafts/document_folder/html_preview/document-preview.html
   ```
2. Open `active_drafts/[draft_type]/html_preview/[document]-preview.html` in browser

#### Final Document Generation
1. Test PDF and Word generation:
   ```bash
   python scripts/generate_final_document.py active_drafts/document_folder/ both
   ```
2. Check output in `final_documents/` folder

### Step 8: Backup and Version Control

#### Recommended Practices
1. **Initialize Git Repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial case setup"
   ```

2. **Regular Backups**: Set up automated backups of case files

3. **Version Control**: Commit changes regularly with descriptive messages

4. **Document History**: Keep track of document versions and changes

### Troubleshooting

#### Common Issues

**Document Processing Fails**:
- Verify Tesseract OCR installation
- Check file permissions
- Ensure sufficient disk space

**Preview Generation Errors**:
- Validate markdown formatting
- Check cross-reference syntax
- Verify all required sections present

**Final Document Issues**:
- Run format validator first
- Check template compatibility
- Verify system dependencies

#### Getting Help

1. **Check Logs**: Review `logs/document_processing.log`
2. **Validation Reports**: Run format validator for specific errors
3. **Documentation**: Refer to README.md and individual script help
4. **System Check**: Use built-in diagnostic tools

### Advanced Configuration

#### Custom Templates
1. Modify YAML templates in `templates/yaml/`
2. Customize HTML templates in `templates/html/`
3. Adjust validation rules in `standards/`

#### Integration Options
1. **Case Management Systems**: Configure API connections
2. **Court Filing Systems**: Set up electronic filing integration
3. **Document Management**: Connect to existing DMS platforms

#### Performance Optimization
1. **Batch Processing**: Configure for multiple documents
2. **Caching**: Enable template and processing caches
3. **Parallel Processing**: Configure for large document sets

---

## Next Steps

Once setup is complete:
1. Begin with case intake and information gathering
2. Process and organize initial documents
3. Start drafting using the appropriate workflow mode
4. Use quality assurance tools throughout the process
5. Generate final court-ready documents

For detailed usage instructions, see the main README.md file and individual script documentation.
