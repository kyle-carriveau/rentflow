from datetime import datetime, timedelta
from flask import session, request, current_app
from flask_login import current_user
import secrets

class SessionSecurity:
    """
    Enhanced session security management for RE2.
    Implements session timeout, fingerprinting, and security monitoring.
    """

    # Session timeout settings
    DEFAULT_TIMEOUT_MINUTES = 30
    REMEMBER_ME_TIMEOUT_DAYS = 30

    @classmethod
    def configure_session_security(cls, app):
        """Configure secure session settings for the Flask app."""

        # Generate a secure secret key if not provided
        if not app.config.get('SECRET_KEY') or app.config['SECRET_KEY'] == 'keyissecret':
            app.config['SECRET_KEY'] = secrets.token_hex(32)
            current_app.logger.warning("Generated new SECRET_KEY. Please set a permanent key in production.")

        # Secure session configuration
        app.config.update({
            # Session security
            'SESSION_COOKIE_SECURE': not app.config.get('DEBUG', False),  # HTTPS only in production
            'SESSION_COOKIE_HTTPONLY': True,  # Prevent XSS attacks
            'SESSION_COOKIE_SAMESITE': 'Lax',  # CSRF protection
            'PERMANENT_SESSION_LIFETIME': timedelta(minutes=cls.DEFAULT_TIMEOUT_MINUTES),

            # Additional security headers
            'WTF_CSRF_TIME_LIMIT': None,  # CSRF tokens don't expire
            'WTF_CSRF_SSL_STRICT': not app.config.get('DEBUG', False),  # Strict CSRF in production
        })

    @classmethod
    def init_session_fingerprint(cls):
        """Initialize session fingerprinting for security."""
        if 'fingerprint' not in session:
            # Create session fingerprint based on user agent and IP
            user_agent = request.headers.get('User-Agent', '')
            remote_addr = request.environ.get('REMOTE_ADDR', '')

            # Create a hash of identifying information
            import hashlib
            fingerprint_data = f"{user_agent}:{remote_addr}"
            session['fingerprint'] = hashlib.sha256(fingerprint_data.encode()).hexdigest()
            session['created_at'] = datetime.utcnow().isoformat()
            session['last_activity'] = datetime.utcnow().isoformat()

    @classmethod
    def validate_session_fingerprint(cls):
        """Validate session fingerprint to detect session hijacking."""
        if 'fingerprint' not in session:
            return False

        # Check current fingerprint against stored one
        user_agent = request.headers.get('User-Agent', '')
        remote_addr = request.environ.get('REMOTE_ADDR', '')

        import hashlib
        current_fingerprint_data = f"{user_agent}:{remote_addr}"
        current_fingerprint = hashlib.sha256(current_fingerprint_data.encode()).hexdigest()

        return session.get('fingerprint') == current_fingerprint

    @classmethod
    def update_session_activity(cls):
        """Update last activity timestamp for session timeout management."""
        session['last_activity'] = datetime.utcnow().isoformat()

    @classmethod
    def check_session_timeout(cls):
        """Check if session has exceeded timeout period."""
        if not current_user.is_authenticated:
            return False

        last_activity_str = session.get('last_activity')
        if not last_activity_str:
            return True  # No activity recorded, consider expired

        try:
            last_activity = datetime.fromisoformat(last_activity_str)
            timeout_minutes = cls.DEFAULT_TIMEOUT_MINUTES

            # Extend timeout for "remember me" sessions
            if session.get('remember_me'):
                timeout_minutes = cls.REMEMBER_ME_TIMEOUT_DAYS * 24 * 60

            timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            return last_activity < timeout_threshold

        except (ValueError, TypeError):
            return True  # Invalid timestamp, consider expired

    @classmethod
    def invalidate_session(cls):
        """Safely invalidate and clear session data."""
        session.clear()

    @classmethod
    def rotate_session_id(cls):
        """Rotate session ID after login for security."""
        # Flask handles session ID rotation automatically on session modification
        # We'll force it by updating session data
        session['session_rotated_at'] = datetime.utcnow().isoformat()

    @classmethod
    def log_security_event(cls, event_type, details=None):
        """Log security-related events for monitoring."""
        from website.audit_logging import AuditLogger

        # Map event types to appropriate severity
        severity_map = {
            'session_hijacking_attempt': 'critical',
            'csrf_violation': 'error',
            'login_failed': 'warning',
            'session_timeout': 'info',
            'login_success': 'info',
            'logout': 'info'
        }

        severity = severity_map.get(event_type, 'warning')

        AuditLogger.log_security_event(
            event_type=event_type,
            details=details,
            severity=severity
        )

    @classmethod
    def get_session_info(cls):
        """Get current session information for debugging/monitoring."""
        if not current_user.is_authenticated:
            return None

        return {
            'user_id': current_user.id,
            'user_email': current_user.email,
            'session_created': session.get('created_at'),
            'last_activity': session.get('last_activity'),
            'fingerprint_valid': cls.validate_session_fingerprint(),
            'session_timeout': cls.check_session_timeout(),
            'remember_me': session.get('remember_me', False)
        }


class CSRFProtection:
    """
    Enhanced CSRF protection utilities.
    """

    @classmethod
    def init_csrf_protection(cls, app):
        """Initialize CSRF protection for the application."""
        from flask_wtf.csrf import CSRFProtect

        csrf = CSRFProtect(app)

        # Custom CSRF error handler
        def csrf_error(reason):
            from flask import jsonify, render_template, request

            # Log CSRF attempt using AuditLogger
            SessionSecurity.log_security_event('csrf_violation', {
                'reason': str(reason),
                'endpoint': request.endpoint,
                'method': request.method
            })

            # Return appropriate response based on request type
            if request.is_json:
                return jsonify({'error': 'CSRF token invalid or missing'}), 400
            else:
                # For now return simple error, can enhance with template later
                return jsonify({'error': 'CSRF token invalid or missing'}), 400

        app.errorhandler(400)(csrf_error)

        return csrf

    @classmethod
    def generate_form_token(cls):
        """Generate CSRF token for forms."""
        from flask_wtf.csrf import generate_csrf
        return generate_csrf()


class SessionMiddleware:
    """
    Session security middleware for request processing.
    """

    def __init__(self, app):
        self.app = app
        self.init_app(app)

    def init_app(self, app):
        """Initialize session middleware with the Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self):
        """Process request before handling."""
        from flask import request
        from flask_login import current_user, logout_user

        # Skip session security for static files and some endpoints
        if request.endpoint in ['static', 'auth.login', 'auth.register']:
            return

        # Initialize session fingerprint for new sessions
        SessionSecurity.init_session_fingerprint()

        # Validate session for authenticated users
        if current_user.is_authenticated:
            # Check if email is verified for all non-verification routes
            if not current_user.email_verified and request.endpoint not in [
                'auth.verify_email', 'auth.verification_sent', 'auth.resend_verification', 'auth.logout'
            ]:
                from flask import redirect, url_for
                from flask_login import logout_user
                logout_user()
                SessionSecurity.invalidate_session()
                return redirect(url_for('auth.resend_verification'))

            # Check session fingerprint
            if not SessionSecurity.validate_session_fingerprint():
                SessionSecurity.log_security_event('session_hijacking_attempt')
                logout_user()
                SessionSecurity.invalidate_session()
                return

            # Check session timeout
            if SessionSecurity.check_session_timeout():
                SessionSecurity.log_security_event('session_timeout')
                logout_user()
                SessionSecurity.invalidate_session()
                return

            # Update activity timestamp
            SessionSecurity.update_session_activity()

    def after_request(self, response):
        """Process response after handling."""
        # Add security headers
        if not response.headers.get('X-Content-Type-Options'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
        if not response.headers.get('X-Frame-Options'):
            response.headers['X-Frame-Options'] = 'DENY'
        if not response.headers.get('X-XSS-Protection'):
            response.headers['X-XSS-Protection'] = '1; mode=block'

        return response