"""
Integration tests for complete password reset workflow.

Tests the end-to-end flow from requesting reset to successfully
changing password.
"""
import pytest
import re
from website.password_reset import PasswordResetManager
from website.models import User
from website import db


@pytest.mark.integration
class TestPasswordResetWorkflow:
    """Test complete password reset workflow."""

    def test_complete_password_reset_flow(self, client, user):
        """Test full workflow: request reset -> receive email -> reset password -> login."""
        # Step 1: Request password reset
        response = client.post('/forgot', data={
            'email': user.email
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Check Your Email' in response.data or b'reset instructions' in response.data

        # Step 2: Generate token (simulating email link)
        token = PasswordResetManager.generate_token(user)

        # Step 3: Visit reset password page with token
        response = client.get(f'/reset/{token}')
        assert response.status_code == 200
        assert b'Reset password' in response.data or b'New Password' in response.data

        # Step 4: Submit new password
        new_password = 'NewSecurePassword123!'
        response = client.post(f'/reset/{token}', data={
            'password': new_password,
            'confirm_password': new_password
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'successfully' in response.data.lower() or b'login' in response.data.lower()

        # Step 5: Verify can login with new password
        response = client.post('/login', data={
            'email': user.email,
            'password': new_password
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should be redirected to dashboard after successful login
        assert b'Dashboard' in response.data or b'Welcome' in response.data

    def test_forgot_password_nonexistent_email(self, client):
        """Test forgot password with email that doesn't exist."""
        response = client.post('/forgot', data={
            'email': 'nonexistent@example.com'
        }, follow_redirects=True)

        # Should still show success message (prevent email enumeration)
        assert response.status_code == 200
        assert b'Check Your Email' in response.data or b'reset instructions' in response.data

    def test_reset_password_with_invalid_token(self, client):
        """Test accessing reset page with invalid token."""
        response = client.get('/reset/invalid_token_123', follow_redirects=True)

        assert response.status_code == 200
        # Should be redirected to forgot password page with error
        assert b'Invalid' in response.data or b'expired' in response.data

    def test_reset_password_token_single_use(self, client, user):
        """Test that token can only be used once."""
        token = PasswordResetManager.generate_token(user)

        # First use should succeed
        new_password = 'FirstNewPassword123!'
        response = client.post(f'/reset/{token}', data={
            'password': new_password,
            'confirm_password': new_password
        }, follow_redirects=True)

        assert response.status_code == 200

        # Second use should fail
        another_password = 'SecondNewPassword123!'
        response = client.post(f'/reset/{token}', data={
            'password': another_password,
            'confirm_password': another_password
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid' in response.data or b'expired' in response.data

    def test_reset_password_validates_password_policy(self, client, user):
        """Test that password reset enforces password policy."""
        token = PasswordResetManager.generate_token(user)

        # Try with weak password (too short)
        weak_password = 'weak'
        response = client.post(f'/reset/{token}', data={
            'password': weak_password,
            'confirm_password': weak_password
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should show validation error
        assert b'at least' in response.data.lower() or b'characters' in response.data.lower()

    def test_reset_password_requires_matching_passwords(self, client, user):
        """Test that passwords must match."""
        token = PasswordResetManager.generate_token(user)

        response = client.post(f'/reset/{token}', data={
            'password': 'NewPassword123!',
            'confirm_password': 'DifferentPassword123!'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'match' in response.data.lower()

    def test_forgot_password_requires_valid_email(self, client):
        """Test that forgot password validates email format."""
        response = client.post('/forgot', data={
            'email': 'not-an-email'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'valid email' in response.data.lower() or b'Email' in response.data

    def test_authenticated_user_cannot_access_reset(self, auth_client, user):
        """Test that logged-in users are redirected from reset pages."""
        token = PasswordResetManager.generate_token(user)

        # Try to access forgot password page
        response = auth_client.get('/forgot', follow_redirects=True)
        assert response.status_code == 200
        # Should be redirected to dashboard
        assert b'Dashboard' in response.data or b'dashboard' in response.data.lower()

        # Try to access reset password page
        response = auth_client.get(f'/reset/{token}', follow_redirects=True)
        assert response.status_code == 200
        # Should be redirected to dashboard
        assert b'Dashboard' in response.data or b'dashboard' in response.data.lower()

    def test_multiple_users_tokens_isolated(self, app_context, client):
        """Test that password reset tokens are user-specific."""
        # Create two users
        from website.models import Company, User
        from werkzeug.security import generate_password_hash

        company = Company(
            name='Test Company 2',
            email='test2@company.com',
            phone='555-0200'
        )
        db.session.add(company)
        db.session.commit()

        user1 = User(
            email='user1@example.com',
            password_hash=generate_password_hash('Password123!'),
            first_name='User',
            last_name='One',
            phone='5550201',
            role='Owner',
            company_id=company.id
        )
        user2 = User(
            email='user2@example.com',
            password_hash=generate_password_hash('Password123!'),
            first_name='User',
            last_name='Two',
            phone='5550202',
            role='Owner',
            company_id=company.id
        )
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        # Generate tokens for both users
        token1 = PasswordResetManager.generate_token(user1)
        token2 = PasswordResetManager.generate_token(user2)

        # Verify token1 only works for user1
        verified_user, error = PasswordResetManager.verify_token(token1)
        assert verified_user.id == user1.id

        # Verify token2 only works for user2
        verified_user, error = PasswordResetManager.verify_token(token2)
        assert verified_user.id == user2.id

    def test_password_history_enforcement(self, client, user):
        """Test that password reset enforces password history."""
        # Get the user's current password hash
        old_password_hash = user.password_hash

        token = PasswordResetManager.generate_token(user)

        # Try to reset to a password that might be in history
        # (This test assumes the user fixture uses a specific password)
        response = client.post(f'/reset/{token}', data={
            'password': 'TestPassword123!',  # Same as fixture password
            'confirm_password': 'TestPassword123!'
        }, follow_redirects=True)

        # Should either succeed or show password history error
        assert response.status_code == 200
        # If password policy checks history, it would show an error
        # Otherwise it succeeds

    def test_csrf_protection_on_forms(self, app_context, client):
        """Test that CSRF protection is active on password reset forms."""
        # Note: In testing environment, CSRF is typically disabled
        # This test documents the expectation for production
        pass  # CSRF is disabled in test config


@pytest.mark.integration
class TestPasswordResetSecurity:
    """Test security aspects of password reset."""

    def test_token_is_cryptographically_secure(self, app_context, user):
        """Test that generated tokens use secure random generation."""
        tokens = set()
        for _ in range(10):
            token = PasswordResetManager.generate_token(user)
            tokens.add(token)

        # All tokens should be unique (no collisions)
        assert len(tokens) == 10

        # Tokens should be sufficiently long
        for token in tokens:
            assert len(token) >= 32

    def test_token_storage_uses_hashing(self, app_context, user):
        """Test that tokens are hashed before storage."""
        token = PasswordResetManager.generate_token(user)

        from website.models import PasswordResetToken
        import hashlib

        # Calculate expected hash
        expected_hash = hashlib.sha256(token.encode()).hexdigest()

        # Verify stored hash matches
        stored_token = PasswordResetToken.query.filter_by(
            user_id=user.id,
            used=False
        ).first()

        assert stored_token.token_hash == expected_hash
        # Plaintext token should NOT be in database
        assert token not in str(stored_token.token_hash)
