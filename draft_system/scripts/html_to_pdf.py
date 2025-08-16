#!/usr/bin/env python3
"""
HTML to PDF Converter for Legal Documents
Converts HTML previews to court-ready PDF documents
"""

import sys
import os
from pathlib import Path

try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class HTMLToPDFConverter:
    def __init__(self, method="weasyprint"):
        """
        Initialize PDF converter
        
        Args:
            method: Conversion method ("weasyprint" or "playwright")
        """
        self.method = method
        self._validate_dependencies()
    
    def _validate_dependencies(self):
        """Validate that required dependencies are available"""
        if self.method == "weasyprint" and not WEASYPRINT_AVAILABLE:
            raise ImportError(
                "WeasyPrint not available. Install with: pip install weasyprint"
            )
        elif self.method == "playwright" and not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not available. Install with: pip install playwright && playwright install"
            )
    
    def convert_html_to_pdf(self, html_file, output_pdf=None, options=None):
        """
        Convert HTML file to PDF
        
        Args:
            html_file: Path to HTML file
            output_pdf: Output PDF path (optional, defaults to same name with .pdf)
            options: Conversion options dictionary
        
        Returns:
            Path to generated PDF file
        """
        html_path = Path(html_file)
        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_file}")
        
        # Default output path
        if output_pdf is None:
            output_pdf = html_path.with_suffix('.pdf')
        else:
            output_pdf = Path(output_pdf)
        
        # Ensure output directory exists
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert based on method
        if self.method == "weasyprint":
            self._convert_with_weasyprint(html_path, output_pdf, options or {})
        elif self.method == "playwright":
            self._convert_with_playwright(html_path, output_pdf, options or {})
        else:
            raise ValueError(f"Unknown conversion method: {self.method}")
        
        print(f"PDF generated: {output_pdf}")
        return output_pdf
    
    def _convert_with_weasyprint(self, html_path, output_pdf, options):
        """Convert using WeasyPrint (better for legal documents)"""
        # Default options for legal documents
        default_options = {
            'presentational_hints': True,
            'optimize_images': True
        }
        default_options.update(options)
        
        # Read HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Create PDF
        html_doc = weasyprint.HTML(string=html_content, base_url=str(html_path.parent))
        css = weasyprint.CSS(string=self._get_legal_pdf_css())
        
        html_doc.write_pdf(
            str(output_pdf),
            stylesheets=[css],
            **default_options
        )
    
    def _convert_with_playwright(self, html_path, output_pdf, options):
        """Convert using Playwright (good for complex layouts)"""
        # Default options for legal documents
        default_options = {
            'format': 'Letter',
            'margin': {
                'top': '1in',
                'right': '1in', 
                'bottom': '1in',
                'left': '1in'
            },
            'print_background': True,
            'prefer_css_page_size': True
        }
        default_options.update(options)
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Load HTML file
            page.goto(f"file://{html_path.absolute()}")
            
            # Wait for content to load
            page.wait_for_load_state('networkidle')
            
            # Generate PDF
            page.pdf(path=str(output_pdf), **default_options)
            
            browser.close()
    
    def _get_legal_pdf_css(self):
        """Additional CSS for PDF generation to ensure legal formatting"""
        return """
        @page {
            size: letter;
            margin: 1in;
            @bottom-center {
                content: "Page " counter(page);
                font-family: "Times New Roman", serif;
                font-size: 10pt;
            }
        }
        
        body {
            font-family: "Times New Roman", serif;
            font-size: 14pt;
            line-height: 2.0;
            color: black;
        }
        
        /* Ensure proper page breaks */
        .page-break {
            page-break-before: always;
        }
        
        /* Prevent orphaned headings */
        .section-title {
            page-break-after: avoid;
        }
        
        /* Keep signature blocks together */
        .signature-block {
            page-break-inside: avoid;
        }
        
        /* Ensure proper table formatting */
        .caption-grid {
            page-break-inside: avoid;
        }
        """
    
    def convert_html_string_to_pdf(self, html_content, output_pdf, options=None):
        """
        Convert HTML string directly to PDF
        
        Args:
            html_content: HTML content as string
            output_pdf: Output PDF path
            options: Conversion options dictionary
        
        Returns:
            Path to generated PDF file
        """
        output_pdf = Path(output_pdf)
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        
        if self.method == "weasyprint":
            # Create PDF from string
            html_doc = weasyprint.HTML(string=html_content)
            css = weasyprint.CSS(string=self._get_legal_pdf_css())
            
            html_doc.write_pdf(
                str(output_pdf),
                stylesheets=[css],
                **(options or {})
            )
        
        elif self.method == "playwright":
            # Save HTML to temp file first
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html = f.name
            
            try:
                self._convert_with_playwright(Path(temp_html), output_pdf, options or {})
            finally:
                os.unlink(temp_html)
        
        print(f"PDF generated: {output_pdf}")
        return output_pdf

class LegalDocumentPDFGenerator:
    """High-level interface for generating PDFs from legal documents"""
    
    def __init__(self, method="weasyprint"):
        self.converter = HTMLToPDFConverter(method)
    
    def generate_pdf_from_markdown(self, markdown_files, document_type="motion", 
                                 metadata=None, output_pdf=None):
        """
        Generate PDF directly from Markdown files
        
        Args:
            markdown_files: List of Markdown file paths
            document_type: Type of document
            metadata: Document metadata
            output_pdf: Output PDF path
        
        Returns:
            Path to generated PDF
        """
        from html_template_engine import HTMLLegalDocumentGenerator
        
        # Generate HTML content
        html_generator = HTMLLegalDocumentGenerator()
        html_content = html_generator.generate_html_from_markdown(
            markdown_files, document_type, metadata or {}
        )
        
        # Default output path
        if output_pdf is None:
            output_pdf = f"{document_type}_document.pdf"
        
        # Convert to PDF
        return self.converter.convert_html_string_to_pdf(html_content, output_pdf)
    
    def generate_pdf_from_yaml(self, yaml_file, output_pdf=None):
        """
        Generate PDF from YAML file
        
        Args:
            yaml_file: Path to YAML file
            output_pdf: Output PDF path
        
        Returns:
            Path to generated PDF
        """
        from html_template_engine import HTMLLegalDocumentGenerator
        
        # Generate HTML content
        html_generator = HTMLLegalDocumentGenerator()
        html_content = html_generator.generate_html_from_yaml(yaml_file)
        
        # Default output path
        if output_pdf is None:
            yaml_path = Path(yaml_file)
            output_pdf = yaml_path.with_suffix('.pdf')
        
        # Convert to PDF
        return self.converter.convert_html_string_to_pdf(html_content, output_pdf)

def main():
    """Command line interface for HTML to PDF conversion"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python html_to_pdf.py convert input.html [output.pdf]")
        print("  python html_to_pdf.py markdown file1.md file2.md [type] [output.pdf]")
        print("  python html_to_pdf.py yaml input.yml [output.pdf]")
        return
    
    command = sys.argv[1].lower()
    
    if command == "convert":
        if len(sys.argv) < 3:
            print("Error: Please specify HTML file")
            return
        
        html_file = sys.argv[2]
        output_pdf = sys.argv[3] if len(sys.argv) > 3 else None
        
        converter = HTMLToPDFConverter()
        converter.convert_html_to_pdf(html_file, output_pdf)
    
    elif command == "markdown":
        if len(sys.argv) < 3:
            print("Error: Please specify Markdown files")
            return
        
        # Parse arguments
        args = sys.argv[2:]
        markdown_files = []
        document_type = "motion"
        output_pdf = None
        
        for arg in args:
            if arg.endswith('.md'):
                markdown_files.append(arg)
            elif arg.endswith('.pdf'):
                output_pdf = arg
            elif not os.path.exists(arg):  # Assume it's document type
                document_type = arg
        
        if not markdown_files:
            print("Error: No Markdown files specified")
            return
        
        # Basic metadata
        metadata = {
            'court_name': 'United States District Court',
            'court_division': 'Northern District of Georgia',
            'case_number': '1:25-cv-00000-ABC',
            'plaintiff_name': 'PLAINTIFF NAME',
            'defendant_name': 'DEFENDANT NAME',
            'document_title': f"Plaintiff's {document_type.title()}",
            'attorney_info': {
                'name': 'Attorney Name',
                'title': 'Pro Se'
            }
        }
        
        generator = LegalDocumentPDFGenerator()
        generator.generate_pdf_from_markdown(markdown_files, document_type, metadata, output_pdf)
    
    elif command == "yaml":
        if len(sys.argv) < 3:
            print("Error: Please specify YAML file")
            return
        
        yaml_file = sys.argv[2]
        output_pdf = sys.argv[3] if len(sys.argv) > 3 else None
        
        generator = LegalDocumentPDFGenerator()
        generator.generate_pdf_from_yaml(yaml_file, output_pdf)
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
