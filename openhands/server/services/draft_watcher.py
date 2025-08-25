"""File system watcher for draft files to enable real-time synchronization."""

import asyncio
import json
import os
import threading
from pathlib import Path
from typing import Dict, Optional, Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from openhands.core.logger import openhands_logger as logger
from openhands.events.observation.draft import (
    DraftContentChangedObservation,
    DraftSectionsChangedObservation,
    DraftSyncStatusObservation,
)


class DraftFileHandler(FileSystemEventHandler):
    """Handles file system events for draft files."""
    
    def __init__(self, watcher: 'DraftWatcher'):
        self.watcher = watcher
        self._debounce_timers: Dict[str, threading.Timer] = {}
        self._debounce_delay = 0.5  # 500ms debounce
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only watch .md files in draft_content directories
        if not (file_path.suffix == '.md' and 'draft_content' in file_path.parts):
            return
            
        # Debounce rapid file changes
        self._debounce_file_change(str(file_path))
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if it's a new section file
        if file_path.suffix == '.md' and 'draft_content' in file_path.parts:
            self._handle_section_change(str(file_path), 'added')
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if it's a deleted section file
        if file_path.suffix == '.md' and 'draft_content' in file_path.parts:
            self._handle_section_change(str(file_path), 'removed')
    
    def _debounce_file_change(self, file_path: str):
        """Debounce file changes to avoid excessive events."""
        # Cancel existing timer for this file
        if file_path in self._debounce_timers:
            self._debounce_timers[file_path].cancel()
        
        # Create new timer
        timer = threading.Timer(
            self._debounce_delay,
            lambda: self._handle_content_change(file_path)
        )
        self._debounce_timers[file_path] = timer
        timer.start()
    
    def _handle_content_change(self, file_path: str):
        """Handle debounced content changes."""
        try:
            # Remove from debounce timers
            self._debounce_timers.pop(file_path, None)
            
            # Parse file path to extract case_id, draft_id, section_id
            path_info = self.watcher._parse_draft_file_path(file_path)
            if not path_info:
                return
            
            case_id, draft_id, section_id = path_info
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Failed to read draft file {file_path}: {e}")
                return
            
            # Create observation
            observation = DraftContentChangedObservation(
                case_id=case_id,
                draft_id=draft_id,
                section_id=section_id,
                content=content,
                file_path=file_path,
                change_source="external"
            )
            
            # Emit to connected clients
            asyncio.create_task(self.watcher._emit_observation(observation))
            
        except Exception as e:
            logger.error(f"Error handling content change for {file_path}: {e}")
    
    def _handle_section_change(self, file_path: str, change_type: str):
        """Handle section addition/removal."""
        try:
            # Parse file path to extract case_id, draft_id
            path_info = self.watcher._parse_draft_file_path(file_path)
            if not path_info:
                return
            
            case_id, draft_id, section_id = path_info
            
            # Get updated sections list
            sections = self.watcher._get_draft_sections(case_id, draft_id)
            
            # Create observation
            observation = DraftSectionsChangedObservation(
                case_id=case_id,
                draft_id=draft_id,
                sections=sections,
                change_type=change_type,
                changed_section_id=section_id
            )
            
            # Emit to connected clients
            asyncio.create_task(self.watcher._emit_observation(observation))
            
        except Exception as e:
            logger.error(f"Error handling section change for {file_path}: {e}")


class DraftWatcher:
    """Watches draft files for changes and emits real-time updates."""

    def __init__(self, workspace_root: str, socket_io=None):
        self.workspace_root = Path(workspace_root)
        self.observer: Optional[Observer] = None
        self.watched_cases: Set[str] = set()
        self._lock = threading.Lock()
        self.socket_io = socket_io
    
    def start(self):
        """Start the file system watcher."""
        if self.observer is not None:
            logger.warning("Draft watcher is already running")
            return
        
        self.observer = Observer()
        logger.info(f"Starting draft file watcher for {self.workspace_root}")
        
        # Start observer
        self.observer.start()
        
        # Emit sync status
        asyncio.create_task(self._emit_sync_status("connected", "Draft watcher started"))
    
    def stop(self):
        """Stop the file system watcher."""
        if self.observer is None:
            return
        
        logger.info("Stopping draft file watcher")
        self.observer.stop()
        self.observer.join()
        self.observer = None
        
        # Emit sync status
        asyncio.create_task(self._emit_sync_status("disconnected", "Draft watcher stopped"))
    
    def watch_case(self, case_id: str):
        """Start watching a specific case's draft files."""
        with self._lock:
            if case_id in self.watched_cases:
                return
            
            case_path = self.workspace_root / "cases" / f"case-{case_id}"
            if not case_path.exists():
                logger.warning(f"Case directory does not exist: {case_path}")
                return
            
            # Add watch for the case directory
            handler = DraftFileHandler(self)
            self.observer.schedule(handler, str(case_path), recursive=True)
            self.watched_cases.add(case_id)
            
            logger.info(f"Now watching draft files for case {case_id}")
    
    def unwatch_case(self, case_id: str):
        """Stop watching a specific case's draft files."""
        with self._lock:
            if case_id not in self.watched_cases:
                return
            
            # Note: watchdog doesn't provide easy way to remove specific watches
            # For now, we'll just remove from our tracking set
            # In production, we might need to restart the observer
            self.watched_cases.discard(case_id)
            
            logger.info(f"Stopped watching draft files for case {case_id}")
    
    def _parse_draft_file_path(self, file_path: str) -> Optional[tuple[str, str, str]]:
        """Parse a draft file path to extract case_id, draft_id, and section_id."""
        try:
            path = Path(file_path)
            parts = path.parts
            
            # Find case directory
            case_part = None
            for i, part in enumerate(parts):
                if part.startswith('case-'):
                    case_part = part
                    case_id = part[5:]  # Remove 'case-' prefix
                    break
            
            if not case_part:
                return None
            
            # Find draft directory
            draft_part = None
            for i, part in enumerate(parts):
                if part.startswith('draft-'):
                    draft_part = part
                    draft_id = part[6:]  # Remove 'draft-' prefix
                    break
            
            if not draft_part:
                return None
            
            # Extract section_id from filename
            section_id = path.stem  # filename without extension
            
            return case_id, draft_id, section_id
            
        except Exception as e:
            logger.error(f"Failed to parse draft file path {file_path}: {e}")
            return None
    
    def _get_draft_sections(self, case_id: str, draft_id: str) -> list:
        """Get the current sections list for a draft."""
        try:
            draft_path = self.workspace_root / "cases" / f"case-{case_id}" / f"draft-{draft_id}"
            content_path = draft_path / "draft_content"
            
            if not content_path.exists():
                return []
            
            sections = []
            for md_file in sorted(content_path.glob("*.md")):
                section_id = md_file.stem
                sections.append({
                    "id": section_id,
                    "name": section_id.replace('_', ' ').title(),
                    "file": f"draft_content/{md_file.name}",
                    "order": len(sections) + 1
                })
            
            return sections
            
        except Exception as e:
            logger.error(f"Failed to get sections for draft {draft_id}: {e}")
            return []
    
    async def _emit_observation(self, observation):
        """Emit an observation to connected WebSocket clients."""
        try:
            if not self.socket_io:
                logger.warning("No socket.io instance available for draft observation emission")
                return

            from openhands.events.serialization import event_to_dict

            # Emit to all connected clients for this case
            await self.socket_io.emit('oh_event', event_to_dict(observation))

            logger.debug(f"Emitted draft observation: {observation.observation}")

        except Exception as e:
            logger.error(f"Failed to emit draft observation: {e}")
    
    async def _emit_sync_status(self, status: str, message: str):
        """Emit sync status update."""
        try:
            observation = DraftSyncStatusObservation(
                content=message,
                status=status,
                message_text=message
            )
            await self._emit_observation(observation)
            
        except Exception as e:
            logger.error(f"Failed to emit sync status: {e}")


# Global draft watcher instance
_draft_watcher: Optional[DraftWatcher] = None


def get_draft_watcher() -> Optional[DraftWatcher]:
    """Get the global draft watcher instance."""
    return _draft_watcher


def initialize_draft_watcher(workspace_root: str, socket_io=None) -> DraftWatcher:
    """Initialize the global draft watcher."""
    global _draft_watcher

    if _draft_watcher is not None:
        _draft_watcher.stop()

    _draft_watcher = DraftWatcher(workspace_root, socket_io)
    _draft_watcher.start()

    return _draft_watcher


def shutdown_draft_watcher():
    """Shutdown the global draft watcher."""
    global _draft_watcher
    
    if _draft_watcher is not None:
        _draft_watcher.stop()
        _draft_watcher = None
