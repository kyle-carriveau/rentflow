"""
Password Reset Token Management

Handles secure token generation, validation, and lifecycle management
for the forgot password functionality.

Security Features:
- Cryptographically secure token generation
- SHA256 hashing for storage (never store plaintext)
- 24-hour expiration window
- Single-use tokens
- IP and user agent tracking
- Automatic cleanup of expired tokens
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from flask import request
from website.models import PasswordResetToken, User
from website import db


class PasswordResetManager:
    """Manages password reset tokens with security best practices."""

    TOKEN_LENGTH = 32  # Bytes (64 hex characters)
    EXPIRY_HOURS = 24

    @classmethod
    def generate_token(cls, user):
        """
        Generate secure reset token and save to database.

        Args:
            user: User instance requesting password reset

        Returns:
            str: Plaintext token to send via email (never logged or stored)

        Security:
            - Uses secrets.token_urlsafe for cryptographic randomness
            - Stores SHA256 hash, never plaintext
            - Invalidates any existing unused tokens for user
            - Tracks IP address and user agent for security monitoring
        """
        # Generate cryptographically secure random token
        token = secrets.token_urlsafe(cls.TOKEN_LENGTH)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Invalidate any existing tokens for this user (one active token at a time)
        PasswordResetToken.query.filter_by(
            user_id=user.id,
            used=False
        ).update({'used': True})

        # Create new token record
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=cls.EXPIRY_HOURS),
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent', '')[:255] if request else None
        )
        db.session.add(reset_token)
        db.session.commit()

        return token  # Return plaintext token for email (never logged)

    @classmethod
    def verify_token(cls, token):
        """
        Verify token and return associated user if valid.

        Args:
            token: Plaintext token from email link

        Returns:
            tuple: (User instance or None, error message or None)

        Example:
            user, error = PasswordResetManager.verify_token(token)
            if error:
                flash(error, 'danger')
                return redirect(url_for('auth.forgot'))
        """
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            reset_token = PasswordResetToken.query.filter_by(
                token_hash=token_hash,
                used=False
            ).first()

            if not reset_token:
                return None, "Invalid or expired reset link. Please request a new one."

            # Check expiration
            if reset_token.expires_at < datetime.utcnow():
                return None, "Reset link has expired. Please request a new one."

            return reset_token.user, None

        except Exception as e:
            # Log error but don't expose details to user
            return None, "Invalid reset link. Please request a new one."

    @classmethod
    def mark_token_used(cls, token):
        """
        Mark token as used after successful password reset.

        Args:
            token: Plaintext token that was successfully used

        Security:
            - Prevents token reuse attacks
            - Idempotent (safe to call multiple times)
        """
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            PasswordResetToken.query.filter_by(
                token_hash=token_hash
            ).update({'used': True})
            db.session.commit()
        except Exception:
            # Silently fail - token may already be marked used
            db.session.rollback()

    @classmethod
    def cleanup_expired_tokens(cls, days_old=7):
        """
        Remove expired tokens older than specified days.

        Args:
            days_old: Delete tokens created more than this many days ago

        Returns:
            int: Number of tokens deleted

        Usage:
            # Call this from a background job or scheduled task
            deleted = PasswordResetManager.cleanup_expired_tokens()
            logger.info(f"Cleaned up {deleted} expired password reset tokens")
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days_old)
            deleted = PasswordResetToken.query.filter(
                PasswordResetToken.created_at < cutoff
            ).delete()
            db.session.commit()
            return deleted
        except Exception:
            db.session.rollback()
            return 0

    @classmethod
    def get_active_token_count(cls, user):
        """
        Get count of active (unused, unexpired) tokens for a user.

        Args:
            user: User instance

        Returns:
            int: Number of active tokens

        Usage:
            # Useful for rate limiting or security monitoring
            if PasswordResetManager.get_active_token_count(user) > 3:
                # Potential abuse detected
                pass
        """
        return PasswordResetToken.query.filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).count()
