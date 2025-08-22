#!/usr/bin/env python3
"""
Exhibit Management System for Draft Agent
Handles exhibit organization, naming, and the three-file system
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json
import shutil
import re

class ExhibitManager:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.exhibits_master = self.base_dir / "exhibits_master"
        self.exhibits_master.mkdir(exist_ok=True)
        self.exhibit_index_file = self.exhibits_master / "exhibit_index.json"
        self.load_exhibit_index()
    
    def load_exhibit_index(self):
        """Load or create exhibit index"""
        if self.exhibit_index_file.exists():
            with open(self.exhibit_index_file, 'r') as f:
                self.exhibit_index = json.load(f)
        else:
            self.exhibit_index = {
                "last_updated": datetime.now().isoformat(),
                "exhibits": {},
                "next_letter": "A"
            }
            self.save_exhibit_index()
    
    def save_exhibit_index(self):
        """Save exhibit index to file"""
        self.exhibit_index["last_updated"] = datetime.now().isoformat()
        with open(self.exhibit_index_file, 'w') as f:
            json.dump(self.exhibit_index, f, indent=2)
    
    def get_next_exhibit_letter(self):
        """Get the next available exhibit letter"""
        current = self.exhibit_index["next_letter"]
        
        # Increment to next letter
        if len(current) == 1:
            if current == 'Z':
                next_letter = 'AA'
            else:
                next_letter = chr(ord(current) + 1)
        else:
            # Handle AA, AB, etc.
            if current[-1] == 'Z':
                if len(current) == 2 and current[0] == 'Z':
                    next_letter = 'AAA'
                else:
                    next_letter = chr(ord(current[0]) + 1) + 'A'
            else:
                next_letter = current[:-1] + chr(ord(current[-1]) + 1)
        
        self.exhibit_index["next_letter"] = next_letter
        return current
    
    def create_exhibit_entry(self, original_file, description, exhibit_letter=None, location="master"):
        """Create a new exhibit entry with three-file system"""
        original_file = Path(original_file)
        
        if not original_file.exists():
            raise FileNotFoundError(f"Original file not found: {original_file}")
        
        # Get exhibit letter
        if not exhibit_letter:
            exhibit_letter = self.get_next_exhibit_letter()
        
        # Determine location
        if location == "master":
            exhibit_dir = self.exhibits_master
        else:
            exhibit_dir = Path(location)
            exhibit_dir.mkdir(parents=True, exist_ok=True)
        
        # Create safe filename base
        safe_description = re.sub(r'[^\w\s-]', '', description).strip()
        safe_description = re.sub(r'[-\s]+', '_', safe_description).lower()
        base_name = f"exhibit_{exhibit_letter.lower()}_{safe_description}"
        
        # Create three files
        files_created = {}
        
        # 1. Original file
        original_dest = exhibit_dir / f"{base_name}_original{original_file.suffix}"
        shutil.copy2(original_file, original_dest)
        files_created['original'] = str(original_dest)
        
        # 2. Text file (placeholder - will be filled by document processor)
        text_dest = exhibit_dir / f"{base_name}_text.txt"
        with open(text_dest, 'w') as f:
            f.write(f"Exhibit {exhibit_letter} - Text Extraction\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write("Text extraction pending. Use document_processor.py to extract text from original file.\n")
        files_created['text'] = str(text_dest)
        
        # 3. Summary file
        summary_dest = exhibit_dir / f"{base_name}_summary.md"
        self.create_exhibit_summary(summary_dest, exhibit_letter, description, original_file)
        files_created['summary'] = str(summary_dest)
        
        # Update exhibit index
        exhibit_id = f"exhibit_{exhibit_letter.lower()}"
        self.exhibit_index["exhibits"][exhibit_id] = {
            "letter": exhibit_letter,
            "description": description,
            "original_filename": original_file.name,
            "created_date": datetime.now().isoformat(),
            "location": str(exhibit_dir),
            "files": files_created,
            "status": "created"
        }
        
        self.save_exhibit_index()
        
        return exhibit_letter, files_created
    
    def create_exhibit_summary(self, summary_path, exhibit_letter, description, original_file):
        """Create exhibit summary markdown file"""
        content = f"""# Exhibit {exhibit_letter} - {description}

## Document Information
- **Exhibit Letter**: {exhibit_letter}
- **Original Filename**: {original_file.name}
- **Document Type**: {self.guess_document_type(original_file)}
- **Date Added**: {datetime.now().strftime('%Y-%m-%d')}
- **Source**: [Where this document was obtained]

## Content Summary
{description}

## Legal Relevance
[How this exhibit relates to the case and supports legal arguments]

## Key Points
- [Important point 1]
- [Important point 2]
- [Important point 3]

## Authentication Notes
- **Custodian**: [Who can authenticate this document]
- **Chain of Custody**: [How document was obtained and maintained]
- **Foundation Requirements**: [What foundation is needed for admission]

## Cross-References
- **Related Exhibits**: [Other exhibits that relate to this one]
- **Supports Claims**: [Which legal arguments this exhibit supports]
- **Referenced In**: [Which documents reference this exhibit]

## Usage Notes
- **Court Admissibility**: [Assessment of likelihood of admission]
- **Strategic Value**: [How this exhibit fits into case strategy]
- **Limitations**: [Any weaknesses or limitations of this exhibit]

---

**Processing Status**: Created
**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(summary_path, 'w') as f:
            f.write(content)
    
    def guess_document_type(self, file_path):
        """Guess document type from file extension"""
        ext = file_path.suffix.lower()
        type_map = {
            '.pdf': 'PDF Document',
            '.doc': 'Word Document',
            '.docx': 'Word Document',
            '.jpg': 'Image/Photo',
            '.jpeg': 'Image/Photo',
            '.png': 'Image/Photo',
            '.tiff': 'Image/Photo',
            '.txt': 'Text Document',
            '.csv': 'Spreadsheet/Data',
            '.xlsx': 'Excel Spreadsheet',
            '.xls': 'Excel Spreadsheet'
        }
        return type_map.get(ext, 'Unknown Document Type')
    
    def list_exhibits(self, location="all"):
        """List all exhibits with their information"""
        exhibits = []
        for exhibit_id, info in self.exhibit_index["exhibits"].items():
            if location == "all" or location in info["location"]:
                exhibits.append({
                    "id": exhibit_id,
                    "letter": info["letter"],
                    "description": info["description"],
                    "created": info["created_date"],
                    "location": info["location"],
                    "status": info.get("status", "unknown")
                })
        
        return sorted(exhibits, key=lambda x: x["letter"])
    
    def get_exhibit_info(self, exhibit_letter):
        """Get information about a specific exhibit"""
        exhibit_id = f"exhibit_{exhibit_letter.lower()}"
        return self.exhibit_index["exhibits"].get(exhibit_id)
    
    def update_exhibit_status(self, exhibit_letter, status, notes=None):
        """Update exhibit processing status"""
        exhibit_id = f"exhibit_{exhibit_letter.lower()}"
        if exhibit_id in self.exhibit_index["exhibits"]:
            self.exhibit_index["exhibits"][exhibit_id]["status"] = status
            self.exhibit_index["exhibits"][exhibit_id]["last_updated"] = datetime.now().isoformat()
            if notes:
                self.exhibit_index["exhibits"][exhibit_id]["notes"] = notes
            self.save_exhibit_index()
            return True
        return False
    
    def generate_exhibit_list(self, output_file=None):
        """Generate a formatted exhibit list for court filing"""
        exhibits = self.list_exhibits()
        
        content = f"""# EXHIBIT LIST

**Case**: [Case Name]
**Date**: {datetime.now().strftime('%B %d, %Y')}

## Exhibits

"""
        
        for exhibit in exhibits:
            content += f"**Exhibit {exhibit['letter']}**: {exhibit['description']}\n\n"
        
        content += f"""
---

**Total Exhibits**: {len(exhibits)}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
        
        return content
    
    def create_active_draft_exhibits(self, draft_folder, exhibit_letters):
        """Copy specific exhibits to an active draft folder"""
        draft_folder = Path(draft_folder)
        exhibits_dir = draft_folder / "exhibits"
        exhibits_dir.mkdir(parents=True, exist_ok=True)
        
        copied_exhibits = []
        
        for letter in exhibit_letters:
            exhibit_info = self.get_exhibit_info(letter)
            if not exhibit_info:
                print(f"Warning: Exhibit {letter} not found")
                continue
            
            # Copy all three files
            for file_type, file_path in exhibit_info["files"].items():
                src_path = Path(file_path)
                if src_path.exists():
                    dest_path = exhibits_dir / src_path.name
                    shutil.copy2(src_path, dest_path)
                    copied_exhibits.append(dest_path)
        
        return copied_exhibits

def main():
    """Command line interface for exhibit management"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python exhibit_manager.py create <file_path> <description> [exhibit_letter]")
        print("  python exhibit_manager.py list")
        print("  python exhibit_manager.py info <exhibit_letter>")
        print("  python exhibit_manager.py generate-list [output_file]")
        sys.exit(1)
    
    manager = ExhibitManager()
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) < 4:
            print("Usage: python exhibit_manager.py create <file_path> <description> [exhibit_letter]")
            sys.exit(1)
        
        file_path = sys.argv[2]
        description = sys.argv[3]
        exhibit_letter = sys.argv[4] if len(sys.argv) > 4 else None
        
        try:
            letter, files = manager.create_exhibit_entry(file_path, description, exhibit_letter)
            print(f"Created Exhibit {letter}:")
            for file_type, file_path in files.items():
                print(f"  {file_type.title()}: {file_path}")
        except Exception as e:
            print(f"Error creating exhibit: {e}")
            sys.exit(1)
    
    elif command == "list":
        exhibits = manager.list_exhibits()
        print(f"Total Exhibits: {len(exhibits)}\n")
        for exhibit in exhibits:
            print(f"Exhibit {exhibit['letter']}: {exhibit['description']}")
            print(f"  Created: {exhibit['created']}")
            print(f"  Status: {exhibit['status']}")
            print()
    
    elif command == "info":
        if len(sys.argv) < 3:
            print("Usage: python exhibit_manager.py info <exhibit_letter>")
            sys.exit(1)
        
        letter = sys.argv[2]
        info = manager.get_exhibit_info(letter)
        if info:
            print(f"Exhibit {info['letter']}: {info['description']}")
            print(f"Original File: {info['original_filename']}")
            print(f"Created: {info['created_date']}")
            print(f"Location: {info['location']}")
            print(f"Status: {info.get('status', 'unknown')}")
            print("\nFiles:")
            for file_type, file_path in info['files'].items():
                print(f"  {file_type.title()}: {file_path}")
        else:
            print(f"Exhibit {letter} not found")
    
    elif command == "generate-list":
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        content = manager.generate_exhibit_list(output_file)
        if output_file:
            print(f"Exhibit list generated: {output_file}")
        else:
            print(content)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
