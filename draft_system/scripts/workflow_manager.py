#!/usr/bin/env python3
"""
Workflow Manager for Draft System
Handles user onboarding, mode detection, and workflow orchestration
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import yaml
import json

class WorkflowManager:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.templates_dir = self.base_dir / "templates"
        self.standards_dir = self.base_dir / "standards"
        
    def assess_user_experience(self, responses):
        """
        Assess user experience level based on questionnaire responses
        Returns: 'guided', 'freehand', or 'choice' (let user decide)
        """
        # Score responses (a=1, b=2, c=3, d=4)
        score_map = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        total_score = sum(score_map.get(response.lower(), 2) for response in responses)
        avg_score = total_score / len(responses)
        
        if avg_score <= 2.0:
            return 'guided'
        elif avg_score >= 3.0:
            return 'freehand'
        else:
            return 'choice'
    
    def create_case_structure(self, case_name, mode='guided'):
        """Create standardized case folder structure"""
        case_dir = self.base_dir / case_name
        
        # Create main case directory
        case_dir.mkdir(exist_ok=True)
        
        # Create Intake folder
        intake_dir = case_dir / "Intake"
        intake_dir.mkdir(exist_ok=True)
        
        # Create Intake subfolders
        (intake_dir / "preliminary_docs").mkdir(exist_ok=True)
        
        # Create Intake template files
        self._create_intake_files(intake_dir, case_name, mode)
        
        # Create Case Summary and Timeline
        self._create_case_summary(case_dir, case_name, mode)
        
        return case_dir
    
    def create_document_structure(self, case_dir, document_type, document_name):
        """Create standardized document folder structure"""
        doc_folder_name = f"{document_type}_{document_name}"
        doc_dir = case_dir / "active_drafts" / doc_folder_name
        
        # Create main document directory
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        # Create required subfolders
        subfolders = [
            "draft_content",
            "research", 
            "exhibits",
            "reference_material",
            "case_documents"
        ]
        
        for folder in subfolders:
            (doc_dir / folder).mkdir(exist_ok=True)
        
        # Create metadata.yml
        self._create_metadata_file(doc_dir, document_type, case_dir.name)
        
        # Create draft content templates based on document type
        self._create_draft_content_templates(doc_dir / "draft_content", document_type)
        
        return doc_dir
    
    def _create_intake_files(self, intake_dir, case_name, mode):
        """Create intake template files"""
        
        # initial_request.md
        initial_request = f"""# Initial Request - {case_name}

## User's Initial Description
**Date**: {datetime.now().strftime('%B %d, %Y')}
**Requestor**: [User Name]

## What the User Wants to Accomplish
[Description of user's goals and objectives]

## Primary Legal Issues Identified
1. **[Legal Issue 1]** - [Brief description]
2. **[Legal Issue 2]** - [Brief description]
3. **[Legal Issue 3]** - [Brief description]

## Preliminary Assessment
[Initial analysis of case strength and viability]

## Recommended Next Steps
- [ ] [Action item 1]
- [ ] [Action item 2]
- [ ] [Action item 3]

## Mode Selected
**Workflow Mode**: {mode.title()} Mode
**Reason**: [Why this mode was selected]
"""
        
        with open(intake_dir / "initial_request.md", 'w') as f:
            f.write(initial_request)
        
        # background_info.md
        background_info = f"""# Background Information - {case_name}

## Case Background
**User**: [User Name]
**Date Compiled**: {datetime.now().strftime('%B %d, %Y')}

## Key Facts and Timeline
[Chronological summary of events]

## Parties Involved
### Plaintiff(s)
- **Name**: [Name]
- **Role**: [Description]
- **Contact**: [Contact information]

### Defendant(s)
- **Name**: [Name]
- **Role**: [Description]
- **Contact**: [Contact information]

## Damages and Relief Sought
[Description of harm suffered and relief requested]

## Evidence Available
[Summary of available evidence and documentation]
"""
        
        with open(intake_dir / "background_info.md", 'w') as f:
            f.write(background_info)
        
        # intake_notes.md
        intake_notes = f"""# Intake Notes - {case_name}

## Initial Consultation Notes
**Date**: {datetime.now().strftime('%B %d, %Y')}
**Case**: {case_name}

## Key Discussion Points

### User's Goals
1. **Primary Objective**: [Main goal]
2. **Relief Sought**: [Specific relief requested]
3. **Court Preference**: [Court preference if any]
4. **Timeline**: [Urgency and timeline considerations]

### Legal Issues Discussed
[Summary of legal issues identified and discussed]

### Evidence Review
[Summary of evidence reviewed during intake]

## Questions for Follow-Up
1. **[Question 1]**: [Details needed]
2. **[Question 2]**: [Details needed]
3. **[Question 3]**: [Details needed]

## Action Items from Intake
- [ ] [Action item 1]
- [ ] [Action item 2]
- [ ] [Action item 3]

## User Preferences Noted
- **Communication Style**: [User's preferred communication style]
- **Document Style**: [Document preferences]
- **Workflow**: [Workflow preferences]
- **Legal Approach**: [Approach to legal strategy]
"""
        
        with open(intake_dir / "intake_notes.md", 'w') as f:
            f.write(intake_notes)
    
    def _create_case_summary(self, case_dir, case_name, mode):
        """Create Case Summary and Timeline from template"""
        template_path = self.templates_dir / "Case_Summary_and_Timeline_Template.md"
        
        if template_path.exists():
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Replace template placeholders
            content = template_content.replace("[Case Name]", case_name)
            content = content.replace("[Date]", datetime.now().strftime('%B %d, %Y'))
            content = content.replace("[Case Type]", "[To be determined]")
            
            # Add mode information
            mode_section = f"""

## Workflow Mode
**Selected Mode**: {mode.title()} Mode
**Date Selected**: {datetime.now().strftime('%B %d, %Y')}
**Reason**: [Reason for mode selection]

### Mode History
- {datetime.now().strftime('%B %d, %Y')}: Started in {mode.title()} Mode
"""
            
            content += mode_section
            
        else:
            # Fallback if template doesn't exist
            content = f"""# Case Summary and Timeline - {case_name}

## Case Overview
**Case Name**: {case_name}
**Date Opened**: {datetime.now().strftime('%B %d, %Y')}
**Current Status**: Active - Initial Setup
**Workflow Mode**: {mode.title()} Mode

## Timeline
### {datetime.now().strftime('%B %d, %Y')} - Case Initiation
- Case folder structure created
- Initial intake process begun
- {mode.title()} Mode selected for workflow

## Next Steps
- [ ] Complete intake process
- [ ] Conduct initial legal research
- [ ] Begin document drafting
"""
        
        with open(case_dir / "Case_Summary_and_Timeline.md", 'w') as f:
            f.write(content)
    
    def _create_metadata_file(self, doc_dir, document_type, case_name):
        """Create metadata.yml file for document"""
        metadata = {
            'document_info': {
                'type': document_type,
                'title': f"{document_type.upper().replace('_', ' ')}",
                'case_name': case_name,
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'draft',
                'version': '1.0'
            },
            'court_info': {
                'court_name': '[TO BE FILLED]',
                'jurisdiction': '[TO BE FILLED]',
                'case_number': '[TO BE ASSIGNED]',
                'judge': ''
            },
            'parties': {
                'plaintiff': {
                    'name': '[TO BE FILLED]',
                    'address': '',
                    'phone': '',
                    'email': '',
                    'role': 'Pro Se'
                },
                'defendants': [
                    {
                        'name': '[TO BE FILLED]',
                        'type': 'individual',
                        'address': '',
                        'state': ''
                    }
                ]
            },
            'generation_options': {
                'validation_level': 'standard',
                'include_cross_references': True,
                'format_citations': True,
                'double_spaced': True
            }
        }
        
        with open(doc_dir / "metadata.yml", 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    
    def _create_draft_content_templates(self, draft_content_dir, document_type):
        """Create appropriate markdown templates based on document type"""
        
        if document_type == 'complaint':
            files = [
                ('01_caption_and_parties.md', '# PARTIES\n\n'),
                ('02_jurisdiction_and_venue.md', '# JURISDICTION AND VENUE\n\n'),
                ('03_factual_allegations.md', '# FACTUAL ALLEGATIONS\n\n'),
                ('04_count_i_[claim_name].md', '# COUNT I\n## [CLAIM NAME]\n\n'),
                ('09_prayer_for_relief.md', '# PRAYER FOR RELIEF\n\n'),
                ('10_jury_demand.md', '# JURY DEMAND\n\n')
            ]
        elif document_type == 'motion':
            files = [
                ('01_introduction.md', '# INTRODUCTION\n\n'),
                ('02_statement_of_facts.md', '# STATEMENT OF FACTS\n\n'),
                ('03_legal_standard.md', '# LEGAL STANDARD\n\n'),
                ('04_argument.md', '# ARGUMENT\n\n'),
                ('05_conclusion.md', '# CONCLUSION\n\n')
            ]
        elif document_type in ['discovery', 'interrogatories', 'requests_for_production']:
            files = [
                ('01_instructions.md', '# INSTRUCTIONS\n\n'),
                ('02_definitions.md', '# DEFINITIONS\n\n'),
                ('03_requests.md', '# REQUESTS\n\n')
            ]
        else:
            # Generic template
            files = [
                ('01_introduction.md', '# INTRODUCTION\n\n'),
                ('02_main_content.md', '# MAIN CONTENT\n\n'),
                ('03_conclusion.md', '# CONCLUSION\n\n')
            ]
        
        for filename, content in files:
            with open(draft_content_dir / filename, 'w') as f:
                f.write(content)

def main():
    """Command line interface for workflow manager"""
    if len(sys.argv) < 2:
        print("Usage: python workflow_manager.py <command> [args]")
        print("Commands:")
        print("  create_case <case_name> [mode]")
        print("  create_document <case_name> <document_type> <document_name>")
        print("  assess_user <responses>")
        return
    
    manager = WorkflowManager()
    command = sys.argv[1]
    
    if command == "create_case":
        if len(sys.argv) < 3:
            print("Usage: python workflow_manager.py create_case <case_name> [mode]")
            return
        
        case_name = sys.argv[2]
        mode = sys.argv[3] if len(sys.argv) > 3 else 'guided'
        
        case_dir = manager.create_case_structure(case_name, mode)
        print(f"Created case structure: {case_dir}")
        
    elif command == "create_document":
        if len(sys.argv) < 5:
            print("Usage: python workflow_manager.py create_document <case_name> <document_type> <document_name>")
            return
        
        case_name = sys.argv[2]
        document_type = sys.argv[3]
        document_name = sys.argv[4]
        
        case_dir = Path(case_name)
        if not case_dir.exists():
            print(f"Case directory {case_name} does not exist")
            return
        
        doc_dir = manager.create_document_structure(case_dir, document_type, document_name)
        print(f"Created document structure: {doc_dir}")
        
    elif command == "assess_user":
        if len(sys.argv) < 3:
            print("Usage: python workflow_manager.py assess_user <responses>")
            print("Example: python workflow_manager.py assess_user a,b,c,d")
            return
        
        responses = sys.argv[2].split(',')
        recommendation = manager.assess_user_experience(responses)
        print(f"Recommended mode: {recommendation}")

if __name__ == "__main__":
    main()
