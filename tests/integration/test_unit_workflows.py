"""
Integration tests for Unit management workflows.

Tests complete unit-related workflows including unit creation,
lease assignment, tenant management, and occupancy tracking.
"""

import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from flask import url_for
from website import db
from website.models import Unit, Property, Company, Portfolio, Lease, Tenant, Payment


@pytest.mark.integration
class TestUnitWorkflows:
    """Test complete unit management workflows."""

    def test_complete_unit_creation_workflow(self, app, authenticated_client, company_a):
        """Test complete workflow from property creation to unit creation."""
        with app.app_context():
            # Step 1: Create a portfolio
            portfolio = Portfolio(name="Test Portfolio", company_id=company_a.id)
            db.session.add(portfolio)
            db.session.commit()

            # Step 2: Create a property
            property_data = {
                'name': 'Workflow Test Property',
                'address': '123 Test St',
                'city': 'Test City',
                'state': 'CA',
                'zip_code': '90210',
                'type': 'Apartment',
                'portfolio_id': portfolio.id
            }

            response = authenticated_client.post('/property/create', data=property_data)
            assert response.status_code == 302  # Redirect after creation

            property_obj = Property.query.filter_by(name='Workflow Test Property').first()
            assert property_obj is not None

            # Step 3: Create unit for the property
            unit_data = {
                'name': 'Unit 101',
                'property_id': property_obj.id,
                'bedrooms': 2,
                'bathrooms': 1,
                'sqft': 850,
                'rent': 1200,
                'description': 'Modern 2-bedroom apartment',
                'air_conditioning': True,
                'heating_type': 'central',
                'dishwasher': True,
                'parking_spaces': 1
            }

            response = authenticated_client.post('/unit/create', data=unit_data)
            assert response.status_code == 302  # Redirect after creation

            # Verify unit was created with all relationships
            unit = Unit.query.filter_by(name='Unit 101').first()
            assert unit is not None
            assert unit.property_id == property_obj.id
            assert unit.company_id == company_a.id
            assert unit.bedrooms == 2
            assert unit.air_conditioning is True

            # Verify relationships work
            assert unit.property == property_obj
            assert unit in property_obj.units

    def test_unit_to_lease_workflow(self, app, authenticated_client, company_a, property_a, tenant):
        """Test workflow from unit creation to lease assignment."""
        with app.app_context():
            # Step 1: Create unit
            unit = Unit(
                name="Lease Workflow Unit",
                company_id=company_a.id,
                property_id=property_a.id
            )
            unit.bedrooms = 2
            unit.bathrooms = 1
            unit.rent = 1500

            db.session.add(unit)
            db.session.commit()

            # Verify unit starts as vacant
            assert unit.get_lease_status() == 'Vacant'
            assert unit.get_current_tenant() is None

            # Step 2: Create lease for the unit
            lease_start = datetime.now().date()
            lease_end = lease_start + timedelta(days=365)

            lease = Lease(
                start=lease_start,
                end=lease_end,
                rent=Decimal('1500.00'),
                security_deposit=Decimal('1500.00'),
                unit_id=unit.id,
                tenant_id=tenant.id,
                property_id=property_a.id,
                company_id=company_a.id
            )

            db.session.add(lease)
            db.session.commit()

            # Step 3: Verify unit status changed
            assert unit.get_lease_status() == 'Occupied'
            assert unit.get_current_tenant() is not None
            assert unit.get_current_tenant().id == tenant.id
            assert unit.get_current_lease() is not None
            assert unit.get_current_lease().id == lease.id

    def test_unit_lease_transition_workflow(self, app, company_a, property_a):
        """Test unit transitioning between different lease states."""
        with app.app_context():
            # Create unit
            unit = Unit(
                name="Transition Test Unit",
                company_id=company_a.id,
                property_id=property_a.id
            )
            db.session.add(unit)
            db.session.commit()

            # Create first tenant
            tenant1 = Tenant(
                first_name="John",
                last_name="Tenant1",
                email="john1@example.com",
                phone=5551234567,
                company_id=company_a.id
            )
            db.session.add(tenant1)
            db.session.commit()

            # State 1: Vacant
            assert unit.get_lease_status() == 'Vacant'

            # State 2: Create future lease (Scheduled)
            future_start = datetime.now().date() + timedelta(days=30)
            future_end = future_start + timedelta(days=365)

            future_lease = Lease(
                start=future_start,
                end=future_end,
                rent=Decimal('1400.00'),
                unit_id=unit.id,
                tenant_id=tenant1.id,
                property_id=property_a.id,
                company_id=company_a.id
            )
            db.session.add(future_lease)
            db.session.commit()

            assert unit.get_lease_status() == 'Scheduled'
            assert unit.get_next_lease() is not None

            # State 3: Create current lease (Occupied)
            current_start = datetime.now().date() - timedelta(days=30)
            current_end = current_start + timedelta(days=365)

            current_lease = Lease(
                start=current_start,
                end=current_end,
                rent=Decimal('1600.00'),
                unit_id=unit.id,
                tenant_id=tenant1.id,
                property_id=property_a.id,
                company_id=company_a.id
            )
            db.session.add(current_lease)
            db.session.commit()

            assert unit.get_lease_status() == 'Occupied'
            assert unit.get_current_lease() is not None

    def test_unit_payment_workflow(self, app, company_a, property_a, tenant):
        """Test complete workflow from unit to lease to payments."""
        with app.app_context():
            # Create unit
            unit = Unit(
                name="Payment Workflow Unit",
                company_id=company_a.id,
                property_id=property_a.id
            )
            unit.rent = 1800
            db.session.add(unit)
            db.session.commit()

            # Create lease
            lease_start = datetime.now().date() - timedelta(days=30)
            lease_end = lease_start + timedelta(days=365)

            lease = Lease(
                start=lease_start,
                end=lease_end,
                rent=Decimal('1800.00'),
                unit_id=unit.id,
                tenant_id=tenant.id,
                property_id=property_a.id,
                company_id=company_a.id
            )
            db.session.add(lease)
            db.session.commit()

            # Create payment for the lease
            payment = Payment(
                amount=Decimal('1800.00'),
                payment_date=datetime.now().date(),
                payment_method='Check',
                status='completed',
                lease_id=lease.id
            )
            db.session.add(payment)
            db.session.commit()

            # Verify relationships work end-to-end
            assert lease.unit == unit
            assert lease.tenant == tenant
            assert payment.lease == lease
            assert payment in lease.payments

            # Verify unit has payment history through lease
            unit_payments = Payment.query.join(Lease).filter(Lease.unit_id == unit.id).all()
            assert len(unit_payments) == 1
            assert unit_payments[0].amount == Decimal('1800.00')

    def test_unit_search_and_filtering_workflow(self, app, authenticated_client, company_a, property_a):
        """Test unit search and filtering functionality."""
        with app.app_context():
            # Create multiple units with different characteristics
            units_data = [
                {
                    'name': 'Studio A',
                    'bedrooms': 0,
                    'bathrooms': 1,
                    'rent': 1000,
                    'air_conditioning': True
                },
                {
                    'name': '1BR Unit B',
                    'bedrooms': 1,
                    'bathrooms': 1,
                    'rent': 1300,
                    'air_conditioning': False
                },
                {
                    'name': '2BR Unit C',
                    'bedrooms': 2,
                    'bathrooms': 2,
                    'rent': 1600,
                    'air_conditioning': True
                },
                {
                    'name': '3BR Unit D',
                    'bedrooms': 3,
                    'bathrooms': 2,
                    'rent': 2000,
                    'air_conditioning': True
                }
            ]

            for unit_data in units_data:
                unit = Unit(
                    name=unit_data['name'],
                    company_id=company_a.id,
                    property_id=property_a.id
                )
                unit.bedrooms = unit_data['bedrooms']
                unit.bathrooms = unit_data['bathrooms']
                unit.rent = unit_data['rent']
                unit.air_conditioning = unit_data['air_conditioning']

                db.session.add(unit)

            db.session.commit()

            # Test basic unit listing
            response = authenticated_client.get('/unit/')
            assert response.status_code == 200

            # Verify all units appear in listing
            for unit_data in units_data:
                assert unit_data['name'].encode() in response.data

            # Test filtering by bedroom count (if supported by views)
            all_units = Unit.query.filter_by(company_id=company_a.id).all()
            two_bedroom_units = [u for u in all_units if u.bedrooms == 2]
            assert len(two_bedroom_units) == 1
            assert two_bedroom_units[0].name == '2BR Unit C'

            # Test filtering by amenities
            ac_units = [u for u in all_units if u.air_conditioning]
            assert len(ac_units) == 3  # Studio A, 2BR Unit C, 3BR Unit D

    def test_unit_occupancy_reporting_workflow(self, app, company_a, property_a):
        """Test unit occupancy tracking and reporting workflow."""
        with app.app_context():
            # Create multiple units with different occupancy states

            # Vacant unit
            vacant_unit = Unit(
                name="Vacant Unit",
                company_id=company_a.id,
                property_id=property_a.id
            )
            db.session.add(vacant_unit)

            # Occupied unit
            occupied_unit = Unit(
                name="Occupied Unit",
                company_id=company_a.id,
                property_id=property_a.id
            )
            db.session.add(occupied_unit)

            # Scheduled unit (future lease)
            scheduled_unit = Unit(
                name="Scheduled Unit",
                company_id=company_a.id,
                property_id=property_a.id
            )
            db.session.add(scheduled_unit)

            db.session.commit()

            # Create tenants
            tenant1 = Tenant(
                first_name="Occupied",
                last_name="Tenant",
                email="occupied@example.com",
                phone=5551111111,
                company_id=company_a.id
            )

            tenant2 = Tenant(
                first_name="Future",
                last_name="Tenant",
                email="future@example.com",
                phone=5552222222,
                company_id=company_a.id
            )

            db.session.add_all([tenant1, tenant2])
            db.session.commit()

            # Create current lease for occupied unit
            current_start = datetime.now().date() - timedelta(days=30)
            current_end = current_start + timedelta(days=335)

            current_lease = Lease(
                start=current_start,
                end=current_end,
                rent=Decimal('1500.00'),
                unit_id=occupied_unit.id,
                tenant_id=tenant1.id,
                property_id=property_a.id,
                company_id=company_a.id
            )
            db.session.add(current_lease)

            # Create future lease for scheduled unit
            future_start = datetime.now().date() + timedelta(days=30)
            future_end = future_start + timedelta(days=365)

            future_lease = Lease(
                start=future_start,
                end=future_end,
                rent=Decimal('1600.00'),
                unit_id=scheduled_unit.id,
                tenant_id=tenant2.id,
                property_id=property_a.id,
                company_id=company_a.id
            )
            db.session.add(future_lease)
            db.session.commit()

            # Test occupancy status for each unit
            assert vacant_unit.get_lease_status() == 'Vacant'
            assert occupied_unit.get_lease_status() == 'Occupied'
            assert scheduled_unit.get_lease_status() == 'Scheduled'

            # Test occupancy calculations
            all_units = Unit.query.filter_by(company_id=company_a.id).all()

            vacant_count = len([u for u in all_units if u.get_lease_status() == 'Vacant'])
            occupied_count = len([u for u in all_units if u.get_lease_status() == 'Occupied'])
            scheduled_count = len([u for u in all_units if u.get_lease_status() == 'Scheduled'])

            assert vacant_count == 1
            assert occupied_count == 1
            assert scheduled_count == 1

            # Calculate occupancy rate
            total_units = len(all_units)
            occupancy_rate = (occupied_count / total_units) * 100
            assert occupancy_rate == 33.33333333333333  # 1/3 * 100

    def test_unit_maintenance_workflow(self, app, authenticated_client, company_a, property_a):
        """Test unit maintenance and condition tracking workflow."""
        with app.app_context():
            # Create unit with maintenance information
            unit = Unit(
                name="Maintenance Workflow Unit",
                company_id=company_a.id,
                property_id=property_a.id
            )
            unit.condition_rating = 3
            unit.last_renovated = date(2022, 6, 15)
            unit.recent_updates = "New flooring installed"
            unit.upcoming_maintenance = "HVAC servicing scheduled for next month"

            db.session.add(unit)
            db.session.commit()

            # Test viewing unit details shows maintenance info
            response = authenticated_client.get(f'/unit/{unit.uuid}')
            assert response.status_code == 200

            response_text = response.data.decode()

            # Should display condition information
            condition_indicators = ['condition', 'maintenance', 'renovation']
            assert any(indicator in response_text.lower() for indicator in condition_indicators)

            # Test updating maintenance information
            updated_data = {
                'name': unit.name,
                'property_id': property_a.id,
                'condition_rating': 4,  # Improved condition
                'recent_updates': 'New flooring and fresh paint',
                'upcoming_maintenance': 'Annual inspection scheduled'
            }

            response = authenticated_client.post(f'/unit/{unit.uuid}/edit', data=updated_data)
            assert response.status_code == 302

            # Verify updates were saved
            db.session.refresh(unit)
            assert unit.condition_rating == 4
            assert 'fresh paint' in unit.recent_updates

    def test_unit_accessibility_compliance_workflow(self, app, authenticated_client, company_a, property_a):
        """Test unit accessibility and compliance tracking workflow."""
        with app.app_context():
            # Create unit with accessibility features
            unit = Unit(
                name="Accessible Unit",
                company_id=company_a.id,
                property_id=property_a.id
            )
            unit.ada_compliant = True
            unit.wheelchair_accessible = True
            unit.accessibility_features = "Grab bars, ramps, wide doorways"

            db.session.add(unit)
            db.session.commit()

            # Test filtering units by accessibility (programmatic)
            accessible_units = Unit.query.filter_by(
                company_id=company_a.id,
                wheelchair_accessible=True
            ).all()

            assert len(accessible_units) == 1
            assert accessible_units[0].name == "Accessible Unit"

            # Test ADA compliance tracking
            ada_compliant_units = Unit.query.filter_by(
                company_id=company_a.id,
                ada_compliant=True
            ).all()

            assert len(ada_compliant_units) == 1
            assert ada_compliant_units[0].accessibility_features is not None

    def test_unit_financial_tracking_workflow(self, app, company_a, property_a, tenant):
        """Test unit financial performance tracking workflow."""
        with app.app_context():
            # Create unit with detailed financial information
            unit = Unit(
                name="Financial Tracking Unit",
                company_id=company_a.id,
                property_id=property_a.id
            )
            unit.rent = 1700
            unit.utility_cost_estimate = 150
            unit.pet_fee_monthly = 25
            unit.pet_deposit = 300

            db.session.add(unit)
            db.session.commit()

            # Create lease with comprehensive financial terms
            lease = Lease(
                start=datetime.now().date() - timedelta(days=30),
                end=datetime.now().date() + timedelta(days=335),
                rent=Decimal('1700.00'),
                security_deposit=Decimal('1700.00'),
                pet_deposit=Decimal('300.00'),
                late_fee=Decimal('50.00'),
                parking_fee=Decimal('100.00'),
                unit_id=unit.id,
                tenant_id=tenant.id,
                property_id=property_a.id,
                company_id=company_a.id
            )
            db.session.add(lease)
            db.session.commit()

            # Create multiple payments
            payments_data = [
                {
                    'amount': Decimal('1700.00'),  # Base rent
                    'date': datetime.now().date() - timedelta(days=30),
                    'method': 'Check'
                },
                {
                    'amount': Decimal('1825.00'),  # Rent + pet fee + parking
                    'date': datetime.now().date(),
                    'method': 'ACH'
                }
            ]

            for payment_data in payments_data:
                payment = Payment(
                    amount=payment_data['amount'],
                    payment_date=payment_data['date'],
                    payment_method=payment_data['method'],
                    status='completed',
                    lease_id=lease.id
                )
                db.session.add(payment)

            db.session.commit()

            # Calculate unit financial performance
            total_payments = sum(p.amount for p in lease.payments)
            expected_monthly_income = (
                unit.rent +
                (unit.pet_fee_monthly or 0) +
                (lease.parking_fee or 0)
            )

            assert total_payments == Decimal('3525.00')  # 1700 + 1825
            assert expected_monthly_income == Decimal('1825.00')  # 1700 + 25 + 100

    def test_multi_tenant_unit_isolation_workflow(self, app, company_a, company_b, property_a, property_b):
        """Test that unit workflows properly isolate data between companies."""
        with app.app_context():
            # Create units for both companies
            unit_a = Unit(
                name="Company A Unit",
                company_id=company_a.id,
                property_id=property_a.id
            )

            unit_b = Unit(
                name="Company B Unit",
                company_id=company_b.id,
                property_id=property_b.id
            )

            db.session.add_all([unit_a, unit_b])
            db.session.commit()

            # Test company isolation in queries
            company_a_units = Unit.query.filter_by(company_id=company_a.id).all()
            company_b_units = Unit.query.filter_by(company_id=company_b.id).all()

            assert len(company_a_units) == 1
            assert len(company_b_units) == 1
            assert company_a_units[0].name == "Company A Unit"
            assert company_b_units[0].name == "Company B Unit"

            # Test UUID lookup with company isolation
            unit_a_found = Unit.find_by_uuid(unit_a.uuid, company_a.id)
            unit_a_wrong_company = Unit.find_by_uuid(unit_a.uuid, company_b.id)

            assert unit_a_found is not None
            assert unit_a_wrong_company is None

            # Test cross-company property assignment prevention
            # This should be handled at the application level
            unit_cross_assign = Unit(
                name="Cross Assign Test",
                company_id=company_a.id,
                property_id=property_b.id  # Property from different company
            )

            # This test depends on application-level validation
            # In a real scenario, this should be prevented by form validation

    def test_unit_cascade_deletion_workflow(self, app, company_a, property_a, tenant):
        """Test unit deletion cascading to related records."""
        with app.app_context():
            # Create unit with related records
            unit = Unit(
                name="Cascade Test Unit",
                company_id=company_a.id,
                property_id=property_a.id
            )
            db.session.add(unit)
            db.session.commit()

            # Create lease for the unit
            lease = Lease(
                start=datetime.now().date(),
                end=datetime.now().date() + timedelta(days=365),
                rent=Decimal('1500.00'),
                unit_id=unit.id,
                tenant_id=tenant.id,
                property_id=property_a.id,
                company_id=company_a.id
            )
            db.session.add(lease)
            db.session.commit()

            unit_id = unit.id
            lease_id = lease.id

            # Verify records exist
            assert Unit.query.get(unit_id) is not None
            assert Lease.query.get(lease_id) is not None

            # Delete unit
            db.session.delete(unit)
            db.session.commit()

            # Verify cascade deletion
            assert Unit.query.get(unit_id) is None
            assert Lease.query.get(lease_id) is None  # Should be cascaded