"""
Tenant Portal Security Decorators

SECURITY NOTES:
- @tenant_required blocks ALL staff users from tenant portal routes
- Resource ownership decorators prevent cross-tenant data access
- All decorators must be applied AFTER @tenant_required
"""

from functools import wraps
from flask import redirect, url_for, flash, abort, g, request
from flask_login import current_user, logout_user
from website.models import TenantUser, Lease, Payment, MaintenanceRequest


def tenant_required(f):
    """
    Decorator to ensure request is from authenticated tenant user.

    SECURITY: This is the primary authorization check for tenant portal.
    - Blocks ALL unauthenticated requests
    - Blocks ALL staff users (they use different User model)
    - Blocks inactive tenant accounts
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to access the tenant portal.', 'info')
            return redirect(url_for('tenant_portal.login', next=request.url))

        # CRITICAL: Block staff users (they use User model, not TenantUser)
        # This prevents any cross-contamination between staff and tenant portals
        if not isinstance(current_user._get_current_object(), TenantUser):
            abort(403)

        # Check account is active
        if not current_user.is_active:
            logout_user()
            flash('Your account has been deactivated. Please contact your property manager.', 'error')
            return redirect(url_for('tenant_portal.login'))

        # Store tenant info in g for easy access in views
        g.tenant_user = current_user
        g.tenant = current_user.tenant
        g.company_id = current_user.company_id

        return f(*args, **kwargs)
    return decorated_function


def owns_lease(f):
    """
    Decorator to verify tenant owns the requested lease.

    SECURITY: Prevents cross-tenant lease data access.
    Must be used AFTER @tenant_required.
    """
    @wraps(f)
    def decorated_function(uuid, *args, **kwargs):
        # Get lease and verify ownership
        lease = Lease.query.filter_by(
            uuid=str(uuid),
            tenant_id=current_user.tenant_id,
            company_id=current_user.company_id
        ).first()

        if not lease:
            abort(404)

        # Inject lease into kwargs
        kwargs['lease'] = lease
        return f(uuid, *args, **kwargs)
    return decorated_function


def owns_payment(f):
    """
    Decorator to verify tenant owns the requested payment.

    SECURITY: Prevents cross-tenant payment data access.
    Must be used AFTER @tenant_required.
    """
    @wraps(f)
    def decorated_function(payment_id, *args, **kwargs):
        # Payments are linked via lease
        payment = Payment.query.join(Lease).filter(
            Payment.id == payment_id,
            Lease.tenant_id == current_user.tenant_id,
            Payment.company_id == current_user.company_id
        ).first()

        if not payment:
            abort(404)

        kwargs['payment'] = payment
        return f(payment_id, *args, **kwargs)
    return decorated_function


def owns_maintenance_request(f):
    """
    Decorator to verify tenant owns the requested maintenance request.

    SECURITY: Prevents cross-tenant maintenance data access.
    Must be used AFTER @tenant_required.
    """
    @wraps(f)
    def decorated_function(uuid, *args, **kwargs):
        request_obj = MaintenanceRequest.query.filter_by(
            uuid=str(uuid),
            tenant_id=current_user.tenant_id,
            company_id=current_user.company_id
        ).first()

        if not request_obj:
            abort(404)

        kwargs['maintenance_request'] = request_obj
        return f(uuid, *args, **kwargs)
    return decorated_function
