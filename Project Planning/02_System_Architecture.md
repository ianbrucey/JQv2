# System Architecture: Legal Case File Management

## High-Level Architecture

### Component Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
├─────────────────────────────────────────────────────────────┤
│  Case Selection UI  │  Case Creation UI  │  Case Management │
│  - Case List        │  - New Case Form   │  - Edit Metadata │
│  - Search/Filter    │  - Template Select │  - Archive Cases │
│  - Recent Cases     │  - Folder Setup    │  - Delete Cases  │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                 API Layer (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│  Case API Endpoints │  Workspace API     │  File System API │
│  - List Cases       │  - Set Workspace   │  - Browse Files  │
│  - Create Case      │  - Initialize Case │  - File Ops      │
│  - Update Metadata  │  - Setup Structure │  - Templates     │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                Business Logic Layer                         │
├─────────────────────────────────────────────────────────────┤
│  Case Manager       │  Metadata Manager  │  Template Engine │
│  - Case Operations  │  - JSON Storage    │  - Folder Setup  │
│  - Validation       │  - Schema Mgmt     │  - File Templates│
│  - Lifecycle Mgmt   │  - Backup/Restore  │  - Legal Docs    │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   Storage Layer                             │
├─────────────────────────────────────────────────────────────┤
│  Case Directory     │  Metadata Store    │  Configuration   │
│  ~/legal-cases/     │  case-metadata.json│  ~/.openhands/   │
│  ├── case-001/      │  - Case titles     │  - Settings      │
│  ├── case-002/      │  - Descriptions    │  - Preferences   │
│  └── case-003/      │  - Created dates   │  - Templates     │
└─────────────────────────────────────────────────────────────┘
```

## Data Architecture

### Case Directory Structure
```
~/legal-cases/                          # Root case directory
├── .legal-workspace/                   # Metadata and configuration
│   ├── case-metadata.json             # Case information database
│   ├── templates/                     # Case templates
│   │   ├── litigation/                # Litigation case template
│   │   ├── transactional/            # Transaction case template
│   │   └── default/                  # Default case template
│   └── config.json                   # Workspace configuration
├── case-001-smith-v-jones/           # Individual case folder
│   ├── .case-info.json              # Case-specific metadata
│   ├── pleadings/                    # Legal pleadings
│   ├── motions/                      # Court motions
│   ├── discovery/                    # Discovery documents
│   ├── exhibits/                     # Evidence and exhibits
│   ├── correspondence/               # Letters and emails
│   ├── research/                     # Legal research
│   ├── drafts/                       # Work in progress
│   └── final/                        # Completed documents
└── case-002-acme-acquisition/
    ├── .case-info.json
    ├── contracts/
    ├── due-diligence/
    ├── regulatory/
    └── closing/
```

### Metadata Schema

#### Global Case Metadata (`case-metadata.json`)
```json
{
  "version": "1.0",
  "cases": {
    "case-001-smith-v-jones": {
      "id": "case-001-smith-v-jones",
      "title": "Smith v. Jones - Personal Injury Litigation",
      "description": "Motor vehicle accident case representing plaintiff",
      "type": "litigation",
      "client": "John Smith",
      "matter_number": "2024-001",
      "created_date": "2024-01-15T10:30:00Z",
      "last_accessed": "2024-08-09T14:22:00Z",
      "status": "active",
      "tags": ["personal-injury", "litigation", "motor-vehicle"],
      "folder_path": "case-001-smith-v-jones"
    }
  },
  "settings": {
    "default_template": "litigation",
    "auto_backup": true,
    "recent_cases_limit": 10
  }
}
```

#### Case-Specific Metadata (`.case-info.json`)
```json
{
  "case_id": "case-001-smith-v-jones",
  "title": "Smith v. Jones - Personal Injury Litigation",
  "client": {
    "name": "John Smith",
    "contact": "john.smith@email.com",
    "phone": "(555) 123-4567"
  },
  "opposing_party": "Jane Jones",
  "court": "Superior Court of Georgia",
  "case_number": "CV-2024-001234",
  "key_dates": {
    "incident_date": "2023-12-15",
    "filing_date": "2024-01-15",
    "discovery_deadline": "2024-06-15",
    "trial_date": "2024-09-15"
  },
  "case_value": "$150,000",
  "notes": "Rear-end collision with clear liability",
  "custom_fields": {}
}
```

## Component Design

### Frontend Components

#### Case Selection Interface
```typescript
interface CaseSelectionProps {
  onCaseSelect: (caseId: string) => void;
  onCreateNew: () => void;
}

interface CaseListItem {
  id: string;
  title: string;
  description: string;
  lastAccessed: Date;
  status: 'active' | 'archived' | 'completed';
  type: string;
  client: string;
}
```

#### Case Creation Interface
```typescript
interface CaseCreationProps {
  onCaseCreated: (caseData: NewCaseData) => void;
  onCancel: () => void;
  templates: CaseTemplate[];
}

interface NewCaseData {
  title: string;
  description: string;
  client: string;
  type: string;
  template: string;
  customFields: Record<string, any>;
}
```

### Backend Services

#### Case Manager Service
```python
class CaseManager:
    def __init__(self, cases_root: str):
        self.cases_root = Path(cases_root)
        self.metadata_file = self.cases_root / ".legal-workspace" / "case-metadata.json"
    
    async def list_cases(self) -> List[CaseInfo]:
        """Return list of all available cases"""
    
    async def create_case(self, case_data: NewCaseData) -> CaseInfo:
        """Create new case with folder structure and metadata"""
    
    async def get_case(self, case_id: str) -> CaseInfo:
        """Get detailed case information"""
    
    async def update_case(self, case_id: str, updates: dict) -> CaseInfo:
        """Update case metadata"""
    
    async def delete_case(self, case_id: str) -> bool:
        """Archive or delete case"""
```

#### Workspace Integration
```python
class LegalWorkspaceManager:
    def __init__(self, case_manager: CaseManager):
        self.case_manager = case_manager
    
    async def set_active_case(self, case_id: str) -> str:
        """Set case as active workspace and return path"""
    
    async def initialize_case_workspace(self, case_id: str) -> None:
        """Set up OpenHands workspace for the case"""
    
    async def get_case_files(self, case_id: str, path: str = "") -> List[FileInfo]:
        """Browse files within case directory"""
```

## Integration Points

### OpenHands Integration

#### Workspace Management Modification
```python
# Modify existing workspace selection logic
class LegalWorkspaceConfig(OpenHandsConfig):
    legal_cases_root: str = Field(default="~/legal-cases")
    active_case_id: str | None = Field(default=None)
    
    @property
    def workspace_base(self) -> str:
        if self.active_case_id:
            return str(Path(self.legal_cases_root) / self.active_case_id)
        return super().workspace_base
```

#### Frontend Route Modification
```typescript
// Replace repository selection with case selection
const routes = [
  {
    path: "/",
    element: <CaseSelectionPage />,  // Instead of RepositorySelectionPage
  },
  {
    path: "/case/:caseId",
    element: <ConversationPage />,   // Existing conversation interface
  },
  {
    path: "/case/:caseId/manage",
    element: <CaseManagementPage />, // New case management interface
  }
];
```

### API Endpoints

#### Case Management API
```
GET    /api/cases                    # List all cases
POST   /api/cases                    # Create new case
GET    /api/cases/{case_id}          # Get case details
PUT    /api/cases/{case_id}          # Update case metadata
DELETE /api/cases/{case_id}          # Archive/delete case

GET    /api/cases/{case_id}/files    # Browse case files
POST   /api/cases/{case_id}/activate # Set as active workspace

GET    /api/templates                # List case templates
POST   /api/templates                # Create custom template
```

## Security Considerations

### File System Security
- **Path Validation**: Ensure case paths stay within legal-cases directory
- **Access Control**: Validate user permissions for case access
- **Sanitization**: Clean case titles and folder names to prevent injection

### Data Protection
- **Metadata Encryption**: Consider encrypting sensitive case information
- **Backup Security**: Secure backup and restore mechanisms
- **Audit Logging**: Track case access and modifications

## Performance Considerations

### Scalability
- **Case Indexing**: Efficient searching and filtering for large case lists
- **Lazy Loading**: Load case details on demand
- **Caching**: Cache frequently accessed case metadata

### File Operations
- **Async Operations**: Non-blocking file system operations
- **Batch Processing**: Efficient bulk operations for case management
- **Progress Tracking**: User feedback for long-running operations

## Migration Strategy

### Phase 1: Core Infrastructure
1. Implement case metadata storage
2. Create case directory structure
3. Build basic case manager service

### Phase 2: Frontend Integration
1. Replace repository selection with case selection
2. Implement case creation interface
3. Integrate with existing workspace management

### Phase 3: Enhanced Features
1. Add case templates and customization
2. Implement search and filtering
3. Add case management features

### Phase 4: Advanced Capabilities
1. Import/export functionality
2. Advanced metadata and custom fields
3. Integration with external legal tools
