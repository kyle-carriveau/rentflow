"""Add multi-tenant performance indexes

Revision ID: c1d2e3f4g5h6
Revises: a1b2c3d4e5f6
Create Date: 2025-12-09 14:30:00.000000

Critical database indexes for multi-tenant query performance.
All indexes are designed to optimize company_id scoped queries.

IDEMPOTENT: This migration is safe to run multiple times. It checks for
existing indexes before creating them, making it compatible with databases
that may have had indexes created manually.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4g5h6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def _get_existing_indexes(conn, table_name):
    """
    Get list of existing index names for a table.

    Args:
        conn: SQLAlchemy connection
        table_name: Name of the table to inspect

    Returns:
        Set of index names that exist on the table
    """
    inspector = inspect(conn)
    try:
        indexes = inspector.get_indexes(table_name)
        return {idx['name'] for idx in indexes}
    except Exception:
        # Table might not exist or other inspection error
        return set()


def _create_index_if_not_exists(index_name, table_name, columns, unique=False):
    """
    Create an index only if it doesn't already exist.

    Args:
        index_name: Name of the index to create
        table_name: Name of the table
        columns: List of column names for the index
        unique: Whether the index should be unique
    """
    conn = op.get_bind()
    existing_indexes = _get_existing_indexes(conn, table_name)

    if index_name not in existing_indexes:
        op.create_index(
            index_name,
            table_name,
            columns,
            unique=unique
        )
        print(f"Created index: {index_name} on {table_name}")
    else:
        print(f"Skipped existing index: {index_name} on {table_name}")


def _drop_index_if_exists(index_name, table_name):
    """
    Drop an index only if it exists.

    Args:
        index_name: Name of the index to drop
        table_name: Name of the table
    """
    conn = op.get_bind()
    existing_indexes = _get_existing_indexes(conn, table_name)

    if index_name in existing_indexes:
        op.drop_index(index_name, table_name=table_name)
        print(f"Dropped index: {index_name} from {table_name}")
    else:
        print(f"Skipped non-existent index: {index_name} from {table_name}")


def upgrade():
    """
    Add critical multi-tenant performance indexes.

    These indexes optimize the following query patterns:
    - Company-scoped queries (all tables)
    - Status-based filtering (properties, units, leases)
    - Property-based lookups (units, tenants, leases)
    - Date-based filtering (leases, payments, expenses)
    - Portfolio organization
    """

    # =============================================================================
    # PROPERTY INDEXES
    # =============================================================================

    # Primary company filter + status
    _create_index_if_not_exists(
        'idx_property_company_id',
        'property',
        ['company_id']
    )

    # Company + occupancy status queries (property listings)
    _create_index_if_not_exists(
        'idx_property_company_occupancy',
        'property',
        ['company_id', 'occupancy_status']
    )

    # Company + portfolio queries (portfolio views)
    _create_index_if_not_exists(
        'idx_property_company_portfolio',
        'property',
        ['company_id', 'portfolio_id']
    )

    # Company + type queries (filter by property type)
    _create_index_if_not_exists(
        'idx_property_company_type',
        'property',
        ['company_id', 'type']
    )

    # Company + location queries (search by city/state)
    _create_index_if_not_exists(
        'idx_property_company_location',
        'property',
        ['company_id', 'state', 'city']
    )

    # =============================================================================
    # UNIT INDEXES
    # =============================================================================

    # Primary company filter
    _create_index_if_not_exists(
        'idx_unit_company_id',
        'unit',
        ['company_id']
    )

    # Company + property queries (most common - unit listings by property)
    _create_index_if_not_exists(
        'idx_unit_company_property',
        'unit',
        ['company_id', 'property_id']
    )

    # Company + occupancy status queries (available unit searches)
    _create_index_if_not_exists(
        'idx_unit_company_occupancy',
        'unit',
        ['company_id', 'occupancy_status']
    )

    # Company + property + occupancy (filtered property views)
    _create_index_if_not_exists(
        'idx_unit_company_property_occupancy',
        'unit',
        ['company_id', 'property_id', 'occupancy_status']
    )

    # Rent range queries (unit search by price)
    _create_index_if_not_exists(
        'idx_unit_company_rent',
        'unit',
        ['company_id', 'rent']
    )

    # =============================================================================
    # TENANT INDEXES
    # =============================================================================

    # Primary company filter
    _create_index_if_not_exists(
        'idx_tenant_company_id',
        'tenant',
        ['company_id']
    )

    # Company + email (unique tenant lookup)
    _create_index_if_not_exists(
        'idx_tenant_company_email',
        'tenant',
        ['company_id', 'email']
    )

    # Company + property (tenants by property)
    _create_index_if_not_exists(
        'idx_tenant_company_property',
        'tenant',
        ['company_id', 'property_id']
    )

    # Name-based searches (tenant directory)
    _create_index_if_not_exists(
        'idx_tenant_company_name',
        'tenant',
        ['company_id', 'last_name', 'first_name']
    )

    # =============================================================================
    # LEASE INDEXES
    # =============================================================================

    # Primary company filter
    _create_index_if_not_exists(
        'idx_lease_company_id',
        'lease',
        ['company_id']
    )

    # Company + status queries (active/expiring lease lists)
    _create_index_if_not_exists(
        'idx_lease_company_status',
        'lease',
        ['company_id', 'lease_status']
    )

    # Company + property queries (leases by property)
    _create_index_if_not_exists(
        'idx_lease_company_property',
        'lease',
        ['company_id', 'property_id']
    )

    # Company + tenant queries (tenant lease history)
    _create_index_if_not_exists(
        'idx_lease_company_tenant',
        'lease',
        ['company_id', 'tenant_id']
    )

    # Company + unit queries (unit lease history)
    _create_index_if_not_exists(
        'idx_lease_company_unit',
        'lease',
        ['company_id', 'unit_id']
    )

    # Date-based queries (expiring leases, lease status automation)
    _create_index_if_not_exists(
        'idx_lease_company_dates',
        'lease',
        ['company_id', 'end', 'start']
    )

    # Lease status + end date (expiring lease notifications)
    _create_index_if_not_exists(
        'idx_lease_company_status_end',
        'lease',
        ['company_id', 'lease_status', 'end']
    )

    # =============================================================================
    # PAYMENT INDEXES
    # =============================================================================

    # Primary company filter
    _create_index_if_not_exists(
        'idx_payment_company_id',
        'payment',
        ['company_id']
    )

    # Company + status queries (completed/pending payments)
    _create_index_if_not_exists(
        'idx_payment_company_status',
        'payment',
        ['company_id', 'status']
    )

    # Company + lease queries (payment history by lease)
    _create_index_if_not_exists(
        'idx_payment_company_lease',
        'payment',
        ['company_id', 'lease_id']
    )

    # Company + property queries (property financial reports)
    _create_index_if_not_exists(
        'idx_payment_company_property',
        'payment',
        ['company_id', 'property_id']
    )

    # Date-based queries (monthly income reports)
    _create_index_if_not_exists(
        'idx_payment_company_date',
        'payment',
        ['company_id', 'payment_date']
    )

    # Company + status + date (completed payments in date range)
    _create_index_if_not_exists(
        'idx_payment_company_status_date',
        'payment',
        ['company_id', 'status', 'payment_date']
    )

    # =============================================================================
    # EXPENSE INDEXES
    # =============================================================================

    # Primary company filter
    _create_index_if_not_exists(
        'idx_expense_company_id',
        'expense',
        ['company_id']
    )

    # Company + category queries (expense reports by category)
    _create_index_if_not_exists(
        'idx_expense_company_category',
        'expense',
        ['company_id', 'category']
    )

    # Company + property queries (property expense tracking)
    _create_index_if_not_exists(
        'idx_expense_company_property',
        'expense',
        ['company_id', 'property_id']
    )

    # Date-based queries (monthly expense reports)
    _create_index_if_not_exists(
        'idx_expense_company_date',
        'expense',
        ['company_id', 'expense_date']
    )

    # Tax-deductible expense queries (tax reporting)
    _create_index_if_not_exists(
        'idx_expense_company_tax_deductible',
        'expense',
        ['company_id', 'tax_deductible', 'expense_date']
    )

    # =============================================================================
    # PORTFOLIO INDEXES
    # =============================================================================

    # Primary company filter
    _create_index_if_not_exists(
        'idx_portfolio_company_id',
        'portfolio',
        ['company_id']
    )

    # Company + name (portfolio lookup by name)
    _create_index_if_not_exists(
        'idx_portfolio_company_name',
        'portfolio',
        ['company_id', 'name']
    )

    # =============================================================================
    # LEASE TEMPLATE INDEXES
    # =============================================================================

    # Primary company filter
    _create_index_if_not_exists(
        'idx_lease_template_company_id',
        'lease_template',
        ['company_id']
    )

    # Company + active status (active template listings)
    _create_index_if_not_exists(
        'idx_lease_template_company_active',
        'lease_template',
        ['company_id', 'is_active']
    )

    # =============================================================================
    # USER INDEXES
    # =============================================================================

    # Company-based user queries (team member lists)
    _create_index_if_not_exists(
        'idx_user_company_id',
        'user',
        ['company_id']
    )

    # Company + role queries (role-based user lists)
    _create_index_if_not_exists(
        'idx_user_company_role',
        'user',
        ['company_id', 'role']
    )

    # Email lookup (login, password reset)
    _create_index_if_not_exists(
        'idx_user_email',
        'user',
        ['email'],
        unique=True
    )


def downgrade():
    """
    Remove all multi-tenant performance indexes.

    This is also idempotent - it will only drop indexes that exist.
    """

    # Property indexes
    _drop_index_if_exists('idx_property_company_id', 'property')
    _drop_index_if_exists('idx_property_company_occupancy', 'property')
    _drop_index_if_exists('idx_property_company_portfolio', 'property')
    _drop_index_if_exists('idx_property_company_type', 'property')
    _drop_index_if_exists('idx_property_company_location', 'property')

    # Unit indexes
    _drop_index_if_exists('idx_unit_company_id', 'unit')
    _drop_index_if_exists('idx_unit_company_property', 'unit')
    _drop_index_if_exists('idx_unit_company_occupancy', 'unit')
    _drop_index_if_exists('idx_unit_company_property_occupancy', 'unit')
    _drop_index_if_exists('idx_unit_company_rent', 'unit')

    # Tenant indexes
    _drop_index_if_exists('idx_tenant_company_id', 'tenant')
    _drop_index_if_exists('idx_tenant_company_email', 'tenant')
    _drop_index_if_exists('idx_tenant_company_property', 'tenant')
    _drop_index_if_exists('idx_tenant_company_name', 'tenant')

    # Lease indexes
    _drop_index_if_exists('idx_lease_company_id', 'lease')
    _drop_index_if_exists('idx_lease_company_status', 'lease')
    _drop_index_if_exists('idx_lease_company_property', 'lease')
    _drop_index_if_exists('idx_lease_company_tenant', 'lease')
    _drop_index_if_exists('idx_lease_company_unit', 'lease')
    _drop_index_if_exists('idx_lease_company_dates', 'lease')
    _drop_index_if_exists('idx_lease_company_status_end', 'lease')

    # Payment indexes
    _drop_index_if_exists('idx_payment_company_id', 'payment')
    _drop_index_if_exists('idx_payment_company_status', 'payment')
    _drop_index_if_exists('idx_payment_company_lease', 'payment')
    _drop_index_if_exists('idx_payment_company_property', 'payment')
    _drop_index_if_exists('idx_payment_company_date', 'payment')
    _drop_index_if_exists('idx_payment_company_status_date', 'payment')

    # Expense indexes
    _drop_index_if_exists('idx_expense_company_id', 'expense')
    _drop_index_if_exists('idx_expense_company_category', 'expense')
    _drop_index_if_exists('idx_expense_company_property', 'expense')
    _drop_index_if_exists('idx_expense_company_date', 'expense')
    _drop_index_if_exists('idx_expense_company_tax_deductible', 'expense')

    # Portfolio indexes
    _drop_index_if_exists('idx_portfolio_company_id', 'portfolio')
    _drop_index_if_exists('idx_portfolio_company_name', 'portfolio')

    # Lease template indexes
    _drop_index_if_exists('idx_lease_template_company_id', 'lease_template')
    _drop_index_if_exists('idx_lease_template_company_active', 'lease_template')

    # User indexes
    _drop_index_if_exists('idx_user_company_id', 'user')
    _drop_index_if_exists('idx_user_company_role', 'user')
    _drop_index_if_exists('idx_user_email', 'user')
