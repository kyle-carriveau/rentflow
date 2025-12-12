"""
Unit tests for password reset token management.

Tests the PasswordResetManager class methods for token generation,
verification, and lifecycle management.
"""
import pytest
from datetime import datetime, timedelta
from website.password_reset import PasswordResetManager
from website.models import PasswordResetToken, User
from website import db


@pytest.mark.unit
class TestPasswordResetManager:
    """Test suite for PasswordResetManager utility class."""

    def test_generate_token_creates_valid_token(self, app_context, user):
        """Test that generate_token creates a valid token."""
        token = PasswordResetManager.generate_token(user)

        # Token should be a non-empty string
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Token should be URL-safe (no problematic characters)
        assert ' ' not in token
        assert '/' not in token or '-' in token  # URL-safe encoding

    def test_generate_token_creates_database_record(self, app_context, user):
        """Test that generate_token creates a database record."""
        token = PasswordResetManager.generate_token(user)

        # Should have one reset token in database
        reset_tokens = PasswordResetToken.query.filter_by(user_id=user.id).all()
        assert len(reset_tokens) >= 1

        # Most recent token should be unused
        latest_token = PasswordResetToken.query.filter_by(
            user_id=user.id,
            used=False
        ).first()
        assert latest_token is not None
        assert latest_token.used is False

    def test_generate_token_invalidates_old_tokens(self, app_context, user):
        """Test that generating new token invalidates old ones."""
        # Generate first token
        token1 = PasswordResetManager.generate_token(user)

        # Generate second token
        token2 = PasswordResetManager.generate_token(user)

        # First token should be marked as used
        import hashlib
        token1_hash = hashlib.sha256(token1.encode()).hexdigest()
        old_token = PasswordResetToken.query.filter_by(token_hash=token1_hash).first()
        assert old_token.used is True

        # Second token should be unused
        token2_hash = hashlib.sha256(token2.encode()).hexdigest()
        new_token = PasswordResetToken.query.filter_by(token_hash=token2_hash).first()
        assert new_token.used is False

    def test_generate_token_sets_expiration(self, app_context, user):
        """Test that generated tokens have correct expiration time."""
        token = PasswordResetManager.generate_token(user)

        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()

        # Expiration should be approximately 24 hours from now
        expected_expiry = datetime.utcnow() + timedelta(hours=24)
        time_diff = abs((reset_token.expires_at - expected_expiry).total_seconds())

        # Allow 5 second tolerance for test execution time
        assert time_diff < 5

    def test_verify_token_with_valid_token(self, app_context, user):
        """Test verify_token returns user for valid token."""
        token = PasswordResetManager.generate_token(user)

        verified_user, error = PasswordResetManager.verify_token(token)

        assert verified_user is not None
        assert verified_user.id == user.id
        assert error is None

    def test_verify_token_with_invalid_token(self, app_context, user):
        """Test verify_token returns error for invalid token."""
        invalid_token = "completely_fake_token_12345"

        verified_user, error = PasswordResetManager.verify_token(invalid_token)

        assert verified_user is None
        assert error is not None
        assert "Invalid" in error

    def test_verify_token_with_expired_token(self, app_context, user):
        """Test verify_token returns error for expired token."""
        token = PasswordResetManager.generate_token(user)

        # Manually expire the token
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
        reset_token.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.session.commit()

        verified_user, error = PasswordResetManager.verify_token(token)

        assert verified_user is None
        assert error is not None
        assert "expired" in error.lower()

    def test_verify_token_with_used_token(self, app_context, user):
        """Test verify_token returns error for already used token."""
        token = PasswordResetManager.generate_token(user)

        # Mark token as used
        PasswordResetManager.mark_token_used(token)

        verified_user, error = PasswordResetManager.verify_token(token)

        assert verified_user is None
        assert error is not None

    def test_mark_token_used(self, app_context, user):
        """Test mark_token_used marks token as used."""
        token = PasswordResetManager.generate_token(user)

        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Verify token is initially unused
        reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
        assert reset_token.used is False

        # Mark as used
        PasswordResetManager.mark_token_used(token)

        # Verify token is now marked as used
        reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
        assert reset_token.used is True

    def test_mark_token_used_idempotent(self, app_context, user):
        """Test mark_token_used can be called multiple times safely."""
        token = PasswordResetManager.generate_token(user)

        # Mark as used twice
        PasswordResetManager.mark_token_used(token)
        PasswordResetManager.mark_token_used(token)

        # Should not raise error
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
        assert reset_token.used is True

    def test_get_active_token_count(self, app_context, user):
        """Test get_active_token_count returns correct count."""
        # Initially should be 0
        count = PasswordResetManager.get_active_token_count(user)
        assert count == 0

        # Generate a token
        token = PasswordResetManager.generate_token(user)
        count = PasswordResetManager.get_active_token_count(user)
        assert count == 1

        # Mark as used
        PasswordResetManager.mark_token_used(token)
        count = PasswordResetManager.get_active_token_count(user)
        assert count == 0

    def test_cleanup_expired_tokens(self, app_context, user):
        """Test cleanup_expired_tokens removes old tokens."""
        token = PasswordResetManager.generate_token(user)

        # Manually set token creation to 8 days ago
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
        reset_token.created_at = datetime.utcnow() - timedelta(days=8)
        db.session.commit()

        # Run cleanup (default 7 days)
        deleted_count = PasswordResetManager.cleanup_expired_tokens(days_old=7)

        # Should have deleted the old token
        assert deleted_count >= 1

        # Token should no longer exist
        reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
        assert reset_token is None

    def test_token_hash_is_secure(self, app_context, user):
        """Test that tokens are hashed with SHA256."""
        token = PasswordResetManager.generate_token(user)

        import hashlib
        expected_hash = hashlib.sha256(token.encode()).hexdigest()

        reset_token = PasswordResetToken.query.filter_by(token_hash=expected_hash).first()
        assert reset_token is not None

        # Hash should be 64 characters (SHA256 hex)
        assert len(reset_token.token_hash) == 64
