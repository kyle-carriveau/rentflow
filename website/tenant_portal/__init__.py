"""
Tenant Portal Blueprint

Provides a secure, separate authentication system for tenants to:
- View their lease information and payment history
- Make online rent payments via Stripe
- Submit and track maintenance requests
- Access lease documents

SECURITY NOTES:
- Completely separate from staff/landlord User model
- Uses TenantUser model for authentication
- All routes protected by @tenant_required decorator
- All data scoped by tenant_id AND company_id
"""

from flask import Blueprint

tenant_portal = Blueprint(
    'tenant_portal',
    __name__,
    template_folder='templates',
    url_prefix='/portal'
)

from . import views  # noqa: E402, F401
