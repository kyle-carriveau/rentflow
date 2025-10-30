"""
Admin Bootstrap System

Automatically creates initial super admin account from environment variables
on first application startup. This is the Docker-friendly, production-ready
way to initialize the admin system without requiring CLI access.

Security Features:
- Only runs if ZERO admins exist (idempotent)
- Validates strong password requirements
- Forces password change on first login
- Logs creation to audit trail
- Never logs passwords in plain text
- Handles missing environment variables gracefully
"""

import os
from datetime import datetime
from website import db
from website.models import SuperAdmin, SuperAdminAuditLog
import logging

logger = logging.getLogger(__name__)


def validate_admin_password(password):
    """
    Validate that admin password meets security requirements.

    Requirements for admin passwords (stricter than regular users):
    - Minimum 12 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains digit
    - Contains special character

    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < 12:
        return False, "Admin password must be at least 12 characters long"

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)

    if not has_upper:
        return False, "Password must contain at least one uppercase letter"
    if not has_lower:
        return False, "Password must contain at least one lowercase letter"
    if not has_digit:
        return False, "Password must contain at least one digit"
    if not has_special:
        return False, "Password must contain at least one special character"

    return True, ""


def create_initial_admin_from_env():
    """
    Create initial super admin account from environment variables.

    This function is designed to be called once during application initialization.
    It will only create an admin if:
    1. No admins currently exist in the database
    2. Required environment variables are present
    3. Password meets security requirements

    Environment Variables:
        INITIAL_ADMIN_USERNAME: Admin username (required)
        INITIAL_ADMIN_PASSWORD: Admin password (required, min 12 chars)
        INITIAL_ADMIN_EMAIL: Admin email (optional)
        INITIAL_ADMIN_FIRST_NAME: First name (optional)
        INITIAL_ADMIN_LAST_NAME: Last name (optional)

    Returns:
        bool: True if admin was created, False otherwise
    """
    try:
        # Check if any admins already exist
        admin_count = SuperAdmin.query.count()
        if admin_count > 0:
            logger.info(f"Admin bootstrap skipped: {admin_count} admin(s) already exist")
            return False

        # Get environment variables
        username = os.getenv('INITIAL_ADMIN_USERNAME')
        password = os.getenv('INITIAL_ADMIN_PASSWORD')
        email = os.getenv('INITIAL_ADMIN_EMAIL', '')
        first_name = os.getenv('INITIAL_ADMIN_FIRST_NAME', '')
        last_name = os.getenv('INITIAL_ADMIN_LAST_NAME', '')

        # Check if required variables are present
        if not username or not password:
            logger.info("Admin bootstrap skipped: INITIAL_ADMIN_USERNAME or INITIAL_ADMIN_PASSWORD not set")
            return False

        # Validate username
        if len(username) < 3 or len(username) > 50:
            logger.error("Admin bootstrap failed: Username must be between 3 and 50 characters")
            return False

        # Validate password strength
        is_valid, error_msg = validate_admin_password(password)
        if not is_valid:
            logger.error(f"Admin bootstrap failed: {error_msg}")
            return False

        # Create the admin account
        admin = SuperAdmin(
            username=username,
            first_name=first_name if first_name else None,
            last_name=last_name if last_name else None,
            email=email if email else None,
            is_active=True,
            must_change_password=True,  # Force password change on first login
            created_by_admin_id=None,  # Bootstrap admin has no creator
            notes="Created automatically via environment variable bootstrap"
        )

        # Set password (also sets password_changed_at)
        admin.set_password(password)

        # Save to database
        db.session.add(admin)
        db.session.commit()

        # Create audit log entry
        audit_log = SuperAdminAuditLog(
            admin_id=admin.id,
            action='admin_bootstrap_created',
            target_company_id=None,
            ip_address='127.0.0.1',  # Local bootstrap
            user_agent='System Bootstrap',
            details='{"source": "environment_variables", "must_change_password": true}'
        )
        db.session.add(audit_log)
        db.session.commit()

        # Log success (NEVER log the password)
        logger.info(f"✅ Initial super admin created successfully: {username}")
        logger.info(f"   Email: {email or 'Not provided'}")
        logger.info(f"   Must change password on first login: Yes")
        logger.warning("⚠️  SECURITY: Admin must change password on first login!")

        return True

    except Exception as e:
        logger.error(f"Admin bootstrap failed with error: {str(e)}")
        db.session.rollback()
        return False


def init_admin_bootstrap(app):
    """
    Initialize admin bootstrap system.

    Call this function from create_app() after database initialization.
    It will automatically create the initial admin if needed.

    Args:
        app: Flask application instance

    Example:
        from website.admin.bootstrap import init_admin_bootstrap
        init_admin_bootstrap(app)
    """
    with app.app_context():
        # Only run bootstrap in non-testing environments
        if app.config.get('TESTING'):
            logger.info("Admin bootstrap skipped: Testing environment")
            return

        logger.info("Checking for initial admin bootstrap...")
        create_initial_admin_from_env()
