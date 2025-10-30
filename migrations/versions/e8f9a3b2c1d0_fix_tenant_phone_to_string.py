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

    Uses PostgreSQL's USING clause to safely convert existing integer
    phone numbers to strings. Existing data is preserved.
    """
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
    op.execute("""
        ALTER TABLE tenant
        ALTER COLUMN phone TYPE INTEGER
        USING NULLIF(phone, '')::INTEGER
    """)
