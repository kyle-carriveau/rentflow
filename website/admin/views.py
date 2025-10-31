"""
Super Admin Views - Authentication and Dashboard

Provides authentication and dashboard views for super administrators.
All routes are protected by @super_admin_required decorator except login/logout.
"""

from flask import render_template, request, redirect, url_for, flash, session
from website.admin import admin
from website.admin.forms import AdminLoginForm
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
