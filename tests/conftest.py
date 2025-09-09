import pytest
import tempfile
import os
from website import create_app, db
from website.models import User, Property, Unit, Tenant, Lease, Portfolio

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to serve as the database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def auth_user(app):
    """Create a test user for authentication tests."""
    with app.app_context():
        user = User(
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def logged_in_user(client, auth_user, app):
    """Log in the test user and return the client."""
    with app.app_context():
        # Refresh the user to make sure it's attached to the current session
        user = User.query.get(auth_user.id)
        client.post('/login', data={
            'email': user.email,
            'password_hash': 'testpassword123'  # Note: using password_hash field name from form
        })
    return client

@pytest.fixture
def sample_property(app, auth_user):
    """Create a sample property for testing."""
    with app.app_context():
        property = Property(
            name='Test Property',
            owner=auth_user.id,
            address='123 Test St',
            city='Test City',
            state='CA',
            zip_code=12345,
            type='Apartment'
        )
        db.session.add(property)
        db.session.commit()
        return property

@pytest.fixture
def sample_unit(app, auth_user, sample_property):
    """Create a sample unit for testing."""
    with app.app_context():
        unit = Unit(
            name='Unit 1A',
            owner=auth_user.id,
            property=sample_property.id,
            bedrooms=2,
            bathrooms=1,
            rent=1500,
            sqft=800,
            description='Nice 2BR apartment'
        )
        db.session.add(unit)
        db.session.commit()
        return unit

@pytest.fixture
def sample_tenant(app, auth_user, sample_property):
    """Create a sample tenant for testing."""
    with app.app_context():
        tenant = Tenant(
            landlord=auth_user.id,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone=5551234567,
            address='456 Tenant St',
            city='Test City',
            state='CA',
            zip_code=12345,
            property=sample_property.id
        )
        db.session.add(tenant)
        db.session.commit()
        return tenant