"""
Super Admin Views - Authentication and Dashboard

Provides authentication and dashboard views for super administrators.
All routes are protected by @super_admin_required decorator except login/logout.
"""

from flask import render_template, request, redirect, url_for, flash, session
from website.admin import admin
from website.admin.forms import AdminLoginForm, AdminPasswordChangeForm, AdminUserCreateForm
from website.models import SuperAdmin, SuperAdminAuditLog, Company, User, Property, Unit, Tenant, Lease
from website.auth_utils import super_admin_required, log_admin_action
from website import db
from sqlalchemy import func
from datetime import datetime, timedelta


@admin.route('/login', methods=['GET', 'POST'])
def login():
    """
    Super admin login page.

    Completely separate from regular user login (/auth/login).
    Creates admin session that doesn't interfere with regular user sessions.
    """
    # If already logged in as admin, redirect to dashboard
    if session.get('admin_id'):
        return redirect(url_for('admin.dashboard'))

    form = AdminLoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Find admin by username
        admin_user = SuperAdmin.query.filter_by(username=username).first()

        if admin_user and admin_user.check_password(password):
            if not admin_user.is_active:
                flash('This admin account has been deactivated', 'error')
                return render_template('admin_login.html', form=form)

            # Create admin session (separate from regular user session)
            session['admin_id'] = admin_user.id
            session['admin_username'] = admin_user.username

            # Update last login
            admin_user.update_last_login()

            # Log the login
            log_admin_action(
                admin_id=admin_user.id,
                action='admin_login',
                path='/admin/login'
            )

            # Check if admin must change password
            if admin_user.must_change_password:
                flash('You must change your password before continuing', 'warning')
                return redirect(url_for('admin.change_password'))

            flash(f'Welcome, {admin_user.first_name or admin_user.username}!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('admin_login.html', form=form)


@admin.route('/logout')
def logout():
    """
    Super admin logout.

    Clears admin session without touching regular user session.
    """
    admin_id = session.get('admin_id')
    if admin_id:
        # Log the logout
        log_admin_action(
            admin_id=admin_id,
            action='admin_logout',
            path='/admin/logout'
        )

    # Clear admin session
    session.pop('admin_id', None)
    session.pop('admin_username', None)

    flash('Logged out successfully', 'info')
    return redirect(url_for('admin.login'))


@admin.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """
    Forced password change for super admins.

    This route is accessible without @super_admin_required because admins
    who must change their password need to access it before they can use
    any other admin features.

    Security:
    - Still requires admin_id in session (must be logged in)
    - Validates current password before allowing change
    - Enforces strong password policy
    - Logs password change action
    - Clears must_change_password flag
    """
    # Require admin to be logged in (but not necessarily past password change)
    admin_id = session.get('admin_id')
    if not admin_id:
        flash('Please log in first', 'warning')
        return redirect(url_for('admin.login'))

    # Get current admin
    admin = SuperAdmin.query.get(admin_id)
    if not admin or not admin.is_active:
        session.clear()
        flash('Admin account not found or inactive', 'error')
        return redirect(url_for('admin.login'))

    form = AdminPasswordChangeForm()

    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data

        # Verify current password
        if not admin.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return render_template('admin_change_password.html', form=form, admin=admin)

        # Check if new password is same as current
        if admin.check_password(new_password):
            flash('New password must be different from current password', 'error')
            return render_template('admin_change_password.html', form=form, admin=admin)

        # Set new password (handles hashing and password_changed_at)
        admin.set_password(new_password)

        # Clear the must_change_password flag
        admin.must_change_password = False

        # Commit changes
        db.session.commit()

        # Log the password change
        log_admin_action(
            admin_id=admin.id,
            action='admin_password_changed',
            path='/admin/change-password',
            details='{"forced": true}'
        )

        flash('Password changed successfully! You can now access the admin dashboard.', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin_change_password.html', form=form, admin=admin)


@admin.route('/dashboard')
@super_admin_required
def dashboard():
    """
    Main Super Admin Dashboard - God View.

    Shows aggregate metrics across all companies:
    - Company overview (total, new, active, inactive)
    - User metrics (total users, by role, by company)
    - Property/asset metrics (properties, units, tenants, occupancy)
    """
    # Get current admin info
    admin_id = session.get('admin_id')
    admin = SuperAdmin.query.get(admin_id)

    # Force password change if required (in case user tries to access dashboard directly)
    if admin.must_change_password:
        flash('You must change your password before accessing the dashboard', 'warning')
        return redirect(url_for('admin.change_password'))

    # Calculate date ranges
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)
    ninety_days_ago = now - timedelta(days=90)

    # ==========================================
    # SECTION 1: COMPANY OVERVIEW
    # ==========================================

    # Total companies
    total_companies = Company.query.count()

    # New companies this month
    new_companies_this_month = Company.query.filter(
        Company.created_at >= start_of_month
    ).count()

    # Active companies (had users login in last 30 days)
    # Subquery to find companies with recent user activity
    active_companies_subquery = db.session.query(User.company_id).join(
        SuperAdminAuditLog, SuperAdminAuditLog.admin_id == admin_id
    ).filter(
        User.date_joined >= thirty_days_ago  # Using date_joined as proxy for activity
    ).distinct().subquery()

    active_companies_count = db.session.query(func.count(Company.id)).filter(
        Company.id.in_(active_companies_subquery)
    ).scalar() or 0

    # Inactive companies (no activity in 90+ days)
    # For simplicity, we'll calculate this as total - active
    # In production, you'd want to track last_activity_at on Company model
    inactive_companies_count = max(0, total_companies - active_companies_count)

    # ==========================================
    # SECTION 2: USER METRICS
    # ==========================================

    # Total users across all companies
    total_users = User.query.count()

    # Users by role
    users_by_role = db.session.query(
        User.role,
        func.count(User.id).label('count')
    ).group_by(User.role).all()

    role_counts = {role: count for role, count in users_by_role}

    # Recent signups (last 30 days)
    recent_signups = User.query.filter(
        User.date_joined >= thirty_days_ago
    ).count()

    # Top companies by user count
    top_companies_by_users = db.session.query(
        Company.name,
        Company.id,
        func.count(User.id).label('user_count')
    ).join(User, User.company_id == Company.id).group_by(
        Company.id, Company.name
    ).order_by(func.count(User.id).desc()).limit(10).all()

    # ==========================================
    # SECTION 3: PROPERTY/ASSET METRICS
    # ==========================================

    # Total properties
    total_properties = Property.query.count()

    # Total units
    total_units = Unit.query.count()

    # Total tenants
    total_tenants = Tenant.query.count()

    # Occupancy calculation
    if total_units > 0:
        occupied_units = Unit.query.filter(
            Unit.occupancy_status == 'Occupied'
        ).count()
        occupancy_rate = (occupied_units / total_units) * 100
    else:
        occupied_units = 0
        occupancy_rate = 0

    # Units by status
    units_by_status = db.session.query(
        Unit.occupancy_status,
        func.count(Unit.id).label('count')
    ).group_by(Unit.occupancy_status).all()

    unit_status_counts = {status: count for status, count in units_by_status}

    # Top companies by property count
    top_companies_by_properties = db.session.query(
        Company.name,
        Company.id,
        func.count(Property.id).label('property_count')
    ).join(Property, Property.company_id == Company.id).group_by(
        Company.id, Company.name
    ).order_by(func.count(Property.id).desc()).limit(10).all()

    # ==========================================
    # SECTION 4: RECENT ACTIVITY
    # ==========================================

    # Recent companies (last 10 signups)
    recent_companies = Company.query.order_by(
        Company.created_at.desc()
    ).limit(10).all()

    # All companies for drill-down list (paginated in template)
    all_companies = Company.query.order_by(Company.name).all()

    # ==========================================
    # RENDER DASHBOARD
    # ==========================================

    return render_template(
        'admin_dashboard.html',
        admin=admin,
        # Company metrics
        total_companies=total_companies,
        new_companies_this_month=new_companies_this_month,
        active_companies_count=active_companies_count,
        inactive_companies_count=inactive_companies_count,
        # User metrics
        total_users=total_users,
        role_counts=role_counts,
        recent_signups=recent_signups,
        top_companies_by_users=top_companies_by_users,
        # Property metrics
        total_properties=total_properties,
        total_units=total_units,
        total_tenants=total_tenants,
        occupied_units=occupied_units,
        occupancy_rate=occupancy_rate,
        unit_status_counts=unit_status_counts,
        top_companies_by_properties=top_companies_by_properties,
        # Lists
        recent_companies=recent_companies,
        all_companies=all_companies
    )


@admin.route('/users')
@super_admin_required
def admin_users_list():
    """
    List all super admin accounts.

    Shows a table of all admin users with:
    - Username, name, email
    - Active status
    - Created date and creator
    - Last login
    - Actions (view, edit, deactivate)
    """
    # Force password change if required
    admin_id = session.get('admin_id')
    current_admin = SuperAdmin.query.get(admin_id)
    if current_admin.must_change_password:
        flash('You must change your password before accessing admin management', 'warning')
        return redirect(url_for('admin.change_password'))

    # Get all admins with their creator information
    admins = SuperAdmin.query.order_by(SuperAdmin.created_at.desc()).all()

    # Build list with creator names
    admin_list = []
    for admin in admins:
        creator_name = None
        if admin.created_by_admin_id:
            creator = SuperAdmin.query.get(admin.created_by_admin_id)
            if creator:
                creator_name = creator.username

        admin_list.append({
            'admin': admin,
            'creator_name': creator_name
        })

    return render_template('admin_users_list.html', admin_list=admin_list, current_admin=current_admin)


@admin.route('/users/create', methods=['GET', 'POST'])
@super_admin_required
def admin_user_create():
    """
    Create a new super administrator account.

    Security:
    - Requires existing admin to be logged in
    - Enforces strong password policy
    - Tracks creator via created_by_admin_id
    - Forces new admin to change password on first login
    - Logs admin creation action
    """
    # Force password change if required
    admin_id = session.get('admin_id')
    current_admin = SuperAdmin.query.get(admin_id)
    if current_admin.must_change_password:
        flash('You must change your password before creating admin accounts', 'warning')
        return redirect(url_for('admin.change_password'))

    form = AdminUserCreateForm()

    if form.validate_on_submit():
        username = form.username.data
        first_name = form.first_name.data or None
        last_name = form.last_name.data or None
        email = form.email.data or None
        password = form.password.data
        notes = form.notes.data or None

        # Check if username already exists
        existing_admin = SuperAdmin.query.filter_by(username=username).first()
        if existing_admin:
            flash(f'Username "{username}" is already taken. Please choose a different username.', 'error')
            return render_template('admin_user_create.html', form=form, current_admin=current_admin)

        try:
            # Create new admin account
            new_admin = SuperAdmin(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_active=True,
                must_change_password=True,  # Force password change on first login
                created_by_admin_id=current_admin.id,  # Track who created this admin
                notes=notes
            )

            # Set password (handles hashing and password_changed_at)
            new_admin.set_password(password)

            # Save to database
            db.session.add(new_admin)
            db.session.commit()

            # Log the admin creation
            log_admin_action(
                admin_id=current_admin.id,
                action='admin_user_created',
                path='/admin/users/create',
                details=f'{{"new_admin_id": {new_admin.id}, "new_admin_username": "{username}"}}'
            )

            flash(f'Admin account "{username}" created successfully! They must change their password on first login.', 'success')
            return redirect(url_for('admin.admin_users_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating admin account: {str(e)}', 'error')
            return render_template('admin_user_create.html', form=form, current_admin=current_admin)

    return render_template('admin_user_create.html', form=form, current_admin=current_admin)


@admin.route('/company/<int:company_id>')
@super_admin_required
def company_detail(company_id):
    """
    Detailed view of a specific company.

    Shows all data for one company:
    - Company information
    - Users in this company
    - Properties, units, tenants
    - Activity metrics
    """
    # Force password change if required
    admin_id = session.get('admin_id')
    admin = SuperAdmin.query.get(admin_id)
    if admin.must_change_password:
        flash('You must change your password before accessing company details', 'warning')
        return redirect(url_for('admin.change_password'))

    company = Company.query.get_or_404(company_id)

    # Get company users
    users = User.query.filter_by(company_id=company_id).all()

    # Get company properties
    properties = Property.query.filter_by(company_id=company_id).all()

    # Get company units
    units = Unit.query.filter_by(company_id=company_id).all()

    # Get company tenants
    tenants = Tenant.query.filter_by(company_id=company_id).all()

    # Get company leases
    leases = Lease.query.filter_by(company_id=company_id).all()

    # Calculate metrics
    total_users = len(users)
    total_properties = len(properties)
    total_units = len(units)
    total_tenants = len(tenants)
    total_leases = len(leases)

    # Occupancy rate
    if total_units > 0:
        occupied_units = sum(1 for unit in units if unit.occupancy_status == 'Occupied')
        occupancy_rate = (occupied_units / total_units) * 100
    else:
        occupied_units = 0
        occupancy_rate = 0

    # Users by role
    users_by_role = {}
    for user in users:
        role = user.role
        users_by_role[role] = users_by_role.get(role, 0) + 1

    return render_template(
        'admin_company_detail.html',
        company=company,
        users=users,
        properties=properties,
        units=units,
        tenants=tenants,
        leases=leases,
        total_users=total_users,
        total_properties=total_properties,
        total_units=total_units,
        total_tenants=total_tenants,
        total_leases=total_leases,
        occupied_units=occupied_units,
        occupancy_rate=occupancy_rate,
        users_by_role=users_by_role
    )
