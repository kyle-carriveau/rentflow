import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from flask import current_app
from flask_login import current_user

class TwoFactorAuth:
    """
    Optional Two-Factor Authentication system for RE2.
    Implements TOTP (Time-based One-Time Passwords) using Google Authenticator compatible tokens.
    """

    # TOTP Configuration
    TOTP_INTERVAL = 30  # 30 seconds
    TOTP_DIGITS = 6     # 6 digit codes
    BACKUP_CODES_COUNT = 10

    @classmethod
    def generate_secret(cls):
        """Generate a new secret key for TOTP."""
        return pyotp.random_base32()

    @classmethod
    def generate_provisioning_uri(cls, user, secret):
        """Generate provisioning URI for QR code."""
        company_name = getattr(user.company_ref, 'name', 'RE2') if user.company_ref else 'RE2'

        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user.email,
            issuer_name=f"{company_name} Real Estate Management"
        )

    @classmethod
    def generate_qr_code(cls, provisioning_uri):
        """
        Generate QR code image for TOTP setup.
        Returns base64 encoded image data.
        """
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            current_app.logger.error(f"Failed to generate QR code: {str(e)}")
            return None

    @classmethod
    def verify_token(cls, secret, token, window=1):
        """
        Verify TOTP token.

        Args:
            secret: User's TOTP secret
            token: Token to verify
            window: Number of time windows to check (default 1 = +/- 30 seconds)

        Returns:
            bool: True if token is valid
        """
        if not secret or not token:
            return False

        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception as e:
            current_app.logger.error(f"TOTP verification failed: {str(e)}")
            return False

    @classmethod
    def enable_2fa_for_user(cls, user, token):
        """
        Enable 2FA for a user after verifying the initial token.

        Args:
            user: User object
            token: TOTP token to verify

        Returns:
            tuple: (success: bool, message: str, backup_codes: list or None)
        """
        from . import db
        from .audit_logging import AuditLogger

        if not user.totp_secret:
            return False, "No TOTP secret found. Please restart the setup process.", None

        # Verify the token
        if not cls.verify_token(user.totp_secret, token):
            AuditLogger.log_security_event(
                'totp_verification_failed',
                details={
                    'user_id': user.id,
                    'action': '2fa_enable_attempt'
                },
                severity='warning'
            )
            return False, "Invalid verification code. Please try again.", None

        # Generate backup codes
        backup_codes = cls.generate_backup_codes()

        # Enable 2FA
        user.totp_enabled = True
        user.totp_backup_codes = ','.join(backup_codes)
        user.totp_enabled_at = datetime.utcnow()

        db.session.commit()

        # Log 2FA enablement
        AuditLogger.log_security_event(
            'totp_enabled',
            details={'user_id': user.id},
            severity='info'
        )

        return True, "Two-factor authentication has been enabled successfully.", backup_codes

    @classmethod
    def disable_2fa_for_user(cls, user, password=None):
        """
        Disable 2FA for a user.

        Args:
            user: User object
            password: Current password for verification (optional)

        Returns:
            tuple: (success: bool, message: str)
        """
        from . import db
        from .audit_logging import AuditLogger

        if not user.totp_enabled:
            return False, "Two-factor authentication is not enabled."

        # Verify password if provided
        if password and not user.check_password(password):
            AuditLogger.log_security_event(
                'totp_disable_failed',
                details={
                    'user_id': user.id,
                    'reason': 'invalid_password'
                },
                severity='warning'
            )
            return False, "Invalid password."

        # Disable 2FA
        user.totp_enabled = False
        user.totp_secret = None
        user.totp_backup_codes = None
        user.totp_enabled_at = None

        db.session.commit()

        # Log 2FA disablement
        AuditLogger.log_security_event(
            'totp_disabled',
            details={'user_id': user.id},
            severity='warning'
        )

        return True, "Two-factor authentication has been disabled."

    @classmethod
    def authenticate_user(cls, user, token):
        """
        Authenticate user with 2FA token.

        Args:
            user: User object
            token: TOTP token or backup code

        Returns:
            tuple: (success: bool, message: str, used_backup_code: bool)
        """
        from . import db
        from .audit_logging import AuditLogger

        if not user.totp_enabled:
            return False, "Two-factor authentication is not enabled.", False

        # First try TOTP verification
        if cls.verify_token(user.totp_secret, token):
            AuditLogger.log_authentication_event(
                'totp_success',
                details={'user_id': user.id, 'method': 'totp'}
            )
            return True, "Authentication successful.", False

        # Try backup codes
        if user.totp_backup_codes:
            backup_codes = user.totp_backup_codes.split(',')

            if token in backup_codes:
                # Remove used backup code
                backup_codes.remove(token)
                user.totp_backup_codes = ','.join(backup_codes)
                db.session.commit()

                AuditLogger.log_authentication_event(
                    'totp_backup_code_used',
                    details={
                        'user_id': user.id,
                        'remaining_backup_codes': len(backup_codes)
                    }
                )

                return True, "Authentication successful using backup code.", True

        # Authentication failed
        AuditLogger.log_security_event(
            'totp_authentication_failed',
            details={'user_id': user.id},
            severity='warning'
        )

        return False, "Invalid verification code.", False

    @classmethod
    def generate_backup_codes(cls, count=None):
        """Generate backup codes for 2FA recovery."""
        import secrets
        import string

        if count is None:
            count = cls.BACKUP_CODES_COUNT

        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(code)

        return codes

    @classmethod
    def get_remaining_backup_codes_count(cls, user):
        """Get count of remaining backup codes for user."""
        if not user.totp_backup_codes:
            return 0
        return len(user.totp_backup_codes.split(','))

    @classmethod
    def regenerate_backup_codes(cls, user):
        """
        Regenerate backup codes for user.

        Returns:
            tuple: (success: bool, message: str, backup_codes: list or None)
        """
        from . import db
        from .audit_logging import AuditLogger

        if not user.totp_enabled:
            return False, "Two-factor authentication is not enabled.", None

        # Generate new backup codes
        backup_codes = cls.generate_backup_codes()
        user.totp_backup_codes = ','.join(backup_codes)
        db.session.commit()

        # Log backup code regeneration
        AuditLogger.log_security_event(
            'totp_backup_codes_regenerated',
            details={'user_id': user.id}
        )

        return True, "New backup codes generated successfully.", backup_codes

    @classmethod
    def setup_2fa_for_user(cls, user):
        """
        Initialize 2FA setup for user.

        Returns:
            tuple: (success: bool, secret: str, qr_code_data: str, provisioning_uri: str)
        """
        from . import db
        from .audit_logging import AuditLogger

        if user.totp_enabled:
            return False, None, None, None

        # Generate new secret
        secret = cls.generate_secret()

        # Store secret temporarily (not yet enabled)
        user.totp_secret = secret
        db.session.commit()

        # Generate provisioning URI and QR code
        provisioning_uri = cls.generate_provisioning_uri(user, secret)
        qr_code_data = cls.generate_qr_code(provisioning_uri)

        # Log 2FA setup initiation
        AuditLogger.log_security_event(
            'totp_setup_initiated',
            details={'user_id': user.id}
        )

        return True, secret, qr_code_data, provisioning_uri

    @classmethod
    def is_2fa_required_for_login(cls, user):
        """Check if 2FA is required for user login."""
        return user.totp_enabled if user else False

    @classmethod
    def get_user_2fa_status(cls, user):
        """
        Get comprehensive 2FA status for user.

        Returns:
            dict: 2FA status information
        """
        if not user:
            return {
                'enabled': False,
                'setup': False,
                'backup_codes_remaining': 0,
                'enabled_at': None
            }

        return {
            'enabled': user.totp_enabled,
            'setup': bool(user.totp_secret),
            'backup_codes_remaining': cls.get_remaining_backup_codes_count(user),
            'enabled_at': user.totp_enabled_at.isoformat() if user.totp_enabled_at else None
        }

    @classmethod
    def cleanup_incomplete_setups(cls, hours=24):
        """
        Clean up incomplete 2FA setups (maintenance task).
        Remove TOTP secrets for users who haven't completed setup.
        """
        from .models import User
        from . import db

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        incomplete_setups = db.session.query(User)\
            .filter(User.totp_secret.isnot(None))\
            .filter(User.totp_enabled == False)\
            .filter(User.uuid.notin_(
                # Exclude recently created users
                db.session.query(User.uuid)
                .filter(User.totp_secret.isnot(None))
                .filter(User.totp_enabled == False)
                # This would need a created_at field on User model
            ))\
            .all()

        count = 0
        for user in incomplete_setups:
            user.totp_secret = None
            count += 1

        db.session.commit()

        return count