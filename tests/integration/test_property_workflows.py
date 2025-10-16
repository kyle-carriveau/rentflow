"""
Integration tests for property management workflows.

This module demonstrates testing patterns for:
- End-to-end business workflows
- Multi-step processes
- Data consistency across operations
- Integration between multiple models
- Workflow validation and error handling
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from flask import url_for

from website.models import Property, Unit, Tenant, Lease, Payment, Expense


@pytest.mark.integration
@pytest.mark.property
class TestPropertyCreationWorkflow:
    """Test complete property creation and setup workflow."""

    def test_complete_property_setup_workflow(self, app, authenticated_client,
                                             company_a, portfolio):
        """Test full property setup from creation to first lease."""
        with app.app_context():
            from website import db

            # Step 1: Create property via API
            property_data = {
                'name': 'Integration Test Property',
                'address': '123 Integration St',
                'city': 'Test City',
                'state': 'CA',
                'zip_code': '90210',
                'property_type': 'Apartment',
                'portfolio_id': portfolio.id,
                'purchase_price': '250000.00',
                'bedrooms': '2',
                'bathrooms': '2',
                'square_feet': '1200'
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('property.create'),
                    data=property_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Verify property was created
            property_obj = Property.query.filter_by(
                name='Integration Test Property',
                company_id=company_a.id
            ).first()
            assert property_obj is not None
            assert property_obj.portfolio_id == portfolio.id

            # Step 2: Add units to the property
            unit_data = {
                'unit_number': '101',
                'bedrooms': '2',
                'bathrooms': '2',
                'square_feet': '1200',
                'rent': '1800.00',
                'property_id': property_obj.id
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('unit.create'),
                    data=unit_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Verify unit was created
            unit = Unit.query.filter_by(
                unit_number='101',
                property_id=property_obj.id
            ).first()
            assert unit is not None
            assert unit.rent == Decimal('1800.00')

            # Step 3: Add tenant
            tenant_data = {
                'first_name': 'Integration',
                'last_name': 'Tester',
                'email': 'integration@test.com',
                'phone': '555-0123',
                'address': '456 Tenant St',
                'city': 'Test City',
                'state': 'CA',
                'zip_code': '90210'
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('tenant.create'),
                    data=tenant_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Verify tenant was created
            tenant = Tenant.query.filter_by(
                email='integration@test.com',
                company_id=company_a.id
            ).first()
            assert tenant is not None

            # Step 4: Create lease
            lease_start = datetime.now().date()
            lease_end = lease_start + timedelta(days=365)

            lease_data = {
                'start': lease_start.strftime('%Y-%m-%d'),
                'end': lease_end.strftime('%Y-%m-%d'),
                'rent': '1800.00',
                'deposit': '1800.00',
                'unit_id': unit.id,
                'tenant_id': tenant.id
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('lease.create'),
                    data=lease_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Verify lease was created and unit status updated
            lease = Lease.query.filter_by(
                unit_id=unit.id,
                tenant_id=tenant.id
            ).first()
            assert lease is not None
            assert lease.rent == Decimal('1800.00')

            # Verify unit shows as occupied
            db.session.refresh(unit)
            assert unit.get_lease_status() == 'Occupied'

            # Step 5: Record first payment
            payment_data = {
                'amount': '1800.00',
                'payment_date': datetime.now().date().strftime('%Y-%m-%d'),
                'payment_method': 'Check',
                'lease_id': lease.id
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('financial.record_payment'),
                    data=payment_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Verify payment was recorded
            payment = Payment.query.filter_by(lease_id=lease.id).first()
            assert payment is not None
            assert payment.amount == Decimal('1800.00')
            assert payment.status == 'completed'

            # Verify outstanding balance is now zero
            assert lease.get_outstanding_balance() == Decimal('0.00')

            # Step 6: Record property expense
            expense_data = {
                'amount': '250.00',
                'description': 'Initial maintenance',
                'category': 'maintenance',
                'expense_date': datetime.now().date().strftime('%Y-%m-%d'),
                'property_id': property_obj.id
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('financial.add_expense'),
                    data=expense_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Verify expense was recorded
            expense = Expense.query.filter_by(
                property_id=property_obj.id,
                description='Initial maintenance'
            ).first()
            assert expense is not None
            assert expense.amount == Decimal('250.00')
            assert expense.company_id == company_a.id


@pytest.mark.integration
@pytest.mark.financial
class TestFinancialWorkflows:
    """Test financial workflows and calculations."""

    def test_monthly_rent_collection_workflow(self, app, authenticated_client,
                                            company_a, property_a, unit, tenant,
                                            active_lease):
        """Test complete monthly rent collection process."""
        with app.app_context():
            from website import db

            # Initial state - lease should have outstanding balance
            initial_balance = active_lease.get_outstanding_balance()
            assert initial_balance > 0

            # Step 1: Record full rent payment
            rent_payment_data = {
                'amount': str(active_lease.rent),
                'payment_date': datetime.now().date().strftime('%Y-%m-%d'),
                'payment_method': 'Bank Transfer',
                'lease_id': active_lease.id,
                'notes': 'Monthly rent payment'
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('financial.record_payment'),
                    data=rent_payment_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Verify payment was recorded
            payment = Payment.query.filter_by(
                lease_id=active_lease.id,
                amount=active_lease.rent
            ).first()
            assert payment is not None
            assert payment.status == 'completed'

            # Step 2: Verify outstanding balance is cleared
            db.session.refresh(active_lease)
            assert active_lease.get_outstanding_balance() == Decimal('0.00')

            # Step 3: Record property maintenance expense
            maintenance_data = {
                'amount': '150.00',
                'description': 'Monthly maintenance check',
                'category': 'maintenance',
                'expense_date': datetime.now().date().strftime('%Y-%m-%d'),
                'property_id': property_a.id
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('financial.add_expense'),
                    data=maintenance_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Step 4: Verify financial summary shows correct profit
            current_month = datetime.now().date()
            month_start = current_month.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            # Calculate monthly revenue
            monthly_revenue = db.session.query(db.func.sum(Payment.amount)).join(Lease).join(Unit).join(Property).filter(
                Property.company_id == company_a.id,
                Payment.payment_date >= month_start,
                Payment.payment_date <= month_end,
                Payment.status == 'completed'
            ).scalar() or Decimal('0.00')

            # Calculate monthly expenses
            monthly_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
                Expense.company_id == company_a.id,
                Expense.expense_date >= month_start,
                Expense.expense_date <= month_end
            ).scalar() or Decimal('0.00')

            # Verify calculations
            expected_revenue = active_lease.rent
            expected_expenses = Decimal('150.00')
            expected_profit = expected_revenue - expected_expenses

            assert monthly_revenue == expected_revenue
            assert monthly_expenses == expected_expenses

            monthly_profit = monthly_revenue - monthly_expenses
            assert monthly_profit == expected_profit


@pytest.mark.integration
@pytest.mark.tenant
class TestTenantLifecycleWorkflow:
    """Test complete tenant lifecycle from move-in to move-out."""

    def test_tenant_move_in_workflow(self, app, authenticated_client, company_a,
                                   property_a, unit, tenant):
        """Test tenant move-in process."""
        with app.app_context():
            from website import db

            # Initial state - unit should be available
            assert unit.get_lease_status() == 'Available'

            # Step 1: Create lease agreement
            move_in_date = datetime.now().date()
            move_out_date = move_in_date + timedelta(days=365)

            lease_data = {
                'start': move_in_date.strftime('%Y-%m-%d'),
                'end': move_out_date.strftime('%Y-%m-%d'),
                'rent': '1500.00',
                'deposit': '1500.00',
                'unit_id': unit.id,
                'tenant_id': tenant.id,
                'notes': 'Standard 12-month lease'
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('lease.create'),
                    data=lease_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Verify lease was created
            lease = Lease.query.filter_by(
                unit_id=unit.id,
                tenant_id=tenant.id
            ).first()
            assert lease is not None

            # Step 2: Record security deposit
            deposit_data = {
                'amount': '1500.00',
                'payment_date': move_in_date.strftime('%Y-%m-%d'),
                'payment_method': 'Check',
                'lease_id': lease.id,
                'notes': 'Security deposit'
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('financial.record_payment'),
                    data=deposit_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Step 3: Record first month's rent
            rent_data = {
                'amount': '1500.00',
                'payment_date': move_in_date.strftime('%Y-%m-%d'),
                'payment_method': 'Check',
                'lease_id': lease.id,
                'notes': 'First month rent'
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('financial.record_payment'),
                    data=rent_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Step 4: Verify unit status and financial state
            db.session.refresh(unit)
            assert unit.get_lease_status() == 'Occupied'

            # Should have two payments
            payments = Payment.query.filter_by(lease_id=lease.id).all()
            assert len(payments) == 2

            total_payments = sum(p.amount for p in payments)
            assert total_payments == Decimal('3000.00')  # Deposit + First month

            # Outstanding balance should be zero (assuming no additional charges)
            db.session.refresh(lease)
            assert lease.get_outstanding_balance() == Decimal('0.00')

    def test_tenant_move_out_workflow(self, app, authenticated_client, company_a,
                                    active_lease, unit, tenant):
        """Test tenant move-out process."""
        with app.app_context():
            from website import db

            # Initial state - tenant is in active lease
            assert unit.get_lease_status() == 'Occupied'

            # Step 1: Record final month's rent payment
            final_rent_data = {
                'amount': str(active_lease.rent),
                'payment_date': (active_lease.end - timedelta(days=5)).strftime('%Y-%m-%d'),
                'payment_method': 'Bank Transfer',
                'lease_id': active_lease.id,
                'notes': 'Final month rent'
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('financial.record_payment'),
                    data=final_rent_data,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Step 2: Record move-out expenses (cleaning, repairs)
            cleaning_expense = {
                'amount': '200.00',
                'description': 'Post-move-out cleaning',
                'category': 'maintenance',
                'expense_date': active_lease.end.strftime('%Y-%m-%d'),
                'property_id': unit.property_id
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('financial.add_expense'),
                    data=cleaning_expense,
                    follow_redirects=True
                )
                assert response.status_code == 200

            # Step 3: Mark unit as available (this would typically happen
            # when lease end date passes or through an admin action)
            # For testing, we'll advance the lease end date to past
            active_lease.end = datetime.now().date() - timedelta(days=1)
            db.session.commit()

            # Step 4: Verify move-out state
            db.session.refresh(unit)
            # Note: This depends on your business logic for determining availability
            # The unit might show as "Available" or "Preparing" depending on implementation

            # Verify expenses were recorded
            move_out_expense = Expense.query.filter_by(
                description='Post-move-out cleaning',
                property_id=unit.property_id
            ).first()
            assert move_out_expense is not None
            assert move_out_expense.amount == Decimal('200.00')


@pytest.mark.integration
@pytest.mark.error_handling
class TestWorkflowErrorHandling:
    """Test error handling in complex workflows."""

    def test_duplicate_lease_prevention(self, app, authenticated_client,
                                       company_a, unit, tenant, active_lease):
        """Test that system prevents creating duplicate active leases."""
        with app.app_context():
            # Try to create another lease for the same unit while one is active
            conflicting_lease_data = {
                'start': datetime.now().date().strftime('%Y-%m-%d'),
                'end': (datetime.now().date() + timedelta(days=365)).strftime('%Y-%m-%d'),
                'rent': '1600.00',
                'deposit': '1600.00',
                'unit_id': unit.id,
                'tenant_id': tenant.id
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('lease.create'),
                    data=conflicting_lease_data
                )

                # Should either redirect with error or show error on same page
                # Exact behavior depends on your implementation
                assert response.status_code in [200, 302, 400]

                if response.status_code == 200:
                    # Error should be displayed on form
                    assert b'error' in response.data.lower() or b'conflict' in response.data.lower()

            # Verify only original lease exists
            leases = Lease.query.filter_by(unit_id=unit.id).all()
            active_leases = [l for l in leases if l.is_active()]
            assert len(active_leases) == 1
            assert active_leases[0].id == active_lease.id

    def test_payment_validation_workflow(self, app, authenticated_client,
                                       company_a, active_lease):
        """Test payment validation in workflow."""
        with app.app_context():
            # Try to record negative payment
            invalid_payment_data = {
                'amount': '-100.00',
                'payment_date': datetime.now().date().strftime('%Y-%m-%d'),
                'payment_method': 'Check',
                'lease_id': active_lease.id
            }

            with app.test_request_context():
                response = authenticated_client.post(
                    url_for('financial.record_payment'),
                    data=invalid_payment_data
                )

                # Should handle error gracefully
                assert response.status_code in [200, 400]

            # Verify no invalid payment was recorded
            invalid_payment = Payment.query.filter(
                Payment.lease_id == active_lease.id,
                Payment.amount < 0
            ).first()
            assert invalid_payment is None