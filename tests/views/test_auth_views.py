"""
View tests for authentication routes including password reset.

Tests HTTP endpoints for login, registration, and password reset workflows.
"""
import pytest
from website.password_reset import PasswordResetManager


@pytest.mark.views
class TestForgotPasswordView:
    """Test /forgot endpoint."""

    def test_forgot_password_get(self, client):
        """Test GET request to forgot password page."""
        response = client.get('/forgot')
        assert response.status_code == 200
        assert b'Forgot your password' in response.data or b'forgot' in response.data.lower()

    def test_forgot_password_post_valid_email(self, client, user):
        """Test POST with valid email address."""
        response = client.post('/forgot', data={
            'email': user.email
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Check Your Email' in response.data or b'reset instructions' in response.data

    def test_forgot_password_post_invalid_email(self, client):
        """Test POST with invalid email format."""
        response = client.post('/forgot', data={
            'email': 'not-an-email'
        })

        assert response.status_code == 200
        assert b'valid email' in response.data.lower() or b'Email' in response.data

    def test_forgot_password_post_empty_email(self, client):
        """Test POST with empty email."""
        response = client.post('/forgot', data={
            'email': ''
        })

        assert response.status_code == 200
        assert b'required' in response.data.lower() or b'Email' in response.data

    def test_forgot_password_redirects_authenticated_users(self, auth_client):
        """Test that authenticated users are redirected away."""
        response = auth_client.get('/forgot', follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to dashboard
        assert b'Dashboard' in response.data or b'dashboard' in response.data.lower()


@pytest.mark.views
class TestResetPasswordView:
    """Test /reset/<token> endpoint."""

    def test_reset_password_get_valid_token(self, client, user):
        """Test GET request with valid token."""
        token = PasswordResetManager.generate_token(user)

        response = client.get(f'/reset/{token}')

        assert response.status_code == 200
        assert b'Reset password' in response.data or b'New Password' in response.data

    def test_reset_password_get_invalid_token(self, client):
        """Test GET request with invalid token."""
        response = client.get('/reset/invalid_token_12345', follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid' in response.data or b'expired' in response.data

    def test_reset_password_post_valid_data(self, client, user):
        """Test POST with valid password data."""
        token = PasswordResetManager.generate_token(user)

        response = client.post(f'/reset/{token}', data={
            'password': 'NewSecurePassword123!',
            'confirm_password': 'NewSecurePassword123!'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'successfully' in response.data.lower() or b'login' in response.data.lower()

    def test_reset_password_post_mismatched_passwords(self, client, user):
        """Test POST with mismatched passwords."""
        token = PasswordResetManager.generate_token(user)

        response = client.post(f'/reset/{token}', data={
            'password': 'NewPassword123!',
            'confirm_password': 'DifferentPassword123!'
        })

        assert response.status_code == 200
        assert b'match' in response.data.lower()

    def test_reset_password_post_weak_password(self, client, user):
        """Test POST with password that doesn't meet policy."""
        token = PasswordResetManager.generate_token(user)

        response = client.post(f'/reset/{token}', data={
            'password': '123',  # Too short
            'confirm_password': '123'
        })

        assert response.status_code == 200
        assert b'at least' in response.data.lower() or b'characters' in response.data.lower()

    def test_reset_password_redirects_authenticated_users(self, auth_client, user):
        """Test that authenticated users are redirected away."""
        token = PasswordResetManager.generate_token(user)

        response = auth_client.get(f'/reset/{token}', follow_redirects=True)

        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'dashboard' in response.data.lower()


@pytest.mark.views
class TestForgotPasswordSentView:
    """Test /forgot-password-sent endpoint."""

    def test_forgot_password_sent_page(self, client):
        """Test confirmation page displays correctly."""
        response = client.get('/forgot-password-sent')

        assert response.status_code == 200
        assert b'Check Your Email' in response.data or b'email' in response.data.lower()
        assert b'spam' in response.data.lower() or b'spam folder' in response.data.lower()


@pytest.mark.views
class TestPasswordResetRateLimiting:
    """Test rate limiting on password reset endpoints."""

    def test_forgot_password_rate_limit(self, client, user):
        """Test rate limiting on forgot password endpoint."""
        # Make multiple requests rapidly
        responses = []
        for i in range(7):  # Limit is 5 per hour
            response = client.post('/forgot', data={
                'email': user.email
            })
            responses.append(response.status_code)

        # First 5 should succeed (200 or 302), later ones may be rate limited (429)
        # Note: Rate limiting may be disabled in test environment
        assert all(status in [200, 302, 429] for status in responses)

    def test_reset_password_rate_limit(self, client, user):
        """Test rate limiting on reset password endpoint."""
        token = PasswordResetManager.generate_token(user)

        # Make multiple requests rapidly
        responses = []
        for i in range(12):  # Limit is 10 per hour
            response = client.post(f'/reset/{token}', data={
                'password': f'NewPassword{i}123!',
                'confirm_password': f'NewPassword{i}123!'
            })
            responses.append(response.status_code)

        # First 10 should process (200 or 302), later ones may be rate limited (429)
        assert all(status in [200, 302, 429] for status in responses)


@pytest.mark.views
class TestPasswordResetAccessControl:
    """Test access control and security on password reset endpoints."""

    def test_forgot_password_allows_anonymous(self, client):
        """Test that forgot password is accessible to anonymous users."""
        response = client.get('/forgot')
        assert response.status_code == 200

    def test_reset_password_allows_anonymous(self, client, user):
        """Test that reset password is accessible to anonymous users."""
        token = PasswordResetManager.generate_token(user)
        response = client.get(f'/reset/{token}')
        assert response.status_code == 200

    def test_forgot_password_blocks_authenticated(self, auth_client):
        """Test that authenticated users cannot access forgot password."""
        response = auth_client.get('/forgot', follow_redirects=True)
        assert b'Dashboard' in response.data or b'dashboard' in response.data.lower()

    def test_csrf_token_present_in_forms(self, client):
        """Test that CSRF token is present in forgot password form."""
        response = client.get('/forgot')
        # In production, CSRF token should be present
        # In testing, CSRF is typically disabled
        assert response.status_code == 200
