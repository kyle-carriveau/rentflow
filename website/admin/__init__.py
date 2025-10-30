"""
Super Admin Blueprint - God View Dashboard

Provides system administrators with read-only access to view all companies,
users, properties, and system metrics across the entire multi-tenant application.

Security Features:
- Separate authentication system (not Flask-Login)
- Isolated admin sessions
- Complete audit logging of all actions
- Read-only access (no modification capabilities)
- No cross-contamination with regular user sessions
"""

from flask import Blueprint

admin = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')

from website.admin import views
