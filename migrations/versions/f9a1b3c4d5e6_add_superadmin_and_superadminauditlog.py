"""Add SuperAdmin and SuperAdminAuditLog tables for God View Dashboard

Revision ID: f9a1b3c4d5e6
Revises: e8f9a3b2c1d0
Create Date: 2025-01-29 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9a1b3c4d5e6'
down_revision = 'e8f9a3b2c1d0'
branch_labels = None
depends_on = None


def upgrade():
    """Create SuperAdmin and SuperAdminAuditLog tables

    SuperAdmin table stores super administrator accounts that exist outside
    the multi-tenant system and have read-only access to all company data.

    SuperAdminAuditLog table tracks all actions taken by super admins for
    security and compliance purposes.
    """
    # Create super_admin table
    op.create_table('super_admin',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=1500), nullable=False),
        sa.Column('first_name', sa.String(length=150), nullable=True),
        sa.Column('last_name', sa.String(length=150), nullable=True),
        sa.Column('email', sa.String(length=150), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_super_admin_username'), 'super_admin', ['username'], unique=True)

    # Create super_admin_audit_log table
    op.create_table('super_admin_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_company_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['super_admin.id'], ),
        sa.ForeignKeyConstraint(['target_company_id'], ['company.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_super_admin_audit_log_timestamp'), 'super_admin_audit_log', ['timestamp'], unique=False)


def downgrade():
    """Drop SuperAdmin and SuperAdminAuditLog tables

    WARNING: This will permanently delete all super admin accounts and
    their audit logs. Only use this in development or if you're certain
    you want to remove the admin system.
    """
    op.drop_index(op.f('ix_super_admin_audit_log_timestamp'), table_name='super_admin_audit_log')
    op.drop_table('super_admin_audit_log')
    op.drop_index(op.f('ix_super_admin_username'), table_name='super_admin')
    op.drop_table('super_admin')
