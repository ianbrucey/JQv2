"""
Draft Workspace API Routes
- List drafts for a case
- Create a draft folder with complete standardized structure per draft_system guidelines

Notes:
- Files live under: /tmp/legal_workspace/cases/case-{case_id}/draft_system/active_drafts
- Creates complete folder structure: draft_content/, html_preview/, research/, exhibits/, etc.
- Generates type-specific sections with proper numbering and legal document structure
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from pathlib import Path
import os
import re
import uuid
import json as jsonlib
import yaml
from datetime import datetime, timezone

from openhands.server.dependencies import get_dependencies
from openhands.server.legal_workspace_manager import (
    get_legal_workspace_manager,
    initialize_legal_workspace_manager,
)
from openhands.server.shared import config
from openhands.storage.legal_case_store import FileLegalCaseStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/legal", tags=["drafts"], dependencies=get_dependencies())


class CreateDraftRequest(BaseModel):
    draft_type: str
    name: str


class DraftResponse(BaseModel):
    draft_id: str
    name: str
    type: str
    created_at: str
    updated_at: str
    sections: List[Dict[str, str]]


# Draft Templates - Complete standardized structures per draft_system guidelines
DRAFT_TEMPLATES = {
    "complaint": {
        "sections": [
            ("01_caption_and_parties.md", "Caption and Parties", "# Caption and Parties\n\n## Case Caption\n\n[Case Name]\n[Court Information]\n[Case Number]\n\n## Parties\n\n### Plaintiff(s)\n\n### Defendant(s)\n\n"),
            ("02_jurisdiction_and_venue.md", "Jurisdiction and Venue", "# Jurisdiction and Venue\n\n## Subject Matter Jurisdiction\n\n## Personal Jurisdiction\n\n## Venue\n\n"),
            ("03_factual_allegations.md", "Factual Allegations", "# Factual Allegations\n\n## Background\n\n## Relevant Facts\n\n## Timeline of Events\n\n"),
            ("04_causes_of_action.md", "Causes of Action", "# Causes of Action\n\n## Count I: [Cause of Action]\n\n### Elements\n\n### Factual Basis\n\n### Damages\n\n"),
            ("05_prayer_for_relief.md", "Prayer for Relief", "# Prayer for Relief\n\nWHEREFORE, Plaintiff respectfully requests that this Court:\n\n1. \n2. \n3. Grant such other relief as this Court deems just and proper.\n\n"),
        ],
        "document_type": "complaint",
        "description": "A formal legal complaint initiating civil litigation"
    },
    "motion": {
        "sections": [
            ("01_caption_and_title.md", "Caption and Title", "# Caption and Title\n\n## Case Caption\n\n[Case Name]\n[Court Information]\n[Case Number]\n\n## Motion Title\n\n[Motion Type and Relief Sought]\n\n"),
            ("02_introduction.md", "Introduction", "# Introduction\n\n[Brief overview of the motion and relief sought]\n\n## Nature of Motion\n\n## Relief Requested\n\n"),
            ("03_statement_of_facts.md", "Statement of Facts", "# Statement of Facts\n\n## Procedural Background\n\n## Relevant Facts\n\n## Current Posture\n\n"),
            ("04_legal_standard.md", "Legal Standard", "# Legal Standard\n\n## Applicable Standard\n\n## Burden of Proof\n\n## Legal Framework\n\n"),
            ("05_argument.md", "Argument", "# Argument\n\n## I. [First Argument Heading]\n\n### A. [Sub-argument]\n\n### B. [Sub-argument]\n\n## II. [Second Argument Heading]\n\n"),
            ("06_conclusion.md", "Conclusion", "# Conclusion\n\nFor the foregoing reasons, [Party] respectfully requests that this Court:\n\n1. \n2. \n3. Grant such other relief as this Court deems just and proper.\n\n"),
        ],
        "document_type": "motion",
        "description": "A formal request for court action or ruling"
    },
    "pleading": {
        "sections": [
            ("01_caption.md", "Caption", "# Caption\n\n[Case Name]\n[Court Information]\n[Case Number]\n\n"),
            ("02_preliminary_statement.md", "Preliminary Statement", "# Preliminary Statement\n\n[Overview of the pleading and its purpose]\n\n"),
            ("03_allegations.md", "Allegations", "# Allegations\n\n## General Allegations\n\n## Specific Allegations\n\n"),
            ("04_affirmative_defenses.md", "Affirmative Defenses", "# Affirmative Defenses\n\n## First Affirmative Defense\n\n## Second Affirmative Defense\n\n"),
            ("05_prayer_for_relief.md", "Prayer for Relief", "# Prayer for Relief\n\nWHEREFORE, [Party] respectfully requests:\n\n1. \n2. \n3. Such other relief as this Court deems just and proper.\n\n"),
        ],
        "document_type": "pleading",
        "description": "A formal written statement of claims or defenses"
    },
    "demurrer": {
        "sections": [
            ("01_caption_and_title.md", "Caption and Title", "# Caption and Title\n\n## Case Caption\n\n[Case Name]\n[Court Information]\n[Case Number]\n\n## Demurrer Title\n\nDEMURRER TO [PLEADING]\n\n"),
            ("02_introduction.md", "Introduction", "# Introduction\n\n[Party] hereby demurs to the [pleading] filed by [opposing party] on the following grounds:\n\n"),
            ("03_grounds_for_demurrer.md", "Grounds for Demurrer", "# Grounds for Demurrer\n\n## I. Failure to State a Cause of Action\n\n## II. Uncertainty\n\n## III. [Additional Grounds]\n\n"),
            ("04_legal_argument.md", "Legal Argument", "# Legal Argument\n\n## Standard for Demurrer\n\n## Analysis of Pleading Defects\n\n## Case Law Support\n\n"),
            ("05_conclusion.md", "Conclusion", "# Conclusion\n\nFor the foregoing reasons, [Party] respectfully requests that this Court sustain this demurrer and dismiss the [pleading] with prejudice.\n\n"),
        ],
        "document_type": "demurrer",
        "description": "A challenge to the legal sufficiency of a pleading"
    },
    "brief": {
        "sections": [
            ("01_table_of_contents.md", "Table of Contents", "# Table of Contents\n\n[To be generated based on final brief structure]\n\n"),
            ("02_table_of_authorities.md", "Table of Authorities", "# Table of Authorities\n\n## Cases\n\n## Statutes\n\n## Rules\n\n## Secondary Sources\n\n"),
            ("03_statement_of_issues.md", "Statement of Issues", "# Statement of Issues\n\n1. \n2. \n3. \n\n"),
            ("04_statement_of_facts.md", "Statement of Facts", "# Statement of Facts\n\n## Procedural History\n\n## Factual Background\n\n## Standard of Review\n\n"),
            ("05_summary_of_argument.md", "Summary of Argument", "# Summary of Argument\n\n[Concise overview of main arguments]\n\n"),
            ("06_argument.md", "Argument", "# Argument\n\n## I. [First Major Argument]\n\n### A. [Sub-argument]\n\n### B. [Sub-argument]\n\n## II. [Second Major Argument]\n\n"),
            ("07_conclusion.md", "Conclusion", "# Conclusion\n\nFor the foregoing reasons, [Party] respectfully requests that this Court:\n\n1. \n2. \n3. \n\n"),
        ],
        "document_type": "brief",
        "description": "A comprehensive legal argument document"
    },
    "memo": {
        "sections": [
            ("01_header.md", "Header", "# Legal Memorandum\n\n**TO:** [Recipient]\n**FROM:** [Author]\n**DATE:** [Date]\n**RE:** [Subject Matter]\n\n"),
            ("02_executive_summary.md", "Executive Summary", "# Executive Summary\n\n[Brief overview of the legal issue and conclusion]\n\n"),
            ("03_issue_presented.md", "Issue Presented", "# Issue Presented\n\n[Concise statement of the legal question]\n\n"),
            ("04_brief_answer.md", "Brief Answer", "# Brief Answer\n\n[Direct answer to the legal question with brief reasoning]\n\n"),
            ("05_statement_of_facts.md", "Statement of Facts", "# Statement of Facts\n\n[Relevant factual background]\n\n"),
            ("06_discussion.md", "Discussion", "# Discussion\n\n## I. Legal Framework\n\n## II. Analysis\n\n## III. Application to Facts\n\n"),
            ("07_conclusion.md", "Conclusion", "# Conclusion\n\n[Summary of analysis and recommendations]\n\n"),
        ],
        "document_type": "memo",
        "description": "An internal legal analysis and recommendation document"
    }
}


def _slugify(name: str) -> str:
    """Convert name to a safe filesystem slug."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\- _]+", "", s)
    s = s.replace(" ", "-")
    s = re.sub(r"-+", "-", s)
    return s or f"draft-{uuid.uuid4().hex[:8]}"


def _create_draft_structure(draft_dir: Path, draft_type: str, name: str, draft_id: str) -> Dict[str, Any]:
    """Create complete standardized draft structure per draft_system guidelines."""
    template = DRAFT_TEMPLATES.get(draft_type)
    if not template:
        raise ValueError(f"Unknown draft type: {draft_type}")

    # Create standard folder structure
    folders = [
        "draft_content",
        "html_preview",
        "research",
        "exhibits",
        "reference_material",
        "case_documents"
    ]

    for folder in folders:
        (draft_dir / folder).mkdir(parents=True, exist_ok=True)

    # Create section files in draft_content/
    content_dir = draft_dir / "draft_content"
    sections_metadata = []

    for filename, section_name, content in template["sections"]:
        section_file = content_dir / filename
        section_file.write_text(content)

        sections_metadata.append({
            "id": filename.replace(".md", "").replace("_", "-"),
            "name": section_name,
            "file": f"draft_content/{filename}",
            "order": str(len(sections_metadata) + 1)
        })

    # Create metadata.yml (draft_system standard)
    now = datetime.now(timezone.utc)
    metadata_yml = {
        "draft_id": draft_id,
        "name": name,
        "document_type": template["document_type"],
        "description": template["description"],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "status": "draft",
        "version": "1.0",
        "sections": sections_metadata,
        "folders": {
            "draft_content": "Main document sections and content",
            "html_preview": "Generated HTML previews",
            "research": "Legal research and supporting materials",
            "exhibits": "Supporting exhibits and attachments",
            "reference_material": "Reference documents and templates",
            "case_documents": "Related case documents and filings"
        }
    }

    metadata_file = draft_dir / "metadata.yml"
    metadata_file.write_text(yaml.dump(metadata_yml, default_flow_style=False, sort_keys=False))

    return metadata_yml


async def _get_case_paths(case_id: str) -> tuple[FileLegalCaseStore, Path, Path]:
    """Return (case_store, case_root, case_workspace)."""
    # Ensure workspace manager and case store are ready
    workspace_manager = get_legal_workspace_manager()
    if not workspace_manager:
        workspace_manager = initialize_legal_workspace_manager(config)
    if not workspace_manager.case_store:
        await workspace_manager.initialize()

    # Validate case exists
    case_store: FileLegalCaseStore = workspace_manager.case_store
    case = await case_store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case_root = Path(case_store.get_case_root_path(case_id))
    case_workspace = Path(case_store.get_case_workspace_path(case_id))
    return case_store, case_root, case_workspace


@router.get("/cases/{case_id}/drafts")
async def list_drafts(case_id: str) -> Dict[str, Any]:
    """List all drafts for a case."""
    try:
        _, case_root, case_workspace = await _get_case_paths(case_id)
        drafts_dir = case_workspace / "active_drafts"
        items: List[Dict[str, Any]] = []
        
        if drafts_dir.exists():
            for d in sorted(drafts_dir.iterdir()):
                if not d.is_dir() or d.name.startswith("."):
                    continue

                # Try metadata.yml first (new format), fallback to manifest.json (legacy)
                metadata_path = d / "metadata.yml"
                manifest_path = d / "manifest.json"

                meta: Dict[str, Any] = {
                    "draft_id": d.name,
                    "name": d.name,
                    "type": None,
                    "created_at": None,
                    "updated_at": None,
                    "sections": []
                }

                if metadata_path.exists():
                    try:
                        m = yaml.safe_load(metadata_path.read_text())
                        meta.update({
                            "draft_id": m.get("draft_id", d.name),
                            "name": m.get("name", d.name),
                            "type": m.get("document_type"),  # metadata.yml uses document_type
                            "created_at": m.get("created_at"),
                            "updated_at": m.get("updated_at"),
                            "sections": m.get("sections", [])
                        })
                    except Exception as e:
                        logger.warning(f"Failed to parse metadata.yml for draft {d.name}: {e}")
                elif manifest_path.exists():
                    # Legacy support for old manifest.json format
                    try:
                        m = jsonlib.loads(manifest_path.read_text())
                        meta.update({
                            "draft_id": m.get("draft_id", d.name),
                            "name": m.get("name", d.name),
                            "type": m.get("type"),
                            "created_at": m.get("created_at"),
                            "updated_at": m.get("updated_at"),
                            "sections": m.get("sections", [])
                        })
                    except Exception as e:
                        logger.warning(f"Failed to parse manifest.json for draft {d.name}: {e}")

                items.append(meta)
                
        return {"items": items, "total": len(items)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list drafts for case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list drafts: {str(e)}")


@router.post("/cases/{case_id}/drafts/create", response_model=DraftResponse)
async def create_draft(case_id: str, req: CreateDraftRequest) -> DraftResponse:
    """Create a new draft with complete standardized structure."""
    try:
        _, case_root, case_workspace = await _get_case_paths(case_id)
        drafts_dir = case_workspace / "active_drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)

        # Validate draft type
        if req.draft_type not in DRAFT_TEMPLATES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid draft type: {req.draft_type}. Valid types: {list(DRAFT_TEMPLATES.keys())}"
            )

        # Generate unique draft ID
        slug = _slugify(req.name)
        draft_id = f"{slug}-{uuid.uuid4().hex[:6]}"
        draft_dir = drafts_dir / draft_id

        if draft_dir.exists():
            # Extremely unlikely due to uuid; handle for completeness
            raise HTTPException(status_code=409, detail="Draft already exists")

        # Create complete draft structure using template
        draft_dir.mkdir(parents=True, exist_ok=True)
        metadata = _create_draft_structure(draft_dir, req.draft_type, req.name, draft_id)

        logger.info(f"Created draft {draft_id} for case {case_id} with {len(metadata['sections'])} sections")

        return DraftResponse(
            draft_id=draft_id,
            name=req.name,
            type=req.draft_type,
            created_at=metadata["created_at"],
            updated_at=metadata["updated_at"],
            sections=metadata["sections"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create draft for case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create draft: {str(e)}")


@router.delete("/cases/{case_id}/drafts/{draft_id}")
async def delete_draft(case_id: str, draft_id: str):
    """
    Delete a draft and all its contents from the filesystem.

    Args:
        case_id: The legal case ID
        draft_id: The draft ID to delete

    Returns:
        Success message

    Raises:
        HTTPException: If draft not found or deletion fails
    """
    try:
        # Get the case workspace path
        _, case_root, case_workspace = await _get_case_paths(case_id)

        # Find the draft folder
        active_drafts_dir = Path(case_workspace) / "active_drafts"

        if not active_drafts_dir.exists():
            raise HTTPException(status_code=404, detail="No drafts found for this case")

        # Look for the draft folder (it should start with the draft_id)
        draft_folder = None
        for folder in active_drafts_dir.iterdir():
            if folder.is_dir() and folder.name.startswith(draft_id):
                draft_folder = folder
                break

        if not draft_folder:
            raise HTTPException(status_code=404, detail="Draft not found")

        # Delete the entire draft folder and all its contents
        import shutil
        shutil.rmtree(draft_folder)

        logger.info(f"Successfully deleted draft {draft_id} for case {case_id}")

        return {"message": f"Draft {draft_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete draft {draft_id} for case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete draft: {str(e)}")


class SectionContent(BaseModel):
    content: str


class SectionResponse(BaseModel):
    section_id: str
    name: str
    content: str
    file_path: str


@router.get("/cases/{case_id}/drafts/{draft_id}/sections/{section_id}", response_model=SectionResponse)
async def get_draft_section(case_id: str, draft_id: str, section_id: str) -> SectionResponse:
    """Get the content of a specific draft section."""
    try:
        _, case_root, case_workspace = await _get_case_paths(case_id)
        draft_dir = case_workspace / "active_drafts" / draft_id

        if not draft_dir.exists():
            raise HTTPException(status_code=404, detail="Draft not found")

        # Load metadata to find section info
        metadata_path = draft_dir / "metadata.yml"
        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Draft metadata not found")

        metadata = yaml.safe_load(metadata_path.read_text())
        sections = metadata.get("sections", [])

        # Find the section
        section = None
        for s in sections:
            if s.get("id") == section_id:
                section = s
                break

        if not section:
            raise HTTPException(status_code=404, detail=f"Section '{section_id}' not found")

        # Read section content
        section_file = draft_dir / section["file"]
        if not section_file.exists():
            # Create empty section file if it doesn't exist
            section_file.parent.mkdir(parents=True, exist_ok=True)
            section_file.write_text(f"# {section['name']}\n\n")

        content = section_file.read_text()

        return SectionResponse(
            section_id=section_id,
            name=section["name"],
            content=content,
            file_path=section["file"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get section {section_id} for draft {draft_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get section: {str(e)}")


@router.put("/cases/{case_id}/drafts/{draft_id}/sections/{section_id}")
async def update_draft_section(case_id: str, draft_id: str, section_id: str, content: SectionContent):
    """Update the content of a specific draft section."""
    try:
        _, case_root, case_workspace = await _get_case_paths(case_id)
        draft_dir = case_workspace / "active_drafts" / draft_id

        if not draft_dir.exists():
            raise HTTPException(status_code=404, detail="Draft not found")

        # Load metadata to find section info
        metadata_path = draft_dir / "metadata.yml"
        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Draft metadata not found")

        metadata = yaml.safe_load(metadata_path.read_text())
        sections = metadata.get("sections", [])

        # Find the section
        section = None
        for s in sections:
            if s.get("id") == section_id:
                section = s
                break

        if not section:
            raise HTTPException(status_code=404, detail=f"Section '{section_id}' not found")

        # Write section content
        section_file = draft_dir / section["file"]
        section_file.parent.mkdir(parents=True, exist_ok=True)
        section_file.write_text(content.content)

        # Update metadata timestamp
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        metadata_path.write_text(yaml.dump(metadata, default_flow_style=False))

        logger.info(f"Updated section {section_id} for draft {draft_id}")

        return {"message": "Section updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update section {section_id} for draft {draft_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update section: {str(e)}")
