"""Add security fields to SuperAdmin for enhanced admin management

Revision ID: a1b2c3d4e5f6
Revises: f9a1b3c4d5e6
Create Date: 2025-01-29 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f9a1b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    """Add security and audit fields to SuperAdmin table

    New fields enable:
    - Forced password changes (must_change_password)
    - Admin creation tracking (created_by_admin_id)
    - Password change auditing (password_changed_at)
    """
    # Add must_change_password field (default False for existing admins)
    op.add_column('super_admin',
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add created_by_admin_id field (nullable - bootstrap admins have NULL)
    op.add_column('super_admin',
        sa.Column('created_by_admin_id', sa.Integer(), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_super_admin_created_by',
        'super_admin', 'super_admin',
        ['created_by_admin_id'], ['id']
    )

    # Add password_changed_at field (NULL = never changed)
    op.add_column('super_admin',
        sa.Column('password_changed_at', sa.DateTime(), nullable=True)
    )


def downgrade():
    """Remove security fields from SuperAdmin table

    WARNING: This will lose password change tracking and admin creation history.
    Only use in development.
    """
    # Drop columns in reverse order
    op.drop_column('super_admin', 'password_changed_at')

    # Drop foreign key first, then column
    op.drop_constraint('fk_super_admin_created_by', 'super_admin', type_='foreignkey')
    op.drop_column('super_admin', 'created_by_admin_id')

    op.drop_column('super_admin', 'must_change_password')
