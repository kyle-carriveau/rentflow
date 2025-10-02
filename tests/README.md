# RE2 Testing Framework

This directory contains comprehensive tests for the RE2 real estate management application, demonstrating best practices for testing Flask applications with multi-tenant architecture.

## Test Organization

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── unit/                      # Unit tests (models, business logic)
│   ├── test_auth.py           # Authentication unit tests
│   ├── test_models.py         # Database model tests
│   └── test_financial_calculations.py  # Financial calculation tests
├── integration/               # Integration tests (workflows)
│   ├── test_property_workflows.py      # Property management workflows
│   └── test_tenant_creation.py         # Tenant creation integration
├── views/                     # View/endpoint tests
│   ├── test_property_views.py # Property view tests
│   └── test_report_views.py   # Report view tests
├── fixtures/                  # Test data factories
└── README.md                  # This file
```

## Running Tests

### Basic Usage

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=website --cov-report=term-missing --cov-report=html

# Run tests verbosely
pytest -v -s
```

### Test Categories

```bash
# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only view tests
pytest -m views

# Run security-focused tests
pytest -m security

# Run financial calculation tests
pytest -m financial

# Combine markers
pytest -m "unit or views"
pytest -m "security and not integration"
```

### Specific Test Files

```bash
# Run specific test file
pytest tests/unit/test_financial_calculations.py

# Run specific test class
pytest tests/unit/test_financial_calculations.py::TestLeaseFinancialCalculations

# Run specific test method
pytest tests/unit/test_financial_calculations.py::TestLeaseFinancialCalculations::test_outstanding_balance_no_payments
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=website --cov-report=html
# Open htmlcov/index.html in browser

# Show missing lines in terminal
pytest --cov=website --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=website --cov-fail-under=80
```

## Writing Tests

### Test Structure Guidelines

1. **File Naming**: `test_[module_name].py`
2. **Class Naming**: `Test[ClassName]` (PascalCase)
3. **Method Naming**: `test_[specific_behavior]` (snake_case)
4. **Markers**: Use `@pytest.mark.[category]` to categorize tests

### Example Test Structure

```python
import pytest
from website.models import User, Company

@pytest.mark.unit
@pytest.mark.models
class TestUserModel:
    """Test User model functionality."""

    def test_user_creation(self, app, company_a):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                first_name='Test',
                last_name='User',
                email='test@example.com',
                role='Staff',
                company_id=company_a.id
            )
            user.set_password('test_password')

            assert user.first_name == 'Test'
            assert user.check_password('test_password')
```

### Multi-Tenant Testing

Always test data isolation between companies:

```python
def test_data_isolation(self, app, company_a, company_b):
    """Test that companies cannot access each other's data."""
    with app.app_context():
        # Create data for each company
        property_a = create_property(company_id=company_a.id)
        property_b = create_property(company_id=company_b.id)

        # Query with company filter
        company_a_properties = Property.query.filter_by(
            company_id=company_a.id
        ).all()

        assert property_a in company_a_properties
        assert property_b not in company_a_properties
```

### Financial Testing

Use `Decimal` for all monetary calculations:

```python
from decimal import Decimal

def test_payment_calculation(self, app, active_lease):
    """Test payment calculations maintain decimal precision."""
    with app.app_context():
        payment_amount = Decimal('1234.56')
        # Test calculation logic
        result = calculate_outstanding_balance(active_lease, payment_amount)
        assert isinstance(result, Decimal)
        assert result == expected_decimal_result
```

### View Testing

Test authentication, authorization, and data isolation:

```python
@pytest.mark.views
@pytest.mark.auth
def test_view_requires_authentication(self, client):
    """Test that view requires authentication."""
    response = client.get('/protected-endpoint/')
    assert response.status_code == 302
    assert '/login' in response.location

@pytest.mark.views
@pytest.mark.security
def test_view_enforces_role_permissions(self, app, authenticated_client, viewer_user):
    """Test role-based access control."""
    # Login as viewer (limited permissions)
    with client.session_transaction() as sess:
        sess['_user_id'] = str(viewer_user.id)

    response = client.post('/admin-only-endpoint/', data={})
    assert response.status_code in [403, 302]  # Forbidden or redirect
```

## Available Fixtures

### App and Client Fixtures

- `app`: Flask application instance with test configuration
- `client`: Test client for making HTTP requests
- `authenticated_client`: Client with authenticated owner user
- `runner`: CLI test runner

### Company and User Fixtures

- `company_a`, `company_b`: Test companies for multi-tenant testing
- `owner_user`: Owner role user for company A
- `manager_user`: Manager role user for company A
- `staff_user`: Staff role user for company A
- `viewer_user`: Viewer role user for company A
- `user_company_b`: User for company B (isolation testing)

### Property and Portfolio Fixtures

- `portfolio`: Test portfolio for company A
- `property_a`: Test property for company A
- `property_b`: Test property for company B
- `unit`: Test unit in property A

### Tenant and Lease Fixtures

- `tenant`: Test tenant for company A
- `active_lease`: Active lease between unit and tenant
- `expiring_lease`: Lease expiring in 30 days (for alerts)

### Financial Fixtures

- `payment`: Test payment for active lease
- `expense`: Test expense for property A

### Utility Fixtures

- `test_factory`: Factory class for creating test data
- `clean_db`: Automatically cleans database between tests

## Best Practices

### 1. Isolation
- Each test should be completely independent
- Use `clean_db` fixture to ensure fresh state
- Don't rely on execution order

### 2. Clarity
- Test one specific behavior per test method
- Use descriptive test names that explain the scenario
- Include docstrings for complex tests

### 3. Completeness
- Test happy path, edge cases, and error conditions
- Verify both success and failure scenarios
- Test security and permission boundaries

### 4. Performance
- Keep unit tests fast (< 100ms each)
- Use appropriate markers for slow integration tests
- Mock external dependencies when possible

### 5. Maintainability
- Use fixtures for common setup
- Group related tests in classes
- Keep test data minimal but realistic

## Debugging Tests

### Running Single Tests with Debug Output

```bash
# Run with output and debugging
pytest -v -s tests/unit/test_models.py::TestUserModel::test_password_hashing

# Drop into debugger on failure
pytest --pdb tests/unit/test_models.py

# Show local variables in traceback
pytest -l tests/unit/test_models.py
```

### Test Database Inspection

```bash
# Run tests with database preserved (for debugging)
pytest --keepdb tests/unit/test_models.py

# Use SQLite browser to inspect test database
# Database file will be in temporary location shown in test output
```

## Continuous Integration

This test suite is designed to run in CI environments:

```yaml
# Example GitHub Actions configuration
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=website --cov-report=xml --cov-fail-under=80

- name: Upload coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage.xml
```

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure multi-tenant isolation
3. Test security boundaries
4. Maintain minimum 80% coverage
5. Use appropriate test markers
6. Update this README if adding new patterns

For questions or issues with the test suite, refer to the main project documentation or create an issue in the project repository.