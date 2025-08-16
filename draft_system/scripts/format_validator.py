#!/usr/bin/env python3
"""
Format Validator for Legal Document Markdown
Validates markdown files against unified formatting standards
"""

import re
import os
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ValidationLevel(Enum):
    STRICT = "strict"
    STANDARD = "standard"
    LENIENT = "lenient"

@dataclass
class ValidationError:
    """Represents a validation error"""
    file_path: str
    line_number: int
    error_type: str
    message: str
    severity: str  # 'error', 'warning', 'info'

class FormatValidator:
    """Validates markdown formatting against unified standards"""
    
    def __init__(self, standards_dir: str = None, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """Initialize validator with standards directory"""
        if standards_dir is None:
            standards_dir = Path(__file__).parent.parent / "standards"
        
        self.standards_dir = Path(standards_dir)
        self.validation_level = validation_level
        self.validation_rules = self._load_validation_rules()
        self.document_specs = self._load_document_specifications()
        self.errors = []
    
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
    
    def validate_document_folder(self, folder_path: str) -> Dict:
        """
        Validate all markdown files in a document folder
        
        Args:
            folder_path: Path to document folder
        
        Returns:
            Validation report
        """
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Document folder not found: {folder_path}")
        
        self.errors = []  # Reset errors
        
        # Load metadata
        metadata = self._load_metadata(folder)
        document_type = metadata.get('document_info', {}).get('type', 'unknown')
        
        # Find draft content folder
        draft_content_dir = folder / "draft_content"
        if not draft_content_dir.exists():
            draft_content_dir = folder
        
        # Validate folder structure
        self._validate_folder_structure(folder)
        
        # Validate metadata
        self._validate_metadata(metadata, folder)
        
        # Get all markdown files
        md_files = sorted([f for f in draft_content_dir.glob("*.md")])
        
        # Validate each file
        for md_file in md_files:
            self._validate_markdown_file(md_file, document_type)
        
        # Validate document structure
        self._validate_document_structure(md_files, document_type)
        
        # Generate report
        return self._generate_report()
    
    def _load_metadata(self, folder: Path) -> Dict:
        """Load metadata.yml from document folder"""
        metadata_file = folder / "metadata.yml"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _validate_folder_structure(self, folder: Path):
        """Validate folder structure against standards"""
        required_subfolders = [
            "draft_content",
            "research", 
            "exhibits",
            "reference_material",
            "case_documents"
        ]
        
        for subfolder in required_subfolders:
            subfolder_path = folder / subfolder
            if not subfolder_path.exists():
                if self.validation_level == ValidationLevel.STRICT:
                    self.errors.append(ValidationError(
                        file_path=str(folder),
                        line_number=0,
                        error_type="folder_structure",
                        message=f"Missing required subfolder: {subfolder}",
                        severity="error"
                    ))
                else:
                    self.errors.append(ValidationError(
                        file_path=str(folder),
                        line_number=0,
                        error_type="folder_structure",
                        message=f"Missing recommended subfolder: {subfolder}",
                        severity="warning"
                    ))
    
    def _validate_metadata(self, metadata: Dict, folder: Path):
        """Validate metadata.yml completeness"""
        required_fields = self.validation_rules.get('metadata_requirements', {}).get('required_fields', [])
        
        for field_path in required_fields:
            if not self._get_nested_value(metadata, field_path):
                self.errors.append(ValidationError(
                    file_path=str(folder / "metadata.yml"),
                    line_number=0,
                    error_type="metadata",
                    message=f"Missing required metadata field: {field_path}",
                    severity="error"
                ))
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested dictionary value using dot notation"""
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _validate_markdown_file(self, md_file: Path, document_type: str):
        """Validate a single markdown file"""
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check line length
            if len(line) > self.validation_rules.get('quality_standards', {}).get('line_length', {}).get('max', 120):
                self.errors.append(ValidationError(
                    file_path=str(md_file),
                    line_number=line_num,
                    error_type="line_length",
                    message=f"Line exceeds maximum length ({len(line)} characters)",
                    severity="warning"
                ))
            
            # Validate paragraph numbering
            self._validate_paragraph_numbering(line, md_file, line_num)
            
            # Validate headers
            self._validate_headers(line, md_file, line_num)
            
            # Validate legal citations
            self._validate_legal_citations(line, md_file, line_num)
            
            # Validate cross-references
            self._validate_cross_references(line, md_file, line_num)
            
            # Check prohibited words
            self._check_prohibited_words(line, md_file, line_num)
    
    def _validate_paragraph_numbering(self, line: str, file_path: Path, line_num: int):
        """Validate paragraph numbering format"""
        # Check for numbered paragraphs
        if re.search(r'^\d+\.', line.strip()):
            self.errors.append(ValidationError(
                file_path=str(file_path),
                line_number=line_num,
                error_type="paragraph_numbering",
                message="Paragraph numbers must be bold: **1.** not 1.",
                severity="error"
            ))
        
        # Check for correct format
        if re.search(r'\*\*\d+\.\*\*', line):
            # Valid format found
            pass
        elif re.search(r'\*\d+\*', line):
            self.errors.append(ValidationError(
                file_path=str(file_path),
                line_number=line_num,
                error_type="paragraph_numbering",
                message="Use double asterisks for bold: **1.** not *1*",
                severity="error"
            ))
    
    def _validate_headers(self, line: str, file_path: Path, line_num: int):
        """Validate header formatting"""
        if line.strip().startswith('#'):
            header_level = len(line) - len(line.lstrip('#'))
            
            # Check maximum header level
            if header_level > 3:
                self.errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=line_num,
                    error_type="headers",
                    message=f"Headers deeper than H3 (###) are not allowed (found H{header_level})",
                    severity="error"
                ))
            
            # Check header format
            header_text = line.lstrip('#').strip()
            if header_text and not header_text[0].isupper():
                self.errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=line_num,
                    error_type="headers",
                    message="Headers must start with uppercase letters",
                    severity="warning"
                ))
            
            # Check header length
            if len(header_text) > 80:
                self.errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=line_num,
                    error_type="headers",
                    message="Header exceeds maximum length of 80 characters",
                    severity="warning"
                ))
    
    def _validate_legal_citations(self, line: str, file_path: Path, line_num: int):
        """Validate legal citation formatting"""
        # Check for unformatted statutes (should be bold)
        statute_pattern = r'\b\d+\s+U\.S\.C\.\s+§\s+\d+'
        if re.search(statute_pattern, line) and not re.search(r'\*\*.*' + statute_pattern + r'.*\*\*', line):
            self.errors.append(ValidationError(
                file_path=str(file_path),
                line_number=line_num,
                error_type="legal_citations",
                message="Statutes must be bold: **15 U.S.C. § 1681n**",
                severity="error"
            ))
        
        # Check for unformatted case names (should be italic)
        case_pattern = r'\b[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+'
        if re.search(case_pattern, line) and not re.search(r'\*.*' + case_pattern + r'.*\*', line):
            self.errors.append(ValidationError(
                file_path=str(file_path),
                line_number=line_num,
                error_type="legal_citations",
                message="Case names must be italic: *Smith v. Jones*",
                severity="warning"
            ))
    
    def _validate_cross_references(self, line: str, file_path: Path, line_num: int):
        """Validate cross-reference formatting"""
        # Check label format
        labels = re.findall(r'\{\{LABEL:([^}]+)\}\}', line)
        for label in labels:
            if not re.match(r'^[a-z][a-z0-9_]*$', label):
                self.errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=line_num,
                    error_type="cross_references",
                    message=f"Label names must be lowercase with underscores: {{{{LABEL:{label}}}}}",
                    severity="error"
                ))
        
        # Check reference format
        refs = re.findall(r'\{\{REF:([^}]+)\}\}', line)
        for ref in refs:
            if not re.match(r'^[a-z][a-z0-9_]*$', ref):
                self.errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=line_num,
                    error_type="cross_references",
                    message=f"Reference names must be lowercase with underscores: {{{{REF:{ref}}}}}",
                    severity="error"
                ))
    
    def _check_prohibited_words(self, line: str, file_path: Path, line_num: int):
        """Check for prohibited weak modifiers"""
        prohibited_words = self.validation_rules.get('quality_standards', {}).get('language', {}).get('prohibited_words', [])
        
        for word in prohibited_words:
            if re.search(r'\b' + word + r'\b', line, re.IGNORECASE):
                self.errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=line_num,
                    error_type="language",
                    message=f"Avoid weak modifier: '{word}'",
                    severity="warning"
                ))
    
    def _validate_document_structure(self, md_files: List[Path], document_type: str):
        """Validate overall document structure"""
        if document_type not in self.document_specs:
            return
        
        spec = self.document_specs[document_type]
        required_sections = spec.get('required_sections', [])
        
        # Check file naming convention
        for md_file in md_files:
            if not re.match(r'^\d{2}_', md_file.name):
                self.errors.append(ValidationError(
                    file_path=str(md_file),
                    line_number=0,
                    error_type="file_naming",
                    message="Files should use numbered prefixes: 01_, 02_, etc.",
                    severity="warning"
                ))
    
    def _generate_report(self) -> Dict:
        """Generate validation report"""
        errors = [e for e in self.errors if e.severity == 'error']
        warnings = [e for e in self.errors if e.severity == 'warning']
        
        return {
            'is_valid': len(errors) == 0,
            'total_issues': len(self.errors),
            'errors': len(errors),
            'warnings': len(warnings),
            'validation_level': self.validation_level.value,
            'issues': [
                {
                    'file': e.file_path,
                    'line': e.line_number,
                    'type': e.error_type,
                    'message': e.message,
                    'severity': e.severity
                }
                for e in self.errors
            ]
        }
    
    def print_report(self, report: Dict):
        """Print formatted validation report"""
        print(f"Validation Report ({report['validation_level']})")
        print("=" * 50)
        print(f"Status: {'PASSED' if report['is_valid'] else 'FAILED'}")
        print(f"Total Issues: {report['total_issues']}")
        print(f"Errors: {report['errors']}")
        print(f"Warnings: {report['warnings']}")
        print()
        
        if report['issues']:
            print("Issues Found:")
            print("-" * 30)
            
            for issue in report['issues']:
                severity_symbol = "❌" if issue['severity'] == 'error' else "⚠️"
                file_name = Path(issue['file']).name
                print(f"{severity_symbol} {file_name}:{issue['line']} [{issue['type']}]")
                print(f"   {issue['message']}")
                print()

def main():
    """Command line interface for format validator"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python format_validator.py <document_folder> [validation_level]")
        print("Validation levels: strict, standard, lenient")
        return
    
    folder_path = sys.argv[1]
    validation_level = ValidationLevel.STANDARD
    
    if len(sys.argv) > 2:
        level_str = sys.argv[2].lower()
        if level_str in ['strict', 'standard', 'lenient']:
            validation_level = ValidationLevel(level_str)
    
    validator = FormatValidator(validation_level=validation_level)
    
    try:
        report = validator.validate_document_folder(folder_path)
        validator.print_report(report)
        
        # Exit with error code if validation failed
        sys.exit(0 if report['is_valid'] else 1)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
