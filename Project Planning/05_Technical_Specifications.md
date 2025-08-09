# Technical Specifications: Legal Case File Management

## Database Schema and Data Models

### Case Metadata Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Legal Case Metadata",
  "type": "object",
  "properties": {
    "version": {
      "type": "string",
      "description": "Schema version for migration compatibility"
    },
    "cases": {
      "type": "object",
      "patternProperties": {
        "^[a-zA-Z0-9-_]+$": {
          "$ref": "#/definitions/CaseInfo"
        }
      }
    },
    "settings": {
      "$ref": "#/definitions/WorkspaceSettings"
    }
  },
  "definitions": {
    "CaseInfo": {
      "type": "object",
      "required": ["id", "title", "created_date", "folder_path"],
      "properties": {
        "id": { "type": "string" },
        "title": { "type": "string", "maxLength": 200 },
        "description": { "type": "string", "maxLength": 1000 },
        "type": { 
          "type": "string",
          "enum": ["litigation", "transactional", "estate", "corporate", "real-estate", "custom"]
        },
        "client": { "type": "string", "maxLength": 100 },
        "matter_number": { "type": "string", "maxLength": 50 },
        "created_date": { "type": "string", "format": "date-time" },
        "last_accessed": { "type": "string", "format": "date-time" },
        "status": {
          "type": "string",
          "enum": ["active", "archived", "completed", "on-hold"]
        },
        "tags": {
          "type": "array",
          "items": { "type": "string" },
          "maxItems": 20
        },
        "folder_path": { "type": "string" },
        "custom_fields": { "type": "object" }
      }
    },
    "WorkspaceSettings": {
      "type": "object",
      "properties": {
        "default_template": { "type": "string" },
        "auto_backup": { "type": "boolean" },
        "recent_cases_limit": { "type": "integer", "minimum": 1, "maximum": 50 },
        "theme": { "type": "string", "enum": ["light", "dark", "auto"] }
      }
    }
  }
}
```

### Case-Specific Metadata Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Individual Case Metadata",
  "type": "object",
  "required": ["case_id", "title"],
  "properties": {
    "case_id": { "type": "string" },
    "title": { "type": "string" },
    "client": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "contact": { "type": "string" },
        "phone": { "type": "string" },
        "address": { "type": "string" }
      }
    },
    "opposing_party": { "type": "string" },
    "court": { "type": "string" },
    "case_number": { "type": "string" },
    "key_dates": {
      "type": "object",
      "properties": {
        "incident_date": { "type": "string", "format": "date" },
        "filing_date": { "type": "string", "format": "date" },
        "discovery_deadline": { "type": "string", "format": "date" },
        "trial_date": { "type": "string", "format": "date" }
      }
    },
    "case_value": { "type": "string" },
    "notes": { "type": "string" },
    "custom_fields": { "type": "object" }
  }
}
```

## API Specifications

### REST API Endpoints

#### Case Management
```yaml
/api/legal/cases:
  get:
    summary: List all cases
    parameters:
      - name: status
        in: query
        schema:
          type: string
          enum: [active, archived, completed, on-hold]
      - name: search
        in: query
        schema:
          type: string
      - name: limit
        in: query
        schema:
          type: integer
          default: 50
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      200:
        description: List of cases
        content:
          application/json:
            schema:
              type: object
              properties:
                cases:
                  type: array
                  items:
                    $ref: '#/components/schemas/CaseInfo'
                total:
                  type: integer
                has_more:
                  type: boolean

  post:
    summary: Create new case
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/NewCaseRequest'
    responses:
      201:
        description: Case created successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CaseInfo'
      400:
        description: Invalid request data
      409:
        description: Case with same name already exists

/api/legal/cases/{case_id}:
  get:
    summary: Get case details
    parameters:
      - name: case_id
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Case details
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CaseDetails'
      404:
        description: Case not found

  put:
    summary: Update case metadata
    parameters:
      - name: case_id
        in: path
        required: true
        schema:
          type: string
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UpdateCaseRequest'
    responses:
      200:
        description: Case updated successfully
      404:
        description: Case not found

  delete:
    summary: Archive or delete case
    parameters:
      - name: case_id
        in: path
        required: true
        schema:
          type: string
      - name: permanent
        in: query
        schema:
          type: boolean
          default: false
    responses:
      204:
        description: Case archived/deleted successfully
      404:
        description: Case not found
```

#### Workspace Management
```yaml
/api/legal/cases/{case_id}/activate:
  post:
    summary: Set case as active workspace
    parameters:
      - name: case_id
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Workspace activated
        content:
          application/json:
            schema:
              type: object
              properties:
                workspace_path:
                  type: string
                case_info:
                  $ref: '#/components/schemas/CaseInfo'
      404:
        description: Case not found

/api/legal/cases/{case_id}/files:
  get:
    summary: List files in case directory
    parameters:
      - name: case_id
        in: path
        required: true
        schema:
          type: string
      - name: path
        in: query
        schema:
          type: string
          default: ""
    responses:
      200:
        description: File listing
        content:
          application/json:
            schema:
              type: object
              properties:
                files:
                  type: array
                  items:
                    $ref: '#/components/schemas/FileInfo'
                current_path:
                  type: string
```

#### Template Management
```yaml
/api/legal/templates:
  get:
    summary: List available case templates
    responses:
      200:
        description: List of templates
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/CaseTemplate'

  post:
    summary: Create custom template
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/NewTemplateRequest'
    responses:
      201:
        description: Template created successfully
```

## Backend Implementation

### Core Classes

#### Case Manager
```python
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid

class CaseManager:
    def __init__(self, cases_root: str):
        self.cases_root = Path(cases_root).expanduser()
        self.metadata_dir = self.cases_root / ".legal-workspace"
        self.metadata_file = self.metadata_dir / "case-metadata.json"
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.cases_root.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        
        if not self.metadata_file.exists():
            self._initialize_metadata()
    
    def _initialize_metadata(self) -> None:
        """Initialize empty metadata file."""
        initial_data = {
            "version": "1.0",
            "cases": {},
            "settings": {
                "default_template": "litigation",
                "auto_backup": True,
                "recent_cases_limit": 10
            }
        }
        self._save_metadata(initial_data)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from JSON file."""
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._initialize_metadata()
            return self._load_metadata()
    
    def _save_metadata(self, data: Dict[str, Any]) -> None:
        """Save metadata to JSON file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    async def list_cases(
        self, 
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List cases with optional filtering."""
        metadata = self._load_metadata()
        cases = list(metadata["cases"].values())
        
        # Apply filters
        if status:
            cases = [c for c in cases if c.get("status") == status]
        
        if search:
            search_lower = search.lower()
            cases = [
                c for c in cases 
                if search_lower in c.get("title", "").lower() 
                or search_lower in c.get("client", "").lower()
                or search_lower in c.get("description", "").lower()
            ]
        
        # Sort by last accessed (most recent first)
        cases.sort(
            key=lambda x: x.get("last_accessed", x.get("created_date", "")), 
            reverse=True
        )
        
        # Apply pagination
        total = len(cases)
        cases = cases[offset:offset + limit]
        
        return {
            "cases": cases,
            "total": total,
            "has_more": offset + len(cases) < total
        }
    
    async def create_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new case with folder structure."""
        case_id = self._generate_case_id(case_data["title"])
        
        # Create case info
        case_info = {
            "id": case_id,
            "title": case_data["title"],
            "description": case_data.get("description", ""),
            "type": case_data.get("type", "litigation"),
            "client": case_data.get("client", ""),
            "matter_number": case_data.get("matter_number", ""),
            "created_date": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "status": "active",
            "tags": case_data.get("tags", []),
            "folder_path": case_id,
            "custom_fields": case_data.get("custom_fields", {})
        }
        
        # Create case directory and structure
        case_path = self.cases_root / case_id
        await self._create_case_structure(case_path, case_data.get("template", "litigation"))
        
        # Save case-specific metadata
        case_metadata_file = case_path / ".case-info.json"
        with open(case_metadata_file, 'w') as f:
            json.dump(case_info, f, indent=2, default=str)
        
        # Update global metadata
        metadata = self._load_metadata()
        metadata["cases"][case_id] = case_info
        self._save_metadata(metadata)
        
        return case_info
    
    async def _create_case_structure(self, case_path: Path, template: str) -> None:
        """Create folder structure based on template."""
        case_path.mkdir(exist_ok=True)
        
        # Define folder structures by template
        templates = {
            "litigation": [
                "pleadings", "motions", "discovery", "exhibits",
                "correspondence", "research", "drafts", "final"
            ],
            "transactional": [
                "contracts", "due-diligence", "regulatory", "closing",
                "correspondence", "drafts", "final"
            ],
            "estate": [
                "wills", "trusts", "probate", "tax-documents",
                "correspondence", "drafts", "final"
            ]
        }
        
        folders = templates.get(template, templates["litigation"])
        
        for folder in folders:
            (case_path / folder).mkdir(exist_ok=True)
            
            # Create .gitkeep files to preserve empty directories
            gitkeep_file = case_path / folder / ".gitkeep"
            gitkeep_file.touch()
    
    def _generate_case_id(self, title: str) -> str:
        """Generate unique case ID from title."""
        # Create base ID from title
        base_id = "".join(c for c in title.lower() if c.isalnum() or c in "-_")
        base_id = base_id[:50]  # Limit length
        
        # Ensure uniqueness
        metadata = self._load_metadata()
        counter = 1
        case_id = base_id
        
        while case_id in metadata["cases"]:
            case_id = f"{base_id}-{counter}"
            counter += 1
        
        return case_id
    
    async def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed case information."""
        metadata = self._load_metadata()
        case_info = metadata["cases"].get(case_id)
        
        if not case_info:
            return None
        
        # Update last accessed time
        case_info["last_accessed"] = datetime.utcnow().isoformat()
        metadata["cases"][case_id] = case_info
        self._save_metadata(metadata)
        
        # Load case-specific metadata if available
        case_path = self.cases_root / case_info["folder_path"]
        case_metadata_file = case_path / ".case-info.json"
        
        if case_metadata_file.exists():
            with open(case_metadata_file, 'r') as f:
                detailed_info = json.load(f)
                case_info.update(detailed_info)
        
        return case_info
    
    async def update_case(self, case_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update case metadata."""
        metadata = self._load_metadata()
        case_info = metadata["cases"].get(case_id)
        
        if not case_info:
            return None
        
        # Update allowed fields
        allowed_fields = [
            "title", "description", "client", "matter_number", 
            "status", "tags", "custom_fields"
        ]
        
        for field in allowed_fields:
            if field in updates:
                case_info[field] = updates[field]
        
        case_info["last_accessed"] = datetime.utcnow().isoformat()
        
        # Save to global metadata
        metadata["cases"][case_id] = case_info
        self._save_metadata(metadata)
        
        # Update case-specific metadata
        case_path = self.cases_root / case_info["folder_path"]
        case_metadata_file = case_path / ".case-info.json"
        
        if case_metadata_file.exists():
            with open(case_metadata_file, 'r') as f:
                detailed_info = json.load(f)
            
            detailed_info.update(updates)
            
            with open(case_metadata_file, 'w') as f:
                json.dump(detailed_info, f, indent=2, default=str)
        
        return case_info
    
    async def delete_case(self, case_id: str, permanent: bool = False) -> bool:
        """Archive or permanently delete case."""
        metadata = self._load_metadata()
        case_info = metadata["cases"].get(case_id)
        
        if not case_info:
            return False
        
        if permanent:
            # Permanently delete case directory and metadata
            case_path = self.cases_root / case_info["folder_path"]
            if case_path.exists():
                import shutil
                shutil.rmtree(case_path)
            
            del metadata["cases"][case_id]
        else:
            # Archive case
            case_info["status"] = "archived"
            metadata["cases"][case_id] = case_info
        
        self._save_metadata(metadata)
        return True
```

### Workspace Integration
```python
class LegalWorkspaceManager:
    def __init__(self, case_manager: CaseManager, config: OpenHandsConfig):
        self.case_manager = case_manager
        self.config = config
    
    async def set_active_case(self, case_id: str) -> Optional[str]:
        """Set case as active workspace."""
        case_info = await self.case_manager.get_case(case_id)
        if not case_info:
            return None
        
        case_path = self.case_manager.cases_root / case_info["folder_path"]
        
        # Update OpenHands config to use case directory as workspace
        self.config.workspace_base = str(case_path)
        
        return str(case_path)
    
    async def get_case_files(self, case_id: str, path: str = "") -> List[Dict[str, Any]]:
        """Get file listing for case directory."""
        case_info = await self.case_manager.get_case(case_id)
        if not case_info:
            return []
        
        case_path = self.case_manager.cases_root / case_info["folder_path"]
        target_path = case_path / path if path else case_path
        
        if not target_path.exists() or not target_path.is_dir():
            return []
        
        files = []
        for item in target_path.iterdir():
            if item.name.startswith('.') and item.name not in ['.case-info.json']:
                continue  # Skip hidden files except case metadata
            
            files.append({
                "name": item.name,
                "path": str(item.relative_to(case_path)),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            })
        
        # Sort directories first, then files
        files.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
        
        return files
```

## Frontend Implementation

### TypeScript Interfaces
```typescript
// types/legal.ts
export interface CaseInfo {
  id: string;
  title: string;
  description?: string;
  type: CaseType;
  client?: string;
  matter_number?: string;
  created_date: string;
  last_accessed: string;
  status: CaseStatus;
  tags: string[];
  folder_path: string;
  custom_fields: Record<string, any>;
}

export type CaseType = 'litigation' | 'transactional' | 'estate' | 'corporate' | 'real-estate' | 'custom';
export type CaseStatus = 'active' | 'archived' | 'completed' | 'on-hold';

export interface NewCaseData {
  title: string;
  description?: string;
  client?: string;
  type: CaseType;
  template: string;
  custom_fields?: Record<string, any>;
}

export interface CaseTemplate {
  id: string;
  name: string;
  description: string;
  folders: string[];
  type: CaseType;
}

export interface FileInfo {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  modified: string;
}
```

### React Hooks
```typescript
// hooks/use-cases.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CaseInfo, NewCaseData } from '../types/legal';
import { legalApi } from '../api/legal';

export function useCases(filters?: CaseFilters) {
  return useQuery({
    queryKey: ['cases', filters],
    queryFn: () => legalApi.listCases(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCase(caseId: string) {
  return useQuery({
    queryKey: ['case', caseId],
    queryFn: () => legalApi.getCase(caseId),
    enabled: !!caseId,
  });
}

export function useCreateCase() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (caseData: NewCaseData) => legalApi.createCase(caseData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] });
    },
  });
}

export function useActivateCase() {
  return useMutation({
    mutationFn: (caseId: string) => legalApi.activateCase(caseId),
  });
}
```

## Performance Optimizations

### Caching Strategy
- **Metadata Caching**: Cache case metadata in memory with TTL
- **File System Caching**: Cache directory listings for frequently accessed paths
- **Query Caching**: Use React Query for client-side caching
- **Pagination**: Implement cursor-based pagination for large case lists

### Database Considerations
- **JSON File Storage**: Suitable for single-user deployments
- **SQLite Migration**: For better performance with many cases
- **Indexing**: Create indexes on frequently queried fields
- **Backup Strategy**: Regular automated backups of metadata

### File System Optimizations
- **Lazy Loading**: Load case details only when needed
- **Batch Operations**: Group file system operations
- **Watch Services**: Monitor file changes for real-time updates
- **Compression**: Compress archived cases to save space
