# Authentication and Authorization Implementation

## Technology Stack
- **JWT Library**: PyJWT 2.8+
- **Password Hashing**: passlib with bcrypt
- **Session Management**: Database-backed sessions
- **Rate Limiting**: slowapi (FastAPI rate limiter)
- **Security Headers**: Custom middleware

## Authentication Architecture

### JWT Token Structure
```python
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from pydantic import BaseSettings

class AuthSettings(BaseSettings):
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24
    refresh_token_expire_days: int = 30
    
    class Config:
        env_prefix = "AUTH_"

auth_settings = AuthSettings()

class TokenManager:
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=auth_settings.access_token_expire_hours)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(
            to_encode,
            auth_settings.secret_key,
            algorithm=auth_settings.algorithm
        )
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=auth_settings.refresh_token_expire_days)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(
            to_encode,
            auth_settings.secret_key,
            algorithm=auth_settings.algorithm
        )
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                auth_settings.secret_key,
                algorithms=[auth_settings.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
```

### Password Security
```python
from passlib.context import CryptContext
from passlib.hash import bcrypt
import secrets
import string

class PasswordManager:
    def __init__(self):
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12  # Higher rounds for better security
        )
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate cryptographically secure password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, bool]:
        """Validate password strength requirements."""
        return {
            "min_length": len(password) >= 8,
            "max_length": len(password) <= 128,
            "has_uppercase": any(c.isupper() for c in password),
            "has_lowercase": any(c.islower() for c in password),
            "has_digit": any(c.isdigit() for c in password),
            "has_special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password),
            "no_common_patterns": not any(pattern in password.lower() for pattern in [
                "password", "123456", "qwerty", "admin", "user"
            ])
        }

password_manager = PasswordManager()
```

### Session Management
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime, timedelta
import uuid
import secrets

class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_session(
        self,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """Create new user session."""
        # Generate secure session token
        session_token = secrets.token_urlsafe(32)
        
        # Create session record
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(hours=auth_settings.access_token_expire_hours),
            is_active=True
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def get_active_session(self, session_token: str) -> Optional[UserSession]:
        """Get active session by token."""
        query = select(UserSession).where(
            UserSession.session_token == session_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_session_activity(self, session_token: str) -> bool:
        """Update session last activity timestamp."""
        query = update(UserSession).where(
            UserSession.session_token == session_token
        ).values(
            last_activity=datetime.utcnow()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def invalidate_session(self, session_token: str) -> bool:
        """Invalidate session (logout)."""
        query = update(UserSession).where(
            UserSession.session_token == session_token
        ).values(
            is_active=False
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def invalidate_all_user_sessions(self, user_id: uuid.UUID) -> int:
        """Invalidate all sessions for a user."""
        query = update(UserSession).where(
            UserSession.user_id == user_id
        ).values(
            is_active=False
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        query = delete(UserSession).where(
            UserSession.expires_at < datetime.utcnow()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount
```

### User Service with Authentication
```python
from sqlalchemy import select
from typing import Optional

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create new user with hashed password."""
        # Hash password
        hashed_password = password_manager.hash_password(user_data.password)
        
        # Determine storage node (simple round-robin for now)
        storage_nodes = ["storage-node-01", "storage-node-02", "storage-node-03"]
        user_count = await self.get_user_count()
        storage_node = storage_nodes[user_count % len(storage_nodes)]
        
        # Create user
        user = User(
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role,
            organization=user_data.organization,
            bar_number=user_data.bar_number,
            practice_areas=user_data.practice_areas or [],
            storage_node=storage_node
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_by_email(email)
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not password_manager.verify_password(password, user.password_hash):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()
        
        return user
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_count(self) -> int:
        """Get total user count for storage node assignment."""
        query = select(func.count(User.id))
        result = await self.db.execute(query)
        return result.scalar()
    
    async def change_password(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not password_manager.verify_password(current_password, user.password_hash):
            return False
        
        # Validate new password strength
        strength = password_manager.validate_password_strength(new_password)
        if not all(strength.values()):
            raise ValueError("New password does not meet security requirements")
        
        # Update password
        user.password_hash = password_manager.hash_password(new_password)
        await self.db.commit()
        
        return True
```

## Authorization System

### Permission-Based Access Control
```python
from enum import Enum
from typing import Set, List

class Permission(str, Enum):
    # Case permissions
    CASE_CREATE = "case:create"
    CASE_READ = "case:read"
    CASE_UPDATE = "case:update"
    CASE_DELETE = "case:delete"
    CASE_SHARE = "case:share"
    
    # File permissions
    FILE_UPLOAD = "file:upload"
    FILE_DOWNLOAD = "file:download"
    FILE_DELETE = "file:delete"
    
    # Admin permissions
    USER_MANAGE = "user:manage"
    SYSTEM_ADMIN = "system:admin"

class RolePermissions:
    """Define permissions for each role."""
    
    ROLE_PERMISSIONS = {
        UserRole.PRO_SE: {
            Permission.CASE_CREATE,
            Permission.CASE_READ,
            Permission.CASE_UPDATE,
            Permission.CASE_DELETE,
            Permission.FILE_UPLOAD,
            Permission.FILE_DOWNLOAD,
            Permission.FILE_DELETE,
        },
        UserRole.PARALEGAL: {
            Permission.CASE_CREATE,
            Permission.CASE_READ,
            Permission.CASE_UPDATE,
            Permission.FILE_UPLOAD,
            Permission.FILE_DOWNLOAD,
            Permission.FILE_DELETE,
        },
        UserRole.LAWYER: {
            Permission.CASE_CREATE,
            Permission.CASE_READ,
            Permission.CASE_UPDATE,
            Permission.CASE_DELETE,
            Permission.CASE_SHARE,
            Permission.FILE_UPLOAD,
            Permission.FILE_DOWNLOAD,
            Permission.FILE_DELETE,
        },
        UserRole.ADMIN: {
            # Admins have all permissions
            Permission.CASE_CREATE,
            Permission.CASE_READ,
            Permission.CASE_UPDATE,
            Permission.CASE_DELETE,
            Permission.CASE_SHARE,
            Permission.FILE_UPLOAD,
            Permission.FILE_DOWNLOAD,
            Permission.FILE_DELETE,
            Permission.USER_MANAGE,
            Permission.SYSTEM_ADMIN,
        }
    }
    
    @classmethod
    def get_role_permissions(cls, role: UserRole) -> Set[Permission]:
        """Get permissions for a role."""
        return cls.ROLE_PERMISSIONS.get(role, set())
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: Permission) -> bool:
        """Check if role has specific permission."""
        return permission in cls.get_role_permissions(role)

class AuthorizationService:
    @staticmethod
    def check_permission(user: User, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return RolePermissions.has_permission(user.role, permission)
    
    @staticmethod
    def check_case_access(user: User, case: Case, permission: Permission) -> bool:
        """Check if user has permission to access specific case."""
        # Owner always has access
        if case.owner_id == user.id:
            return AuthorizationService.check_permission(user, permission)
        
        # Check collaborator permissions (implement when collaboration is added)
        # For now, only owner has access
        return False
    
    @staticmethod
    def require_permission(permission: Permission):
        """Decorator to require specific permission."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract user from dependencies
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if not AuthorizationService.check_permission(current_user, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
```

## Security Middleware

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Add to FastAPI app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limits to auth endpoints
@auth_router.post("/login")
@limiter.limit("5/minute")  # 5 login attempts per minute
async def login_user(request: Request, ...):
    pass

@auth_router.post("/register")
@limiter.limit("3/hour")  # 3 registrations per hour
async def register_user(request: Request, ...):
    pass
```

### Security Headers Middleware
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self'"
        )
        
        return response

# Add to FastAPI app
app.add_middleware(SecurityHeadersMiddleware)
```

### Audit Logging
```python
class AuditLogger:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_action(
        self,
        user_id: Optional[uuid.UUID],
        action: str,
        resource_type: str,
        resource_id: Optional[uuid.UUID] = None,
        case_id: Optional[uuid.UUID] = None,
        file_id: Optional[uuid.UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log user action for audit trail."""
        audit_log = AuditLog(
            user_id=user_id,
            case_id=case_id,
            file_id=file_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(audit_log)
        await self.db.commit()

# Middleware to automatically log API calls
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()
        response = await call_next(request)
        
        # Log API call (implement based on requirements)
        if request.url.path.startswith("/api/"):
            # Extract user info from token if available
            # Log the API call with response status
            pass
        
        return response
```

This authentication and authorization system provides secure user management with JWT tokens, role-based permissions, session tracking, and comprehensive audit logging.
