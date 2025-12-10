"""Add multi-tenant performance indexes

Revision ID: c1d2e3f4g5h6
Revises: a1b2c3d4e5f6
Create Date: 2025-12-09 14:30:00.000000

Critical database indexes for multi-tenant query performance.
All indexes are designed to optimize company_id scoped queries.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4g5h6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


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
    op.create_index(
        'idx_property_company_id',
        'property',
        ['company_id'],
        unique=False
    )

    # Company + occupancy status queries (property listings)
    op.create_index(
        'idx_property_company_occupancy',
        'property',
        ['company_id', 'occupancy_status'],
        unique=False
    )

    # Company + portfolio queries (portfolio views)
    op.create_index(
        'idx_property_company_portfolio',
        'property',
        ['company_id', 'portfolio_id'],
        unique=False
    )

    # Company + type queries (filter by property type)
    op.create_index(
        'idx_property_company_type',
        'property',
        ['company_id', 'type'],
        unique=False
    )

    # Company + location queries (search by city/state)
    op.create_index(
        'idx_property_company_location',
        'property',
        ['company_id', 'state', 'city'],
        unique=False
    )

    # =============================================================================
    # UNIT INDEXES
    # =============================================================================

    # Primary company filter
    op.create_index(
        'idx_unit_company_id',
        'unit',
        ['company_id'],
        unique=False
    )

    # Company + property queries (most common - unit listings by property)
    op.create_index(
        'idx_unit_company_property',
        'unit',
        ['company_id', 'property_id'],
        unique=False
    )

    # Company + occupancy status queries (available unit searches)
    op.create_index(
        'idx_unit_company_occupancy',
        'unit',
        ['company_id', 'occupancy_status'],
        unique=False
    )

    # Company + property + occupancy (filtered property views)
    op.create_index(
        'idx_unit_company_property_occupancy',
        'unit',
        ['company_id', 'property_id', 'occupancy_status'],
        unique=False
    )

    # Rent range queries (unit search by price)
    op.create_index(
        'idx_unit_company_rent',
        'unit',
        ['company_id', 'rent'],
        unique=False
    )

    # =============================================================================
    # TENANT INDEXES
    # =============================================================================

    # Primary company filter
    op.create_index(
        'idx_tenant_company_id',
        'tenant',
        ['company_id'],
        unique=False
    )

    # Company + email (unique tenant lookup)
    op.create_index(
        'idx_tenant_company_email',
        'tenant',
        ['company_id', 'email'],
        unique=False
    )

    # Company + property (tenants by property)
    op.create_index(
        'idx_tenant_company_property',
        'tenant',
        ['company_id', 'property_id'],
        unique=False
    )

    # Name-based searches (tenant directory)
    op.create_index(
        'idx_tenant_company_name',
        'tenant',
        ['company_id', 'last_name', 'first_name'],
        unique=False
    )

    # =============================================================================
    # LEASE INDEXES
    # =============================================================================

    # Primary company filter
    op.create_index(
        'idx_lease_company_id',
        'lease',
        ['company_id'],
        unique=False
    )

    # Company + status queries (active/expiring lease lists)
    op.create_index(
        'idx_lease_company_status',
        'lease',
        ['company_id', 'lease_status'],
        unique=False
    )

    # Company + property queries (leases by property)
    op.create_index(
        'idx_lease_company_property',
        'lease',
        ['company_id', 'property_id'],
        unique=False
    )

    # Company + tenant queries (tenant lease history)
    op.create_index(
        'idx_lease_company_tenant',
        'lease',
        ['company_id', 'tenant_id'],
        unique=False
    )

    # Company + unit queries (unit lease history)
    op.create_index(
        'idx_lease_company_unit',
        'lease',
        ['company_id', 'unit_id'],
        unique=False
    )

    # Date-based queries (expiring leases, lease status automation)
    op.create_index(
        'idx_lease_company_dates',
        'lease',
        ['company_id', 'end', 'start'],
        unique=False
    )

    # Lease status + end date (expiring lease notifications)
    op.create_index(
        'idx_lease_company_status_end',
        'lease',
        ['company_id', 'lease_status', 'end'],
        unique=False
    )

    # =============================================================================
    # PAYMENT INDEXES
    # =============================================================================

    # Primary company filter
    op.create_index(
        'idx_payment_company_id',
        'payment',
        ['company_id'],
        unique=False
    )

    # Company + status queries (completed/pending payments)
    op.create_index(
        'idx_payment_company_status',
        'payment',
        ['company_id', 'status'],
        unique=False
    )

    # Company + lease queries (payment history by lease)
    op.create_index(
        'idx_payment_company_lease',
        'payment',
        ['company_id', 'lease_id'],
        unique=False
    )

    # Company + property queries (property financial reports)
    op.create_index(
        'idx_payment_company_property',
        'payment',
        ['company_id', 'property_id'],
        unique=False
    )

    # Date-based queries (monthly income reports)
    op.create_index(
        'idx_payment_company_date',
        'payment',
        ['company_id', 'payment_date'],
        unique=False
    )

    # Company + status + date (completed payments in date range)
    op.create_index(
        'idx_payment_company_status_date',
        'payment',
        ['company_id', 'status', 'payment_date'],
        unique=False
    )

    # =============================================================================
    # EXPENSE INDEXES
    # =============================================================================

    # Primary company filter
    op.create_index(
        'idx_expense_company_id',
        'expense',
        ['company_id'],
        unique=False
    )

    # Company + category queries (expense reports by category)
    op.create_index(
        'idx_expense_company_category',
        'expense',
        ['company_id', 'category'],
        unique=False
    )

    # Company + property queries (property expense tracking)
    op.create_index(
        'idx_expense_company_property',
        'expense',
        ['company_id', 'property_id'],
        unique=False
    )

    # Date-based queries (monthly expense reports)
    op.create_index(
        'idx_expense_company_date',
        'expense',
        ['company_id', 'expense_date'],
        unique=False
    )

    # Tax-deductible expense queries (tax reporting)
    op.create_index(
        'idx_expense_company_tax_deductible',
        'expense',
        ['company_id', 'tax_deductible', 'expense_date'],
        unique=False
    )

    # =============================================================================
    # PORTFOLIO INDEXES
    # =============================================================================

    # Primary company filter
    op.create_index(
        'idx_portfolio_company_id',
        'portfolio',
        ['company_id'],
        unique=False
    )

    # Company + name (portfolio lookup by name)
    op.create_index(
        'idx_portfolio_company_name',
        'portfolio',
        ['company_id', 'name'],
        unique=False
    )

    # =============================================================================
    # LEASE TEMPLATE INDEXES
    # =============================================================================

    # Primary company filter
    op.create_index(
        'idx_lease_template_company_id',
        'lease_template',
        ['company_id'],
        unique=False
    )

    # Company + active status (active template listings)
    op.create_index(
        'idx_lease_template_company_active',
        'lease_template',
        ['company_id', 'is_active'],
        unique=False
    )

    # =============================================================================
    # USER INDEXES
    # =============================================================================

    # Company-based user queries (team member lists)
    op.create_index(
        'idx_user_company_id',
        'user',
        ['company_id'],
        unique=False
    )

    # Company + role queries (role-based user lists)
    op.create_index(
        'idx_user_company_role',
        'user',
        ['company_id', 'role'],
        unique=False
    )

    # Email lookup (login, password reset)
    op.create_index(
        'idx_user_email',
        'user',
        ['email'],
        unique=True
    )


def downgrade():
    """
    Remove all multi-tenant performance indexes.
    """

    # Property indexes
    op.drop_index('idx_property_company_id', table_name='property')
    op.drop_index('idx_property_company_occupancy', table_name='property')
    op.drop_index('idx_property_company_portfolio', table_name='property')
    op.drop_index('idx_property_company_type', table_name='property')
    op.drop_index('idx_property_company_location', table_name='property')

    # Unit indexes
    op.drop_index('idx_unit_company_id', table_name='unit')
    op.drop_index('idx_unit_company_property', table_name='unit')
    op.drop_index('idx_unit_company_occupancy', table_name='unit')
    op.drop_index('idx_unit_company_property_occupancy', table_name='unit')
    op.drop_index('idx_unit_company_rent', table_name='unit')

    # Tenant indexes
    op.drop_index('idx_tenant_company_id', table_name='tenant')
    op.drop_index('idx_tenant_company_email', table_name='tenant')
    op.drop_index('idx_tenant_company_property', table_name='tenant')
    op.drop_index('idx_tenant_company_name', table_name='tenant')

    # Lease indexes
    op.drop_index('idx_lease_company_id', table_name='lease')
    op.drop_index('idx_lease_company_status', table_name='lease')
    op.drop_index('idx_lease_company_property', table_name='lease')
    op.drop_index('idx_lease_company_tenant', table_name='lease')
    op.drop_index('idx_lease_company_unit', table_name='lease')
    op.drop_index('idx_lease_company_dates', table_name='lease')
    op.drop_index('idx_lease_company_status_end', table_name='lease')

    # Payment indexes
    op.drop_index('idx_payment_company_id', table_name='payment')
    op.drop_index('idx_payment_company_status', table_name='payment')
    op.drop_index('idx_payment_company_lease', table_name='payment')
    op.drop_index('idx_payment_company_property', table_name='payment')
    op.drop_index('idx_payment_company_date', table_name='payment')
    op.drop_index('idx_payment_company_status_date', table_name='payment')

    # Expense indexes
    op.drop_index('idx_expense_company_id', table_name='expense')
    op.drop_index('idx_expense_company_category', table_name='expense')
    op.drop_index('idx_expense_company_property', table_name='expense')
    op.drop_index('idx_expense_company_date', table_name='expense')
    op.drop_index('idx_expense_company_tax_deductible', table_name='expense')

    # Portfolio indexes
    op.drop_index('idx_portfolio_company_id', table_name='portfolio')
    op.drop_index('idx_portfolio_company_name', table_name='portfolio')

    # Lease template indexes
    op.drop_index('idx_lease_template_company_id', table_name='lease_template')
    op.drop_index('idx_lease_template_company_active', table_name='lease_template')

    # User indexes
    op.drop_index('idx_user_company_id', table_name='user')
    op.drop_index('idx_user_company_role', table_name='user')
    op.drop_index('idx_user_email', table_name='user')
