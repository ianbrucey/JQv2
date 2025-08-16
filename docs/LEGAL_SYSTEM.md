# Legal Document Management System Architecture

## Overview

The JQv2 Legal Document Management System is a comprehensive solution built on top of OpenHands that provides specialized functionality for legal professionals. This document details the architecture, components, and implementation of the legal system.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    JQv2 Legal System                        │
├─────────────────────────────────────────────────────────────┤
│  Frontend Layer                                            │
│  ├── Legal Case Management UI                              │
│  │   ├── Case List Component                               │
│  │   ├── Case Creation Modal                               │
│  │   ├── Case Detail View                                  │
│  │   └── Runtime Status Indicators                         │
│  ├── Document Workspace Interface                          │
│  │   ├── Document Editor                                   │
│  │   ├── Template Selector                                 │
│  │   └── Collaboration Tools                               │
│  └── API Integration Layer                                 │
│      ├── Legal Case API Client                             │
│      ├── React Query Hooks                                 │
│      └── Error Handling                                    │
├─────────────────────────────────────────────────────────────┤
│  Backend Layer                                             │
│  ├── Legal API Routes                                      │
│  │   ├── Case Management Endpoints                         │
│  │   ├── Workspace Management                              │
│  │   └── System Status                                     │
│  ├── Legal Workspace Manager                               │
│  │   ├── Case Workspace Creation                           │
│  │   ├── Runtime Configuration                             │
│  │   └── Template Integration                              │
│  ├── Runtime Optimization Layer                            │
│  │   ├── Smart Runtime Selection                           │
│  │   ├── Performance Monitoring                            │
│  │   └── Fallback Mechanisms                               │
│  └── Document Template System                              │
│      ├── Template Repository                               │
│      ├── Template Rendering                                │
│      └── Custom Template Support                           │
├─────────────────────────────────────────────────────────────┤
│  OpenHands Core (Modified)                                 │
│  ├── Session Management                                    │
│  │   ├── Legal Context Detection                           │
│  │   ├── Runtime Selection Logic                           │
│  │   └── Session Lifecycle                                 │
│  ├── Agent Controllers                                     │
│  │   ├── Legal-Aware Agents                                │
│  │   ├── Document Processing                               │
│  │   └── Context Management                                │
│  └── Event System                                          │
│      ├── Legal Event Types                                 │
│      ├── Audit Trail                                       │
│      └── Notification System                               │
├─────────────────────────────────────────────────────────────┤
│  Runtime Layer                                             │
│  ├── LocalRuntime (Legal Cases)                            │
│  │   ├── Instant Startup (< 5s)                            │
│  │   ├── tmux Session Management                           │
│  │   └── Process Isolation                                 │
│  ├── DockerRuntime (Development)                           │
│  │   ├── Full Container Isolation                          │
│  │   ├── Development Tools                                 │
│  │   └── Debugging Support                                 │
│  └── Runtime Detection Logic                               │
│      ├── Context Analysis                                  │
│      ├── Performance Optimization                          │
│      └── Automatic Selection                               │
├─────────────────────────────────────────────────────────────┤
│  Storage Layer                                             │
│  ├── Legal Case Store                                      │
│  │   ├── File-based Storage                                │
│  │   ├── Case Metadata                                     │
│  │   └── Workspace Paths                                   │
│  ├── Document Templates                                    │
│  │   ├── Template Repository                               │
│  │   ├── Version Control                                   │
│  │   └── Custom Templates                                  │
│  └── Workspace Management                                  │
│      ├── Directory Structure                               │
│      ├── File Organization                                 │
│      └── Access Control                                    │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Legal Workspace Manager

**Location**: `openhands/server/legal_workspace_manager.py`

The Legal Workspace Manager is the central component that orchestrates legal case workspaces and runtime configuration.

#### Key Responsibilities:
- **Case Workspace Creation**: Creates isolated workspaces for each legal case
- **Runtime Selection**: Determines optimal runtime based on context
- **Template Integration**: Manages document templates and draft system
- **Workspace Lifecycle**: Handles creation, access, and cleanup of workspaces

#### Key Methods:
```python
class LegalWorkspaceManager:
    async def initialize(self) -> None
    async def enter_case_workspace(self, case_id: str) -> Dict[str, Any]
    async def exit_workspace(self) -> Dict[str, Any]
    async def get_current_workspace(self) -> Dict[str, Any]
    def _should_use_local_runtime(self, case_id: str) -> bool
```

#### Runtime Selection Logic:
```python
def _should_use_local_runtime(self, case_id: str) -> bool:
    """Determine if LocalRuntime should be used for this case."""
    # Always use LocalRuntime for legal cases for instant startup
    if case_id and case_id.startswith('case-'):
        return True
    
    # Check workspace path patterns
    workspace_base = getattr(self.config, 'workspace_base', '')
    if 'legal_workspace' in workspace_base:
        return True
    
    return False
```

### 2. Legal Case Store

**Location**: `openhands/storage/legal_case_store.py`

The Legal Case Store provides persistent storage for legal case metadata and workspace management.

#### Key Features:
- **File-based Storage**: Uses JSON files for case metadata
- **Workspace Path Management**: Tracks workspace locations
- **Template Integration**: Links cases to document templates
- **Audit Trail**: Maintains creation and access timestamps

#### Storage Structure:
```
/tmp/legal_workspace/
├── cases/
│   ├── case-{uuid}/
│   │   ├── metadata.json
│   │   ├── draft_system/
│   │   │   ├── templates/
│   │   │   └── documents/
│   │   └── workspace/
│   └── case-{uuid2}/
├── system/
│   ├── backups/
│   ├── versions/
│   └── audit_logs/
└── files/
```

#### Case Metadata Schema:
```python
class LegalCase(BaseModel):
    case_id: str
    title: str
    case_number: Optional[str] = None
    description: Optional[str] = None
    status: CaseStatus = CaseStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    workspace_path: Optional[str] = None
    draft_system_initialized: bool = False
    conversation_id: Optional[str] = None
```

### 3. Runtime Optimization Layer

**Location**: `openhands/server/session/session.py` (modified)

The Runtime Optimization Layer provides intelligent runtime selection for optimal performance.

#### Smart Runtime Selection:
```python
def _determine_runtime_type(self, config: OpenHandsConfig, sid: str) -> str:
    """Determine the optimal runtime type based on context."""
    
    # Check for legal case context
    if self._is_legal_case_context(config, sid):
        logger.info(f"🏛️ Legal case detected for session {sid}, using LocalRuntime for instant startup")
        return "local"
    
    # Default to configured runtime
    return config.runtime

def _is_legal_case_context(self, config: OpenHandsConfig, sid: str) -> bool:
    """Detect if this is a legal case context."""
    
    # Check session ID patterns
    if sid and ('legal' in sid.lower() or 'case' in sid.lower()):
        return True
    
    # Check workspace paths
    workspace_base = getattr(config, 'workspace_base', '')
    if workspace_base and 'legal_workspace' in workspace_base:
        return True
    
    # Check environment variables
    legal_workspace = os.environ.get('LEGAL_WORKSPACE_ROOT')
    if legal_workspace and workspace_base and legal_workspace in workspace_base:
        return True
    
    return False
```

### 4. Legal API Routes

**Location**: `openhands/server/routes/legal_cases.py`

The Legal API Routes provide RESTful endpoints for legal case management.

#### Available Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/legal/cases` | List all legal cases |
| POST | `/api/legal/cases` | Create a new legal case |
| GET | `/api/legal/cases/{case_id}` | Get specific case details |
| PUT | `/api/legal/cases/{case_id}` | Update case information |
| DELETE | `/api/legal/cases/{case_id}` | Delete a legal case |
| POST | `/api/legal/cases/{case_id}/enter` | Enter case workspace |
| POST | `/api/legal/workspace/exit` | Exit current workspace |
| GET | `/api/legal/workspace/current` | Get current workspace info |
| GET | `/api/legal/system/status` | Get system status |

#### Example API Response:
```json
{
  "case_id": "87517639-290e-48be-b61d-6f032e75635c",
  "title": "Contract Review - Acme Corp",
  "case_number": "2024-001",
  "description": "Review and analysis of software licensing agreement",
  "status": "active",
  "created_at": "2025-08-16T15:22:57.584589+00:00",
  "updated_at": "2025-08-16T15:23:00.415003+00:00",
  "last_accessed_at": "2025-08-16T15:23:00.414978+00:00",
  "workspace_path": "/tmp/legal_workspace/cases/case-87517639-290e-48be-b61d-6f032e75635c/draft_system",
  "draft_system_initialized": true,
  "conversation_id": null
}
```

## Frontend Components

### 1. Legal Case Management UI

**Location**: `frontend/src/components/features/legal-cases/`

#### Key Components:
- **LegalCaseHeader**: Main navigation and system status
- **CaseList**: Display and manage legal cases
- **CreateCaseModal**: Create new legal cases
- **CaseCard**: Individual case display and actions

#### Component Structure:
```typescript
// Legal Case Header
interface LegalCaseHeaderProps {
  onCreateCase: () => void;
  systemStatus: SystemStatus;
}

// Case List
interface CaseListProps {
  cases: LegalCase[];
  onEnterCase: (caseId: string) => void;
  onDeleteCase: (caseId: string) => void;
}

// Create Case Modal
interface CreateCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateCaseRequest) => void;
}
```

### 2. API Integration Layer

**Location**: `frontend/src/api/legal-cases.ts`

The API Integration Layer provides type-safe communication with the backend.

#### Key Features:
- **Type Safety**: Full TypeScript interfaces
- **Error Handling**: Comprehensive error management
- **React Query Integration**: Optimistic updates and caching

#### API Client Example:
```typescript
class LegalCaseAPI {
  private baseUrl = '/api/legal';

  async createCase(data: CreateCaseRequest): Promise<LegalCase> {
    const response = await fetch(`${this.baseUrl}/cases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create case');
    }

    return response.json();
  }
}
```

## Performance Optimizations

### 1. Runtime Selection Strategy

The system uses intelligent runtime selection to optimize performance:

#### LocalRuntime for Legal Cases:
- **Startup Time**: < 5 seconds
- **Resource Usage**: Minimal memory/CPU overhead
- **Isolation**: Process-level isolation sufficient for legal workflows
- **Dependencies**: Only requires tmux

#### DockerRuntime for Development:
- **Startup Time**: 60-120+ seconds
- **Resource Usage**: Higher memory/CPU requirements
- **Isolation**: Full container isolation
- **Dependencies**: Docker daemon and images

### 2. Workspace Management

#### Efficient Directory Structure:
```
/tmp/legal_workspace/
├── cases/                    # Individual case workspaces
├── system/                   # System-level data
│   ├── backups/             # Automated backups
│   ├── versions/            # Version control
│   └── audit_logs/          # Audit trail
└── files/                   # Shared file storage
```

#### Template System:
- **Pre-built Templates**: Common legal document templates
- **Custom Templates**: User-defined templates
- **Version Control**: Template versioning and rollback
- **Inheritance**: Template inheritance and composition

## Security Considerations

### 1. Workspace Isolation

Each legal case gets its own isolated workspace:
- **File System Isolation**: Separate directories per case
- **Process Isolation**: LocalRuntime provides process-level isolation
- **Access Control**: Path-based access restrictions

### 2. Data Protection

- **Local Storage**: All data stored locally by default
- **Audit Trail**: Complete audit log of all actions
- **Backup System**: Automated backup and recovery
- **Version Control**: Document version tracking

## Configuration

### Environment Variables

```bash
# Legal Workspace Configuration
LEGAL_WORKSPACE_ROOT=/tmp/legal_workspace
DRAFT_SYSTEM_PATH=/tmp/draft_system

# OpenHands Configuration
WORKSPACE_BASE=/tmp/legal_workspace
DEFAULT_WORKSPACE_MOUNT_PATH_IN_SANDBOX=/workspace

# File Storage Configuration
FILE_STORE=local
FILE_STORE_PATH=/tmp/legal_workspace/files
```

### Runtime Configuration

The system automatically configures LocalRuntime for legal cases:

```python
# Automatic LocalRuntime configuration
if config.runtime == "docker" and is_legal_context:
    config.runtime = "local"
    logger.info("🚀 Configured LocalRuntime for instant startup")
```

## Monitoring and Logging

### Performance Metrics

The system tracks key performance indicators:
- **Startup Time**: Runtime initialization duration
- **Response Time**: API response times
- **Resource Usage**: Memory and CPU utilization
- **User Activity**: Case access patterns

### Logging Strategy

```python
# Performance logging
logger.info(f"🏛️ Legal case detected for session {sid}, using LocalRuntime for instant startup")
logger.info(f"⚡ Runtime startup completed in {startup_time:.2f}s")
logger.info(f"📊 Legal workspace manager initialized successfully")
```

## Future Enhancements

### Planned Features

1. **Database Integration**: PostgreSQL for enterprise deployments
2. **Real-time Collaboration**: Multi-user document editing
3. **Advanced Templates**: More legal document types
4. **Integration APIs**: Connect with legal practice management systems
5. **Cloud Deployment**: Kubernetes and cloud-native options

### Scalability Considerations

- **Multi-tenant Support**: Isolated workspaces per organization
- **Load Balancing**: Horizontal scaling capabilities
- **Caching Strategy**: Redis for session and data caching
- **Database Optimization**: Query optimization and indexing

---

This architecture provides a solid foundation for legal document management while maintaining the performance benefits of the LocalRuntime optimization.
