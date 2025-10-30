"""
Flask CLI commands for Super Admin management.

Provides command-line tools for creating and managing super administrator accounts.
"""

import click
from flask import Blueprint
from website import db
from website.models import SuperAdmin


admin_cli = Blueprint('admin_cli', __name__)


@admin_cli.cli.command('create-admin')
@click.option('--username', prompt=True, help='Admin username (3-50 characters)')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
@click.option('--first-name', prompt='First name (optional)', default='', help='Admin first name')
@click.option('--last-name', prompt='Last name (optional)', default='', help='Admin last name')
@click.option('--email', prompt='Email (optional)', default='', help='Admin email for notifications')
def create_admin(username, password, first_name, last_name, email):
    """
    Create a new super administrator account.

    This command creates a new super admin with full read-only access to all
    companies and system data. Super admins exist outside the multi-tenant
    system and can view all data but cannot modify anything.

    Usage:
        flask admin-cli create-admin

    The command will prompt for all required information interactively.
    """
    # Validate username length
    if len(username) < 3 or len(username) > 50:
        click.echo(click.style('Error: Username must be between 3 and 50 characters', fg='red'))
        return

    # Check if username already exists
    existing_admin = SuperAdmin.query.filter_by(username=username).first()
    if existing_admin:
        click.echo(click.style(f'Error: Admin with username "{username}" already exists', fg='red'))
        return

    # Validate password length
    if len(password) < 8:
        click.echo(click.style('Error: Password must be at least 8 characters long', fg='red'))
        return

    try:
        # Create new super admin
        admin = SuperAdmin(
            username=username,
            first_name=first_name if first_name else None,
            last_name=last_name if last_name else None,
            email=email if email else None,
            is_active=True
        )
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        click.echo(click.style('\n✓ Super Admin created successfully!', fg='green', bold=True))
        click.echo(f'  Username: {username}')
        if first_name or last_name:
            click.echo(f'  Name: {first_name} {last_name}')
        if email:
            click.echo(f'  Email: {email}')
        click.echo(f'  Status: Active')
        click.echo(f'\nYou can now log in at /admin/login')

    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f'Error creating admin: {str(e)}', fg='red'))


@admin_cli.cli.command('list-admins')
def list_admins():
    """
    List all super administrator accounts.

    Shows all super admin accounts with their status and last login time.

    Usage:
        flask admin-cli list-admins
    """
    admins = SuperAdmin.query.order_by(SuperAdmin.created_at.desc()).all()

    if not admins:
        click.echo(click.style('No super admins found.', fg='yellow'))
        click.echo('\nCreate one with: flask admin-cli create-admin')
        return

    click.echo(click.style(f'\nSuper Administrators ({len(admins)} total):', fg='cyan', bold=True))
    click.echo('─' * 80)

    for admin in admins:
        status_color = 'green' if admin.is_active else 'red'
        status_text = 'Active' if admin.is_active else 'Inactive'

        click.echo(f'\n  ID: {admin.id}')
        click.echo(f'  Username: {admin.username}')
        if admin.first_name or admin.last_name:
            click.echo(f'  Name: {admin.first_name or ""} {admin.last_name or ""}')
        if admin.email:
            click.echo(f'  Email: {admin.email}')
        click.echo(f'  Status: {click.style(status_text, fg=status_color)}')
        click.echo(f'  Created: {admin.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
        if admin.last_login:
            click.echo(f'  Last Login: {admin.last_login.strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            click.echo(f'  Last Login: Never')

    click.echo('\n' + '─' * 80)


@admin_cli.cli.command('deactivate-admin')
@click.argument('username')
def deactivate_admin(username):
    """
    Deactivate a super administrator account.

    Deactivated admins cannot log in but their account and audit logs are preserved.

    Usage:
        flask admin-cli deactivate-admin USERNAME
    """
    admin = SuperAdmin.query.filter_by(username=username).first()

    if not admin:
        click.echo(click.style(f'Error: Admin "{username}" not found', fg='red'))
        return

    if not admin.is_active:
        click.echo(click.style(f'Admin "{username}" is already inactive', fg='yellow'))
        return

    try:
        admin.is_active = False
        db.session.commit()
        click.echo(click.style(f'✓ Admin "{username}" has been deactivated', fg='green'))
    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f'Error deactivating admin: {str(e)}', fg='red'))


@admin_cli.cli.command('activate-admin')
@click.argument('username')
def activate_admin(username):
    """
    Reactivate a super administrator account.

    Reactivates a previously deactivated admin, allowing them to log in again.

    Usage:
        flask admin-cli activate-admin USERNAME
    """
    admin = SuperAdmin.query.filter_by(username=username).first()

    if not admin:
        click.echo(click.style(f'Error: Admin "{username}" not found', fg='red'))
        return

    if admin.is_active:
        click.echo(click.style(f'Admin "{username}" is already active', fg='yellow'))
        return

    try:
        admin.is_active = True
        db.session.commit()
        click.echo(click.style(f'✓ Admin "{username}" has been activated', fg='green'))
    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f'Error activating admin: {str(e)}', fg='red'))


@admin_cli.cli.command('reset-password')
@click.argument('username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='New password')
def reset_password(username, password):
    """
    Reset a super administrator's password.

    Usage:
        flask admin-cli reset-password USERNAME
    """
    admin = SuperAdmin.query.filter_by(username=username).first()

    if not admin:
        click.echo(click.style(f'Error: Admin "{username}" not found', fg='red'))
        return

    if len(password) < 8:
        click.echo(click.style('Error: Password must be at least 8 characters long', fg='red'))
        return

    try:
        admin.set_password(password)
        db.session.commit()
        click.echo(click.style(f'✓ Password reset successfully for "{username}"', fg='green'))
    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f'Error resetting password: {str(e)}', fg='red'))
