# Unified Markdown Formatting Standards
## Draft System Framework - Legal Document Generation

### **Overview**
This document establishes the unified markdown formatting standards for all legal documents in the draft_system framework. These standards ensure consistent formatting across HTML and YAML workflows while maintaining professional legal document quality.

---

## **1. PARAGRAPH NUMBERING**

### **Standard Format**
Use sequential numbering with bold formatting:
```markdown
**1.** Plaintiff IAN BRUCE is a resident of Georgia.
**2.** Defendant HILTON RESORTS CORPORATION is a Delaware corporation.
**3.** This Court has jurisdiction over this matter.
```

### **Document Type Rules**
- **Complaints/Pleadings**: Always use numbered paragraphs
- **Motions**: Use numbered paragraphs for factual sections
- **Briefs**: Use numbered paragraphs for statement of facts only
- **Discovery**: Use numbered requests/interrogatories
- **Affidavits**: Use numbered paragraphs throughout

### **Pre-numbered Content**
For content with existing paragraph numbers, use the P-prefix format:
```markdown
**P1.** This paragraph maintains original numbering.
**P55.** This continues from existing document numbering.
```
*Note: The system will convert P-format to sequential numbering during processing.*

---

## **2. CROSS-REFERENCE SYSTEM**

### **Label Placement**
Labels are invisible markers for cross-referencing:
```markdown
**1.** {{LABEL:parties_start}}Plaintiff IAN BRUCE is a resident of Georgia.
**4.** Defendants are collectively referred to as "Hilton."{{LABEL:parties_end}}
**10.** {{LABEL:jurisdiction_basis}}This Court has subject matter jurisdiction.
```

### **Reference Usage**
Reference other paragraphs using these formats:
```markdown
# Range References
**15.** Plaintiff realleges paragraphs {{REF_RANGE:parties_start:parties_end}}.

# Single References  
**16.** As alleged in paragraph {{REF:jurisdiction_basis}}, this Court has jurisdiction.

# Multiple Single References
**17.** As set forth in paragraphs {{REF:facts_start}}, {{REF:contract_formation}}, and {{REF:breach_occurred}}, Defendants breached their duties.
```

### **Label Naming Conventions**
- Use descriptive, lowercase names with underscores
- Include section indicators: `facts_start`, `facts_end`
- Use specific descriptors: `contract_formation`, `breach_occurred`
- Avoid generic names: `para1`, `section_a`

---

## **3. HEADER HIERARCHY**

### **Section Headers**
```markdown
# MAJOR SECTIONS (H1)
## Subsection Titles (H2)  
### Detailed Subsections (H3)
```

### **Document Structure Examples**

#### **Complaints**
```markdown
# PARTIES
# JURISDICTION AND VENUE
## Subject Matter Jurisdiction
## Personal Jurisdiction  
## Venue
# FACTUAL ALLEGATIONS
# COUNT I
## VIOLATIONS OF FEDERAL LAW
### (15 U.S.C. § 1681n)
# PRAYER FOR RELIEF
```

#### **Motions**
```markdown
# INTRODUCTION
# STATEMENT OF FACTS
# LEGAL STANDARD
# ARGUMENT
## First Argument Point
### Supporting Legal Authority
## Second Argument Point
# CONCLUSION
```

### **Header Restrictions**
- **Maximum**: H3 level (###)
- **No H4+**: Use bold text instead of #### headers
- **Consistency**: Same level headers should be parallel in content

---

## **4. LEGAL CITATION FORMATTING**

### **Statutes (Bold)**
```markdown
**15 U.S.C. § 1681n**
**O.C.G.A. § 9-11-55(b)**
**NRS 3.220**
**Fed. R. Civ. P. 12(b)(6)**
```

### **Case Citations (Italic)**
```markdown
*Smith v. Jones*, 123 F.3d 456 (11th Cir. 2020)
*Brown v. Board of Education*, 347 U.S. 483 (1954)
*Nevada Supreme Court Case*, 456 P.3d 789 (Nev. 2019)
```

### **Regulations (Regular Text)**
```markdown
12 C.F.R. § 1026.19(f)
29 C.F.R. § 1630.2(g)
```

### **Legal Emphasis (Italic)**
```markdown
Defendants *willfully* violated federal law.
The contract was *unconscionable* at the time of formation.
```

### **Defined Terms (Quotes)**
```markdown
"Purchase Agreement"
"Closing Disclosure"  
"Truth in Lending Act"
```

---

## **5. LIST FORMATTING**

### **Enumerated Lists**
```markdown
**25.** Defendants' violations include:

    a. Failure to provide required disclosures;
    b. Misrepresentation of material terms; and
    c. Violation of federal lending laws.
```

### **Prayer for Relief**
```markdown
WHEREFORE, Plaintiff respectfully requests that this Court:

a. Enter judgment in favor of Plaintiff;
b. Award actual damages in an amount to be proven at trial;
c. Award statutory damages as provided by law;
d. Award attorney's fees and costs; and
e. Grant such other relief as the Court deems just and proper.
```

### **List Guidelines**
- Use lowercase letters (a, b, c) for sub-items
- End each item with semicolon except last (use period)
- Use "and" before final item
- Maintain parallel structure

---

## **6. SPECIAL LEGAL ELEMENTS**

### **Party Names**
```markdown
# First Reference (Full Name)
Defendant **HILTON RESORTS CORPORATION**, a Delaware corporation ("Hilton Resorts")

# Subsequent References (Short Name)
**Hilton Resorts** failed to comply with federal law.
```

### **Monetary Amounts**
```markdown
$1,000,000.00
$50,000 in damages
an amount in excess of $75,000
```

### **Dates**
```markdown
December 15, 2024
On or about January 1, 2023
```

### **Document References**
```markdown
the "Purchase Agreement" (attached as Exhibit A)
Defendants' Motion to Dismiss (Doc. 15)
```

---

## **7. DOCUMENT TYPE SPECIFICATIONS**

### **Complaints**
- **Numbered paragraphs**: Required throughout
- **Cross-references**: Extensive use for reallegation paragraphs
- **Count structure**: Each count as separate H1 section
- **Prayer**: Enumerated list format

### **Motions**
- **Numbered paragraphs**: Facts section only
- **Cross-references**: Limited, mainly for fact references
- **Argument structure**: H2/H3 hierarchy for legal points
- **Conclusion**: Brief paragraph format

### **Discovery Documents**
- **Numbered requests**: Required for interrogatories/requests
- **Definitions**: H2 section with numbered definitions
- **Instructions**: H2 section with enumerated instructions
- **Cross-references**: Reference to definitions

### **Briefs**
- **Numbered paragraphs**: Statement of facts only
- **Argument structure**: Detailed H2/H3 hierarchy
- **Citations**: Extensive case and statute citations
- **Cross-references**: Minimal, mainly for record references

### **Affidavits**
- **Numbered paragraphs**: Required throughout
- **Personal knowledge**: First-person statements
- **Cross-references**: Reference to attached exhibits
- **Signature block**: Required sworn statement format

---

## **8. VALIDATION RULES**

### **Required Elements**
- All paragraphs must use **number.** format
- All cross-references must resolve to valid labels
- All headers must follow H1/H2/H3 hierarchy
- All legal citations must use proper formatting

### **Prohibited Elements**
- H4+ headers (#### or deeper)
- Unformatted paragraph numbers
- Broken cross-references
- Inconsistent citation formatting

### **Quality Standards**
- Maximum line length: 120 characters
- Consistent spacing around headers
- Proper punctuation in lists
- Professional tone and language

---

## **9. METADATA INTEGRATION**

Each document folder's `metadata.yml` should specify:
```yaml
formatting:
  paragraph_numbering: true  # or false for briefs
  numbering_style: "sequential"  # or "preserve" for P-format
  cross_references: true
  document_type: "complaint"  # affects formatting rules
  validation_level: "strict"  # or "standard"
```

---

## **10. CONVERSION COMPATIBILITY**

These standards ensure seamless conversion between:
- **Markdown → HTML**: Direct parsing with CSS styling
- **Markdown → YAML**: Structured data population
- **YAML → Word**: Professional document generation
- **HTML → PDF**: Court-ready output

All formatting elements are designed to work consistently across all output formats while maintaining legal document standards and court requirements.

## Case Management and File Organization

### Case-Level Structure
Each case should have the following top-level organization:

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

### Document-Level Structure
Each individual document must follow the standardized folder structure:

```
{document_type}_{document_name}/
├── draft_content/              # Markdown files (numbered: 01_, 02_, etc.)
├── research/                   # Legal research and analysis
├── exhibits/                   # Supporting documents and evidence
├── reference_material/         # Background materials and templates
├── case_documents/            # Filed documents and court orders
└── metadata.yml               # Document configuration
```

### Case Summary and Timeline
The `Case_Summary_and_Timeline.md` file serves as the central reference point for the entire case. This living document should be updated after each significant event and contains:

- **Case Overview**: Basic case information and current status
- **Key Parties**: All parties and their contact information
- **Timeline**: Chronological record of all case events
- **Next Steps**: Current action items and deadlines
- **Legal Issues**: Summary of claims, defenses, and key legal questions
- **Agent Context**: Important notes for AI agents to understand case context

**Purpose**: Allows agents to quickly understand the entire case context without needing to pull information from multiple files.

### Intake Folder Purpose
The `Intake/` folder serves as the collection point for all preliminary case information:

- **Initial User Requests**: What the user wants to accomplish
- **Background Information**: Context and history provided by user
- **Preliminary Documents**: Any existing documents user provides
- **Intake Notes**: Questions, clarifications, and initial analysis

**Purpose**: Provides agents with complete context about user's goals and situation before beginning document drafting.

### File Naming Conventions
- **Markdown Files**: Use numbered prefixes (`01_`, `02_`, `03_`)
- **Document Folders**: `{document_type}_{descriptive_name}`
- **Case Folders**: Use clear, descriptive names without special characters
- **Intake Files**: Descriptive names indicating content type

### Maintenance Guidelines
- **Update Case Summary**: After each significant event or document completion
- **Archive Completed Documents**: Move finalized documents to appropriate case_documents folders
- **Regular Review**: Periodically review and update timeline and next steps
- **Context Preservation**: Always update agent context notes when patterns or preferences emerge
