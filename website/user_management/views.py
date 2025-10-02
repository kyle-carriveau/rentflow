from flask import render_template, Blueprint, request, redirect, url_for, flash, jsonify
from website.models import User, Company
from website import db 
from flask_login import login_required, current_user
from website.auth_utils import owner_required
from website.errors import page_not_found
import re

user_management = Blueprint('user_management', __name__, template_folder='templates')

@user_management.route('/', methods=['GET'])
@login_required
@owner_required
def users():
    """List all users in the current user's company."""
    company_id = current_user.get_company_id()
    company_users = User.query.filter_by(company_id=company_id).order_by(User.last_name.asc(), User.first_name.asc()).all()
    return render_template("users.html", user=current_user, users=company_users)

@user_management.route('/invite', methods=['GET', 'POST'])
@login_required
@owner_required
def invite_user():
    """Invite a new user to the company."""
    if request.method == "POST":
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        role = request.form.get('role', '').strip()
        password = request.form.get('password', '').strip()

        # Server-side validation
        if not first_name:
            flash('First name is required.', 'error')
            return render_template("invite_user.html", user=current_user, roles=User.ROLES)
            
        if not last_name:
            flash('Last name is required.', 'error')
            return render_template("invite_user.html", user=current_user, roles=User.ROLES)

        if not email:
            flash('Email is required.', 'error')
            return render_template("invite_user.html", user=current_user, roles=User.ROLES)

        # Email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Please enter a valid email address.', 'error')
            return render_template("invite_user.html", user=current_user, roles=User.ROLES)

        # Role validation
        if role not in User.ROLES:
            flash('Invalid role selected.', 'error')
            return render_template("invite_user.html", user=current_user, roles=User.ROLES)

        # Password validation
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template("invite_user.html", user=current_user, roles=User.ROLES)

        # Check if email is already in use
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already in use.', 'error')
            return render_template("invite_user.html", user=current_user, roles=User.ROLES)

        # Create new user in the same company
        company_id = current_user.get_company_id()
        new_user = User(
            first_name=first_name, 
            last_name=last_name, 
            email=email, 
            password=password,
            company_id=company_id, 
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'User "{first_name} {last_name}" invited successfully with role: {role.title()}!', 'success')
        return redirect(url_for('user_management.users'))

    return render_template("invite_user.html", user=current_user, roles=User.ROLES)

@user_management.route('/<uuid:user_uuid>/edit', methods=['GET', 'POST'])
@login_required
@owner_required
def edit_user(user_uuid):
    """Edit user role and information."""
    company_id = current_user.get_company_id()
    target_user = User.find_by_uuid(str(user_uuid), company_id)
    
    if not target_user:
        return page_not_found(404)
    
    # Prevent editing the current user's own role
    if target_user.id == current_user.id:
        flash('You cannot edit your own role.', 'error')
        return redirect(url_for('user_management.users'))
    
    if request.method == "POST":
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        role = request.form.get('role', '').strip()

        # Server-side validation
        if not first_name:
            flash('First name is required.', 'error')
            return render_template("edit_user.html", user=current_user, target_user=target_user, roles=User.ROLES)
            
        if not last_name:
            flash('Last name is required.', 'error')
            return render_template("edit_user.html", user=current_user, target_user=target_user, roles=User.ROLES)

        if not email:
            flash('Email is required.', 'error')
            return render_template("edit_user.html", user=current_user, target_user=target_user, roles=User.ROLES)

        # Email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Please enter a valid email address.', 'error')
            return render_template("edit_user.html", user=current_user, target_user=target_user, roles=User.ROLES)

        # Role validation
        if role not in User.ROLES:
            flash('Invalid role selected.', 'error')
            return render_template("edit_user.html", user=current_user, target_user=target_user, roles=User.ROLES)

        # Check if email is already in use (excluding current user)
        existing_user = User.query.filter_by(email=email).filter(User.id != target_user.id).first()
        if existing_user:
            flash('Email is already in use.', 'error')
            return render_template("edit_user.html", user=current_user, target_user=target_user, roles=User.ROLES)

        # Update user
        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.email = email
        target_user.role = role
        
        db.session.commit()
        flash(f'User "{first_name} {last_name}" updated successfully!', 'success')
        return redirect(url_for('user_management.users'))

    return render_template("edit_user.html", user=current_user, target_user=target_user, roles=User.ROLES)

@user_management.route('/<uuid:user_uuid>/delete', methods=['POST'])
@login_required
@owner_required
def delete_user(user_uuid):
    """Delete a user from the company."""
    company_id = current_user.get_company_id()
    target_user = User.find_by_uuid(str(user_uuid), company_id)
    
    if not target_user:
        return page_not_found(404)
    
    # Prevent deleting the current user
    if target_user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('user_management.users'))
    
    # Prevent deleting the last owner
    owners_count = User.query.filter_by(company_id=company_id, role=User.ROLE_OWNER).count()
    if target_user.role == User.ROLE_OWNER and owners_count <= 1:
        flash('Cannot delete the last company owner.', 'error')
        return redirect(url_for('user_management.users'))
    
    user_name = f"{target_user.first_name} {target_user.last_name}"
    
    try:
        db.session.delete(target_user)
        db.session.commit()
        flash(f'User "{user_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting user. They may have associated data.', 'error')
    
    return redirect(url_for('user_management.users'))

@user_management.route('/<uuid:user_uuid>/role', methods=['POST'])
@login_required
@owner_required
def update_user_role(user_uuid):
    """Ajax endpoint to quickly update user role."""
    company_id = current_user.get_company_id()
    target_user = User.find_by_uuid(str(user_uuid), company_id)
    
    if not target_user:
        return jsonify({'success': False, 'error': 'User not found'})
    
    # Prevent editing the current user's own role
    if target_user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot edit your own role'})
    
    new_role = request.json.get('role')
    if new_role not in User.ROLES:
        return jsonify({'success': False, 'error': 'Invalid role'})
    
    # Prevent removing the last owner
    if target_user.role == User.ROLE_OWNER and new_role != User.ROLE_OWNER:
        owners_count = User.query.filter_by(company_id=company_id, role=User.ROLE_OWNER).count()
        if owners_count <= 1:
            return jsonify({'success': False, 'error': 'Cannot remove the last company owner'})
    
    target_user.role = new_role
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Role updated to {new_role.title()}'})