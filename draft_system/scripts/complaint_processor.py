#!/usr/bin/env python3
"""
Complaint-specific processor for Ian Bruce's Markdown format
Handles the specific **P1**, **P2** paragraph numbering and legal formatting
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from jinja2 import Template, Environment, FileSystemLoader

class ComplaintProcessor:
    def __init__(self, template_dir: str = None):
        """Initialize the complaint processor"""
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates" / "html"
        
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        self.current_paragraph_number = 1
        
    def process_complaint_directory(self, complaint_dir: str, metadata: Dict = None) -> str:
        """
        Process all Markdown files in a complaint directory
        
        Args:
            complaint_dir: Path to directory containing complaint Markdown files
            metadata: Document metadata (caption info, etc.)
        
        Returns:
            Complete HTML document as string
        """
        complaint_path = Path(complaint_dir)
        if not complaint_path.exists():
            raise FileNotFoundError(f"Complaint directory not found: {complaint_dir}")
        
        # Find draft content folder
        draft_content_dir = complaint_path / "draft_content"
        if not draft_content_dir.exists():
            # Fallback to root folder for backward compatibility
            draft_content_dir = complaint_path

        # Get all markdown files in order
        md_files = sorted([f for f in draft_content_dir.glob("*.md")])
        
        # Process each file
        content_sections = []
        for md_file in md_files:
            section = self._process_markdown_file(md_file)
            if section:
                content_sections.append(section)
        
        # Load complaint template
        template = self.env.get_template('complaint.html')
        
        # Prepare template variables
        template_vars = self._prepare_template_variables(content_sections, metadata or {})
        
        # Render final HTML
        return template.render(**template_vars)
    
    def _process_markdown_file(self, md_file: Path) -> Optional[Dict]:
        """Process a single Markdown file"""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            return None
        
        # Extract section info from filename
        filename = md_file.stem
        section_info = self._parse_filename(filename)
        
        # Parse content
        parsed_content = self._parse_markdown_content(content)
        
        return {
            'filename': filename,
            'title': parsed_content['title'],
            'is_count': section_info['is_count'],
            'subtitles': parsed_content['subtitles'],
            'paragraphs': parsed_content['paragraphs'],
            'lists': parsed_content['lists'],
            'subsections': parsed_content['subsections']
        }
    
    def _parse_filename(self, filename: str) -> Dict:
        """Parse filename to determine section type"""
        is_count = 'count_' in filename.lower()
        return {
            'is_count': is_count,
            'order': filename[:2] if filename[:2].isdigit() else '99'
        }
    
    def _parse_markdown_content(self, content: str) -> Dict:
        """Parse Markdown content with **P1** style numbering"""
        lines = content.split('\n')
        
        parsed = {
            'title': '',
            'subtitles': [],
            'paragraphs': [],
            'lists': [],
            'subsections': []
        }
        
        current_subsection = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Handle main title (# TITLE)
            if line.startswith('# ') and not parsed['title']:
                parsed['title'] = line[2:].strip()
                continue
            
            # Handle count subtitles (## and ###)
            if line.startswith('## '):
                subtitle = line[3:].strip()
                parsed['subtitles'].append(subtitle)
                # Start new subsection
                current_subsection = {
                    'title': subtitle,
                    'level': 2,
                    'paragraphs': []
                }
                continue
            
            if line.startswith('### '):
                subtitle = line[4:].strip()
                parsed['subtitles'].append(subtitle)
                # Start new subsection
                current_subsection = {
                    'title': subtitle,
                    'level': 3,
                    'paragraphs': []
                }
                continue
            
            # Handle numbered paragraphs (**P1**, **P2**, etc.)
            paragraph_match = re.match(r'\*\*P?(\d+)\*\*\s*(.*)', line)
            if paragraph_match:
                para_num = paragraph_match.group(1)
                para_content = paragraph_match.group(2)
                
                # Process legal formatting
                formatted_content = self._format_legal_text(para_content)
                
                paragraph = {
                    'number': self.current_paragraph_number,
                    'original_number': para_num,
                    'content': formatted_content
                }
                
                # Add to current subsection or main paragraphs
                if current_subsection:
                    current_subsection['paragraphs'].append(paragraph)
                else:
                    parsed['paragraphs'].append(paragraph)
                
                self.current_paragraph_number += 1
                continue
            
            # Handle regular numbered paragraphs (**55.**, **56.**, etc.)
            numbered_match = re.match(r'\*\*(\d+)\.\*\*\s*(.*)', line)
            if numbered_match:
                para_num = numbered_match.group(1)
                para_content = numbered_match.group(2)
                
                # Process legal formatting
                formatted_content = self._format_legal_text(para_content)
                
                paragraph = {
                    'number': self.current_paragraph_number,
                    'original_number': para_num,
                    'content': formatted_content
                }
                
                # Add to current subsection or main paragraphs
                if current_subsection:
                    current_subsection['paragraphs'].append(paragraph)
                else:
                    parsed['paragraphs'].append(paragraph)
                
                self.current_paragraph_number += 1
                continue
            
            # Handle list items (a., b., c.)
            if re.match(r'\s*[a-z]\.\s+', line):
                # This is part of a list - we'll handle this in post-processing
                continue
        
        # Add any remaining subsection
        if current_subsection and current_subsection['paragraphs']:
            parsed['subsections'].append(current_subsection)
        
        return parsed
    
    def _format_legal_text(self, text: str) -> str:
        """Format legal text with proper HTML markup"""
        # Convert **bold** to <strong> for statutes and legal terms
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # Convert *italic* to <em>
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # Handle list items within paragraphs
        text = re.sub(r'\n\s*([a-z])\.\s+', r'<br/>   \1. ', text)
        
        return text
    
    def _prepare_template_variables(self, content_sections: List[Dict], metadata: Dict) -> Dict:
        """Prepare variables for template rendering"""
        # Default metadata for Nevada state court
        default_metadata = {
            'court_name': 'IN THE DISTRICT COURT OF CLARK COUNTY',
            'court_division': 'STATE OF NEVADA',
            'case_number': '[TO BE ASSIGNED]',
            'plaintiff_name': 'IAN BRUCE',
            'defendant_name': 'HILTON RESORTS CORPORATION, et al.',
            'document_title': 'COMPLAINT FOR DAMAGES',
            'current_date': 'December 2024',
            'attorney_info': {
                'name': 'Ian Bruce',
                'title': 'Pro Se',
                'address': '7219 Laurel Creek Dr.\nStockbridge, GA 30281',
                'phone': '(404) 555-1212',
                'email': 'ib708090@gmail.com'
            }
        }
        
        # Merge with provided metadata
        default_metadata.update(metadata)
        
        return {
            **default_metadata,
            'content_sections': content_sections
        }

def main():
    """Command line interface for complaint processing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python complaint_processor.py <complaint_directory>")
        return

    complaint_dir = sys.argv[1]

    # Always output to standardized preview location
    script_dir = Path(__file__).parent.parent  # Go up to draft_system directory
    preview_dir = script_dir / "html_preview"
    preview_dir.mkdir(exist_ok=True)
    output_file = preview_dir / "draft-preview.html"

    processor = ComplaintProcessor()

    try:
        html_content = processor.process_complaint_directory(complaint_dir)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Preview generated: {output_file}")

        # Open in browser
        import webbrowser
        webbrowser.open(f"file://{output_file.absolute()}")
        print("Preview opened in browser")

    except Exception as e:
        print(f"Error processing complaint: {e}")

if __name__ == "__main__":
    main()
