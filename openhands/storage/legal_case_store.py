"""
Legal Case Storage System - manages legal cases and their associated data
"""
import json
import os
import shutil
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.storage.data_models.legal_case import LegalCase, CaseStatus, CaseDocument


class LegalCaseStore(ABC):
    """Abstract base class for legal case storage."""
    
    @abstractmethod
    async def create_case(self, title: str, user_id: str | None = None, 
                         case_number: str | None = None, description: str | None = None) -> LegalCase:
        """Create a new legal case."""
        
    @abstractmethod
    async def get_case(self, case_id: str) -> Optional[LegalCase]:
        """Get a legal case by ID."""
        
    @abstractmethod
    async def update_case(self, case: LegalCase) -> None:
        """Update a legal case."""
        
    @abstractmethod
    async def delete_case(self, case_id: str) -> None:
        """Delete a legal case."""
        
    @abstractmethod
    async def list_cases(self, user_id: str | None = None) -> List[LegalCase]:
        """List all cases for a user."""
        
    @abstractmethod
    async def case_exists(self, case_id: str) -> bool:
        """Check if a case exists."""


class FileLegalCaseStore(LegalCaseStore):
    """File-based implementation of legal case storage."""

    def __init__(self, config: OpenHandsConfig, user_id: str | None = None):
        self.config = config
        self.user_id = user_id
        self._db_initialized = False

        # Set up storage paths
        self.workspace_root = Path(os.environ.get('LEGAL_WORKSPACE_ROOT', '/app/legal_workspace'))
        self.cases_dir = self.workspace_root / 'cases'

        # Resolve draft_system template path with a robust fallback
        env_path = os.environ.get('DRAFT_SYSTEM_PATH')
        resolved_path: Path | None = None
        if env_path:
            p = Path(env_path)
            if p.exists():
                resolved_path = p
        if resolved_path is None:
            # Fallback to repository OpenHands/draft_system next to this file
            here = Path(__file__).resolve()
            root = None
            for parent in here.parents:
                if parent.name == 'OpenHands':
                    root = parent
                    break
            if root is not None:
                candidate = root / 'draft_system'
                if candidate.exists():
                    resolved_path = candidate
        if resolved_path is None:
            # Last resort default (containerized paths) - may not exist locally
            resolved_path = Path('/app/draft_system')

        self.draft_system_template = resolved_path

        # Auto-create all necessary directories
        self._ensure_directories_exist()

        # Verify draft system exists or bail with clear error
        if not self.draft_system_template.exists():
            raise ValueError(
                f"Draft system template not found at {self.draft_system_template}. "
                "Set DRAFT_SYSTEM_PATH to your OpenHands/draft_system folder."
            )

        # Stabilize environment for this process so future instances reuse the resolved path
        try:
            os.environ['DRAFT_SYSTEM_PATH'] = str(self.draft_system_template)
        except Exception:
            pass

    def _ensure_directories_exist(self):
        """Automatically create all necessary directories."""
        directories = [
            self.workspace_root,
            self.cases_dir,
            self.workspace_root / 'system' / 'backups',
            self.workspace_root / 'system' / 'versions',
            self.workspace_root / 'system' / 'audit_logs',
            self.workspace_root / 'files'
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def _ensure_database_initialized(self):
        """Automatically initialize database schema if needed."""
        if self._db_initialized:
            return

        try:
            from openhands.storage.legal_database_setup import LegalDatabaseManager

            db_manager = LegalDatabaseManager()

            # Create database if it doesn't exist
            await db_manager.create_database_if_not_exists()

            # Connect and setup schema
            await db_manager.connect()
            await db_manager.setup_schema()

            # Verify setup worked
            if await db_manager.verify_setup():
                self._db_initialized = True
                print("✅ Legal database initialized automatically")
            else:
                print("⚠️  Database setup verification failed")

            await db_manager.disconnect()

        except Exception as e:
            print(f"⚠️  Database auto-initialization failed: {e}")
            print("   Database operations may not work until manually initialized")
            # Don't raise - allow file-based operations to continue
    
    async def create_case(self, title: str, user_id: str | None = None,
                         case_number: str | None = None, description: str | None = None) -> LegalCase:
        """Create a new legal case with draft_system template."""
        # Auto-initialize database if needed
        await self._ensure_database_initialized()

        case_id = str(uuid.uuid4())
        case_dir = self.cases_dir / f"case-{case_id}"
        
        # Create case directory
        case_dir.mkdir(exist_ok=True)
        
        # Copy draft_system template to case directory
        case_draft_system = case_dir / "draft_system"
        shutil.copytree(self.draft_system_template, case_draft_system)
        
        # Initialize case-specific files
        await self._initialize_case_draft_system(case_draft_system, title, case_id, user_id or self.user_id)
        
        # Create case object
        case = LegalCase(
            case_id=case_id,
            title=title,
            user_id=user_id or self.user_id,
            case_number=case_number,
            description=description,
            workspace_path=str(case_draft_system),
            draft_system_initialized=True
        )
        
        # Save case metadata
        await self._save_case_metadata(case)
        
        return case
    
    async def _initialize_case_draft_system(self, draft_system_dir: Path, case_title: str, 
                                          case_id: str, user_id: str | None):
        """Initialize case-specific files in the copied draft_system."""
        
        # Initialize Case_Summary_and_Timeline.md with case details
        case_summary_file = draft_system_dir / "Case_Summary_and_Timeline.md"
        if case_summary_file.exists():
            try:
                with open(case_summary_file, 'r') as f:
                    template_content = f.read()
                
                # Replace template placeholders
                case_content = template_content.replace("{{CASE_NAME}}", case_title)
                case_content = case_content.replace("{{CASE_ID}}", case_id)
                case_content = case_content.replace("{{CREATED_DATE}}", datetime.now().strftime("%Y-%m-%d"))
                case_content = case_content.replace("{{CREATED_BY}}", user_id or "Unknown")
                
                with open(case_summary_file, 'w') as f:
                    f.write(case_content)
            except Exception as e:
                print(f"Warning: Could not initialize case summary file: {e}")
        
        # Initialize Intake folder with case-specific files
        intake_dir = draft_system_dir / "Intake"
        if intake_dir.exists():
            initial_request_file = intake_dir / "initial_request.md"
            if not initial_request_file.exists():
                try:
                    with open(initial_request_file, 'w') as f:
                        f.write(f"# Initial Request - {case_title}\n\n")
                        f.write(f"**Case ID:** {case_id}\n")
                        f.write(f"**Created:** {datetime.now().strftime('%Y-%m-%d')}\n")
                        f.write(f"**Created By:** {user_id or 'Unknown'}\n\n")
                        f.write("## Client Request\n\n[Document the initial client request here]\n\n")
                except Exception as e:
                    print(f"Warning: Could not create initial request file: {e}")
        
        # Clear any template documents from active_drafts
        active_drafts_dir = draft_system_dir / "active_drafts"
        if active_drafts_dir.exists():
            try:
                for item in active_drafts_dir.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            except Exception as e:
                print(f"Warning: Could not clear active_drafts: {e}")
    
    async def _save_case_metadata(self, case: LegalCase):
        """Save case metadata to file."""
        case_dir = self.cases_dir / f"case-{case.case_id}"
        metadata_file = case_dir / "metadata.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(case.to_dict(), f, indent=2)
    
    async def get_case(self, case_id: str) -> Optional[LegalCase]:
        """Get a legal case by ID."""
        case_dir = self.cases_dir / f"case-{case_id}"
        metadata_file = case_dir / "metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            return LegalCase.from_dict(data)
        except Exception as e:
            print(f"Error loading case {case_id}: {e}")
            return None
    
    async def update_case(self, case: LegalCase) -> None:
        """Update a legal case."""
        case.updated_at = datetime.now(timezone.utc)
        await self._save_case_metadata(case)
    
    async def delete_case(self, case_id: str) -> None:
        """Delete a legal case, its workspace, and associated conversations."""
        # Get case info before deletion to access conversation_id
        case = await self.get_case(case_id)

        # Delete the case workspace directory
        case_dir = self.cases_dir / f"case-{case_id}"
        if case_dir.exists():
            shutil.rmtree(case_dir)

        # Clean up conversation if it exists
        if case and case.conversation_id:
            try:
                # Import here to avoid circular imports
                from openhands.storage.conversation import get_file_store
                conversation_store = get_file_store()
                await conversation_store.delete_conversation(case.conversation_id)
            except Exception as e:
                # Log but don't fail the case deletion if conversation cleanup fails
                print(f"Warning: Failed to delete conversation {case.conversation_id} for case {case_id}: {e}")
    
    async def list_cases(self, user_id: str | None = None) -> List[LegalCase]:
        """List all cases for a user."""
        cases = []
        target_user_id = user_id or self.user_id
        
        for case_dir in self.cases_dir.iterdir():
            if case_dir.is_dir() and case_dir.name.startswith("case-"):
                case_id = case_dir.name.replace("case-", "")
                case = await self.get_case(case_id)
                if case and (not target_user_id or case.user_id == target_user_id):
                    cases.append(case)
        
        # Sort by last updated
        cases.sort(key=lambda c: c.updated_at, reverse=True)
        return cases
    
    async def case_exists(self, case_id: str) -> bool:
        """Check if a case exists."""
        case_dir = self.cases_dir / f"case-{case_id}"
        metadata_file = case_dir / "metadata.json"
        return metadata_file.exists()
    
    def get_case_workspace_path(self, case_id: str) -> str:
        """Get the workspace path for a case (points to case's draft_system)."""
        return str(self.cases_dir / f"case-{case_id}" / "draft_system")
    
    def get_case_root_path(self, case_id: str) -> str:
        """Get the root case directory path."""
        return str(self.cases_dir / f"case-{case_id}")
    
    @classmethod
    async def get_instance(cls, config: OpenHandsConfig, user_id: str | None = None) -> 'FileLegalCaseStore':
        """Get a store instance for the user."""
        return cls(config, user_id)
