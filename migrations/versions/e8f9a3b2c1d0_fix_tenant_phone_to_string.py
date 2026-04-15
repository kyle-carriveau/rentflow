"""Fix Tenant phone field: change from Integer to String(20)

Revision ID: e8f9a3b2c1d0
Revises: d6b2d5aa460c
Create Date: 2025-01-29 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8f9a3b2c1d0'
down_revision = 'd6b2d5aa460c'
branch_labels = None
depends_on = None


def upgrade():
    """Change tenant.phone from INTEGER to VARCHAR(20)

    Uses batch operations for SQLite compatibility.
    PostgreSQL would use: ALTER COLUMN phone TYPE VARCHAR(20) USING phone::VARCHAR(20)
    """
    # Get the database dialect
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'sqlite':
        # SQLite requires batch operations for column type changes
        with op.batch_alter_table('tenant', schema=None) as batch_op:
            batch_op.alter_column('phone',
                                  existing_type=sa.Integer(),
                                  type_=sa.String(length=20),
                                  existing_nullable=False)
    else:
        # PostgreSQL syntax
        op.execute("""
            ALTER TABLE tenant
            ALTER COLUMN phone TYPE VARCHAR(20)
            USING phone::VARCHAR(20)
        """)


def downgrade():
    """Revert tenant.phone from VARCHAR(20) back to INTEGER

    WARNING: This will fail if any phone numbers contain non-numeric
    characters (e.g., dashes, spaces, parentheses). Only use if you're
    certain all phone data is numeric-only.
    """
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'sqlite':
        # SQLite requires batch operations
        with op.batch_alter_table('tenant', schema=None) as batch_op:
            batch_op.alter_column('phone',
                                  existing_type=sa.String(length=20),
                                  type_=sa.Integer(),
                                  existing_nullable=False)
    else:
        # PostgreSQL syntax
        op.execute("""
            ALTER TABLE tenant
            ALTER COLUMN phone TYPE INTEGER
            USING NULLIF(phone, '')::INTEGER
        """)
