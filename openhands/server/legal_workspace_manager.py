"""
Legal Workspace Manager - Simplified singleton for single-tenant legal case management
"""
import os
import logging
import json
from typing import Optional, Dict, Any
from pathlib import Path

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.storage.legal_case_store import FileLegalCaseStore
from openhands.storage.data_models.legal_case import LegalCase
from openhands.server.services.draft_watcher import initialize_draft_watcher, shutdown_draft_watcher

logger = logging.getLogger(__name__)


class SimpleLegalWorkspaceManager:
    """Simplified singleton workspace manager for single-tenant legal case management."""

    _instance: Optional['SimpleLegalWorkspaceManager'] = None

    def __init__(self, config: OpenHandsConfig):
        self.config = config
        self.case_store: Optional[FileLegalCaseStore] = None
        self.current_case_id: Optional[str] = None

        # Store original workspace configuration for restoration
        self.original_workspace_base = config.workspace_base
        self.original_runtime = config.runtime

    @classmethod
    def get_instance(cls, config: Optional[OpenHandsConfig] = None) -> 'SimpleLegalWorkspaceManager':
        """Get or create the singleton instance."""
        if cls._instance is None:
            if config is None:
                raise ValueError("Config required for first initialization")
            cls._instance = cls(config)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
        
    async def initialize(self, user_id: str | None = None):
        """Initialize the workspace manager with case store."""
        if self.case_store is None:
            try:
                self.case_store = await FileLegalCaseStore.get_instance(self.config, user_id)
                logger.info("Legal workspace manager initialized")

                # Initialize draft file watcher for real-time synchronization
                workspace_root = os.environ.get('LEGAL_WORKSPACE_ROOT', '/tmp/legal_workspace')

                # Import socket.io here to avoid circular imports
                try:
                    from openhands.server.shared import sio
                    initialize_draft_watcher(workspace_root, sio)
                    logger.info("Draft file watcher initialized for real-time synchronization")
                except Exception as e:
                    logger.warning(f"Failed to initialize draft file watcher: {e}")
                    logger.info("Draft system will work without real-time synchronization")

            except Exception as e:
                logger.error(f"Failed to initialize legal workspace manager: {e}")
                raise
    
    async def enter_case_workspace(self, case_id: str) -> Dict[str, Any]:
        """Enter a legal case workspace by updating configuration."""
        if not self.case_store:
            await self.initialize()
        
        # Get the case
        case = await self.case_store.get_case(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        # Get the case workspace path (points to case's draft_system)
        case_workspace_path = self.case_store.get_case_workspace_path(case_id)
        
        if not Path(case_workspace_path).exists():
            raise ValueError(f"Case workspace not found: {case_workspace_path}")
        
        # Update configuration for this case
        self._update_workspace_config(case_workspace_path)

        # Write sentinel and export env var for guardrail
        try:
            os.environ['OH_CASE_WORKSPACE'] = case_workspace_path
            sentinel_path = Path(case_workspace_path) / '.case_workspace.json'
            sentinel_path.write_text(
                json.dumps({
                    'case_id': case_id,
                    'title': case.title,
                    'workspace_path': case_workspace_path
                }, indent=2)
            )
        except Exception as e:
            logger.warning(f"Failed to write sentinel or set env var for case {case_id}: {e}")

        # Update case last accessed time
        from datetime import datetime, timezone
        case.last_accessed_at = datetime.now(timezone.utc)
        await self.case_store.update_case(case)

        self.current_case_id = case_id

        # Start watching this case's draft files for real-time updates
        from openhands.server.services.draft_watcher import get_draft_watcher
        draft_watcher = get_draft_watcher()
        if draft_watcher:
            draft_watcher.watch_case(case_id)

        logger.info(f"Entered case workspace: {case_id} at {case_workspace_path}")

        return {
            'case_id': case_id,
            'case_title': case.title,
            'workspace_path': case_workspace_path,
            'draft_system_initialized': case.draft_system_initialized,
            'workspace_mounted': True
        }
    
    def _update_workspace_config(self, workspace_path: str):
        """Update the OpenHands configuration to use the case workspace."""
        # Update the configuration object
        self.config.workspace_base = workspace_path
        
        # Also set environment variables that Docker runtime uses
        os.environ['WORKSPACE_BASE'] = workspace_path
        
        # Update sandbox volumes to mount the case workspace
        case_mount = f"{workspace_path}:/workspace:rw"
        
        if self.config.sandbox.volumes:
            # Replace any existing workspace mount or add new one
            volumes = self.config.sandbox.volumes.split(',')
            # Remove any existing workspace mounts
            volumes = [v for v in volumes if not v.strip().endswith(':/workspace:rw') and not v.strip().endswith(':/workspace')]
            # Add the case workspace mount
            volumes.append(case_mount)
            self.config.sandbox.volumes = ','.join(volumes)
        else:
            self.config.sandbox.volumes = case_mount

        # Configure for LocalRuntime to avoid Docker startup delays
        # Store original runtime for restoration
        if not hasattr(self, 'original_runtime'):
            self.original_runtime = self.config.runtime
        self.config.runtime = "local"

        logger.info(f"🏛️ Legal workspace configured with LocalRuntime for instant startup")
        logger.debug(f"Updated workspace config: {workspace_path}")
        logger.debug(f"Updated sandbox volumes: {self.config.sandbox.volumes}")
        logger.debug(f"Runtime changed from '{self.original_runtime}' to 'local'")
    
    async def exit_case_workspace(self) -> Dict[str, Any]:
        """Exit the current case workspace and restore original configuration."""
        if not self.current_case_id:
            return {'message': 'No active case workspace'}

        # Restore original configuration
        self.config.workspace_base = self.original_workspace_base
        self.config.runtime = self.original_runtime

        # Restore environment variables
        if self.original_workspace_base:
            os.environ['WORKSPACE_BASE'] = self.original_workspace_base
        elif 'WORKSPACE_BASE' in os.environ:
            del os.environ['WORKSPACE_BASE']
        
        # Restore sandbox volumes (remove case-specific mount)
        if self.config.sandbox.volumes:
            volumes = self.config.sandbox.volumes.split(',')
            # Remove case workspace mounts
            volumes = [v for v in volumes if not v.strip().endswith(':/workspace:rw') and not v.strip().endswith(':/workspace')]
            self.config.sandbox.volumes = ','.join(volumes) if volumes else None
        
        previous_case_id = self.current_case_id
        self.current_case_id = None
        
        logger.info(f"Exited case workspace: {previous_case_id}")
        
        return {
            'previous_case_id': previous_case_id,
            'workspace_restored': True,
            'message': 'Exited case workspace'
        }
    
    async def get_current_case(self) -> Optional[LegalCase]:
        """Get the currently active case."""
        if not self.current_case_id or not self.case_store:
            return None
        
        return await self.case_store.get_case(self.current_case_id)
    
    def get_current_case_id(self) -> Optional[str]:
        """Get the current case ID."""
        return self.current_case_id
    
    def is_in_case_workspace(self) -> bool:
        """Check if currently in a case workspace."""
        return self.current_case_id is not None
    
    async def list_available_cases(self) -> list[Dict[str, Any]]:
        """List all available cases for workspace switching."""
        if not self.case_store:
            return []
        
        cases = await self.case_store.list_cases()
        
        return [
            {
                'case_id': case.case_id,
                'title': case.title,
                'case_number': case.case_number,
                'status': case.status.value,
                'last_accessed_at': case.last_accessed_at.isoformat() if case.last_accessed_at else None,
                'is_current': case.case_id == self.current_case_id
            }
            for case in cases
        ]
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """Get current workspace information."""
        return {
            'current_case_id': self.current_case_id,
            'is_in_case_workspace': self.is_in_case_workspace(),
            'workspace_base': self.config.workspace_base,
            'sandbox_volumes': self.config.sandbox.volumes,
            'original_workspace_base': self.original_workspace_base
        }


# Simplified global functions for backward compatibility
def get_legal_workspace_manager(session_id: str | None = None) -> Optional[SimpleLegalWorkspaceManager]:
    """Get the singleton legal workspace manager instance."""
    try:
        return SimpleLegalWorkspaceManager.get_instance()
    except ValueError:
        return None


def initialize_legal_workspace_manager(config: OpenHandsConfig, session_id: str = None, user_id: str | None = None) -> SimpleLegalWorkspaceManager:
    """Initialize the singleton legal workspace manager."""
    return SimpleLegalWorkspaceManager.get_instance(config)


def cleanup_legal_workspace_manager(session_id: str = None):
    """Clean up function for backward compatibility - now shuts down draft watcher."""
    # Shutdown the draft watcher when cleaning up
    shutdown_draft_watcher()
    logger.info("Legal workspace manager cleanup completed")
