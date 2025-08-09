# Testing Framework Setup

## Technology Stack
- **Testing Framework**: pytest with async support
- **Test Database**: PostgreSQL with pytest-postgresql
- **Mocking**: pytest-mock and unittest.mock
- **HTTP Testing**: httpx for async HTTP client testing
- **Container Testing**: testcontainers-python
- **Coverage**: pytest-cov
- **Fixtures**: pytest-asyncio for async fixtures

## Test Project Structure
```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── unit/                       # Unit tests
│   ├── test_auth.py
│   ├── test_cases.py
│   ├── test_files.py
│   └── test_containers.py
├── integration/                # Integration tests
│   ├── test_api_auth.py
│   ├── test_api_cases.py
│   ├── test_storage.py
│   └── test_workspace.py
├── e2e/                       # End-to-end tests
│   ├── test_user_journey.py
│   └── test_case_workflow.py
├── fixtures/                  # Test data fixtures
│   ├── users.json
│   ├── cases.json
│   └── files/
└── utils/                     # Test utilities
    ├── factories.py
    ├── helpers.py
    └── mocks.py
```

## Test Configuration

### pytest Configuration
```ini
# pytest.ini
[tool:pytest]
minversion = 6.0
addopts = 
    -ra
    -q
    --strict-markers
    --strict-config
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    auth: Authentication related tests
    storage: Storage related tests
    container: Container related tests
asyncio_mode = auto
```

### Shared Test Configuration
```python
# tests/conftest.py
import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer
from testcontainers.minio import MinioContainer

from app.main import app
from app.database import Base, get_db
from app.core.config import Settings, get_settings
from app.models import User, Case, CaseFile
from tests.utils.factories import UserFactory, CaseFactory

# Test settings
class TestSettings(Settings):
    testing: bool = True
    database_url: str = "postgresql+asyncpg://test:test@localhost:5432/test_legal_workspace"
    storage_endpoint: str = "http://localhost:9000"
    storage_access_key: str = "minioadmin"
    storage_secret_key: str = "minioadmin"
    storage_bucket: str = "test-legal-workspace"
    redis_url: str = "redis://localhost:6379/1"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def postgres_container():
    """Start PostgreSQL container for testing."""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture(scope="session")
async def minio_container():
    """Start MinIO container for testing."""
    with MinioContainer() as minio:
        yield minio

@pytest.fixture(scope="session")
async def test_settings(postgres_container, minio_container) -> TestSettings:
    """Create test settings with container URLs."""
    settings = TestSettings()
    settings.database_url = postgres_container.get_connection_url().replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    settings.storage_endpoint = f"http://{minio_container.get_container_host_ip()}:{minio_container.get_exposed_port(9000)}"
    return settings

@pytest.fixture(scope="session")
async def test_engine(test_settings):
    """Create test database engine."""
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
        pool_pre_ping=True
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session, test_settings) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: test_settings
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clear overrides
    app.dependency_overrides.clear()

@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user: User) -> AsyncClient:
    """Create authenticated HTTP client."""
    # Login and get token
    login_response = await client.post("/api/auth/login", json={
        "email": test_user.email,
        "password": "testpassword123"
    })
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Set authorization header
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    return client
```

## Test Factories and Fixtures

### Model Factories
```python
# tests/utils/factories.py
import factory
from factory import Faker, SubFactory
from datetime import datetime, date
import uuid

from app.models import User, Case, CaseFile

class UserFactory(factory.Factory):
    """Factory for creating test users."""
    
    class Meta:
        model = User
    
    id = factory.LazyFunction(uuid.uuid4)
    email = Faker('email')
    password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJgusgqSu"  # "testpassword123"
    full_name = Faker('name')
    role = "lawyer"
    organization = Faker('company')
    bar_number = Faker('bothify', text='##-####')
    practice_areas = factory.LazyFunction(lambda: ["litigation", "corporate"])
    storage_node = "test-storage-node"
    is_active = True
    email_verified = True
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

class CaseFactory(factory.Factory):
    """Factory for creating test cases."""
    
    class Meta:
        model = Case
    
    id = factory.LazyFunction(uuid.uuid4)
    owner = SubFactory(UserFactory)
    title = Faker('sentence', nb_words=4)
    description = Faker('text', max_nb_chars=500)
    client_name = Faker('name')
    matter_number = Faker('bothify', text='####-##')
    case_type = "litigation"
    status = "active"
    court = Faker('company')
    case_number = Faker('bothify', text='##-CV-####')
    incident_date = Faker('date_between', start_date='-2y', end_date='today')
    filing_date = Faker('date_between', start_date='-1y', end_date='today')
    discovery_deadline = Faker('date_between', start_date='today', end_date='+6m')
    trial_date = Faker('date_between', start_date='+6m', end_date='+1y')
    case_value = Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    folder_path = factory.LazyAttribute(lambda obj: f"/cases/{obj.id}")
    storage_prefix = factory.LazyAttribute(lambda obj: f"users/{obj.owner.id}/cases/{obj.id}")
    total_size_bytes = 0
    file_count = 0
    is_pinned = False
    tags = factory.LazyFunction(lambda: ["important", "urgent"])
    custom_fields = factory.LazyFunction(dict)
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    last_accessed = factory.LazyFunction(datetime.utcnow)

class CaseFileFactory(factory.Factory):
    """Factory for creating test case files."""
    
    class Meta:
        model = CaseFile
    
    id = factory.LazyFunction(uuid.uuid4)
    case = SubFactory(CaseFactory)
    logical_path = "pleadings/complaint.pdf"
    file_name = "complaint.pdf"
    file_type = "pdf"
    mime_type = "application/pdf"
    file_size = Faker('pyint', min_value=1024, max_value=1024*1024)
    content_hash = Faker('sha256')
    storage_key = factory.LazyAttribute(lambda obj: f"{obj.case.storage_prefix}/{obj.logical_path}")
    is_derived = False
    upload_status = "completed"
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

# Pytest fixtures using factories
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user."""
    user = UserFactory()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_case(db_session: AsyncSession, test_user: User) -> Case:
    """Create test case."""
    case = CaseFactory(owner=test_user)
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)
    return case

@pytest.fixture
async def test_case_file(db_session: AsyncSession, test_case: Case) -> CaseFile:
    """Create test case file."""
    case_file = CaseFileFactory(case=test_case)
    db_session.add(case_file)
    await db_session.commit()
    await db_session.refresh(case_file)
    return case_file
```

## Unit Tests

### Authentication Tests
```python
# tests/unit/test_auth.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.services.auth import AuthService, TokenManager, PasswordManager
from app.models import User
from app.schemas.auth import UserCreate, UserLogin
from tests.utils.factories import UserFactory

class TestPasswordManager:
    """Test password management functionality."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password_manager = PasswordManager()
        password = "testpassword123"
        
        hashed = password_manager.hash_password(password)
        
        assert hashed != password
        assert password_manager.verify_password(password, hashed)
    
    def test_verify_password_invalid(self):
        """Test password verification with invalid password."""
        password_manager = PasswordManager()
        password = "testpassword123"
        wrong_password = "wrongpassword"
        
        hashed = password_manager.hash_password(password)
        
        assert not password_manager.verify_password(wrong_password, hashed)
    
    def test_validate_password_strength(self):
        """Test password strength validation."""
        password_manager = PasswordManager()
        
        # Strong password
        strong_password = "StrongPass123!"
        result = password_manager.validate_password_strength(strong_password)
        assert all(result.values())
        
        # Weak password
        weak_password = "weak"
        result = password_manager.validate_password_strength(weak_password)
        assert not all(result.values())

class TestTokenManager:
    """Test JWT token management."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_data = {"sub": "user123", "email": "test@example.com"}
        
        token = TokenManager.create_access_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        user_data = {"sub": "user123", "email": "test@example.com"}
        
        token = TokenManager.create_access_token(user_data)
        payload = TokenManager.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = TokenManager.verify_token(invalid_token)
        
        assert payload is None

@pytest.mark.asyncio
class TestAuthService:
    """Test authentication service."""
    
    async def test_create_user(self, db_session):
        """Test user creation."""
        auth_service = AuthService(db_session)
        user_data = UserCreate(
            email="test@example.com",
            password="TestPass123!",
            full_name="Test User",
            role="lawyer"
        )
        
        user = await auth_service.create_user(user_data)
        
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "lawyer"
        assert user.password_hash != "TestPass123!"
    
    async def test_authenticate_user_valid(self, db_session, test_user):
        """Test user authentication with valid credentials."""
        auth_service = AuthService(db_session)
        
        user = await auth_service.authenticate_user(
            test_user.email, 
            "testpassword123"
        )
        
        assert user is not None
        assert user.id == test_user.id
    
    async def test_authenticate_user_invalid_password(self, db_session, test_user):
        """Test user authentication with invalid password."""
        auth_service = AuthService(db_session)
        
        user = await auth_service.authenticate_user(
            test_user.email, 
            "wrongpassword"
        )
        
        assert user is None
    
    async def test_authenticate_user_nonexistent(self, db_session):
        """Test user authentication with nonexistent user."""
        auth_service = AuthService(db_session)
        
        user = await auth_service.authenticate_user(
            "nonexistent@example.com", 
            "password"
        )
        
        assert user is None
```

### Case Management Tests
```python
# tests/unit/test_cases.py
import pytest
from unittest.mock import Mock, AsyncMock
import uuid

from app.services.cases import CaseService
from app.schemas.cases import CaseCreate, CaseUpdate
from app.exceptions import ResourceNotFoundError, AuthorizationError
from tests.utils.factories import UserFactory, CaseFactory

@pytest.mark.asyncio
class TestCaseService:
    """Test case management service."""
    
    async def test_create_case(self, db_session, test_user):
        """Test case creation."""
        case_service = CaseService(db_session)
        case_data = CaseCreate(
            title="Test Case",
            description="Test case description",
            client_name="Test Client",
            case_type="litigation"
        )
        
        case = await case_service.create_case(test_user.id, case_data)
        
        assert case.title == "Test Case"
        assert case.owner_id == test_user.id
        assert case.status == "active"
    
    async def test_get_case_with_access(self, db_session, test_case):
        """Test getting case with proper access."""
        case_service = CaseService(db_session)
        
        case = await case_service.get_case_with_access_check(
            test_case.id, 
            test_case.owner_id
        )
        
        assert case is not None
        assert case.id == test_case.id
    
    async def test_get_case_without_access(self, db_session, test_case):
        """Test getting case without access."""
        case_service = CaseService(db_session)
        other_user_id = uuid.uuid4()
        
        case = await case_service.get_case_with_access_check(
            test_case.id, 
            other_user_id
        )
        
        assert case is None
    
    async def test_update_case(self, db_session, test_case):
        """Test case update."""
        case_service = CaseService(db_session)
        update_data = CaseUpdate(
            title="Updated Case Title",
            status="on_hold"
        )
        
        updated_case = await case_service.update_case(
            test_case.id,
            test_case.owner_id,
            update_data
        )
        
        assert updated_case.title == "Updated Case Title"
        assert updated_case.status == "on_hold"
    
    async def test_list_user_cases(self, db_session, test_user):
        """Test listing user cases."""
        case_service = CaseService(db_session)
        
        # Create multiple cases
        for i in range(3):
            case = CaseFactory(owner=test_user)
            db_session.add(case)
        await db_session.commit()
        
        cases, total = await case_service.list_user_cases(
            user_id=test_user.id,
            page=1,
            page_size=10
        )
        
        assert len(cases) == 3
        assert total == 3
        assert all(case.owner_id == test_user.id for case in cases)
```

## Integration Tests

### API Integration Tests
```python
# tests/integration/test_api_auth.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestAuthAPI:
    """Test authentication API endpoints."""
    
    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "NewPass123!",
            "full_name": "New User",
            "role": "lawyer"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "password_hash" not in data
    
    async def test_login_valid_credentials(self, client: AsyncClient, test_user):
        """Test login with valid credentials."""
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["id"] == str(test_user.id)
    
    async def test_login_invalid_credentials(self, client: AsyncClient, test_user):
        """Test login with invalid credentials."""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "access_token" not in data
    
    async def test_get_current_user(self, authenticated_client: AsyncClient, test_user):
        """Test getting current user info."""
        response = await authenticated_client.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
```

## End-to-End Tests

### User Journey Tests
```python
# tests/e2e/test_user_journey.py
import pytest
from httpx import AsyncClient

@pytest.mark.e2e
class TestUserJourney:
    """Test complete user journeys."""
    
    async def test_complete_case_creation_workflow(self, client: AsyncClient):
        """Test complete workflow from registration to case creation."""
        
        # 1. Register user
        user_data = {
            "email": "journey@example.com",
            "password": "JourneyPass123!",
            "full_name": "Journey User",
            "role": "lawyer"
        }
        
        register_response = await client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # 2. Login
        login_data = {
            "email": "journey@example.com",
            "password": "JourneyPass123!"
        }
        
        login_response = await client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        
        # 3. Create case
        case_data = {
            "title": "Journey Test Case",
            "description": "Test case for user journey",
            "client_name": "Journey Client",
            "case_type": "litigation"
        }
        
        case_response = await client.post("/api/cases", json=case_data)
        assert case_response.status_code == 201
        
        case_id = case_response.json()["id"]
        
        # 4. Get case details
        get_case_response = await client.get(f"/api/cases/{case_id}")
        assert get_case_response.status_code == 200
        assert get_case_response.json()["title"] == "Journey Test Case"
        
        # 5. List user cases
        list_response = await client.get("/api/cases")
        assert list_response.status_code == 200
        assert len(list_response.json()["cases"]) == 1
```

## Test Utilities

### Mock Helpers
```python
# tests/utils/mocks.py
from unittest.mock import AsyncMock, Mock
import uuid

class MockStorageService:
    """Mock storage service for testing."""
    
    def __init__(self):
        self.objects = {}
    
    async def upload_object(self, key: str, content: bytes, **kwargs):
        self.objects[key] = content
        return Mock(
            key=key,
            size=len(content),
            etag=str(uuid.uuid4())
        )
    
    async def download_object(self, key: str) -> bytes:
        if key not in self.objects:
            raise Exception("Object not found")
        return self.objects[key]
    
    async def delete_object(self, key: str) -> bool:
        if key in self.objects:
            del self.objects[key]
            return True
        return False
    
    async def object_exists(self, key: str) -> bool:
        return key in self.objects

class MockContainerManager:
    """Mock container manager for testing."""
    
    def __init__(self):
        self.containers = {}
    
    async def provision_container(self, user_id: str, case_id: str, workspace_path: str):
        container_info = Mock(
            container_id=f"container_{user_id}",
            port=8001,
            user_id=user_id,
            case_id=case_id,
            workspace_path=workspace_path
        )
        self.containers[user_id] = container_info
        return container_info
    
    async def cleanup_container(self, user_id: str) -> bool:
        if user_id in self.containers:
            del self.containers[user_id]
            return True
        return False
```

## Test Execution

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

This comprehensive testing framework provides unit tests, integration tests, end-to-end tests, and proper test utilities for ensuring the reliability and correctness of the legal workspace application.
