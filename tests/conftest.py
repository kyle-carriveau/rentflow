"""
Pytest Configuration and Shared Fixtures

This file contains shared fixtures used across all test modules.
Fixtures are automatically discovered by pytest.
"""

import pytest
from website import create_app, db
from website.models import Company, User
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='session')
def app():
    """
    Create and configure a test application instance.

    This fixture has session scope, meaning it's created once per test session.
    """
    app = create_app('testing')

    # Ensure we're using the testing config
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SERVER_NAME': 'localhost.localdomain',
    })

    return app


@pytest.fixture(scope='function')
def app_context(app):
    """
    Create application context for tests that need it.

    This fixture has function scope, meaning it's created for each test function.
    """
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def db_session(app):
    """
    Create a database session for testing with automatic rollback.

    Creates all tables before the test and drops them after.
    Each test gets a clean database state.
    """
    with app.app_context():
        # Create all tables
        db.create_all()

        yield db

        # Cleanup: rollback any changes and drop all tables
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app, db_session):
    """
    Create a test client for making requests to the application.

    The test client simulates HTTP requests without running a server.
    """
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """
    Create a CLI test runner for testing Flask CLI commands.
    """
    return app.test_cli_runner()


@pytest.fixture
def company(db_session):
    """
    Create a test company for use in tests.
    """
    company = Company(
        name='Test Company',
        email='test@company.com',
        phone='555-0100',
        address='123 Test St',
        city='Test City',
        state='CA',
        zip_code='90000'
    )
    db_session.session.add(company)
    db_session.session.commit()
    return company


@pytest.fixture
def user(db_session, company):
    """
    Create a test user for use in tests.
    """
    user = User(
        email='testuser@example.com',
        first_name='Test',
        last_name='User',
        # phone removed from constructor - will be set after
        role='Owner',
        company_id=company.id
    )
    # Set password using the set_password method
    user.set_password('TestPassword123!', validate_policy=False)

    # Set optional fields after initialization
    user.phone = '5550101'

    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def auth_client(client, user):
    """
    Create an authenticated test client.

    Logs in the test user and returns the client with an active session.
    """
    with client:
        client.post('/auth/login', data={
            'email': user.email,
            'password': 'TestPassword123!'
        }, follow_redirects=True)
        yield client
