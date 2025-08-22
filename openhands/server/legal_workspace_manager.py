"""
Legal Workspace Manager - handles workspace switching for legal cases
"""
import os
import logging
import json
from typing import Optional, Dict, Any
from pathlib import Path

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.storage.legal_case_store import FileLegalCaseStore
from openhands.storage.data_models.legal_case import LegalCase

logger = logging.getLogger(__name__)

# Global instance registry - now session-aware
_legal_workspace_managers: Dict[str, 'LegalWorkspaceManager'] = {}

class LegalWorkspaceManager:
    """Manages workspace switching for legal cases with session isolation."""

    def __init__(self, config: OpenHandsConfig, session_id: str):
        self.config = config
        self.session_id = session_id
        self.case_store: Optional[FileLegalCaseStore] = None
        self.current_case_id: Optional[str] = None

        # Store original workspace configuration immediately
        self.original_workspace_config: Dict[str, Any] = {
            'workspace_base': config.workspace_base,
            'workspace_mount_path': getattr(config, 'workspace_mount_path', None),
            'workspace_mount_path_in_sandbox': config.workspace_mount_path_in_sandbox
        }

        # Store original runtime for restoration
        self.original_runtime = config.runtime
        
    async def initialize(self, user_id: str | None = None):
        """Initialize the workspace manager with case store."""
        try:
            self.case_store = await FileLegalCaseStore.get_instance(self.config, user_id)

            # Original workspace configuration is already stored in __init__
            # Just update it if it wasn't set properly
            if not self.original_workspace_config.get('workspace_base'):
                self.original_workspace_config.update({
                    'workspace_base': self.config.workspace_base,
                    'workspace_mount_path': getattr(self.config, 'workspace_mount_path', None),
                    'workspace_mount_path_in_sandbox': self.config.workspace_mount_path_in_sandbox
                })

            logger.info("Legal workspace manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize legal workspace manager: {e}")
            logger.info("Legal case functionality may be limited")
            # Don't raise - allow OpenHands to start without legal features
    
    async def enter_case_workspace(self, case_id: str) -> Dict[str, Any]:
        """Enter a legal case workspace by updating configuration."""
        if not self.case_store:
            raise RuntimeError("Workspace manager not initialized")
        
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

        logger.info(f"Entered case workspace: {case_id} at {case_workspace_path}")

        return {
            'case_id': case_id,
            'case_title': case.title,
            'workspace_path': case_workspace_path,
            'draft_agent_initialized': case.draft_system_initialized,
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
        self.config.workspace_base = self.original_workspace_config['workspace_base']

        # Restore original runtime
        if hasattr(self, 'original_runtime'):
            self.config.runtime = self.original_runtime

        # Restore environment variables
        if self.original_workspace_config['workspace_base']:
            os.environ['WORKSPACE_BASE'] = self.original_workspace_config['workspace_base']
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
            'session_id': self.session_id,
            'current_case_id': self.current_case_id,
            'is_in_case_workspace': self.is_in_case_workspace(),
            'workspace_base': self.config.workspace_base,
            'sandbox_volumes': self.config.sandbox.volumes,
            'original_workspace_base': self.original_workspace_config.get('workspace_base')
        }


def get_legal_workspace_manager(session_id: str | None = None) -> Optional[LegalWorkspaceManager]:
    """Get the legal workspace manager instance for a specific session."""
    if session_id is None:
        # Return any available manager if no session specified (backward compatibility)
        if _legal_workspace_managers:
            return next(iter(_legal_workspace_managers.values()))
        return None
    return _legal_workspace_managers.get(session_id)


def initialize_legal_workspace_manager(config: OpenHandsConfig, session_id: str, user_id: str | None = None):
    """Initialize a session-specific legal workspace manager."""
    # Create a deep copy of config for this session to avoid shared state
    session_config = config.model_copy(deep=True)
    manager = LegalWorkspaceManager(session_config, session_id)
    _legal_workspace_managers[session_id] = manager
    logger.info(f"Initialized legal workspace manager for session: {session_id}")
    return manager


def cleanup_legal_workspace_manager(session_id: str):
    """Clean up the legal workspace manager for a specific session."""
    if session_id in _legal_workspace_managers:
        manager = _legal_workspace_managers[session_id]
        # Restore original configuration if needed
        try:
            if manager.current_case_id:
                # Exit current case workspace before cleanup
                import asyncio
                asyncio.create_task(manager.exit_case_workspace())
        except Exception as e:
            logger.warning(f"Error during workspace cleanup for session {session_id}: {e}")

        del _legal_workspace_managers[session_id]
        logger.info(f"Cleaned up legal workspace manager for session: {session_id}")
