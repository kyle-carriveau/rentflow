"""
Tenant Portal Views

SECURITY NOTES:
- All authentication routes have rate limiting
- Timing attack prevention on login
- Account lockout after failed attempts
- Session rotation on login
- CSRF protection via Flask-WTF
"""

from flask import render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import secrets

from . import tenant_portal
from .forms import (
    TenantLoginForm,
    TenantRegistrationForm,
    TenantForgotPasswordForm,
    TenantResetPasswordForm,
    MaintenanceRequestForm,
    MaintenanceFeedbackForm
)
from .decorators import tenant_required, owns_lease, owns_maintenance_request
from website.models import TenantUser, Tenant, Lease, Payment, MaintenanceRequest
from website import db, limiter
from website.session_security import SessionSecurity
from website.audit_logging import AuditLogger


# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@tenant_portal.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """
    Tenant portal login with security protections.

    SECURITY:
    - Rate limiting: 5 attempts per minute
    - Timing attack prevention (constant-time password check)
    - Account lockout after 5 failed attempts
    - Session rotation on successful login
    """
    # Redirect if already logged in as tenant
    if current_user.is_authenticated and isinstance(current_user._get_current_object(), TenantUser):
        return redirect(url_for('tenant_portal.dashboard'))

    # If logged in as staff user, show message
    if current_user.is_authenticated:
        flash('Please log out of your staff account to access the tenant portal.', 'info')
        return redirect(url_for('profile.dashboard'))

    form = TenantLoginForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        # SECURITY: Timing attack prevention - always perform hash check
        DUMMY_HASH = 'pbkdf2:sha256:600000$dummysalt$dummyhashfortimingattackprevention1234567890abcdef'

        tenant_user = TenantUser.query.filter_by(email=email).first()

        if tenant_user:
            # Check account lockout
            if tenant_user.is_locked():
                remaining_minutes = int((tenant_user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
                flash(f'Account temporarily locked. Please try again in {remaining_minutes} minutes.', 'error')
                return render_template('tenant_portal/login.html', form=form)

            # Check password
            password_valid = tenant_user.check_password(form.password.data)
        else:
            # Perform dummy hash check to prevent timing attack
            check_password_hash(DUMMY_HASH, form.password.data)
            password_valid = False

        if not tenant_user or not password_valid:
            # Record failed attempt
            if tenant_user:
                tenant_user.record_failed_login()

            # Log security event
            AuditLogger.log_event(
                event_type='tenant_login_failed',
                category=AuditLogger.CATEGORY_SECURITY,
                details={'email': email, 'ip': request.remote_addr},
                severity='warning'
            )

            flash('Invalid email or password.', 'error')
            return redirect(url_for('tenant_portal.login'))

        # Check if account is active
        if not tenant_user.is_active:
            flash('Your account has been deactivated. Please contact your property manager.', 'error')
            return redirect(url_for('tenant_portal.login'))

        # Check if email is verified (for invited users who completed registration)
        if not tenant_user.email_verified:
            flash('Please complete your registration using the invitation link sent to your email.', 'warning')
            return redirect(url_for('tenant_portal.login'))

        # Successful login
        tenant_user.record_successful_login(ip_address=request.remote_addr)

        # Rotate session ID for security
        SessionSecurity.rotate_session_id()

        # Set session flag to identify tenant user
        session['is_tenant_user'] = True

        # Log successful login
        AuditLogger.log_event(
            event_type='tenant_login_success',
            category=AuditLogger.CATEGORY_SECURITY,
            resource_type='tenant_user',
            resource_id=tenant_user.id,
            details={'ip': request.remote_addr},
            company_id=tenant_user.company_id
        )

        login_user(tenant_user, remember=form.remember_me.data)

        # Handle redirect after login
        next_page = request.args.get('next')
        if next_page and _is_safe_url(next_page):
            return redirect(next_page)

        flash(f'Welcome back, {tenant_user.tenant.first_name}!', 'success')
        return redirect(url_for('tenant_portal.dashboard'))

    return render_template('tenant_portal/login.html', form=form)


@tenant_portal.route('/logout')
@tenant_required
def logout():
    """Log out tenant user and clear session."""
    tenant_name = current_user.tenant.first_name

    # Log logout event
    AuditLogger.log_event(
        event_type='tenant_logout',
        category=AuditLogger.CATEGORY_SECURITY,
        resource_type='tenant_user',
        resource_id=current_user.id,
        company_id=current_user.company_id
    )

    # Clear session
    session.pop('is_tenant_user', None)
    logout_user()
    SessionSecurity.invalidate_session()

    flash(f'Goodbye, {tenant_name}! You have been logged out.', 'info')
    return redirect(url_for('tenant_portal.login'))


@tenant_portal.route('/register/<token>', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def register(token):
    """
    Accept tenant portal invitation and set password.

    SECURITY:
    - Token validated with constant-time comparison
    - Token expires after 72 hours
    - Token can only be used once
    - Password policy enforced
    """
    # Find tenant user by invitation token
    tenant_user = TenantUser.query.filter_by(invitation_token=token).first()

    if not tenant_user:
        flash('Invalid or expired invitation link.', 'error')
        return redirect(url_for('tenant_portal.login'))

    # Verify token is valid and not expired
    if not tenant_user.verify_invitation_token(token):
        flash('This invitation link has expired. Please contact your property manager for a new invitation.', 'error')
        return redirect(url_for('tenant_portal.login'))

    # Check if already registered
    if tenant_user.invitation_accepted_at:
        flash('You have already registered. Please log in.', 'info')
        return redirect(url_for('tenant_portal.login'))

    form = TenantRegistrationForm()

    if form.validate_on_submit():
        # Accept invitation and set password
        success, errors = tenant_user.accept_invitation(form.password.data)

        if not success:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'tenant_portal/register.html',
                form=form,
                tenant_user=tenant_user
            )

        # Update tenant record
        tenant_user.tenant.has_portal_access = True
        tenant_user.tenant.portal_invitation_accepted = datetime.utcnow()
        db.session.commit()

        # Log registration
        AuditLogger.log_event(
            event_type='tenant_registration_completed',
            category=AuditLogger.CATEGORY_SECURITY,
            resource_type='tenant_user',
            resource_id=tenant_user.id,
            company_id=tenant_user.company_id
        )

        flash('Registration complete! You can now log in to the tenant portal.', 'success')
        return redirect(url_for('tenant_portal.login'))

    return render_template(
        'tenant_portal/register.html',
        form=form,
        tenant_user=tenant_user
    )


@tenant_portal.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def forgot_password():
    """
    Request password reset for tenant portal.

    SECURITY:
    - Always shows success message (prevents email enumeration)
    - Timing attack prevention with minimum response time
    - Rate limited to 3 per hour
    """
    if current_user.is_authenticated:
        return redirect(url_for('tenant_portal.dashboard'))

    form = TenantForgotPasswordForm()

    if form.validate_on_submit():
        import time
        import random
        start_time = time.time()

        email = form.email.data.lower().strip()
        tenant_user = TenantUser.query.filter_by(email=email).first()

        if tenant_user and tenant_user.is_active and tenant_user.email_verified:
            # Generate reset token
            token = tenant_user.generate_password_reset_token()

            # Log password reset request
            AuditLogger.log_event(
                event_type='tenant_password_reset_requested',
                category=AuditLogger.CATEGORY_SECURITY,
                resource_type='tenant_user',
                resource_id=tenant_user.id,
                company_id=tenant_user.company_id
            )

            # TODO: Send email with reset link
            # EmailService.send_tenant_password_reset(tenant_user, token)

            current_app.logger.info(f"Password reset requested for tenant: {email}")

        # SECURITY: Timing attack prevention
        elapsed = time.time() - start_time
        min_response_time = 2.0
        if elapsed < min_response_time:
            time.sleep(min_response_time - elapsed + random.uniform(0.1, 0.5))

        # Always show success message
        flash('If an account exists with that email, you will receive password reset instructions.', 'info')
        return redirect(url_for('tenant_portal.login'))

    return render_template('tenant_portal/forgot_password.html', form=form)


@tenant_portal.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def reset_password(token):
    """
    Reset tenant password using token.

    SECURITY:
    - Token validated with constant-time comparison
    - Token expires after 1 hour
    - Token can only be used once
    - Password policy enforced
    """
    if current_user.is_authenticated:
        return redirect(url_for('tenant_portal.dashboard'))

    # Find user by reset token
    tenant_user = TenantUser.query.filter_by(password_reset_token=token).first()

    if not tenant_user or not tenant_user.verify_password_reset_token(token):
        flash('Invalid or expired password reset link.', 'error')
        return redirect(url_for('tenant_portal.forgot_password'))

    form = TenantResetPasswordForm()

    if form.validate_on_submit():
        success, errors = tenant_user.set_password(form.password.data, validate_policy=True)

        if not success:
            for error in errors:
                flash(error, 'error')
            return render_template('tenant_portal/reset_password.html', form=form, token=token)

        # Clear reset token
        tenant_user.clear_password_reset_token()

        # Log password change
        AuditLogger.log_event(
            event_type='tenant_password_changed',
            category=AuditLogger.CATEGORY_SECURITY,
            resource_type='tenant_user',
            resource_id=tenant_user.id,
            details={'method': 'password_reset'},
            company_id=tenant_user.company_id
        )

        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('tenant_portal.login'))

    return render_template('tenant_portal/reset_password.html', form=form, token=token)


# =============================================================================
# DASHBOARD AND MAIN VIEWS
# =============================================================================

@tenant_portal.route('/')
@tenant_required
def dashboard():
    """Tenant portal main dashboard."""
    tenant = current_user.tenant
    today = datetime.now().date()

    # Get active lease
    active_lease = None
    for lease in tenant.leases:
        if lease.start.date() <= today <= lease.end.date():
            active_lease = lease
            break

    # Get payment history
    recent_payments = []
    if active_lease:
        recent_payments = Payment.query.filter_by(
            lease_id=active_lease.id,
            company_id=current_user.company_id
        ).order_by(Payment.payment_date.desc()).limit(5).all()

    # Get maintenance requests
    recent_requests = MaintenanceRequest.get_for_tenant(
        tenant_id=current_user.tenant_id,
        company_id=current_user.company_id
    )[:5]

    # Calculate outstanding balance
    outstanding_balance = 0
    if active_lease:
        outstanding_balance = active_lease.get_outstanding_balance()

    return render_template(
        'tenant_portal/dashboard.html',
        tenant=tenant,
        active_lease=active_lease,
        recent_payments=recent_payments,
        recent_requests=recent_requests,
        outstanding_balance=outstanding_balance
    )


@tenant_portal.route('/lease')
@tenant_required
def lease_details():
    """View current lease details."""
    tenant = current_user.tenant
    today = datetime.now().date()

    # Get active lease
    active_lease = None
    for lease in tenant.leases:
        if lease.start.date() <= today <= lease.end.date():
            active_lease = lease
            break

    if not active_lease:
        flash('No active lease found.', 'info')
        return redirect(url_for('tenant_portal.dashboard'))

    return render_template(
        'tenant_portal/lease_details.html',
        lease=active_lease,
        tenant=tenant
    )


@tenant_portal.route('/payments')
@tenant_required
def payment_history():
    """View payment history."""
    page = request.args.get('page', 1, type=int)

    # Get all payments for this tenant's leases
    payments = Payment.query.join(Lease).filter(
        Lease.tenant_id == current_user.tenant_id,
        Payment.company_id == current_user.company_id
    ).order_by(Payment.payment_date.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template(
        'tenant_portal/payment_history.html',
        payments=payments
    )


# =============================================================================
# MAINTENANCE REQUESTS
# =============================================================================

@tenant_portal.route('/maintenance')
@tenant_required
def maintenance_list():
    """View all maintenance requests."""
    status_filter = request.args.get('status', 'all')

    requests_query = MaintenanceRequest.query.filter_by(
        tenant_id=current_user.tenant_id,
        company_id=current_user.company_id
    )

    if status_filter != 'all':
        requests_query = requests_query.filter_by(status=status_filter)

    requests = requests_query.order_by(MaintenanceRequest.submitted_at.desc()).all()

    return render_template(
        'tenant_portal/maintenance_list.html',
        requests=requests,
        status_filter=status_filter
    )


@tenant_portal.route('/maintenance/new', methods=['GET', 'POST'])
@tenant_required
def maintenance_submit():
    """Submit a new maintenance request."""
    tenant = current_user.tenant

    # Get current lease and unit
    active_lease = tenant.get_current_lease()
    if not active_lease:
        flash('You must have an active lease to submit maintenance requests.', 'error')
        return redirect(url_for('tenant_portal.dashboard'))

    form = MaintenanceRequestForm()

    if form.validate_on_submit():
        maintenance_request = MaintenanceRequest(
            company_id=current_user.company_id,
            tenant_id=current_user.tenant_id,
            tenant_user_id=current_user.id,
            unit_id=active_lease.unit_id,
            property_id=active_lease.property_id,
            category=form.category.data,
            priority=form.priority.data,
            title=form.title.data,
            description=form.description.data
        )

        maintenance_request.permission_to_enter = form.permission_to_enter.data
        if form.preferred_entry_time.data:
            maintenance_request.preferred_entry_time = form.preferred_entry_time.data

        db.session.add(maintenance_request)
        db.session.commit()

        # Log event
        AuditLogger.log_event(
            event_type='maintenance_request_submitted',
            category=AuditLogger.CATEGORY_GENERAL,
            resource_type='maintenance_request',
            resource_id=maintenance_request.id,
            company_id=current_user.company_id
        )

        flash('Your maintenance request has been submitted. We will respond shortly.', 'success')
        return redirect(url_for('tenant_portal.maintenance_detail', uuid=maintenance_request.uuid))

    return render_template(
        'tenant_portal/maintenance_submit.html',
        form=form,
        lease=active_lease
    )


@tenant_portal.route('/maintenance/<uuid>')
@tenant_required
@owns_maintenance_request
def maintenance_detail(uuid, maintenance_request):
    """View maintenance request details."""
    return render_template(
        'tenant_portal/maintenance_detail.html',
        request=maintenance_request
    )


@tenant_portal.route('/maintenance/<uuid>/feedback', methods=['GET', 'POST'])
@tenant_required
@owns_maintenance_request
def maintenance_feedback(uuid, maintenance_request):
    """Submit feedback for completed maintenance request."""
    if maintenance_request.status not in ['completed', 'closed']:
        flash('You can only provide feedback for completed requests.', 'error')
        return redirect(url_for('tenant_portal.maintenance_detail', uuid=uuid))

    if maintenance_request.tenant_rating:
        flash('You have already submitted feedback for this request.', 'info')
        return redirect(url_for('tenant_portal.maintenance_detail', uuid=uuid))

    form = MaintenanceFeedbackForm()

    if form.validate_on_submit():
        maintenance_request.add_tenant_feedback(
            rating=form.rating.data,
            feedback=form.feedback.data if form.feedback.data else None
        )

        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('tenant_portal.maintenance_detail', uuid=uuid))

    return render_template(
        'tenant_portal/maintenance_feedback.html',
        form=form,
        request=maintenance_request
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _is_safe_url(target):
    """
    Validate redirect URL to prevent open redirect vulnerabilities.

    SECURITY: Only allows redirects to same host.
    """
    from urllib.parse import urlparse, urljoin
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
