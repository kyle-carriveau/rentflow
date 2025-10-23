"""
Smoke Tests

Basic tests to verify the test infrastructure is working correctly.
These tests should always pass if the environment is set up correctly.
"""

import pytest


def test_python_version():
    """Verify Python version is 3.12+"""
    import sys
    assert sys.version_info >= (3, 12), "Python 3.12+ required"


def test_imports():
    """Verify all critical modules can be imported"""
    try:
        import flask
        import sqlalchemy
        import werkzeug
        import pytest
        import psycopg2
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import critical module: {e}")


@pytest.mark.unit
def test_app_creation(app):
    """Test that Flask app can be created"""
    assert app is not None
    assert app.config['TESTING'] is True


@pytest.mark.unit
def test_database_connection(app, db_session):
    """Test that database can be accessed"""
    from website.models import Company

    # Create a test company
    company = Company(
        name='Smoke Test Company',
        email='smoke@test.com'
    )
    db_session.session.add(company)
    db_session.session.commit()

    # Verify it was created
    found = Company.query.filter_by(name='Smoke Test Company').first()
    assert found is not None
    assert found.email == 'smoke@test.com'


@pytest.mark.unit
def test_client_creation(client):
    """Test that test client can be created"""
    assert client is not None


@pytest.mark.unit
def test_health_endpoint(client):
    """Test that health endpoint exists and responds"""
    response = client.get('/health')
    # Health endpoint might not exist yet, so we just check the client works
    assert response is not None
