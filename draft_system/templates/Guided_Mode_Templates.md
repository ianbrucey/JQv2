# Guided Mode Templates and Interactive Elements

## **Initial User Assessment Template**

### **Experience Level Assessment**
```
Agent: "Welcome to the draft_system! To provide you with the best experience, 
I'd like to understand your background and preferences.

1. How familiar are you with legal document drafting?
   a) New to legal writing
   b) Some experience with legal documents
   c) Experienced legal writer
   d) Professional attorney/paralegal

2. Have you used the draft_system before?
   a) First time user
   b) Used it once or twice
   c) Regular user
   d) Very familiar with the system

3. What type of case are you working on?
   a) Brand new case - starting from scratch
   b) Adding documents to existing case
   c) Updating or revising existing documents
   d) Research or analysis only

4. How do you prefer to work?
   a) Step-by-step guidance with explanations
   b) Some guidance but move efficiently
   c) Minimal guidance, I know what I'm doing
   d) Let me direct the process

Based on your answers, I'll recommend either Guided Mode (structured, educational) 
or Freehand Mode (efficient, user-directed). You can switch modes anytime."
```

### **Mode Recommendation Logic**
- **Recommend Guided Mode**: Answers mostly a) and b)
- **Recommend Freehand Mode**: Answers mostly c) and d)
- **Offer Choice**: Mixed answers - explain both options

---

## **Guided Mode: Case Setup Interview Template**

### **Phase 1: Basic Case Information**
```
Agent: "Let's start by gathering the essential information for your case. 
I'll ask a series of questions to ensure we capture everything needed.

CASE BASICS:
1. What type of legal issue is this? (contract dispute, personal injury, 
   consumer protection, employment, etc.)

2. Who are the main parties involved?
   - Who is the plaintiff/petitioner?
   - Who is the defendant/respondent?
   - Any other important parties?

3. Where should this case be filed?
   - Do you have a court preference?
   - What state/jurisdiction?
   - Federal or state court?

4. What is your primary goal?
   - Monetary damages?
   - Injunctive relief?
   - Specific performance?
   - Other relief?

5. Are there any time-sensitive issues?
   - Statute of limitations concerns?
   - Pending deadlines?
   - Urgent relief needed?"
```

### **Phase 2: Detailed Fact Gathering**
```
Agent: "Now let's develop the factual foundation for your case. 
This information will form the backbone of your legal documents.

TIMELINE AND EVENTS:
1. When did the events giving rise to this case begin?

2. Can you provide a chronological summary of key events?

3. What specific actions or omissions form the basis of your claims?

4. What damages or harm have you suffered?

5. Do you have documentation supporting these events?

EVIDENCE AND DOCUMENTATION:
1. What documents do you have related to this case?
   - Contracts or agreements
   - Correspondence
   - Financial records
   - Photos or videos
   - Other evidence

2. Are there witnesses to any of the events?

3. Have you communicated with the other party about this issue?

4. Have you attempted to resolve this matter outside of court?"
```

### **Phase 3: Legal Strategy Discussion**
```
Agent: "Based on the information you've provided, let me explain the potential 
legal theories and help you understand your options.

LEGAL ANALYSIS:
Based on your facts, I see potential claims for:
[Agent lists applicable legal theories]

Let me explain each one:

1. [Legal Theory 1]: 
   - What it means: [Plain language explanation]
   - Required elements: [What must be proven]
   - Your evidence: [How user's facts support this claim]
   - Potential damages: [What relief is available]

2. [Legal Theory 2]:
   [Same structure]

STRATEGY QUESTIONS:
1. Which of these claims seems most important to you?

2. Are you interested in pursuing all viable claims or focusing on the strongest?

3. What is your risk tolerance for litigation?

4. Are you open to settlement discussions?"
```

---

## **Guided Mode: Document Creation Templates**

### **Document Type Selection**
```
Agent: "Now that we have your case foundation, let's create your first document. 
Based on your case, I recommend starting with a [DOCUMENT TYPE].

Let me explain what this document will accomplish:

PURPOSE: [Explanation of document's role in litigation]

STRUCTURE: This document will include:
- [Section 1]: [Purpose and content]
- [Section 2]: [Purpose and content]
- [Section 3]: [Purpose and content]

TIMELINE: This process typically takes [timeframe] and involves:
1. Creating the document outline
2. Drafting each section with your input
3. Reviewing and refining the content
4. Generating the final professional documents

Are you ready to begin, or do you have questions about this document type?"
```

### **Section-by-Section Guidance**
```
Agent: "Let's start with the [SECTION NAME] section. 

WHAT THIS SECTION DOES:
[Explanation of section's purpose and legal significance]

WHAT WE NEED TO INCLUDE:
- [Required element 1]: [Explanation]
- [Required element 2]: [Explanation]
- [Required element 3]: [Explanation]

LEGAL STANDARDS:
[Explanation of relevant legal requirements]

Let me draft this section based on the information you provided, and then 
we'll review it together. You can suggest changes or additions.

[Agent drafts content]

Here's what I've drafted for this section. Let me walk through each paragraph:

Paragraph 1: [Explanation of content and purpose]
Paragraph 2: [Explanation of content and purpose]

What do you think? Should we modify anything or add additional information?"
```

---

## **Guided Mode: Quality Assurance Templates**

### **Validation Explanation**
```
Agent: "Before we generate your final documents, let's ensure everything meets 
professional legal standards. I'll run our validation system and explain what 
we're checking.

FORMATTING STANDARDS:
- Paragraph numbering: All numbered paragraphs use **1.** format
- Legal citations: Statutes in bold, cases in italics
- Cross-references: All references link to valid labels
- Document structure: Proper heading hierarchy

CONTENT STANDARDS:
- Professional legal tone throughout
- Complete legal arguments with supporting citations
- Proper reallegation of facts where required
- All required elements for each legal claim

Let me run the validation now...

[Validation results]

RESULTS EXPLANATION:
✅ Passed: [Explanation of what passed and why it's important]
⚠️  Warnings: [Explanation of warnings and whether action is needed]
❌ Errors: [Explanation of errors and how to fix them]

Should I automatically fix the issues I can correct, or would you like to 
review each one individually?"
```

### **Preview Review Guidance**
```
Agent: "I've generated an HTML preview of your document. This shows exactly 
how your final PDF and Word documents will look.

WHAT TO REVIEW:
1. Overall appearance and professional formatting
2. Accuracy of all factual statements
3. Completeness of legal arguments
4. Proper citation formatting
5. Cross-reference functionality

REVIEW CHECKLIST:
□ Caption information is correct (parties, court, case number)
□ All facts are accurate and properly stated
□ Legal citations are correct and properly formatted
□ Cross-references work (click to test)
□ Document flows logically from section to section
□ Professional appearance throughout

The preview is available at: html_preview/draft-preview.html

Take your time reviewing. When you're satisfied, I'll generate the final 
PDF and Word documents for filing."
```

---

## **Guided Mode: Educational Components**

### **Legal Concept Explanations**
```
CROSS-REFERENCE SYSTEM:
"The draft_system uses a sophisticated cross-reference system that allows you 
to reference information from one part of your document in another part. 

For example, instead of retyping all the party information in every count, 
you can simply reference the parties section. This ensures consistency and 
makes updates easier.

Here's how it works:
- Labels mark important sections: {{LABEL:parties_start}}
- References point to those sections: {{REF_RANGE:parties_start:parties_end}}
- The system automatically inserts the correct paragraph numbers

This is especially useful in complaints where you 'reallege' previous 
paragraphs in each count."

LEGAL CITATION FORMAT:
"Legal documents require specific citation formats:
- Statutes: **15 U.S.C. § 1681n** (bold formatting)
- Cases: *Smith v. Jones* (italic formatting)  
- Regulations: 12 C.F.R. § 1026.19(f) (regular formatting)

This formatting helps judges and attorneys quickly identify the type of 
authority you're citing."

PARAGRAPH NUMBERING:
"Legal documents use numbered paragraphs for easy reference. The draft_system 
requires the **1.** format (bold number with period) because:
- It's the standard format in most courts
- It's easily readable and professional
- It works consistently across all document types
- It integrates properly with the cross-reference system"
```

### **Progress Tracking Template**
```
Agent: "Here's your current progress on this case:

CASE: [Case Name]
DOCUMENT: [Document Type]

COMPLETED PHASES:
✅ Phase 1: Case Setup and Information Gathering
✅ Phase 2: Legal Research and Strategy Development  
🔄 Phase 3: Content Creation (Currently working on Section 3 of 5)
⏳ Phase 4: Document Generation and Quality Assurance
⏳ Phase 5: Final Review and Filing Preparation

CURRENT STATUS:
We're currently working on [specific section/task]. 

NEXT STEPS:
1. Complete [current task]
2. [Next immediate task]
3. [Following task]

ESTIMATED TIME TO COMPLETION:
Approximately [timeframe] remaining for this document.

Would you like to continue with the current section or take a break and 
return to this later?"
```

This template system ensures consistent, educational, and supportive guidance for users choosing the structured workflow approach.
