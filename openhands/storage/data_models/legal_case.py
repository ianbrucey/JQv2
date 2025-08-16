from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any


class CaseStatus(Enum):
    ACTIVE = 'active'
    CLOSED = 'closed'
    ARCHIVED = 'archived'
    ON_HOLD = 'on_hold'


@dataclass
class LegalCase:
    """Data model for legal cases in the document management system."""
    
    case_id: str
    title: str
    user_id: str | None = None
    case_number: str | None = None
    description: str | None = None
    status: CaseStatus = CaseStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime | None = None
    
    # Workspace information
    workspace_path: str | None = None
    draft_system_initialized: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Conversation tracking
    conversation_id: str | None = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'case_id': self.case_id,
            'title': self.title,
            'user_id': self.user_id,
            'case_number': self.case_number,
            'description': self.description,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'workspace_path': self.workspace_path,
            'draft_system_initialized': self.draft_system_initialized,
            'metadata': self.metadata,
            'conversation_id': self.conversation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LegalCase':
        """Create instance from dictionary."""
        return cls(
            case_id=data['case_id'],
            title=data['title'],
            user_id=data.get('user_id'),
            case_number=data.get('case_number'),
            description=data.get('description'),
            status=CaseStatus(data.get('status', 'active')),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            last_accessed_at=datetime.fromisoformat(data['last_accessed_at']) if data.get('last_accessed_at') else None,
            workspace_path=data.get('workspace_path'),
            draft_system_initialized=data.get('draft_system_initialized', False),
            metadata=data.get('metadata', {}),
            conversation_id=data.get('conversation_id')
        )


@dataclass
class CaseDocument:
    """Data model for documents within a legal case."""
    
    document_id: str
    case_id: str
    filename: str
    document_type: str  # 'complaint', 'motion', 'research', etc.
    file_path: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
    size_bytes: int = 0
    checksum: str | None = None
    
    # Document metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'document_id': self.document_id,
            'case_id': self.case_id,
            'filename': self.filename,
            'document_type': self.document_type,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version,
            'size_bytes': self.size_bytes,
            'checksum': self.checksum,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CaseDocument':
        """Create instance from dictionary."""
        return cls(
            document_id=data['document_id'],
            case_id=data['case_id'],
            filename=data['filename'],
            document_type=data['document_type'],
            file_path=data['file_path'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            version=data.get('version', 1),
            size_bytes=data.get('size_bytes', 0),
            checksum=data.get('checksum'),
            metadata=data.get('metadata', {})
        )
