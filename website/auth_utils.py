from functools import wraps
from flask import abort, flash, redirect, url_for, session, request
from flask_login import current_user

def role_required(required_role):
    """Decorator to require a specific role or higher."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth.login'))
            
            # Define role hierarchy (higher index = higher privilege)
            role_hierarchy = ['viewer', 'staff', 'manager', 'owner']
            
            try:
                current_role_level = role_hierarchy.index(current_user.role)
                required_role_level = role_hierarchy.index(required_role)
                
                if current_role_level >= required_role_level:
                    return f(*args, **kwargs)
                else:
                    flash('You do not have permission to access this page.', 'error')
                    abort(403)
            except ValueError:
                # Invalid role
                flash('Invalid user role. Please contact administrator.', 'error')
                abort(403)
                
        return decorated_function
    return decorator

def can_create_required(f):
    """Decorator to require create permissions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.can_create():
            flash('You do not have permission to create new records.', 'error')
            abort(403)
            
        return f(*args, **kwargs)
    return decorated_function

def can_edit_required(f):
    """Decorator to require edit permissions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.can_edit():
            flash('You do not have permission to edit records.', 'error')
            abort(403)
            
        return f(*args, **kwargs)
    return decorated_function

def can_delete_required(f):
    """Decorator to require delete permissions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.can_delete():
            flash('You do not have permission to delete records.', 'error')
            abort(403)
            
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    """Decorator to require manager role or higher."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))

        if not (current_user.is_manager() or current_user.is_owner()):
            flash('Manager permissions or higher required to access this page.', 'error')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function

def owner_required(f):
    """Decorator to require owner role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))

        if not current_user.is_owner():
            flash('Only company owners can access this page.', 'error')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def super_admin_required(f):
    """
    Decorator to require super admin authentication.

    Checks admin session (completely separate from regular user session).
    Verifies admin exists and is active.
    Logs all admin actions for security and compliance.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check admin session
        admin_id = session.get('admin_id')
        if not admin_id:
            flash('Admin authentication required', 'error')
            return redirect(url_for('admin.login'))

        # Verify admin exists and is active
        from website.models import SuperAdmin
        admin = SuperAdmin.query.get(admin_id)
        if not admin or not admin.is_active:
            session.pop('admin_id', None)
            session.pop('admin_username', None)
            flash('Invalid or inactive admin account', 'error')
            return redirect(url_for('admin.login'))

        # Log the action for audit trail
        log_admin_action(
            admin_id=admin_id,
            action=f.__name__,
            path=request.path,
            company_id=kwargs.get('company_id', None)
        )

        return f(*args, **kwargs)
    return decorated_function


def log_admin_action(admin_id, action, path, company_id=None):
    """
    Log super admin actions for audit trail and compliance.

    Args:
        admin_id: SuperAdmin ID performing the action
        action: Function name or action description
        path: Request path
        company_id: Company ID if viewing specific company (optional)
    """
    from website.models import SuperAdminAuditLog
    from website import db
    import json

    log_entry = SuperAdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_company_id=company_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        details=json.dumps({
            'path': path,
            'method': request.method,
            'endpoint': request.endpoint
        })
    )
    db.session.add(log_entry)
    db.session.commit()