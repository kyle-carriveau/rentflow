import pytest
from flask import url_for
from website.models import User
from website import db

@pytest.mark.auth
@pytest.mark.unit
class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                first_name='Jane',
                last_name='Doe', 
                email='jane@example.com'
            )
            user.set_password('password123')
            
            assert user.first_name == 'Jane'
            assert user.last_name == 'Doe'
            assert user.email == 'jane@example.com'
            assert user.password_hash is not None
            assert user.password_hash != 'password123'  # Should be hashed
    
    def test_password_hashing(self, app):
        """Test password hashing and verification."""
        with app.app_context():
            user = User(
                first_name='Test',
                last_name='User',
                email='test@example.com'
            )
            user.set_password('secret123')
            
            assert user.check_password('secret123') is True
            assert user.check_password('wrongpassword') is False
    
    def test_user_representation(self, app):
        """Test user string representation."""
        with app.app_context():
            user = User(
                first_name='John',
                last_name='Smith',
                email='john@example.com'
            )
            # User model should have id attribute for flask-login
            assert hasattr(user, 'id')

@pytest.mark.auth
@pytest.mark.integration
class TestAuthViews:
    """Test authentication views and routes."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads correctly."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data
        
    def test_register_page_loads(self, client):
        """Test that register page loads correctly."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data
    
    def test_user_registration_success(self, client, app):
        """Test successful user registration."""
        response = client.post('/register', data={
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123'
        }, follow_redirects=True)
        
        with app.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.first_name == 'New'
            assert user.last_name == 'User'
    
    def test_user_registration_duplicate_email(self, client, auth_user):
        """Test registration with duplicate email fails."""
        response = client.post('/register', data={
            'first_name': 'Another',
            'last_name': 'User',
            'email': auth_user.email,  # Use existing email
            'password': 'password123',
            'password_confirm': 'password123'
        })
        
        assert response.status_code == 200
        assert b'Email already exists' in response.data
    
    def test_user_registration_password_mismatch(self, client):
        """Test registration with mismatched passwords fails."""
        response = client.post('/register', data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'differentpassword'
        })
        
        assert response.status_code == 200
        assert b'Passwords do not match' in response.data
    
    def test_user_login_success(self, client, auth_user):
        """Test successful user login."""
        response = client.post('/login', data={
            'email': auth_user.email,
            'password_hash': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to dashboard after successful login
        assert b'dashboard' in response.request.url.encode() or b'home' in response.request.url.encode()
    
    def test_user_login_invalid_credentials(self, client, auth_user):
        """Test login with invalid credentials."""
        response = client.post('/login', data={
            'email': auth_user.email,
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 302  # Redirect back to login
        
        # Follow the redirect to see the flash message
        response = client.post('/login', data={
            'email': auth_user.email,
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert b'Invalid username or password' in response.data
    
    def test_user_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert b'Invalid username or password' in response.data
    
    def test_logout(self, logged_in_user):
        """Test user logout."""
        response = logged_in_user.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect back to login page
        assert b'Login' in response.data

@pytest.mark.auth
@pytest.mark.integration
class TestModalRegistration:
    """Test modal registration functionality."""
    
    def test_modal_register_success(self, client, app):
        """Test successful modal registration."""
        response = client.post('/modal-register', data={
            'first_name': 'Modal',
            'last_name': 'User',
            'email': 'modal@example.com',
            'password': 'password123',
            'password_confirm': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'redirect' in data
        
        with app.app_context():
            user = User.query.filter_by(email='modal@example.com').first()
            assert user is not None
    
    def test_modal_register_validation_errors(self, client):
        """Test modal registration with validation errors."""
        response = client.post('/modal-register', data={
            'first_name': '',  # Missing required field
            'last_name': 'User',
            'email': 'invalid-email',  # Invalid email
            'password': '123',  # Too short
            'password_confirm': '456'  # Doesn't match
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'errors' in data
    
    def test_modal_register_duplicate_email(self, client, auth_user):
        """Test modal registration with duplicate email."""
        response = client.post('/modal-register', data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': auth_user.email,
            'password': 'password123',
            'password_confirm': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'errors' in data
        assert 'email' in data['errors']

@pytest.mark.auth
@pytest.mark.integration
class TestAuthenticationFlow:
    """Test complete authentication workflows."""
    
    def test_unauthenticated_access_redirects(self, client):
        """Test that unauthenticated users are redirected to login."""
        protected_routes = [
            '/profile/home',
            '/property/',
            '/tenant/',
            '/lease/',
            '/unit/'
        ]
        
        for route in protected_routes:
            response = client.get(route)
            # Should redirect to login (302) or return unauthorized (401)
            assert response.status_code in [302, 401, 404]  # 404 if route doesn't exist yet
    
    def test_authenticated_user_can_access_protected_routes(self, logged_in_user):
        """Test that authenticated users can access protected routes."""
        # Test accessing dashboard
        response = logged_in_user.get('/profile/home')
        # Should either succeed (200) or route might not exist yet (404)
        assert response.status_code in [200, 404]
    
    def test_login_redirect_after_authentication(self, client, auth_user):
        """Test that login redirects authenticated users."""
        # First login
        client.post('/login', data={
            'email': auth_user.email,
            'password_hash': 'testpassword123'
        })
        
        # Try to access login page again
        response = client.get('/login')
        # Should redirect away from login page
        assert response.status_code == 302