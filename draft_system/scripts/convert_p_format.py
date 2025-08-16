#!/usr/bin/env python3
"""
Convert P-format paragraph numbering to standard format
Converts **P1**, **P2** etc. to **1.**, **2.** etc.
"""

import re
import os
from pathlib import Path

def convert_p_format_in_file(file_path: Path) -> int:
    """Convert P-format numbering in a single file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Convert **P15** to **15.**, **P16** to **16.**, etc.
    def replace_p_format(match):
        number = match.group(1)
        return f"**{number}.**"

    # Pattern to match **P1**, **P15**, **P123**, etc. (any number after P)
    content = re.sub(r'\*\*P(\d+)\*\*', replace_p_format, content)
    
    # Count changes
    changes = len(re.findall(r'\*\*P\d+\*\*', original_content))
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {file_path.name}: Converted {changes} P-format paragraphs")
    else:
        print(f"ℹ️  {file_path.name}: No P-format paragraphs found")
    
    return changes

def convert_p_format_in_folder(folder_path: str) -> int:
    """Convert P-format numbering in all markdown files in a folder"""
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    # Find draft content folder
    draft_content_dir = folder / "draft_content"
    if not draft_content_dir.exists():
        draft_content_dir = folder
    
    # Get all markdown files
    md_files = sorted([f for f in draft_content_dir.glob("*.md")])
    
    total_changes = 0
    for md_file in md_files:
        changes = convert_p_format_in_file(md_file)
        total_changes += changes
    
    return total_changes

def main():
    """Command line interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python convert_p_format.py <document_folder>")
        return
    
    folder_path = sys.argv[1]
    
    try:
        total_changes = convert_p_format_in_folder(folder_path)
        
        print(f"\n🎉 P-format conversion complete!")
        print(f"Total paragraphs converted: {total_changes}")
        
        if total_changes > 0:
            print("\nRecommendation: Run format_validator.py to verify the changes.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
