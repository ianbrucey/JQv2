# Freehand Mode Quick Reference Guide

## **Quick Commands**

### **Document Generation (3-Step Process)**
```bash
# Activate environment
source venv/bin/activate

# Step 1: Validate and fix
python scripts/format_validator.py active_drafts/document_folder/ standard
python scripts/format_fixer.py active_drafts/document_folder/

# Step 2: Generate preview (Manual HTML creation by AI agent)
# Output: active_drafts/document_folder/html_preview/document-preview.html

# Step 3: Generate finals
python scripts/generate_final_document.py active_drafts/document_folder/ both
```

### **Quick-Start Phrases**
- **"Create new case for [case description]"**
- **"Add [document type] to existing [case name]"**
- **"Generate finals for [document folder]"**
- **"Validate [document folder]"**
- **"Research [legal issue]"**

---

## **Common Entry Points**

### **1. New Case Setup**
**Command**: "Create new case for [description]"
**Agent Creates**:
- Case folder with Intake/ subfolder
- Case_Summary_and_Timeline.md
- Initial document folder structure

### **2. Add Document to Existing Case**
**Command**: "Add [document type] to [case name]"
**Agent Creates**:
- New document folder with standard structure
- Metadata.yml configured for document type
- Reallegation strategy for existing facts

### **3. Document Validation**
**Command**: "Validate [document folder]"
**Agent Runs**:
- format_validator.py with standard level
- format_fixer.py for automatic corrections
- Re-validation to confirm fixes

### **4. Final Document Generation**
**Command**: "Generate finals for [document folder]"
**Agent Executes**:
- Complete 3-step workflow
- PDF and Word document generation
- Timestamped output files

### **5. Research Task**
**Command**: "Research [legal issue] for [case]"
**Agent Provides**:
- Targeted legal research
- Organized research file in research/ folder
- Integration with existing case materials

---

## **Document Types and Structures**

### **Complaint**
```
complaint_case_name/
├── draft_content/
│   ├── 01_caption_and_parties.md
│   ├── 02_jurisdiction_and_venue.md
│   ├── 03_factual_allegations.md
│   ├── 04_count_i_[claim].md
│   ├── 05_count_ii_[claim].md
│   ├── 09_prayer_for_relief.md
│   └── 10_jury_demand.md
├── research/
├── exhibits/
├── reference_material/
├── case_documents/
└── metadata.yml
```

### **Motion**
```
motion_descriptive_name/
├── draft_content/
│   ├── 01_introduction.md
│   ├── 02_statement_of_facts.md
│   ├── 03_legal_standard.md
│   ├── 04_argument.md
│   └── 05_conclusion.md
├── research/
├── exhibits/
├── reference_material/
├── case_documents/
└── metadata.yml
```

### **Discovery**
```
discovery_type_description/
├── draft_content/
│   ├── 01_instructions.md
│   ├── 02_definitions.md
│   └── 03_requests.md
├── research/
├── exhibits/
├── reference_material/
├── case_documents/
└── metadata.yml
```

---

## **Formatting Standards (Quick Reference)**

### **Paragraph Numbering**
```markdown
**1.** Standard format for all numbered paragraphs
**2.** Use double asterisks and period
```

### **Legal Citations**
```markdown
**15 U.S.C. § 1681n** (statutes - bold)
*Smith v. Jones* (cases - italic)
12 C.F.R. § 1026.19(f) (regulations - regular)
```

### **Cross-References**
```markdown
**1.** {{LABEL:parties_start}}Plaintiff is...
**4.** ...referred to as "Defendants."{{LABEL:parties_end}}

**15.** Plaintiff realleges paragraphs {{REF_RANGE:parties_start:parties_end}}.
```

### **Headers**
```markdown
# MAJOR SECTIONS (H1)
## Subsection Titles (H2)
### Detailed Subsections (H3)
```
**PROHIBITED**: H4+ headers (#### or deeper)

---

## **File Naming Conventions**

### **Document Folders**
- `complaint_case_name`
- `motion_descriptive_name`
- `discovery_type_description`
- Use underscores, not spaces

### **Markdown Files**
- `01_caption_and_parties.md`
- `02_jurisdiction_and_venue.md`
- Use numbered prefixes for proper ordering

### **Research Files**
- `YYYY-MM-DD_topic.md`
- `2024-12-15_statute_of_limitations.md`

---

## **Output Locations**

### **HTML Preview**
- **Location**: `html_preview/draft-preview.html`
- **Behavior**: Overwritten each generation
- **Purpose**: Review before final generation

### **Final Documents**
- **Location**: `final_documents/`
- **Naming**: `document_type_name_YYYYMMDD_HHMMSS.{pdf,docx}`
- **Behavior**: Timestamped, never overwritten

---

## **Troubleshooting**

### **Validation Errors**
1. Run `format_fixer.py` first
2. Check cross-reference labels
3. Verify paragraph numbering format
4. Confirm header hierarchy (H1-H3 only)

### **Cross-Reference Issues**
- Ensure labels exist: `{{LABEL:name}}`
- Check reference syntax: `{{REF:name}}` or `{{REF_RANGE:start:end}}`
- Verify label placement in correct paragraphs

### **Citation Problems**
- Statutes: `**15 U.S.C. § 1681n**` (bold)
- Cases: `*Smith v. Jones*` (italic)
- Regulations: `12 C.F.R. § 1026.19(f)` (regular)

### **Document Generation Issues**
1. Verify folder structure exists
2. Check metadata.yml configuration
3. Ensure all required markdown files present
4. Run validation before generation

---

## **Mode Switching**

### **Need More Guidance?**
Say: "I'd like more guidance on this step" or "Can you explain this process?"

### **Want Educational Content?**
Say: "Can you explain why this standard exists?" or "Help me understand this requirement"

### **Switch Back to Freehand**
Say: "I understand now, let's move quickly" or "Skip the explanations"

---

## **Emergency Commands**

### **If Lost or Confused**
- **"Show me current case status"** - Reviews Case_Summary_and_Timeline.md
- **"What are my next steps?"** - Provides action items and guidance
- **"Switch to guided mode"** - Changes to structured workflow
- **"Help with [specific issue]"** - Targeted assistance

### **If Standards Conflict**
- Refer to `standards/markdown_formatting_guide.md`
- Choose most conservative/formal option
- Ask agent for clarification

### **If System Issues**
1. Check file locations and naming
2. Verify markdown formatting
3. Run format_validator.py
4. Use format_fixer.py for corrections
5. Re-run 3-step workflow

This quick reference provides everything you need for efficient freehand mode operation while maintaining the draft_system's high quality standards.
