#!/usr/bin/env python3
"""
Universal Preview Generator
Generates HTML previews for any document type and outputs to standardized location
"""

import os
import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class UniversalPreviewGenerator:
    """Universal HTML preview generator for all legal document types"""
    
    def __init__(self):
        """Initialize the preview generator"""
        self.script_dir = Path(__file__).parent.parent
        self.templates_dir = self.script_dir / "templates" / "html"
        self.preview_dir = self.script_dir / "html_preview"
        self.preview_file = self.preview_dir / "draft-preview.html"
        
        # Ensure preview directory exists
        self.preview_dir.mkdir(exist_ok=True)
    
    def generate_preview(self, document_folder: str) -> str:
        """
        Generate HTML preview for any document type
        
        Args:
            document_folder: Path to document folder
            
        Returns:
            Path to generated preview file
        """
        folder = Path(document_folder)
        if not folder.exists():
            raise FileNotFoundError(f"Document folder not found: {document_folder}")
        
        # Load metadata to determine document type
        metadata = self._load_metadata(folder)
        document_type = metadata.get('document_info', {}).get('type', 'unknown')
        
        # Find draft content folder
        draft_content_dir = folder / "draft_content"
        if not draft_content_dir.exists():
            draft_content_dir = folder
        
        # Get all markdown files
        md_files = sorted([f for f in draft_content_dir.glob("*.md")])
        
        if not md_files:
            raise ValueError(f"No markdown files found in {draft_content_dir}")
        
        # Parse content
        content_sections = []
        for md_file in md_files:
            section = self._parse_markdown_file(md_file)
            if section:
                content_sections.append(section)
        
        # Generate HTML based on document type
        if document_type == 'complaint':
            html_content = self._generate_complaint_html(content_sections, metadata)
        elif document_type == 'motion':
            html_content = self._generate_motion_html(content_sections, metadata)
        else:
            html_content = self._generate_generic_html(content_sections, metadata, document_type)
        
        # Write to standardized location
        with open(self.preview_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(self.preview_file)
    
    def _load_metadata(self, folder: Path) -> Dict:
        """Load metadata.yml from document folder"""
        metadata_file = folder / "metadata.yml"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _parse_markdown_file(self, md_file: Path) -> Optional[Dict]:
        """Parse a single markdown file"""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            return None
        
        lines = content.split('\n')
        
        # Extract title (first H1)
        title = ""
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        # Parse paragraphs
        paragraphs = []
        current_paragraph = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_paragraph:
                    paragraphs.append(self._format_legal_text(current_paragraph))
                    current_paragraph = ""
                continue
            
            # Skip headers
            if line.startswith('#'):
                if current_paragraph:
                    paragraphs.append(self._format_legal_text(current_paragraph))
                    current_paragraph = ""
                continue
            
            # Add to current paragraph
            if current_paragraph:
                current_paragraph += " " + line
            else:
                current_paragraph = line
        
        # Add final paragraph
        if current_paragraph:
            paragraphs.append(self._format_legal_text(current_paragraph))
        
        return {
            'title': title,
            'paragraphs': paragraphs,
            'file_name': md_file.name
        }
    
    def _format_legal_text(self, text: str) -> str:
        """Format legal text with proper HTML markup"""
        # Remove cross-reference labels (they're invisible)
        text = re.sub(r'\{\{LABEL:[^}]+\}\}', '', text)
        
        # Convert **bold** to <strong>
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # Convert *italic* to <em>
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # Handle line breaks
        text = re.sub(r'\n\s*([a-z])\.\s+', r'<br/>   \1. ', text)
        
        return text.strip()
    
    def _generate_complaint_html(self, content_sections: List[Dict], metadata: Dict) -> str:
        """Generate HTML for complaint documents"""
        template_file = self.templates_dir / "complaint.html"
        if template_file.exists():
            try:
                # Try to use Jinja2 for proper template processing
                import jinja2

                with open(template_file, 'r', encoding='utf-8') as f:
                    template_content = f.read()

                template = jinja2.Template(template_content)
                variables = self._prepare_complaint_variables(content_sections, metadata)

                return template.render(**variables)

            except ImportError:
                print("Warning: jinja2 not installed. Using default template.")
                template = self._get_default_template()
            except Exception as e:
                print(f"Warning: Template processing failed: {e}. Using default template.")
                template = self._get_default_template()
        else:
            template = self._get_default_template()

        # Fallback: use default template with simple substitution
        variables = self._prepare_complaint_variables(content_sections, metadata)

        # Simple template substitution for default template
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))

        return template
    
    def _generate_motion_html(self, content_sections: List[Dict], metadata: Dict) -> str:
        """Generate HTML for motion documents"""
        template_file = self.templates_dir / "motion.html"
        if template_file.exists():
            with open(template_file, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            template = self._get_default_template()
        
        # Prepare template variables
        variables = self._prepare_motion_variables(content_sections, metadata)
        
        # Simple template substitution
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        
        return template
    
    def _generate_generic_html(self, content_sections: List[Dict], metadata: Dict, document_type: str) -> str:
        """Generate HTML for any document type"""
        template = self._get_default_template()
        
        # Prepare generic variables
        variables = self._prepare_generic_variables(content_sections, metadata, document_type)
        
        # Simple template substitution
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        
        return template
    
    def _prepare_complaint_variables(self, content_sections: List[Dict], metadata: Dict) -> Dict:
        """Prepare variables for complaint template"""
        # Extract metadata
        court_info = metadata.get('court_info', {})
        parties = metadata.get('parties', {})
        document_info = metadata.get('document_info', {})

        # Prepare content sections for Jinja2 template
        processed_sections = []
        for section in content_sections:
            processed_section = {
                'title': section.get('title', ''),
                'paragraphs': [],
                'lists': [],
                'subsections': [],
                'is_count': 'COUNT' in section.get('title', '').upper()
            }

            # Process paragraphs
            for i, paragraph in enumerate(section.get('paragraphs', []), 1):
                processed_section['paragraphs'].append({
                    'number': i,
                    'content': paragraph
                })

            processed_sections.append(processed_section)

        # Default values
        return {
            'court_name': court_info.get('court_name', 'IN THE DISTRICT COURT OF CLARK COUNTY'),
            'court_division': court_info.get('jurisdiction', 'STATE OF NEVADA'),
            'court_subdivision': court_info.get('subdivision', ''),
            'case_number': court_info.get('case_number', '[TO BE ASSIGNED]'),
            'judge': court_info.get('judge', ''),
            'plaintiff_name': parties.get('plaintiff', {}).get('name', 'IAN BRUCE'),
            'defendant_name': self._format_defendant_names(parties.get('defendants', [])),
            'document_title': document_info.get('title', 'COMPLAINT FOR DAMAGES'),
            'current_date': datetime.now().strftime('%B %d, %Y'),
            'content_sections': processed_sections,
            'attorney_info': {
                'name': parties.get('plaintiff', {}).get('name', 'IAN BRUCE'),
                'title': parties.get('plaintiff', {}).get('role', 'Pro Se'),
                'address': parties.get('plaintiff', {}).get('address', ''),
                'phone': parties.get('plaintiff', {}).get('phone', ''),
                'email': parties.get('plaintiff', {}).get('email', '')
            },
            'certificate_of_service': None  # Can be added later if needed
        }

    def _format_defendant_names(self, defendants: List[Dict]) -> str:
        """Format defendant names for display"""
        if not defendants:
            return 'HILTON RESORTS CORPORATION, et al.'

        names = []
        for defendant in defendants:
            name = defendant.get('name', '')
            if defendant.get('type') == 'corporation':
                state = defendant.get('state', '')
                if state:
                    name += f', a {state} corporation'
            names.append(name)

        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]} and {names[1]}"
        else:
            return ', '.join(names[:-1]) + f', and {names[-1]}'
    
    def _prepare_motion_variables(self, content_sections: List[Dict], metadata: Dict) -> Dict:
        """Prepare variables for motion template"""
        # Default metadata for motions
        default_metadata = {
            'court_name': 'IN THE DISTRICT COURT OF CLARK COUNTY',
            'court_division': 'STATE OF NEVADA',
            'case_number': '[TO BE ASSIGNED]',
            'plaintiff_name': 'IAN BRUCE',
            'defendant_name': 'HILTON RESORTS CORPORATION, et al.',
            'document_title': 'MOTION',
            'current_date': datetime.now().strftime('%B %Y')
        }
        
        # Combine content
        content_html = ""
        for section in content_sections:
            if section['title']:
                content_html += f"<h2>{section['title']}</h2>\n"
            for paragraph in section['paragraphs']:
                content_html += f"<p>{paragraph}</p>\n"
        
        return {
            **default_metadata,
            'content': content_html
        }
    
    def _prepare_generic_variables(self, content_sections: List[Dict], metadata: Dict, document_type: str) -> Dict:
        """Prepare variables for generic template"""
        # Default metadata
        default_metadata = {
            'court_name': 'IN THE DISTRICT COURT OF CLARK COUNTY',
            'court_division': 'STATE OF NEVADA',
            'case_number': '[TO BE ASSIGNED]',
            'plaintiff_name': 'IAN BRUCE',
            'defendant_name': 'HILTON RESORTS CORPORATION, et al.',
            'document_title': document_type.upper(),
            'current_date': datetime.now().strftime('%B %Y')
        }
        
        # Combine content
        content_html = ""
        for section in content_sections:
            if section['title']:
                content_html += f"<h2>{section['title']}</h2>\n"
            for paragraph in section['paragraphs']:
                content_html += f"<p>{paragraph}</p>\n"
        
        return {
            **default_metadata,
            'content': content_html
        }
    
    def _get_default_template(self) -> str:
        """Get default HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{document_title}} - Preview</title>
    <style>
        body {
            font-family: 'Times New Roman', serif;
            font-size: 14pt;
            line-height: 2.0;
            margin: 1in;
            color: #000;
            background: #fff;
        }
        .header {
            text-align: center;
            margin-bottom: 2em;
        }
        .court-name {
            font-weight: bold;
            font-size: 16pt;
        }
        .case-caption {
            margin: 2em 0;
            border-collapse: collapse;
            width: 100%;
        }
        .case-caption td {
            border: 1px solid #000;
            padding: 0.5em;
            vertical-align: top;
        }
        .case-caption .parties {
            width: 70%;
        }
        .case-caption .case-info {
            width: 30%;
            text-align: center;
        }
        h1, h2, h3 {
            text-align: center;
            font-weight: bold;
        }
        h1 { font-size: 16pt; }
        h2 { font-size: 14pt; }
        h3 { font-size: 14pt; }
        p {
            text-align: justify;
            margin: 1em 0;
        }
        .signature-block {
            margin-top: 3em;
            text-align: left;
        }
        strong { font-weight: bold; }
        em { font-style: italic; }
    </style>
</head>
<body>
    <div class="header">
        <div class="court-name">{{court_name}}</div>
        <div>{{court_division}}</div>
    </div>
    
    <table class="case-caption">
        <tr>
            <td class="parties">
                <strong>{{plaintiff_name}},</strong><br/>
                <em>Plaintiff,</em><br/><br/>
                <strong>v.</strong><br/><br/>
                <strong>{{defendant_name}},</strong><br/>
                <em>Defendants.</em>
            </td>
            <td class="case-info">
                <strong>Case No.:</strong> {{case_number}}<br/><br/>
                <strong>{{document_title}}</strong>
            </td>
        </tr>
    </table>
    
    <div class="content">
        {{content}}
    </div>
    
    <div class="signature-block">
        <p>Respectfully submitted,</p>
        <br/><br/>
        <p>_________________________<br/>
        {{plaintiff_name}}<br/>
        Pro Se<br/>
        {{current_date}}</p>
    </div>
</body>
</html>"""

def main():
    """Command line interface for universal preview generator"""
    if len(sys.argv) < 2:
        print("Usage: python universal_preview_generator.py <document_folder>")
        return
    
    document_folder = sys.argv[1]
    
    generator = UniversalPreviewGenerator()
    
    try:
        preview_file = generator.generate_preview(document_folder)
        print(f"Preview generated: {preview_file}")
        
        # Open in browser
        import webbrowser
        webbrowser.open(f"file://{Path(preview_file).absolute()}")
        print("Preview opened in browser")
        
    except Exception as e:
        print(f"Error generating preview: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
