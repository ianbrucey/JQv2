# API Layer Architecture and Endpoint Specifications

## Technology Stack
- **Framework**: FastAPI 0.104+
- **Async Runtime**: asyncio with uvicorn
- **Validation**: Pydantic v2
- **Documentation**: OpenAPI 3.0 (auto-generated)
- **Middleware**: CORS, rate limiting, request logging

## API Architecture Pattern

### Layered Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Router    │  │ Middleware  │  │ Exception   │         │
│  │  Endpoints  │  │   Stack     │  │  Handlers   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                  Service Layer                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    User     │  │    Case     │  │    File     │         │
│  │  Service    │  │  Service    │  │  Service    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                Repository Layer                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    User     │  │    Case     │  │    File     │         │
│  │ Repository  │  │ Repository  │  │ Repository  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Pydantic Schemas

### User Schemas
```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

class UserRole(str, Enum):
    LAWYER = "lawyer"
    PARALEGAL = "paralegal"
    PRO_SE = "pro_se"
    ADMIN = "admin"

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.LAWYER
    organization: Optional[str] = Field(None, max_length=255)
    bar_number: Optional[str] = Field(None, max_length=50)
    practice_areas: Optional[List[str]] = []
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    organization: Optional[str]
    bar_number: Optional[str]
    practice_areas: List[str]
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    organization: Optional[str] = Field(None, max_length=255)
    bar_number: Optional[str] = Field(None, max_length=50)
    practice_areas: Optional[List[str]] = None
```

### Case Schemas
```python
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date

class CaseType(str, Enum):
    LITIGATION = "litigation"
    TRANSACTIONAL = "transactional"
    ESTATE = "estate"
    CORPORATE = "corporate"
    REAL_ESTATE = "real_estate"
    CRIMINAL = "criminal"
    FAMILY = "family"
    CUSTOM = "custom"

class CaseStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"

class CaseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    description: Optional[str] = None
    client_name: Optional[str] = Field(None, max_length=255)
    matter_number: Optional[str] = Field(None, max_length=100)
    case_type: CaseType = CaseType.LITIGATION
    court: Optional[str] = Field(None, max_length=255)
    case_number: Optional[str] = Field(None, max_length=100)
    incident_date: Optional[date] = None
    filing_date: Optional[date] = None
    discovery_deadline: Optional[date] = None
    trial_date: Optional[date] = None
    case_value: Optional[Decimal] = Field(None, ge=0)
    tags: Optional[List[str]] = []
    custom_fields: Optional[Dict[str, Any]] = {}

class CaseResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: Optional[str]
    client_name: Optional[str]
    matter_number: Optional[str]
    case_type: CaseType
    status: CaseStatus
    court: Optional[str]
    case_number: Optional[str]
    incident_date: Optional[date]
    filing_date: Optional[date]
    discovery_deadline: Optional[date]
    trial_date: Optional[date]
    case_value: Optional[Decimal]
    folder_path: str
    total_size_bytes: int
    file_count: int
    is_pinned: bool
    tags: List[str]
    custom_fields: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_accessed: datetime
    
    class Config:
        from_attributes = True

class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = None
    client_name: Optional[str] = Field(None, max_length=255)
    matter_number: Optional[str] = Field(None, max_length=100)
    status: Optional[CaseStatus] = None
    court: Optional[str] = Field(None, max_length=255)
    case_number: Optional[str] = Field(None, max_length=100)
    incident_date: Optional[date] = None
    filing_date: Optional[date] = None
    discovery_deadline: Optional[date] = None
    trial_date: Optional[date] = None
    case_value: Optional[Decimal] = Field(None, ge=0)
    is_pinned: Optional[bool] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

class CaseListResponse(BaseModel):
    cases: List[CaseResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
```

### File Schemas
```python
class FileUploadInit(BaseModel):
    file_name: str = Field(..., max_length=255)
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., max_length=100)
    logical_path: str = Field(..., max_length=1000)
    content_hash: Optional[str] = Field(None, max_length=64)

class FileUploadResponse(BaseModel):
    file_id: uuid.UUID
    upload_url: str
    expires_at: datetime
    required_headers: Dict[str, str]

class FileResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    logical_path: str
    file_name: str
    file_type: Optional[str]
    mime_type: Optional[str]
    file_size: int
    content_hash: Optional[str]
    is_derived: bool
    derived_from: Optional[uuid.UUID]
    upload_status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FileListResponse(BaseModel):
    files: List[FileResponse]
    total: int
    current_path: str
```

## API Endpoints

### Authentication Endpoints
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Register new user account."""
    user_service = UserService(db)
    
    # Check if user already exists
    existing_user = await user_service.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Create user
    user = await user_service.create_user(user_data)
    return UserResponse.from_orm(user)

@auth_router.post("/login", response_model=dict)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Authenticate user and return JWT token."""
    user_service = UserService(db)
    
    # Authenticate user
    user = await user_service.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create session and JWT token
    session_service = SessionService(db)
    session = await session_service.create_session(user.id)
    
    return {
        "access_token": session.session_token,
        "token_type": "bearer",
        "expires_at": session.expires_at,
        "user": UserResponse.from_orm(user)
    }

@auth_router.post("/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Logout user and invalidate session."""
    session_service = SessionService(db)
    await session_service.invalidate_session(credentials.credentials)
    
    return {"message": "Successfully logged out"}

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user information."""
    return UserResponse.from_orm(current_user)
```

### Case Management Endpoints
```python
case_router = APIRouter(prefix="/api/cases", tags=["cases"])

@case_router.get("/", response_model=CaseListResponse)
async def list_user_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[CaseStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CaseListResponse:
    """List user's cases with pagination and filtering."""
    case_service = CaseService(db)
    
    cases, total = await case_service.list_user_cases(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
        search=search
    )
    
    return CaseListResponse(
        cases=[CaseResponse.from_orm(case) for case in cases],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total
    )

@case_router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CaseResponse:
    """Create new case."""
    case_service = CaseService(db)
    
    case = await case_service.create_case(
        owner_id=current_user.id,
        case_data=case_data
    )
    
    return CaseResponse.from_orm(case)

@case_router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CaseResponse:
    """Get case details."""
    case_service = CaseService(db)
    
    case = await case_service.get_case_with_access_check(
        case_id=case_id,
        user_id=current_user.id
    )
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Update last accessed time
    await case_service.update_last_accessed(case_id)
    
    return CaseResponse.from_orm(case)

@case_router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: uuid.UUID,
    case_data: CaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CaseResponse:
    """Update case details."""
    case_service = CaseService(db)
    
    case = await case_service.update_case(
        case_id=case_id,
        user_id=current_user.id,
        case_data=case_data
    )
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    return CaseResponse.from_orm(case)

@case_router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: uuid.UUID,
    permanent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete or archive case."""
    case_service = CaseService(db)
    
    success = await case_service.delete_case(
        case_id=case_id,
        user_id=current_user.id,
        permanent=permanent
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
```

### File Management Endpoints
```python
file_router = APIRouter(prefix="/api/cases/{case_id}/files", tags=["files"])

@file_router.post("/upload/init", response_model=FileUploadResponse)
async def init_file_upload(
    case_id: uuid.UUID,
    file_data: FileUploadInit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FileUploadResponse:
    """Initialize file upload and get presigned URL."""
    file_service = FileService(db)
    
    # Verify case access
    case_service = CaseService(db)
    case = await case_service.get_case_with_access_check(case_id, current_user.id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Create file record and presigned URL
    upload_info = await file_service.init_file_upload(
        case_id=case_id,
        file_data=file_data
    )
    
    return upload_info

@file_router.post("/upload/complete")
async def complete_file_upload(
    case_id: uuid.UUID,
    file_id: uuid.UUID,
    etag: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Complete file upload after successful upload to storage."""
    file_service = FileService(db)
    
    success = await file_service.complete_file_upload(
        file_id=file_id,
        etag=etag
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Upload completion failed")
    
    return {"message": "File upload completed successfully"}

@file_router.get("/", response_model=FileListResponse)
async def list_case_files(
    case_id: uuid.UUID,
    path: str = Query("", description="Directory path within case"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FileListResponse:
    """List files in case directory."""
    file_service = FileService(db)
    
    # Verify case access
    case_service = CaseService(db)
    case = await case_service.get_case_with_access_check(case_id, current_user.id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    files = await file_service.list_case_files(case_id, path)
    
    return FileListResponse(
        files=[FileResponse.from_orm(file) for file in files],
        total=len(files),
        current_path=path
    )
```

## Dependency Injection

### Authentication Dependencies
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    session_service = SessionService(db)
    
    session = await session_service.get_active_session(credentials.credentials)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_service = UserService(db)
    user = await user_service.get_by_id(session.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (additional validation)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
```

## Error Handling

### Custom Exception Classes
```python
class LegalWorkspaceException(Exception):
    """Base exception for legal workspace application."""
    pass

class UserNotFoundError(LegalWorkspaceException):
    """User not found error."""
    pass

class CaseNotFoundError(LegalWorkspaceException):
    """Case not found error."""
    pass

class InsufficientPermissionsError(LegalWorkspaceException):
    """Insufficient permissions error."""
    pass

class FileUploadError(LegalWorkspaceException):
    """File upload error."""
    pass
```

### Exception Handlers
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": "User not found"}
    )

@app.exception_handler(CaseNotFoundError)
async def case_not_found_handler(request: Request, exc: CaseNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": "Case not found"}
    )

@app.exception_handler(InsufficientPermissionsError)
async def insufficient_permissions_handler(request: Request, exc: InsufficientPermissionsError):
    return JSONResponse(
        status_code=403,
        content={"detail": "Insufficient permissions"}
    )
```

This API layer provides a clean, well-structured interface following FastAPI best practices with proper validation, error handling, and dependency injection.
