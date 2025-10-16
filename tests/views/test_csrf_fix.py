"""
Test CSRF token refresh functionality for portfolio creation.
"""
import pytest
import tempfile
from flask import url_for
from website import create_app, db
from website.models import Portfolio


@pytest.fixture
def csrf_app():
    """Create a test app with CSRF enabled."""
    db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')

    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{temp_db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': True,  # Enable CSRF for this test
        'SECRET_KEY': 'test-secret-key-csrf',
        'LOGIN_DISABLED': False,
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


class TestCSRFTokenRefresh:
    """Test the CSRF token refresh functionality."""

    def test_csrf_token_endpoint_exists(self, csrf_app):
        """Test that the CSRF token refresh endpoint exists and works."""
        # Since we need a user in the CSRF app context, create one
        with csrf_app.app_context():
            from website.models import User, Company

            # Create a test company
            company = Company(name='Test Company', company_size='1-10')
            db.session.add(company)
            db.session.commit()

            # Create a test user
            user = User(
                email='test@example.com',
                first_name='Test',
                last_name='User',
                company_id=company.id,
                role='owner',
                password='password123'
            )
            db.session.add(user)
            db.session.commit()

            with csrf_app.test_client() as client:
                # Login first
                client.post('/login', data={
                    'email': user.email,
                    'password_hash': 'password123'
                })

                # Test CSRF token endpoint
                response = client.get('/auth/csrf-token', headers={
                    'X-Requested-With': 'XMLHttpRequest'
                })

                assert response.status_code == 200
                data = response.get_json()
                assert 'csrf_token' in data
                assert len(data['csrf_token']) > 0

    def test_portfolio_creation_without_csrf_token(self, csrf_app):
        """Test portfolio creation without CSRF token should fail."""
        with csrf_app.app_context():
            from website.models import User, Company

            # Create test data
            company = Company(name='Test Company', company_size='1-10')
            db.session.add(company)
            db.session.commit()

            user = User(
                email='test2@example.com',
                first_name='Test',
                last_name='User',
                company_id=company.id,
                role='owner',
                password='password123'
            )
            db.session.add(user)
            db.session.commit()

            with csrf_app.test_client() as client:
                # Login first
                client.post('/login', data={
                    'email': user.email,
                    'password_hash': 'password123'
                })

                # Test portfolio creation without CSRF token
                response = client.post('/portfolio/', data={
                    'portfolio_name': 'Test Portfolio No CSRF',
                    'description': 'Test description'
                }, headers={
                    'X-Requested-With': 'XMLHttpRequest'
                })

                # Should fail with 400 error
                assert response.status_code == 400

                # Verify portfolio was NOT created
                portfolio = Portfolio.query.filter_by(
                    name='Test Portfolio No CSRF',
                    company_id=user.get_company_id()
                ).first()
                assert portfolio is None

    def test_csrf_token_endpoint_requires_authentication(self, csrf_app):
        """Test that CSRF token endpoint requires authentication."""
        with csrf_app.test_client() as client:
            # Test CSRF token endpoint without login
            response = client.get('/auth/csrf-token', headers={
                'X-Requested-With': 'XMLHttpRequest'
            })

            # Should redirect to login or return 401/403
            assert response.status_code in [302, 401, 403]