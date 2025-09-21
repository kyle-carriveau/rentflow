from functools import wraps
from flask import abort, flash, redirect, url_for
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