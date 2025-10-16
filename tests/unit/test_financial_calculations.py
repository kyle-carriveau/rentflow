"""
Unit tests for financial calculations and models.

This module demonstrates testing patterns for:
- Financial calculations with decimal precision
- Multi-tenant data isolation
- Model business logic
- Edge cases and error handling
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from website.models import Lease, Payment, Expense


@pytest.mark.unit
@pytest.mark.financial
class TestLeaseFinancialCalculations:
    """Test financial calculations in Lease model."""

    def test_outstanding_balance_no_payments(self, app, active_lease):
        """Test outstanding balance calculation with no payments."""
        with app.app_context():
            # Fresh lease should have outstanding balance equal to one month's rent
            # (assuming monthly billing)
            expected = active_lease.rent
            actual = active_lease.get_outstanding_balance()
            assert actual == expected

    def test_outstanding_balance_with_partial_payment(self, app, active_lease):
        """Test outstanding balance with partial payment."""
        with app.app_context():
            # Create partial payment
            partial_amount = Decimal('500.00')
            payment = Payment(
                amount=partial_amount,
                payment_date=datetime.now().date(),
                payment_method='Check',
                status='completed',
                lease_id=active_lease.id
            )

            from website import db
            db.session.add(payment)
            db.session.commit()

            # Outstanding should be rent minus payment
            expected = active_lease.rent - partial_amount
            actual = active_lease.get_outstanding_balance()
            assert actual == expected

    def test_outstanding_balance_fully_paid(self, app, active_lease):
        """Test outstanding balance when fully paid."""
        with app.app_context():
            # Create full payment
            payment = Payment(
                amount=active_lease.rent,
                payment_date=datetime.now().date(),
                payment_method='Check',
                status='completed',
                lease_id=active_lease.id
            )

            from website import db
            db.session.add(payment)
            db.session.commit()

            # Outstanding should be zero
            expected = Decimal('0.00')
            actual = active_lease.get_outstanding_balance()
            assert actual == expected

    def test_outstanding_balance_overpaid(self, app, active_lease):
        """Test outstanding balance when overpaid (should be zero, not negative)."""
        with app.app_context():
            # Create overpayment
            overpayment = active_lease.rent + Decimal('100.00')
            payment = Payment(
                amount=overpayment,
                payment_date=datetime.now().date(),
                payment_method='Check',
                status='completed',
                lease_id=active_lease.id
            )

            from website import db
            db.session.add(payment)
            db.session.commit()

            # Outstanding should still be zero (not negative)
            expected = Decimal('0.00')
            actual = active_lease.get_outstanding_balance()
            assert actual == expected

    def test_outstanding_balance_ignores_pending_payments(self, app, active_lease):
        """Test that pending payments don't affect outstanding balance."""
        with app.app_context():
            # Create pending payment
            payment = Payment(
                amount=active_lease.rent,
                payment_date=datetime.now().date(),
                payment_method='Check',
                status='pending',  # Not completed
                lease_id=active_lease.id
            )

            from website import db
            db.session.add(payment)
            db.session.commit()

            # Outstanding should still be full rent amount
            expected = active_lease.rent
            actual = active_lease.get_outstanding_balance()
            assert actual == expected

    def test_decimal_precision_maintained(self, app, active_lease):
        """Test that decimal precision is maintained in calculations."""
        with app.app_context():
            # Create payment with precise decimal amount
            payment = Payment(
                amount=Decimal('1234.56'),
                payment_date=datetime.now().date(),
                payment_method='Check',
                status='completed',
                lease_id=active_lease.id
            )

            from website import db
            db.session.add(payment)
            db.session.commit()

            # Calculation should maintain precision
            expected = active_lease.rent - Decimal('1234.56')
            actual = active_lease.get_outstanding_balance()
            assert actual == expected
            assert isinstance(actual, Decimal)


@pytest.mark.unit
@pytest.mark.financial
@pytest.mark.security
class TestFinancialMultiTenantIsolation:
    """Test multi-tenant isolation for financial data."""

    def test_lease_payments_isolated_by_company(self, app, company_a, company_b,
                                               property_a, property_b, unit, tenant,
                                               test_factory):
        """Test that lease payments are isolated by company."""
        with app.app_context():
            from website import db

            # Create a second unit for company B
            unit_b = test_factory.create_property(app, company_b)
            unit_b = Unit(
                unit_number='201',
                bedrooms=1,
                bathrooms=1,
                square_feet=800,
                rent=Decimal('1200.00'),
                property_id=property_b.id
            )
            db.session.add(unit_b)

            # Create tenant for company B
            tenant_b = Tenant(
                first_name='Jane',
                last_name='CompanyB',
                email='jane@companyb.com',
                phone='555-0456',
                company_id=company_b.id
            )
            db.session.add(tenant_b)

            # Create leases for both companies
            lease_a = Lease(
                start=datetime.now().date(),
                end=datetime.now().date() + timedelta(days=365),
                rent=Decimal('1500.00'),
                deposit=Decimal('1500.00'),
                unit_id=unit.id,
                tenant_id=tenant.id
            )

            lease_b = Lease(
                start=datetime.now().date(),
                end=datetime.now().date() + timedelta(days=365),
                rent=Decimal('1200.00'),
                deposit=Decimal('1200.00'),
                unit_id=unit_b.id,
                tenant_id=tenant_b.id
            )

            db.session.add_all([lease_a, lease_b])
            db.session.commit()

            # Create payments for both leases
            payment_a = Payment(
                amount=Decimal('1500.00'),
                payment_date=datetime.now().date(),
                payment_method='Check',
                status='completed',
                lease_id=lease_a.id
            )

            payment_b = Payment(
                amount=Decimal('1200.00'),
                payment_date=datetime.now().date(),
                payment_method='Transfer',
                status='completed',
                lease_id=lease_b.id
            )

            db.session.add_all([payment_a, payment_b])
            db.session.commit()

            # Query payments for company A - should not see company B's data
            company_a_payments = db.session.query(Payment).join(Lease).join(Unit).join(Property).filter(
                Property.company_id == company_a.id
            ).all()

            assert len(company_a_payments) == 1
            assert company_a_payments[0].id == payment_a.id
            assert company_a_payments[0].amount == Decimal('1500.00')

            # Query payments for company B - should not see company A's data
            company_b_payments = db.session.query(Payment).join(Lease).join(Unit).join(Property).filter(
                Property.company_id == company_b.id
            ).all()

            assert len(company_b_payments) == 1
            assert company_b_payments[0].id == payment_b.id
            assert company_b_payments[0].amount == Decimal('1200.00')


@pytest.mark.unit
@pytest.mark.financial
class TestExpenseCalculations:
    """Test expense-related calculations."""

    def test_expense_categorization(self, app, company_a, property_a):
        """Test expense categorization and filtering."""
        with app.app_context():
            from website import db

            # Create expenses in different categories
            maintenance_expense = Expense(
                amount=Decimal('250.00'),
                description='HVAC repair',
                category='maintenance',
                expense_date=datetime.now().date(),
                company_id=company_a.id,
                property_id=property_a.id
            )

            utility_expense = Expense(
                amount=Decimal('180.00'),
                description='Electric bill',
                category='utilities',
                expense_date=datetime.now().date(),
                company_id=company_a.id,
                property_id=property_a.id
            )

            tax_expense = Expense(
                amount=Decimal('1200.00'),
                description='Property tax',
                category='taxes',
                expense_date=datetime.now().date(),
                company_id=company_a.id,
                property_id=property_a.id
            )

            db.session.add_all([maintenance_expense, utility_expense, tax_expense])
            db.session.commit()

            # Test filtering by category
            maintenance_expenses = Expense.query.filter_by(
                company_id=company_a.id,
                category='maintenance'
            ).all()

            assert len(maintenance_expenses) == 1
            assert maintenance_expenses[0].description == 'HVAC repair'
            assert maintenance_expenses[0].amount == Decimal('250.00')

            # Test total calculation for property
            total_expenses = db.session.query(db.func.sum(Expense.amount)).filter_by(
                company_id=company_a.id,
                property_id=property_a.id
            ).scalar()

            expected_total = Decimal('250.00') + Decimal('180.00') + Decimal('1200.00')
            assert total_expenses == expected_total

    def test_monthly_expense_calculation(self, app, company_a, property_a):
        """Test monthly expense calculations."""
        with app.app_context():
            from website import db

            # Create expenses across different months
            current_month = datetime.now().date()
            last_month = current_month - timedelta(days=30)

            current_expense = Expense(
                amount=Decimal('300.00'),
                description='Current month expense',
                category='maintenance',
                expense_date=current_month,
                company_id=company_a.id,
                property_id=property_a.id
            )

            last_month_expense = Expense(
                amount=Decimal('450.00'),
                description='Last month expense',
                category='maintenance',
                expense_date=last_month,
                company_id=company_a.id,
                property_id=property_a.id
            )

            db.session.add_all([current_expense, last_month_expense])
            db.session.commit()

            # Calculate current month expenses
            month_start = current_month.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            current_month_total = db.session.query(db.func.sum(Expense.amount)).filter(
                Expense.company_id == company_a.id,
                Expense.expense_date >= month_start,
                Expense.expense_date <= month_end
            ).scalar()

            assert current_month_total == Decimal('300.00')