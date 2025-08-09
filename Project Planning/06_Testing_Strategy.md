# Testing Strategy: Legal Case File Management

## Testing Overview

### Testing Pyramid
```
                    ┌─────────────────┐
                    │   E2E Tests     │  ← User workflows, integration
                    │   (Playwright)  │
                    └─────────────────┘
                  ┌───────────────────────┐
                  │  Integration Tests    │  ← API + Database + File System
                  │  (FastAPI TestClient) │
                  └───────────────────────┘
              ┌─────────────────────────────────┐
              │        Unit Tests               │  ← Individual functions/components
              │  (pytest + Jest/Vitest)        │
              └─────────────────────────────────┘
```

### Test Categories
1. **Unit Tests**: Individual functions, components, and classes
2. **Integration Tests**: API endpoints, database operations, file system
3. **End-to-End Tests**: Complete user workflows
4. **Performance Tests**: Load testing and benchmarks
5. **Security Tests**: Access control and data validation
6. **Accessibility Tests**: WCAG compliance and screen reader support

## Backend Testing

### Unit Tests (pytest)

#### Case Manager Tests
```python
# tests/test_case_manager.py
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from openhands.legal.case_manager import CaseManager

@pytest.fixture
def temp_cases_dir():
    """Create temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def case_manager(temp_cases_dir):
    """Create CaseManager instance for testing."""
    return CaseManager(temp_cases_dir)

class TestCaseManager:
    async def test_create_case_success(self, case_manager):
        """Test successful case creation."""
        case_data = {
            "title": "Test Case",
            "description": "Test description",
            "client": "Test Client",
            "type": "litigation",
            "template": "litigation"
        }
        
        result = await case_manager.create_case(case_data)
        
        assert result["title"] == "Test Case"
        assert result["client"] == "Test Client"
        assert result["status"] == "active"
        assert "id" in result
        assert "created_date" in result
        
        # Verify folder structure was created
        case_path = case_manager.cases_root / result["folder_path"]
        assert case_path.exists()
        assert (case_path / "pleadings").exists()
        assert (case_path / "motions").exists()
        assert (case_path / ".case-info.json").exists()
    
    async def test_create_case_duplicate_title(self, case_manager):
        """Test case creation with duplicate title generates unique ID."""
        case_data = {
            "title": "Duplicate Case",
            "type": "litigation"
        }
        
        case1 = await case_manager.create_case(case_data)
        case2 = await case_manager.create_case(case_data)
        
        assert case1["id"] != case2["id"]
        assert case2["id"].endswith("-1")
    
    async def test_list_cases_empty(self, case_manager):
        """Test listing cases when none exist."""
        result = await case_manager.list_cases()
        
        assert result["cases"] == []
        assert result["total"] == 0
        assert result["has_more"] is False
    
    async def test_list_cases_with_filters(self, case_manager):
        """Test case listing with status filter."""
        # Create test cases
        await case_manager.create_case({"title": "Active Case", "type": "litigation"})
        case2 = await case_manager.create_case({"title": "Completed Case", "type": "litigation"})
        
        # Archive one case
        await case_manager.update_case(case2["id"], {"status": "completed"})
        
        # Test filter
        active_cases = await case_manager.list_cases(status="active")
        completed_cases = await case_manager.list_cases(status="completed")
        
        assert len(active_cases["cases"]) == 1
        assert len(completed_cases["cases"]) == 1
        assert active_cases["cases"][0]["title"] == "Active Case"
        assert completed_cases["cases"][0]["title"] == "Completed Case"
    
    async def test_get_case_not_found(self, case_manager):
        """Test getting non-existent case."""
        result = await case_manager.get_case("non-existent")
        assert result is None
    
    async def test_update_case_success(self, case_manager):
        """Test successful case update."""
        case = await case_manager.create_case({"title": "Original Title", "type": "litigation"})
        
        updates = {
            "title": "Updated Title",
            "description": "New description",
            "status": "completed"
        }
        
        result = await case_manager.update_case(case["id"], updates)
        
        assert result["title"] == "Updated Title"
        assert result["description"] == "New description"
        assert result["status"] == "completed"
    
    async def test_delete_case_archive(self, case_manager):
        """Test case archiving (soft delete)."""
        case = await case_manager.create_case({"title": "To Archive", "type": "litigation"})
        
        success = await case_manager.delete_case(case["id"], permanent=False)
        assert success is True
        
        # Case should still exist but be archived
        archived_case = await case_manager.get_case(case["id"])
        assert archived_case["status"] == "archived"
    
    async def test_delete_case_permanent(self, case_manager):
        """Test permanent case deletion."""
        case = await case_manager.create_case({"title": "To Delete", "type": "litigation"})
        case_path = case_manager.cases_root / case["folder_path"]
        
        assert case_path.exists()
        
        success = await case_manager.delete_case(case["id"], permanent=True)
        assert success is True
        
        # Case should be completely removed
        deleted_case = await case_manager.get_case(case["id"])
        assert deleted_case is None
        assert not case_path.exists()
```

#### Workspace Integration Tests
```python
# tests/test_legal_workspace.py
import pytest
from openhands.legal.workspace import LegalWorkspaceManager
from openhands.core.config import OpenHandsConfig

class TestLegalWorkspaceManager:
    async def test_set_active_case(self, case_manager):
        """Test setting active case workspace."""
        config = OpenHandsConfig()
        workspace_manager = LegalWorkspaceManager(case_manager, config)
        
        case = await case_manager.create_case({"title": "Test Case", "type": "litigation"})
        
        workspace_path = await workspace_manager.set_active_case(case["id"])
        
        assert workspace_path is not None
        assert config.workspace_base == workspace_path
        assert case["folder_path"] in workspace_path
    
    async def test_get_case_files(self, case_manager):
        """Test getting case file listing."""
        config = OpenHandsConfig()
        workspace_manager = LegalWorkspaceManager(case_manager, config)
        
        case = await case_manager.create_case({"title": "Test Case", "type": "litigation"})
        
        files = await workspace_manager.get_case_files(case["id"])
        
        # Should include default folders
        folder_names = [f["name"] for f in files if f["type"] == "directory"]
        assert "pleadings" in folder_names
        assert "motions" in folder_names
        assert "discovery" in folder_names
```

### Integration Tests (FastAPI TestClient)

#### API Endpoint Tests
```python
# tests/test_legal_api.py
import pytest
from fastapi.testclient import TestClient
from openhands.server.app import app

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

class TestLegalAPI:
    def test_list_cases_empty(self, client):
        """Test GET /api/legal/cases with no cases."""
        response = client.get("/api/legal/cases")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cases"] == []
        assert data["total"] == 0
    
    def test_create_case_success(self, client):
        """Test POST /api/legal/cases with valid data."""
        case_data = {
            "title": "Test Case",
            "description": "Test description",
            "client": "Test Client",
            "type": "litigation",
            "template": "litigation"
        }
        
        response = client.post("/api/legal/cases", json=case_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Case"
        assert data["client"] == "Test Client"
        assert "id" in data
    
    def test_create_case_invalid_data(self, client):
        """Test POST /api/legal/cases with invalid data."""
        case_data = {
            "title": "",  # Empty title should fail
            "type": "invalid_type"  # Invalid type should fail
        }
        
        response = client.post("/api/legal/cases", json=case_data)
        assert response.status_code == 400
    
    def test_get_case_success(self, client):
        """Test GET /api/legal/cases/{id} with existing case."""
        # First create a case
        case_data = {"title": "Test Case", "type": "litigation"}
        create_response = client.post("/api/legal/cases", json=case_data)
        case_id = create_response.json()["id"]
        
        # Then get it
        response = client.get(f"/api/legal/cases/{case_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Case"
    
    def test_get_case_not_found(self, client):
        """Test GET /api/legal/cases/{id} with non-existent case."""
        response = client.get("/api/legal/cases/non-existent")
        assert response.status_code == 404
    
    def test_activate_case_success(self, client):
        """Test POST /api/legal/cases/{id}/activate."""
        # Create case first
        case_data = {"title": "Test Case", "type": "litigation"}
        create_response = client.post("/api/legal/cases", json=case_data)
        case_id = create_response.json()["id"]
        
        # Activate it
        response = client.post(f"/api/legal/cases/{case_id}/activate")
        
        assert response.status_code == 200
        data = response.json()
        assert "workspace_path" in data
        assert "case_info" in data
```

## Frontend Testing

### Unit Tests (Vitest + React Testing Library)

#### Component Tests
```typescript
// tests/components/CaseSelectionForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CaseSelectionForm } from '../src/components/legal/case-selection/CaseSelectionForm';
import { mockCases } from './mocks/cases';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('CaseSelectionForm', () => {
  it('renders case list correctly', async () => {
    renderWithProviders(
      <CaseSelectionForm onCaseSelect={jest.fn()} onCreateNew={jest.fn()} />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Recent Cases')).toBeInTheDocument();
    });
    
    // Should show mock cases
    expect(screen.getByText('Smith v. Jones')).toBeInTheDocument();
    expect(screen.getByText('ACME Corp Acquisition')).toBeInTheDocument();
  });
  
  it('calls onCaseSelect when case is clicked', async () => {
    const mockOnCaseSelect = jest.fn();
    
    renderWithProviders(
      <CaseSelectionForm onCaseSelect={mockOnCaseSelect} onCreateNew={jest.fn()} />
    );
    
    await waitFor(() => {
      const caseCard = screen.getByText('Smith v. Jones');
      fireEvent.click(caseCard);
    });
    
    expect(mockOnCaseSelect).toHaveBeenCalledWith('smith-v-jones');
  });
  
  it('filters cases by search term', async () => {
    renderWithProviders(
      <CaseSelectionForm onCaseSelect={jest.fn()} onCreateNew={jest.fn()} />
    );
    
    const searchInput = screen.getByPlaceholderText('Search cases...');
    fireEvent.change(searchInput, { target: { value: 'Smith' } });
    
    await waitFor(() => {
      expect(screen.getByText('Smith v. Jones')).toBeInTheDocument();
      expect(screen.queryByText('ACME Corp Acquisition')).not.toBeInTheDocument();
    });
  });
});
```

#### Hook Tests
```typescript
// tests/hooks/useCases.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useCases } from '../src/hooks/use-cases';
import { mockApiResponse } from './mocks/api';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useCases', () => {
  it('fetches cases successfully', async () => {
    const { result } = renderHook(() => useCases(), {
      wrapper: createWrapper(),
    });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data?.cases).toHaveLength(2);
    expect(result.current.data?.total).toBe(2);
  });
  
  it('handles error state', async () => {
    // Mock API error
    jest.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('API Error'));
    
    const { result } = renderHook(() => useCases(), {
      wrapper: createWrapper(),
    });
    
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
    
    expect(result.current.error).toBeDefined();
  });
});
```

### End-to-End Tests (Playwright)

#### User Workflow Tests
```typescript
// tests/e2e/case-management.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Case Management', () => {
  test('complete case creation workflow', async ({ page }) => {
    await page.goto('/');
    
    // Should show case selection screen
    await expect(page.getByText('Welcome back! Select a case')).toBeVisible();
    
    // Click create new case
    await page.getByRole('button', { name: 'Create New Case' }).click();
    
    // Fill out case creation form
    await page.getByLabel('Case Title').fill('Test Case E2E');
    await page.getByLabel('Description').fill('End-to-end test case');
    await page.getByLabel('Client Name').fill('Test Client');
    await page.getByRole('radio', { name: 'Litigation' }).check();
    
    // Submit form
    await page.getByRole('button', { name: 'Create Case' }).click();
    
    // Should navigate to case workspace
    await expect(page.getByText('Test Case E2E')).toBeVisible();
    await expect(page.getByText('pleadings')).toBeVisible();
    await expect(page.getByText('motions')).toBeVisible();
  });
  
  test('case selection and navigation', async ({ page }) => {
    // Assuming cases already exist
    await page.goto('/');
    
    // Click on existing case
    await page.getByText('Smith v. Jones').click();
    
    // Should navigate to case workspace
    await expect(page.getByText('Smith v. Jones - Personal Injury')).toBeVisible();
    await expect(page.getByText('File Browser')).toBeVisible();
    await expect(page.getByText('AI Assistant')).toBeVisible();
  });
  
  test('case search functionality', async ({ page }) => {
    await page.goto('/');
    
    // Search for specific case
    await page.getByPlaceholder('Search cases...').fill('Smith');
    
    // Should filter results
    await expect(page.getByText('Smith v. Jones')).toBeVisible();
    await expect(page.getByText('ACME Corp')).not.toBeVisible();
    
    // Clear search
    await page.getByPlaceholder('Search cases...').clear();
    
    // Should show all cases again
    await expect(page.getByText('ACME Corp')).toBeVisible();
  });
});
```

## Performance Testing

### Load Testing
```python
# tests/performance/test_load.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from openhands.legal.case_manager import CaseManager

async def test_concurrent_case_creation():
    """Test creating multiple cases concurrently."""
    case_manager = CaseManager("/tmp/test-cases")
    
    async def create_test_case(i):
        case_data = {
            "title": f"Load Test Case {i}",
            "type": "litigation",
            "client": f"Client {i}"
        }
        start_time = time.time()
        result = await case_manager.create_case(case_data)
        end_time = time.time()
        return end_time - start_time, result
    
    # Create 100 cases concurrently
    tasks = [create_test_case(i) for i in range(100)]
    results = await asyncio.gather(*tasks)
    
    # Analyze performance
    times = [r[0] for r in results]
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    print(f"Average creation time: {avg_time:.3f}s")
    print(f"Maximum creation time: {max_time:.3f}s")
    
    # Assert performance requirements
    assert avg_time < 1.0  # Average should be under 1 second
    assert max_time < 5.0  # No single operation should take over 5 seconds

async def test_case_listing_performance():
    """Test case listing performance with many cases."""
    case_manager = CaseManager("/tmp/test-cases")
    
    # Create 1000 test cases
    for i in range(1000):
        await case_manager.create_case({
            "title": f"Performance Test Case {i}",
            "type": "litigation"
        })
    
    # Test listing performance
    start_time = time.time()
    result = await case_manager.list_cases(limit=50)
    end_time = time.time()
    
    listing_time = end_time - start_time
    print(f"Case listing time (50 of 1000): {listing_time:.3f}s")
    
    assert listing_time < 0.5  # Should list cases in under 500ms
    assert len(result["cases"]) == 50
    assert result["total"] == 1000
```

## Security Testing

### Access Control Tests
```python
# tests/security/test_access_control.py
import pytest
from pathlib import Path
from openhands.legal.case_manager import CaseManager

class TestSecurityAccessControl:
    async def test_path_traversal_prevention(self, case_manager):
        """Test that path traversal attacks are prevented."""
        malicious_case_data = {
            "title": "../../../etc/passwd",
            "type": "litigation"
        }
        
        case = await case_manager.create_case(malicious_case_data)
        
        # Case ID should be sanitized
        assert "../" not in case["id"]
        assert case["folder_path"] == case["id"]
        
        # Case directory should be within cases root
        case_path = case_manager.cases_root / case["folder_path"]
        assert case_manager.cases_root in case_path.parents
    
    async def test_file_access_restrictions(self, workspace_manager):
        """Test that file access is restricted to case directory."""
        case = await case_manager.create_case({"title": "Test Case", "type": "litigation"})
        
        # Should not be able to access files outside case directory
        with pytest.raises(ValueError):
            await workspace_manager.get_case_files(case["id"], "../../../etc")
    
    def test_metadata_validation(self, case_manager):
        """Test that case metadata is properly validated."""
        invalid_cases = [
            {"title": "", "type": "litigation"},  # Empty title
            {"title": "Test", "type": "invalid"},  # Invalid type
            {"title": "A" * 300, "type": "litigation"},  # Title too long
        ]
        
        for invalid_case in invalid_cases:
            with pytest.raises(ValueError):
                await case_manager.create_case(invalid_case)
```

## Test Data Management

### Test Fixtures
```python
# tests/fixtures/cases.py
import pytest
from typing import List, Dict, Any

@pytest.fixture
def sample_cases() -> List[Dict[str, Any]]:
    """Sample case data for testing."""
    return [
        {
            "title": "Smith v. Jones - Personal Injury",
            "description": "Motor vehicle accident case",
            "client": "John Smith",
            "type": "litigation",
            "status": "active",
            "tags": ["personal-injury", "motor-vehicle"]
        },
        {
            "title": "ACME Corp Acquisition",
            "description": "Corporate acquisition transaction",
            "client": "ACME Corporation",
            "type": "transactional",
            "status": "active",
            "tags": ["corporate", "acquisition"]
        },
        {
            "title": "Johnson Estate Planning",
            "description": "Estate planning and will preparation",
            "client": "Mary Johnson",
            "type": "estate",
            "status": "completed",
            "tags": ["estate-planning", "wills"]
        }
    ]

@pytest.fixture
def case_templates() -> List[Dict[str, Any]]:
    """Sample case templates for testing."""
    return [
        {
            "id": "litigation",
            "name": "Litigation Case",
            "description": "Standard litigation case structure",
            "folders": ["pleadings", "motions", "discovery", "exhibits"],
            "type": "litigation"
        },
        {
            "id": "transactional",
            "name": "Transactional Matter",
            "description": "Business transaction structure",
            "folders": ["contracts", "due-diligence", "regulatory"],
            "type": "transactional"
        }
    ]
```

## Continuous Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=openhands/legal
    
    - name: Run integration tests
      run: pytest tests/integration/ -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: npm ci
      working-directory: ./frontend
    
    - name: Run unit tests
      run: npm run test
      working-directory: ./frontend
    
    - name: Run E2E tests
      run: npm run test:e2e
      working-directory: ./frontend

  performance-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run performance tests
      run: pytest tests/performance/ -v
    
    - name: Generate performance report
      run: python scripts/generate_perf_report.py
```

## Test Coverage Goals

### Coverage Targets
- **Unit Tests**: 90%+ code coverage
- **Integration Tests**: 80%+ API endpoint coverage
- **E2E Tests**: 100% critical user path coverage
- **Performance Tests**: All major operations benchmarked
- **Security Tests**: All input validation and access control tested

### Reporting
- Automated coverage reports in CI/CD
- Performance benchmarks tracked over time
- Security scan results integrated into PR reviews
- Accessibility audit reports for UI changes
