#!/usr/bin/env python3
"""
Universal Markdown Parser for Legal Documents
Replaces document-specific processors with unified approach following standardized formatting
"""

import re
import os
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

@dataclass
class ParsedParagraph:
    """Represents a parsed paragraph with metadata"""
    number: int
    original_number: Optional[str]
    content: str
    labels: List[str]
    is_numbered: bool

@dataclass
class ParsedSection:
    """Represents a parsed document section"""
    title: str
    level: int
    paragraphs: List[ParsedParagraph]
    subsections: List['ParsedSection']
    lists: List[List[str]]
    document_order: int

class UniversalMarkdownParser:
    """Universal parser for all legal document types following unified standards"""
    
    def __init__(self, standards_dir: str = None):
        """Initialize parser with standards directory"""
        if standards_dir is None:
            standards_dir = Path(__file__).parent.parent / "standards"
        
        self.standards_dir = Path(standards_dir)
        self.validation_rules = self._load_validation_rules()
        self.document_specs = self._load_document_specifications()
        
        # Parser state
        self.current_paragraph_number = 1
        self.labels = {}  # label_name -> paragraph_number
        self.errors = []
        self.warnings = []
    
    def _load_validation_rules(self) -> Dict:
        """Load validation rules from standards"""
        rules_file = self.standards_dir / "validation_rules.yml"
        if rules_file.exists():
            with open(rules_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _load_document_specifications(self) -> Dict:
        """Load document type specifications"""
        specs_file = self.standards_dir / "document_type_specifications.yml"
        if specs_file.exists():
            with open(specs_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def parse_document_folder(self, folder_path: str, document_type: str = None) -> Dict:
        """
        Parse all markdown files in a document folder
        
        Args:
            folder_path: Path to document folder
            document_type: Type of document (auto-detected if None)
        
        Returns:
            Parsed document structure
        """
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Document folder not found: {folder_path}")
        
        # Load metadata if available
        metadata = self._load_metadata(folder)
        if document_type is None:
            document_type = metadata.get('document_info', {}).get('type', 'unknown')
        
        # Find draft content folder
        draft_content_dir = folder / "draft_content"
        if not draft_content_dir.exists():
            # Fallback to root folder for backward compatibility
            draft_content_dir = folder
        
        # Get all markdown files
        md_files = sorted([f for f in draft_content_dir.glob("*.md")])
        
        # Parse each file
        sections = []
        for i, md_file in enumerate(md_files):
            section = self._parse_markdown_file(md_file, i + 1)
            if section:
                sections.append(section)
        
        # Validate document structure
        self._validate_document_structure(sections, document_type)
        
        return {
            'metadata': metadata,
            'document_type': document_type,
            'sections': sections,
            'labels': self.labels,
            'errors': self.errors,
            'warnings': self.warnings,
            'total_paragraphs': self.current_paragraph_number - 1
        }
    
    def _load_metadata(self, folder: Path) -> Dict:
        """Load metadata.yml from document folder"""
        metadata_file = folder / "metadata.yml"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _parse_markdown_file(self, md_file: Path, order: int) -> Optional[ParsedSection]:
        """Parse a single markdown file"""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            return None
        
        lines = content.split('\n')
        
        # Initialize section
        section = ParsedSection(
            title="",
            level=1,
            paragraphs=[],
            subsections=[],
            lists=[],
            document_order=order
        )
        
        current_subsection = None
        current_list = []
        in_list = False
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                # Handle headers
                if line.startswith('#'):
                    header_level = len(line) - len(line.lstrip('#'))
                    header_text = line.lstrip('#').strip()
                    
                    # Validate header level
                    if header_level > 3:
                        self.errors.append(f"Header level {header_level} exceeds maximum (H3) in {md_file.name}:{line_num}")
                        continue
                    
                    if header_level == 1 and not section.title:
                        section.title = header_text
                        section.level = 1
                    elif header_level > 1:
                        # Create subsection
                        if current_subsection and current_subsection.paragraphs:
                            section.subsections.append(current_subsection)
                        
                        current_subsection = ParsedSection(
                            title=header_text,
                            level=header_level,
                            paragraphs=[],
                            subsections=[],
                            lists=[],
                            document_order=order
                        )
                    continue
                
                # Handle numbered paragraphs
                paragraph_match = self._match_numbered_paragraph(line)
                if paragraph_match:
                    original_num, content_text = paragraph_match
                    
                    # Extract labels
                    labels = self._extract_labels(content_text)
                    
                    # Clean content (remove labels)
                    clean_content = self._clean_content(content_text)
                    
                    # Format legal text
                    formatted_content = self._format_legal_text(clean_content)
                    
                    # Create paragraph
                    paragraph = ParsedParagraph(
                        number=self.current_paragraph_number,
                        original_number=original_num,
                        content=formatted_content,
                        labels=labels,
                        is_numbered=True
                    )
                    
                    # Store labels
                    for label in labels:
                        self.labels[label] = self.current_paragraph_number
                    
                    # Add to appropriate section
                    if current_subsection:
                        current_subsection.paragraphs.append(paragraph)
                    else:
                        section.paragraphs.append(paragraph)
                    
                    self.current_paragraph_number += 1
                    continue
                
                # Handle list items
                if re.match(r'^\s*[a-z]\.\s+', line):
                    if not in_list:
                        current_list = []
                        in_list = True
                    
                    list_content = re.sub(r'^\s*[a-z]\.\s+', '', line)
                    current_list.append(self._format_legal_text(list_content))
                    continue
                
                # End of list
                if in_list and not re.match(r'^\s*[a-z]\.\s+', line):
                    if current_list:
                        if current_subsection:
                            current_subsection.lists.append(current_list)
                        else:
                            section.lists.append(current_list)
                    current_list = []
                    in_list = False
                
                # Handle regular paragraphs (non-numbered)
                if line and not line.startswith('#'):
                    formatted_content = self._format_legal_text(line)
                    
                    paragraph = ParsedParagraph(
                        number=0,  # Non-numbered
                        original_number=None,
                        content=formatted_content,
                        labels=[],
                        is_numbered=False
                    )
                    
                    if current_subsection:
                        current_subsection.paragraphs.append(paragraph)
                    else:
                        section.paragraphs.append(paragraph)
            
            except Exception as e:
                self.errors.append(f"Error parsing {md_file.name}:{line_num}: {str(e)}")
        
        # Add final subsection if exists
        if current_subsection and (current_subsection.paragraphs or current_subsection.lists):
            section.subsections.append(current_subsection)
        
        # Add final list if exists
        if current_list:
            if current_subsection:
                current_subsection.lists.append(current_list)
            else:
                section.lists.append(current_list)
        
        return section
    
    def _match_numbered_paragraph(self, line: str) -> Optional[Tuple[str, str]]:
        """Match numbered paragraph formats: **1.** or **P1.**"""
        # Standard format: **1.**
        match = re.match(r'\*\*(\d+)\.\*\*\s*(.*)', line)
        if match:
            return match.group(1), match.group(2)
        
        # P-format: **P1.**
        match = re.match(r'\*\*P?(\d+)\.\*\*\s*(.*)', line)
        if match:
            return f"P{match.group(1)}", match.group(2)
        
        return None
    
    def _extract_labels(self, text: str) -> List[str]:
        """Extract cross-reference labels from text"""
        labels = re.findall(r'\{\{LABEL:([^}]+)\}\}', text)
        return labels
    
    def _clean_content(self, text: str) -> str:
        """Remove label markers from content"""
        return re.sub(r'\{\{LABEL:[^}]+\}\}', '', text).strip()
    
    def _format_legal_text(self, text: str) -> str:
        """Apply legal formatting to text"""
        # Convert **bold** to <strong> for HTML compatibility
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # Convert *italic* to <em>
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # Handle line breaks in lists
        text = re.sub(r'\n\s*([a-z])\.\s+', r'<br/>   \1. ', text)
        
        return text
    
    def _validate_document_structure(self, sections: List[ParsedSection], document_type: str):
        """Validate document structure against type specifications"""
        if document_type not in self.document_specs:
            self.warnings.append(f"Unknown document type: {document_type}")
            return
        
        spec = self.document_specs[document_type]
        required_sections = spec.get('required_sections', [])
        
        section_titles = [s.title.upper() for s in sections if s.title]
        
        for req_section in required_sections:
            section_name = req_section['name'].upper()
            if section_name not in section_titles:
                self.errors.append(f"Missing required section: {section_name}")
    
    def resolve_cross_references(self, text: str) -> str:
        """Resolve cross-references in text"""
        # Handle range references: {{REF_RANGE:start:end}}
        def replace_range_ref(match):
            start_label = match.group(1)
            end_label = match.group(2)
            
            start_num = self.labels.get(start_label)
            end_num = self.labels.get(end_label)
            
            if start_num is not None and end_num is not None:
                if start_num == end_num:
                    return str(start_num)
                else:
                    return f"{start_num} through {end_num}"
            else:
                self.errors.append(f"Unresolved reference range: {start_label}:{end_label}")
                return f"[REF ERROR: {start_label}:{end_label}]"
        
        text = re.sub(r'\{\{REF_RANGE:([^:]+):([^}]+)\}\}', replace_range_ref, text)
        
        # Handle single references: {{REF:label}}
        def replace_single_ref(match):
            label = match.group(1)
            num = self.labels.get(label)
            if num is not None:
                return str(num)
            else:
                self.errors.append(f"Unresolved reference: {label}")
                return f"[REF ERROR: {label}]"
        
        text = re.sub(r'\{\{REF:([^}]+)\}\}', replace_single_ref, text)
        
        return text
    
    def get_validation_report(self) -> Dict:
        """Get validation report with errors and warnings"""
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'is_valid': len(self.errors) == 0
        }

def main():
    """Command line interface for universal parser"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python universal_markdown_parser.py <document_folder> [document_type]")
        return
    
    folder_path = sys.argv[1]
    document_type = sys.argv[2] if len(sys.argv) > 2 else None
    
    parser = UniversalMarkdownParser()
    
    try:
        result = parser.parse_document_folder(folder_path, document_type)
        
        print(f"Parsed document: {result['document_type']}")
        print(f"Sections: {len(result['sections'])}")
        print(f"Total paragraphs: {result['total_paragraphs']}")
        print(f"Labels: {len(result['labels'])}")
        
        # Show validation report
        report = parser.get_validation_report()
        print(f"\nValidation: {'PASSED' if report['is_valid'] else 'FAILED'}")
        print(f"Errors: {report['total_errors']}")
        print(f"Warnings: {report['total_warnings']}")
        
        if report['errors']:
            print("\nErrors:")
            for error in report['errors']:
                print(f"  - {error}")
        
        if report['warnings']:
            print("\nWarnings:")
            for warning in report['warnings']:
                print(f"  - {warning}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
