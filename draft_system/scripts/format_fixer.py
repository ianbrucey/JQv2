#!/usr/bin/env python3
"""
Format Fixer for Legal Document Markdown
Automatically fixes common formatting issues to comply with unified standards
"""

import re
import os
from pathlib import Path
from typing import List, Tuple

class FormatFixer:
    """Automatically fixes markdown formatting issues"""
    
    def __init__(self):
        self.fixes_applied = []
    
    def fix_document_folder(self, folder_path: str) -> dict:
        """
        Fix all markdown files in a document folder
        
        Args:
            folder_path: Path to document folder
        
        Returns:
            Report of fixes applied
        """
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Document folder not found: {folder_path}")
        
        self.fixes_applied = []
        
        # Find draft content folder
        draft_content_dir = folder / "draft_content"
        if not draft_content_dir.exists():
            draft_content_dir = folder
        
        # Get all markdown files
        md_files = sorted([f for f in draft_content_dir.glob("*.md")])
        
        # Fix each file
        for md_file in md_files:
            self._fix_markdown_file(md_file)
        
        return {
            'files_processed': len(md_files),
            'total_fixes': len(self.fixes_applied),
            'fixes': self.fixes_applied
        }
    
    def _fix_markdown_file(self, md_file: Path):
        """Fix a single markdown file"""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = self._fix_paragraph_numbering(content, md_file)
        content = self._fix_legal_citations(content, md_file)
        content = self._fix_headers(content, md_file)
        content = self._fix_line_lengths(content, md_file)
        
        # Write back if changes were made
        if content != original_content:
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.fixes_applied.append({
                'file': str(md_file.name),
                'type': 'multiple_fixes',
                'message': 'Applied formatting fixes'
            })
    
    def _fix_paragraph_numbering(self, content: str, md_file: Path) -> str:
        """Fix paragraph numbering format"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix unformatted paragraph numbers: 1. -> **1.**
            if re.match(r'^\d+\.\s', line):
                match = re.match(r'^(\d+)\.\s(.*)', line)
                if match:
                    num, text = match.groups()
                    line = f"**{num}.** {text}"
                    self.fixes_applied.append({
                        'file': str(md_file.name),
                        'type': 'paragraph_numbering',
                        'message': f'Fixed paragraph number: {num}'
                    })
            
            # Fix single asterisk format: *1* -> **1.**
            line = re.sub(r'\*(\d+)\*', r'**\1.**', line)
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_legal_citations(self, content: str, md_file: Path) -> str:
        """Fix legal citation formatting"""
        # Fix unformatted statutes
        statute_patterns = [
            (r'\b(\d+\s+U\.S\.C\.\s+§\s+\d+[a-z]*(?:\([^)]+\))?)', r'**\1**'),
            (r'\b(\d+\s+C\.F\.R\.\s+§\s+\d+[.\d]*)', r'**\1**'),
            (r'\b([A-Z]{2,}\s+§?\s*\d+[.\d]*(?:\([^)]+\))?)', r'**\1**'),  # State statutes
            (r'\b(Fed\.\s+R\.\s+Civ\.\s+P\.\s+\d+[a-z]*(?:\([^)]+\))?)', r'**\1**'),
        ]
        
        for pattern, replacement in statute_patterns:
            # Only apply if not already bold
            def replace_if_not_bold(match):
                full_match = match.group(0)
                if '**' in full_match:
                    return full_match  # Already formatted
                return replacement.replace(r'\1', match.group(1))
            
            content = re.sub(pattern, replace_if_not_bold, content)
        
        # Fix case names (make italic if not already)
        case_pattern = r'\b([A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+[^,]*)'
        def fix_case_name(match):
            case_name = match.group(1)
            if '*' in case_name:
                return case_name  # Already formatted
            return f'*{case_name}*'
        
        content = re.sub(case_pattern, fix_case_name, content)
        
        return content
    
    def _fix_headers(self, content: str, md_file: Path) -> str:
        """Fix header formatting issues"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if line.strip().startswith('#'):
                # Count header level
                header_level = len(line) - len(line.lstrip('#'))
                
                # Fix headers deeper than H3
                if header_level > 3:
                    # Convert H4+ to H3
                    header_text = line.lstrip('#').strip()
                    line = f"### {header_text}"
                    self.fixes_applied.append({
                        'file': str(md_file.name),
                        'type': 'header_level',
                        'message': f'Converted H{header_level} to H3: {header_text}'
                    })
                
                # Fix header case (ensure starts with uppercase)
                header_text = line.lstrip('#').strip()
                if header_text and header_text[0].islower():
                    fixed_text = header_text[0].upper() + header_text[1:]
                    line = '#' * (len(line) - len(line.lstrip('#'))) + ' ' + fixed_text
                    self.fixes_applied.append({
                        'file': str(md_file.name),
                        'type': 'header_case',
                        'message': f'Fixed header case: {header_text}'
                    })
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_line_lengths(self, content: str, md_file: Path) -> str:
        """Fix line length issues by breaking long lines"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if len(line) > 120:
                # Try to break at sentence boundaries
                if '. ' in line:
                    sentences = line.split('. ')
                    current_line = sentences[0]
                    
                    for sentence in sentences[1:]:
                        if len(current_line + '. ' + sentence) <= 120:
                            current_line += '. ' + sentence
                        else:
                            fixed_lines.append(current_line + '.')
                            current_line = sentence
                    
                    if current_line:
                        fixed_lines.append(current_line)
                    
                    self.fixes_applied.append({
                        'file': str(md_file.name),
                        'type': 'line_length',
                        'message': f'Broke long line into sentences'
                    })
                else:
                    # Try to break at word boundaries
                    words = line.split()
                    current_line = ""
                    
                    for word in words:
                        if len(current_line + ' ' + word) <= 120:
                            current_line += (' ' if current_line else '') + word
                        else:
                            if current_line:
                                fixed_lines.append(current_line)
                            current_line = word
                    
                    if current_line:
                        fixed_lines.append(current_line)
                    
                    self.fixes_applied.append({
                        'file': str(md_file.name),
                        'type': 'line_length',
                        'message': f'Broke long line at word boundaries'
                    })
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def print_report(self, report: dict):
        """Print formatted fix report"""
        print(f"Format Fixer Report")
        print("=" * 30)
        print(f"Files Processed: {report['files_processed']}")
        print(f"Total Fixes: {report['total_fixes']}")
        print()
        
        if report['fixes']:
            print("Fixes Applied:")
            print("-" * 20)
            
            by_file = {}
            for fix in report['fixes']:
                file_name = fix['file']
                if file_name not in by_file:
                    by_file[file_name] = []
                by_file[file_name].append(fix)
            
            for file_name, fixes in by_file.items():
                print(f"\n📄 {file_name}:")
                for fix in fixes:
                    print(f"  ✅ {fix['type']}: {fix['message']}")

def main():
    """Command line interface for format fixer"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python format_fixer.py <document_folder>")
        return
    
    folder_path = sys.argv[1]
    
    fixer = FormatFixer()
    
    try:
        report = fixer.fix_document_folder(folder_path)
        fixer.print_report(report)
        
        print(f"\n✅ Formatting fixes completed!")
        print("Run format_validator.py again to verify fixes.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
