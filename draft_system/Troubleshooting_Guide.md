# Draft System Troubleshooting Guide

## **Common Workflow Issues and Solutions**

### **1. Mode Selection and Switching Issues**

#### **Problem**: User unsure which mode to choose
**Symptoms**: 
- User asks "Which mode should I use?"
- User seems overwhelmed by options
- User has mixed experience levels

**Solution**:
```
Agent Response: "Let me help you choose the right mode:

CHOOSE GUIDED MODE if you:
- Are new to legal document drafting
- Want to learn the draft_system features
- Prefer step-by-step explanations
- Have a complex case requiring organization
- Want educational content about legal concepts

CHOOSE FREEHAND MODE if you:
- Are experienced with legal writing
- Know the draft_system already
- Want to work efficiently without explanations
- Are adding documents to existing cases
- Prefer to direct the workflow yourself

If you're unsure, start with Guided Mode. You can always switch to 
Freehand Mode once you're comfortable.

Which would you prefer to try first?"
```

#### **Problem**: User wants to switch modes mid-process
**Symptoms**:
- "This is too slow, can we move faster?"
- "I'm confused, can you explain more?"
- "I don't need all these explanations"

**Solution**:
```
Agent Response: "Absolutely! I'm switching to [NEW MODE] now.

[If switching to Freehand]: I'll provide direct responses without detailed 
explanations. You can ask for clarification anytime.

[If switching to Guided]: I'll provide more detailed explanations and 
step-by-step guidance. Let me know if you need more or less detail.

Let's continue with [current task] in [new mode]."
```

---

### **2. Document Structure and Organization Issues**

#### **Problem**: User doesn't understand folder structure
**Symptoms**:
- "Where should I put this file?"
- "I don't understand the folder organization"
- "What's the difference between research/ and reference_material/?"

**Solution**:
```
Agent Response: "Let me explain the standardized folder structure:

CASE LEVEL (case_name/):
├── Intake/ - Initial user information and preliminary documents
├── Case_Summary_and_Timeline.md - Central case tracking document
└── active_drafts/ - Individual document folders

DOCUMENT LEVEL (document_type_name/):
├── draft_content/ - Markdown files for document generation
├── research/ - Legal research and case law analysis  
├── exhibits/ - Evidence and supporting documents
├── reference_material/ - Background materials and templates
├── case_documents/ - Filed documents and court orders
└── metadata.yml - Document configuration

PURPOSE OF EACH FOLDER:
- draft_content/: The actual content that becomes your legal document
- research/: Legal research supporting your arguments
- exhibits/: Evidence you'll attach to your document
- reference_material/: Background info and similar cases
- case_documents/: Documents already filed in court

I'll create this structure automatically. You just need to know where 
to find things."
```

#### **Problem**: User has files in wrong locations
**Symptoms**:
- Validation errors about missing files
- Content not appearing in generated documents
- Cross-references not working

**Solution**:
```
Agent Response: "I see some files may be in the wrong locations. Let me help 
organize them properly:

CURRENT ISSUE: [Specific problem identified]

SOLUTION: I'll move files to the correct locations:
- [File] should be in [correct location] because [reason]
- [File] should be in [correct location] because [reason]

This will ensure:
- Document generation works properly
- Cross-references function correctly
- All content appears in final documents

Should I reorganize these files for you?"
```

---

### **3. Formatting and Validation Issues**

#### **Problem**: Validation errors that user doesn't understand
**Symptoms**:
- "What does this error mean?"
- "How do I fix formatting issues?"
- "Why is my paragraph numbering wrong?"

**Solution**:
```
Agent Response: "Let me explain these validation errors and how to fix them:

ERROR: [Specific error message]
MEANING: [Plain language explanation]
SOLUTION: [How to fix it]
WHY IT MATTERS: [Why this standard exists]

COMMON FIXES:
- Paragraph numbering: Use **1.** format (bold number with period)
- Headers: Use # ## ### only (no #### or deeper)
- Citations: **Statutes in bold**, *cases in italics*
- Cross-references: Check that labels exist where referenced

I can automatically fix most of these issues. Should I run the auto-fixer?"
```

#### **Problem**: Cross-references not working
**Symptoms**:
- "My references show as {{REF:name}} instead of paragraph numbers"
- "Cross-references aren't linking properly"
- "I get errors about missing labels"

**Solution**:
```
Agent Response: "Cross-reference issues are usually caused by missing or 
misplaced labels. Let me check:

COMMON CAUSES:
1. Missing label: You reference {{REF:parties}} but no {{LABEL:parties}} exists
2. Wrong location: Label is in wrong paragraph or section
3. Typo: {{REF:partys}} vs {{LABEL:parties}} (spelling mismatch)

CHECKING YOUR DOCUMENT:
[Agent analyzes cross-references]

FOUND ISSUES:
- [Specific issue]: [Solution]
- [Specific issue]: [Solution]

I can fix these automatically. The cross-reference system will then work 
properly in your final documents."
```

---

### **4. Content Creation Issues**

#### **Problem**: User doesn't know what to include in sections
**Symptoms**:
- "What should go in the jurisdiction section?"
- "How do I write factual allegations?"
- "What's required for a count?"

**Solution**:
```
Agent Response: "Let me explain what each section requires:

[SECTION NAME] SECTION:
PURPOSE: [What this section accomplishes legally]

REQUIRED ELEMENTS:
1. [Element]: [Explanation and example]
2. [Element]: [Explanation and example]
3. [Element]: [Explanation and example]

BASED ON YOUR CASE:
- [Specific guidance for user's situation]
- [Relevant legal standards]
- [Evidence or facts to include]

I can draft this section for you based on the information you've provided, 
then we can review and refine it together."
```

#### **Problem**: User wants to deviate from standard structure
**Symptoms**:
- "Can I add a different section?"
- "Do I have to follow this exact format?"
- "What if my case is different?"

**Solution**:
```
Agent Response: "The draft_system is flexible while maintaining professional 
standards. Here are your options:

STANDARD STRUCTURE: [Explanation of why it's recommended]
YOUR SITUATION: [Analysis of user's specific needs]

OPTIONS:
1. Modify standard structure: [How to adapt while maintaining quality]
2. Add custom sections: [Where and how to add them]
3. Alternative approach: [If completely different structure is needed]

RECOMMENDATION: [Specific advice for user's case]

The key is maintaining professional legal document standards while 
accommodating your case's unique requirements."
```

---

### **5. Technical and System Issues**

#### **Problem**: Commands not working or producing errors
**Symptoms**:
- "The validation script isn't working"
- "I get permission errors"
- "Files aren't being generated"

**Solution**:
```
Agent Response: "Let me help troubleshoot this technical issue:

FIRST, CHECK BASICS:
1. Are you in the correct directory? (should be in draft_system/)
2. Is the virtual environment activated? (run: source venv/bin/activate)
3. Do the files exist in the expected locations?

COMMON SOLUTIONS:
- Permission errors: Check file permissions and ownership
- Missing files: Verify folder structure and file names
- Script errors: Check that all dependencies are installed

Let me run a diagnostic:
[Agent checks system status]

ISSUE IDENTIFIED: [Specific problem]
SOLUTION: [Step-by-step fix]

Try this fix and let me know if the issue persists."
```

#### **Problem**: Generated documents don't look right
**Symptoms**:
- "The PDF formatting is wrong"
- "Word document is missing content"
- "Caption isn't showing properly"

**Solution**:
```
Agent Response: "Document generation issues are usually caused by:

1. CONTENT ISSUES:
   - Missing or incorrectly formatted content
   - Cross-reference problems
   - Metadata configuration errors

2. SYSTEM ISSUES:
   - Browser not available for PDF generation
   - Word generation template problems
   - File permission issues

Let me check your specific issue:
[Agent analyzes the problem]

DIAGNOSIS: [What's causing the problem]
SOLUTION: [How to fix it]

I'll regenerate your documents with the fix applied."
```

---

### **6. Case Management Issues**

#### **Problem**: User lost track of case status or next steps
**Symptoms**:
- "Where am I in the process?"
- "What should I do next?"
- "I can't remember what we were working on"

**Solution**:
```
Agent Response: "Let me check your case status and get you oriented:

CURRENT CASE: [Case name from Case_Summary_and_Timeline.md]
LAST ACTIVITY: [Most recent timeline entry]
CURRENT STATUS: [Where things stand]

COMPLETED WORK:
✅ [Completed items]
✅ [Completed items]

IN PROGRESS:
🔄 [Current work]

NEXT STEPS:
1. [Immediate next action]
2. [Following action]
3. [Subsequent action]

Would you like to continue with [current work] or start something different?"
```

---

### **Emergency Procedures**

#### **When User is Completely Lost**
```
Agent Response: "No problem! Let me help you get back on track:

1. IMMEDIATE ORIENTATION:
   - What case are you working on?
   - What were you trying to accomplish?
   - What's the last thing you remember doing?

2. QUICK ASSESSMENT:
   - I'll check your Case_Summary_and_Timeline.md
   - Review your current document status
   - Identify where you are in the process

3. RESTART OPTIONS:
   - Continue where you left off
   - Start a specific task
   - Switch to guided mode for more support
   - Begin with a quick tutorial

What would be most helpful right now?"
```

#### **When Standards Conflict or User is Confused**
```
Agent Response: "When in doubt, I follow this priority order:

1. standards/markdown_formatting_guide.md (primary authority)
2. standards/document_type_specifications.yml (document-specific rules)
3. standards/validation_rules.yml (technical requirements)
4. Most conservative/formal option when unclear

For your specific question: [Specific guidance]

This ensures your documents meet the highest professional standards."
```

This troubleshooting guide provides comprehensive solutions for the most common issues users encounter in both guided and freehand modes.
