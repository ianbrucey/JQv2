"""Draft-related observation classes for real-time synchronization."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class DraftSectionsChangedObservation(Observation):
    """Observation for when draft sections are added, removed, or reordered."""
    
    observation: str = ObservationType.DRAFT_SECTIONS_CHANGED
    case_id: str = ""
    draft_id: str = ""
    sections: List[Dict[str, Any]] = None
    change_type: str = ""  # "added", "removed", "reordered"
    changed_section_id: Optional[str] = None
    
    def __post_init__(self):
        if self.sections is None:
            self.sections = []

    @property
    def message(self) -> str:
        if self.change_type == "added":
            return f"Section '{self.changed_section_id}' added to draft '{self.draft_id}'"
        elif self.change_type == "removed":
            return f"Section '{self.changed_section_id}' removed from draft '{self.draft_id}'"
        elif self.change_type == "reordered":
            return f"Sections reordered in draft '{self.draft_id}'"
        return f"Sections changed in draft '{self.draft_id}'"


@dataclass
class DraftContentChangedObservation(Observation):
    """Observation for when draft section content is modified."""
    
    observation: str = ObservationType.DRAFT_CONTENT_CHANGED
    case_id: str = ""
    draft_id: str = ""
    section_id: str = ""
    content: str = ""
    file_path: str = ""
    change_source: str = "external"  # "external", "user", "agent"
    
    @property
    def message(self) -> str:
        return f"Content changed in section '{self.section_id}' of draft '{self.draft_id}'"


@dataclass
class DraftMetadataChangedObservation(Observation):
    """Observation for when draft metadata (name, type, etc.) is modified."""
    
    observation: str = ObservationType.DRAFT_METADATA_CHANGED
    case_id: str = ""
    draft_id: str = ""
    metadata: Dict[str, Any] = None
    changed_fields: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.changed_fields is None:
            self.changed_fields = []

    @property
    def message(self) -> str:
        fields_str = ", ".join(self.changed_fields)
        return f"Metadata changed in draft '{self.draft_id}': {fields_str}"


@dataclass
class DraftSyncStatusObservation(Observation):
    """Observation for draft synchronization status updates."""
    
    observation: str = ObservationType.DRAFT_SYNC_STATUS
    case_id: str = ""
    draft_id: Optional[str] = None
    status: str = ""  # "connected", "disconnected", "syncing", "error"
    message_text: str = ""
    
    @property
    def message(self) -> str:
        if self.message_text:
            return self.message_text
        return f"Draft sync status: {self.status}"
