from datetime import datetime
from flask import request, session, current_app
from flask_login import current_user
import json
import uuid

class AuditLogger:
    """
    Comprehensive audit logging system for RE2.
    Tracks all security-relevant events and user activities for compliance.
    """

    # Event categories
    CATEGORY_AUTHENTICATION = 'authentication'
    CATEGORY_AUTHORIZATION = 'authorization'
    CATEGORY_DATA_ACCESS = 'data_access'
    CATEGORY_DATA_MODIFICATION = 'data_modification'
    CATEGORY_SYSTEM = 'system'
    CATEGORY_SECURITY = 'security'

    # Event types
    EVENT_LOGIN_SUCCESS = 'login_success'
    EVENT_LOGIN_FAILED = 'login_failed'
    EVENT_LOGOUT = 'logout'
    EVENT_PASSWORD_CHANGE = 'password_change'
    EVENT_ACCOUNT_LOCKED = 'account_locked'
    EVENT_REGISTRATION = 'user_registration'

    EVENT_DATA_CREATE = 'data_create'
    EVENT_DATA_READ = 'data_read'
    EVENT_DATA_UPDATE = 'data_update'
    EVENT_DATA_DELETE = 'data_delete'
    EVENT_BULK_OPERATION = 'bulk_operation'

    EVENT_PERMISSION_DENIED = 'permission_denied'
    EVENT_ROLE_CHANGE = 'role_change'
    EVENT_ACCESS_ATTEMPT = 'access_attempt'

    EVENT_SESSION_TIMEOUT = 'session_timeout'
    EVENT_SESSION_HIJACK = 'session_hijacking_attempt'
    EVENT_CSRF_VIOLATION = 'csrf_violation'
    EVENT_RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded'
    EVENT_SUSPICIOUS_ACTIVITY = 'suspicious_activity'

    @classmethod
    def log_event(cls, event_type, category=None, resource_type=None, resource_id=None,
                  details=None, severity='info', company_id=None):
        """
        Log an audit event with comprehensive metadata.

        Args:
            event_type: Type of event (from EVENT_* constants)
            category: Event category (from CATEGORY_* constants)
            resource_type: Type of resource affected (e.g., 'property', 'tenant')
            resource_id: ID/UUID of the specific resource
            details: Additional event details (dict)
            severity: Event severity ('info', 'warning', 'error', 'critical')
            company_id: Company ID for multi-tenant logging
        """
        from . import db
        from .models import AuditLogModel

        try:
            # Gather context information
            user_id = getattr(current_user, 'id', None) if current_user.is_authenticated else None
            user_email = getattr(current_user, 'email', None) if current_user.is_authenticated else None
            user_role = getattr(current_user, 'role', None) if current_user.is_authenticated else None

            # Use user's company_id if not explicitly provided
            if not company_id and current_user.is_authenticated:
                company_id = getattr(current_user, 'company_id', None)

            # Request context
            ip_address = cls._get_client_ip()
            user_agent = request.headers.get('User-Agent', '') if request else ''
            endpoint = request.endpoint if request else None
            method = request.method if request else None
            url = request.url if request else None

            # Session context
            session_id = session.get('_id', '') if session else ''

            # Create audit log entry
            audit_entry = AuditLogModel(
                id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                event_type=event_type,
                category=category or cls._infer_category(event_type),
                severity=severity,
                user_id=user_id,
                user_email=user_email,
                user_role=user_role,
                company_id=company_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                http_method=method,
                url=url,
                resource_type=resource_type,
                resource_id=resource_id,
                details=json.dumps(details or {}),
                success=True  # Assume success unless specified otherwise
            )

            db.session.add(audit_entry)
            db.session.commit()

            # Also log to application logger for immediate visibility
            log_message = cls._format_log_message(audit_entry)

            if severity == 'critical':
                current_app.logger.critical(log_message)
            elif severity == 'error':
                current_app.logger.error(log_message)
            elif severity == 'warning':
                current_app.logger.warning(log_message)
            else:
                current_app.logger.info(log_message)

        except Exception as e:
            # Ensure audit logging failures don't break the application
            current_app.logger.error(f"Audit logging failed: {str(e)}")

    @classmethod
    def log_data_access(cls, resource_type, resource_id, action='read', details=None, company_id=None):
        """Log data access events."""
        cls.log_event(
            event_type=f'data_{action}',
            category=cls.CATEGORY_DATA_ACCESS,
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=details,
            company_id=company_id
        )

    @classmethod
    def log_authentication_event(cls, event_type, details=None, severity='info'):
        """Log authentication-related events."""
        cls.log_event(
            event_type=event_type,
            category=cls.CATEGORY_AUTHENTICATION,
            details=details,
            severity=severity
        )

    @classmethod
    def log_security_event(cls, event_type, details=None, severity='warning'):
        """Log security-related events."""
        cls.log_event(
            event_type=event_type,
            category=cls.CATEGORY_SECURITY,
            details=details,
            severity=severity
        )

    @classmethod
    def log_permission_denied(cls, resource_type=None, resource_id=None, required_permission=None):
        """Log permission denied events."""
        details = {
            'required_permission': required_permission,
            'user_role': getattr(current_user, 'role', None) if current_user.is_authenticated else None
        }

        cls.log_event(
            event_type=cls.EVENT_PERMISSION_DENIED,
            category=cls.CATEGORY_AUTHORIZATION,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            severity='warning'
        )

    @classmethod
    def get_user_activity_summary(cls, user_id, days=30):
        """Get activity summary for a specific user."""
        from . import db
        from .models import AuditLogModel
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        activities = db.session.query(AuditLogModel)\
            .filter(AuditLogModel.user_id == user_id)\
            .filter(AuditLogModel.timestamp >= start_date)\
            .order_by(AuditLogModel.timestamp.desc())\
            .all()

        return {
            'total_events': len(activities),
            'by_category': cls._group_by_field(activities, 'category'),
            'by_severity': cls._group_by_field(activities, 'severity'),
            'recent_events': [cls._serialize_audit_entry(entry) for entry in activities[:10]]
        }

    @classmethod
    def get_company_security_report(cls, company_id, days=30):
        """Get security report for a company."""
        from . import db
        from .models import AuditLogModel
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        security_events = db.session.query(AuditLogModel)\
            .filter(AuditLogModel.company_id == company_id)\
            .filter(AuditLogModel.category.in_([cls.CATEGORY_SECURITY, cls.CATEGORY_AUTHENTICATION]))\
            .filter(AuditLogModel.timestamp >= start_date)\
            .all()

        return {
            'period_days': days,
            'total_security_events': len(security_events),
            'failed_logins': len([e for e in security_events if e.event_type == cls.EVENT_LOGIN_FAILED]),
            'successful_logins': len([e for e in security_events if e.event_type == cls.EVENT_LOGIN_SUCCESS]),
            'security_violations': len([e for e in security_events if e.severity in ['error', 'critical']]),
            'by_event_type': cls._group_by_field(security_events, 'event_type'),
            'critical_events': [cls._serialize_audit_entry(e) for e in security_events if e.severity == 'critical']
        }

    @classmethod
    def _get_client_ip(cls):
        """Get the client IP address, considering proxies."""
        if not request:
            return None

        # Check for forwarded headers first (common in production with load balancers)
        ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        if ip:
            return ip

        ip = request.headers.get('X-Real-IP', '').strip()
        if ip:
            return ip

        return request.remote_addr

    @classmethod
    def _infer_category(cls, event_type):
        """Infer event category from event type."""
        if event_type in [cls.EVENT_LOGIN_SUCCESS, cls.EVENT_LOGIN_FAILED, cls.EVENT_LOGOUT,
                         cls.EVENT_PASSWORD_CHANGE, cls.EVENT_REGISTRATION]:
            return cls.CATEGORY_AUTHENTICATION
        elif event_type in [cls.EVENT_PERMISSION_DENIED, cls.EVENT_ROLE_CHANGE]:
            return cls.CATEGORY_AUTHORIZATION
        elif event_type.startswith('data_'):
            if event_type in [cls.EVENT_DATA_CREATE, cls.EVENT_DATA_UPDATE, cls.EVENT_DATA_DELETE]:
                return cls.CATEGORY_DATA_MODIFICATION
            else:
                return cls.CATEGORY_DATA_ACCESS
        elif event_type in [cls.EVENT_SESSION_TIMEOUT, cls.EVENT_SESSION_HIJACK, cls.EVENT_CSRF_VIOLATION]:
            return cls.CATEGORY_SECURITY
        else:
            return cls.CATEGORY_SYSTEM

    @classmethod
    def _format_log_message(cls, audit_entry):
        """Format audit entry for application logger."""
        return f"AUDIT: {audit_entry.event_type} | User: {audit_entry.user_email or 'Anonymous'} | " \
               f"IP: {audit_entry.ip_address} | Resource: {audit_entry.resource_type}:{audit_entry.resource_id} | " \
               f"Details: {audit_entry.details}"

    @classmethod
    def _group_by_field(cls, entries, field):
        """Group audit entries by a specific field."""
        groups = {}
        for entry in entries:
            value = getattr(entry, field, 'unknown')
            groups[value] = groups.get(value, 0) + 1
        return groups

    @classmethod
    def _serialize_audit_entry(cls, entry):
        """Serialize audit entry for JSON response."""
        return {
            'id': entry.id,
            'timestamp': entry.timestamp.isoformat(),
            'event_type': entry.event_type,
            'category': entry.category,
            'severity': entry.severity,
            'user_email': entry.user_email,
            'ip_address': entry.ip_address,
            'resource_type': entry.resource_type,
            'resource_id': entry.resource_id,
            'details': json.loads(entry.details) if entry.details else {}
        }


class AuditDecorator:
    """
    Decorator for automatically logging function calls and data access.
    """

    @staticmethod
    def log_data_access(resource_type, action='read'):
        """Decorator to log data access."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)

                # Try to extract resource ID from result or args
                resource_id = None
                if hasattr(result, 'id'):
                    resource_id = result.id
                elif hasattr(result, 'uuid'):
                    resource_id = result.uuid
                elif args and hasattr(args[0], 'id'):
                    resource_id = args[0].id

                AuditLogger.log_data_access(
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action,
                    details={'function': func.__name__}
                )

                return result
            return wrapper
        return decorator

    @staticmethod
    def log_permission_check(required_permission):
        """Decorator to log permission checks."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    return result
                except PermissionError:
                    AuditLogger.log_permission_denied(
                        required_permission=required_permission,
                        details={'function': func.__name__}
                    )
                    raise
            return wrapper
        return decorator