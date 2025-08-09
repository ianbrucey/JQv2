# Database Schema and Migrations

## Technology Stack
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 with async support
- **Migration Tool**: Alembic
- **Connection Pool**: asyncpg driver

## Core Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'lawyer',
    organization VARCHAR(255),
    bar_number VARCHAR(50),
    practice_areas TEXT[], -- PostgreSQL array
    storage_node VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_role CHECK (role IN ('lawyer', 'paralegal', 'pro_se', 'admin')),
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_storage_node ON users(storage_node);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### Cases Table
```sql
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    client_name VARCHAR(255),
    matter_number VARCHAR(100),
    case_type VARCHAR(50) NOT NULL DEFAULT 'litigation',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    court VARCHAR(255),
    case_number VARCHAR(100),
    incident_date DATE,
    filing_date DATE,
    discovery_deadline DATE,
    trial_date DATE,
    case_value DECIMAL(15,2),
    folder_path VARCHAR(500) NOT NULL,
    storage_prefix TEXT NOT NULL, -- S3/Azure path prefix
    total_size_bytes BIGINT DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    is_pinned BOOLEAN DEFAULT false,
    tags TEXT[], -- PostgreSQL array
    custom_fields JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_case_type CHECK (case_type IN ('litigation', 'transactional', 'estate', 'corporate', 'real_estate', 'criminal', 'family', 'custom')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'archived', 'completed', 'on_hold')),
    CONSTRAINT valid_title_length CHECK (char_length(title) >= 3)
);

CREATE INDEX idx_cases_owner_id ON cases(owner_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_last_accessed ON cases(last_accessed DESC);
CREATE INDEX idx_cases_owner_status ON cases(owner_id, status);
CREATE INDEX idx_cases_search ON cases USING gin(to_tsvector('english', title || ' ' || COALESCE(client_name, '') || ' ' || COALESCE(description, '')));
```

### Case Files Table
```sql
CREATE TABLE case_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    logical_path TEXT NOT NULL, -- Path within case (e.g., "pleadings/complaint.pdf")
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    mime_type VARCHAR(100),
    file_size BIGINT NOT NULL,
    content_hash VARCHAR(64), -- SHA-256 hash
    storage_key TEXT NOT NULL, -- Full S3/Azure key
    version_id VARCHAR(100), -- Object storage version ID
    is_derived BOOLEAN DEFAULT false,
    derived_from UUID REFERENCES case_files(id),
    upload_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_upload_status CHECK (upload_status IN ('pending', 'uploading', 'completed', 'failed')),
    CONSTRAINT unique_case_logical_path UNIQUE (case_id, logical_path),
    CONSTRAINT valid_file_size CHECK (file_size >= 0)
);

CREATE INDEX idx_case_files_case_id ON case_files(case_id);
CREATE INDEX idx_case_files_logical_path ON case_files(logical_path);
CREATE INDEX idx_case_files_content_hash ON case_files(content_hash);
CREATE INDEX idx_case_files_upload_status ON case_files(upload_status);
CREATE INDEX idx_case_files_search ON case_files USING gin(to_tsvector('english', file_name));
```

### User Sessions Table
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    container_id VARCHAR(100),
    container_port INTEGER,
    active_case_id UUID REFERENCES cases(id),
    workspace_path TEXT,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_container_port CHECK (container_port BETWEEN 8001 AND 9999)
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active, expires_at);
```

### Case Collaborators Table
```sql
CREATE TABLE case_collaborators (
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL DEFAULT 'viewer',
    added_by UUID NOT NULL REFERENCES users(id),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (case_id, user_id),
    CONSTRAINT valid_permission_level CHECK (permission_level IN ('viewer', 'editor', 'admin'))
);

CREATE INDEX idx_case_collaborators_user_id ON case_collaborators(user_id);
```

### Audit Log Table
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    case_id UUID REFERENCES cases(id),
    file_id UUID REFERENCES case_files(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_action CHECK (action IN ('create', 'read', 'update', 'delete', 'upload', 'download', 'login', 'logout')),
    CONSTRAINT valid_resource_type CHECK (resource_type IN ('user', 'case', 'file', 'session'))
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_case_id ON audit_logs(case_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

## SQLAlchemy Models

### Base Model
```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### User Model
```python
from sqlalchemy import Column, String, Boolean, DateTime, ARRAY, Text
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="lawyer")
    organization = Column(String(255))
    bar_number = Column(String(50))
    practice_areas = Column(ARRAY(Text))
    storage_node = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    cases = relationship("Case", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)
    
    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)
    
    @property
    def storage_prefix(self) -> str:
        return f"users/{self.id}"
```

### Case Model
```python
from sqlalchemy import Column, String, Text, Date, DECIMAL, BigInteger, Integer, Boolean, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

class Case(BaseModel):
    __tablename__ = "cases"
    
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    client_name = Column(String(255))
    matter_number = Column(String(100))
    case_type = Column(String(50), nullable=False, default="litigation")
    status = Column(String(20), nullable=False, default="active")
    court = Column(String(255))
    case_number = Column(String(100))
    incident_date = Column(Date)
    filing_date = Column(Date)
    discovery_deadline = Column(Date)
    trial_date = Column(Date)
    case_value = Column(DECIMAL(15, 2))
    folder_path = Column(String(500), nullable=False)
    storage_prefix = Column(Text, nullable=False)
    total_size_bytes = Column(BigInteger, default=0)
    file_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    tags = Column(ARRAY(Text))
    custom_fields = Column(JSONB, default={})
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="cases")
    files = relationship("CaseFile", back_populates="case", cascade="all, delete-orphan")
    collaborators = relationship("CaseCollaborator", back_populates="case", cascade="all, delete-orphan")
    
    @property
    def full_storage_prefix(self) -> str:
        return f"{self.owner.storage_prefix}/cases/{self.id}"
```

## Alembic Migration Configuration

### alembic.ini
```ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://user:password@localhost/legal_workspace

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 88
```

### Migration Template
```python
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

def upgrade() -> None:
    ${upgrades if upgrades else "pass"}

def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

## Database Connection Configuration

### Database Settings
```python
from pydantic import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class DatabaseSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@localhost/legal_workspace"
    echo_sql: bool = False
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    class Config:
        env_prefix = "DB_"

# Engine configuration
engine = create_async_engine(
    settings.database_url,
    echo=settings.echo_sql,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_timeout=settings.pool_timeout,
    pool_recycle=settings.pool_recycle,
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

## Initial Data Seeding

### Seed Script
```python
async def seed_database():
    async with AsyncSessionLocal() as session:
        # Create default storage nodes
        storage_nodes = ["storage-node-01", "storage-node-02", "storage-node-03"]
        
        # Create admin user
        admin_user = User(
            email="admin@justicequest.com",
            full_name="System Administrator",
            role="admin",
            storage_node=storage_nodes[0],
            email_verified=True
        )
        admin_user.set_password("admin123")
        
        session.add(admin_user)
        await session.commit()
        
        print("Database seeded successfully")
```

This schema provides the foundation for user authentication, case management, file tracking, and audit logging with proper indexing for performance and constraints for data integrity.
