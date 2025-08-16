"""
LocalRuntime Workspace Manager - handles workspace transitions for legal cases
"""
import os
import logging
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalRuntimeWorkspaceManager:
    """Manages workspace transitions for LocalRuntime with proper session isolation."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_workspace_path: Optional[str] = None
        self.tmux_session_name: Optional[str] = None
        
    def get_tmux_session_name(self, workspace_path: str) -> str:
        """Generate a unique tmux session name for this workspace."""
        # Create a unique session name that includes both session ID and workspace context
        workspace_hash = abs(hash(workspace_path)) % 10000
        return f"openhands-{self.session_id}-{workspace_hash}"
    
    async def transition_workspace(self, new_workspace_path: str) -> Dict[str, Any]:
        """Transition to a new workspace, handling tmux session management."""
        try:
            # If we're already in the target workspace, no need to transition
            if self.current_workspace_path == new_workspace_path:
                return {
                    'status': 'already_in_workspace',
                    'workspace_path': new_workspace_path,
                    'tmux_session': self.tmux_session_name
                }
            
            old_workspace = self.current_workspace_path
            old_tmux_session = self.tmux_session_name
            
            # Generate new tmux session name for the new workspace
            new_tmux_session = self.get_tmux_session_name(new_workspace_path)
            
            # Create or switch to the tmux session for the new workspace
            await self._ensure_tmux_session(new_tmux_session, new_workspace_path)
            
            # Clean up old tmux session if it exists and is different
            if old_tmux_session and old_tmux_session != new_tmux_session:
                await self._cleanup_tmux_session(old_tmux_session)
            
            # Update current state
            self.current_workspace_path = new_workspace_path
            self.tmux_session_name = new_tmux_session
            
            logger.info(
                f"Workspace transition completed for session {self.session_id}: "
                f"{old_workspace} -> {new_workspace_path}"
            )
            
            return {
                'status': 'transitioned',
                'old_workspace': old_workspace,
                'new_workspace': new_workspace_path,
                'old_tmux_session': old_tmux_session,
                'new_tmux_session': new_tmux_session
            }
            
        except Exception as e:
            logger.error(f"Workspace transition failed for session {self.session_id}: {e}")
            raise RuntimeError(f"Workspace transition failed: {e}")
    
    async def _ensure_tmux_session(self, session_name: str, workspace_path: str):
        """Ensure a tmux session exists for the given workspace."""
        try:
            # Check if session already exists
            result = subprocess.run(
                ['tmux', 'has-session', '-t', session_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Create new session
                subprocess.run([
                    'tmux', 'new-session', '-d', '-s', session_name,
                    '-c', workspace_path
                ], check=True)
                
                logger.info(f"Created tmux session: {session_name} in {workspace_path}")
            else:
                # Session exists, switch to the workspace directory
                subprocess.run([
                    'tmux', 'send-keys', '-t', session_name,
                    f'cd "{workspace_path}"', 'Enter'
                ], check=True)
                
                logger.info(f"Switched tmux session {session_name} to {workspace_path}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to manage tmux session {session_name}: {e}")
            raise RuntimeError(f"tmux session management failed: {e}")
    
    async def _cleanup_tmux_session(self, session_name: str):
        """Clean up a tmux session."""
        try:
            subprocess.run([
                'tmux', 'kill-session', '-t', session_name
            ], check=True)
            
            logger.info(f"Cleaned up tmux session: {session_name}")
            
        except subprocess.CalledProcessError as e:
            # Session might not exist, which is fine
            logger.debug(f"Could not clean up tmux session {session_name}: {e}")
    
    async def get_current_workspace_info(self) -> Dict[str, Any]:
        """Get information about the current workspace."""
        return {
            'session_id': self.session_id,
            'workspace_path': self.current_workspace_path,
            'tmux_session': self.tmux_session_name
        }
    
    async def cleanup(self):
        """Clean up all resources for this workspace manager."""
        if self.tmux_session_name:
            await self._cleanup_tmux_session(self.tmux_session_name)
        
        self.current_workspace_path = None
        self.tmux_session_name = None
        
        logger.info(f"Cleaned up workspace manager for session: {self.session_id}")


# Global registry of workspace managers per session
_workspace_managers: Dict[str, LocalRuntimeWorkspaceManager] = {}


def get_workspace_manager(session_id: str) -> LocalRuntimeWorkspaceManager:
    """Get or create a workspace manager for the given session."""
    if session_id not in _workspace_managers:
        _workspace_managers[session_id] = LocalRuntimeWorkspaceManager(session_id)
    return _workspace_managers[session_id]


def cleanup_workspace_manager(session_id: str):
    """Clean up the workspace manager for a session."""
    if session_id in _workspace_managers:
        import asyncio
        manager = _workspace_managers[session_id]
        # Run cleanup in background
        asyncio.create_task(manager.cleanup())
        del _workspace_managers[session_id]
        logger.info(f"Cleaned up workspace manager for session: {session_id}")
