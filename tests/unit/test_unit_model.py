"""
Unit tests for Unit model functionality.

Tests the Unit model including field validation, relationships,
business logic methods, and multi-tenant isolation.
"""

import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from website import db
from website.models import Unit, Property, Company, Portfolio, Lease, Tenant


@pytest.mark.unit
class TestUnitModel:
    """Test Unit model functionality."""

    def test_unit_creation_with_required_fields(self, app, company_a):
        """Test creating a unit with minimum required fields."""
        with app.app_context():
            unit = Unit(
                name="Test Unit 101",
                company_id=company_a.id
            )
            db.session.add(unit)
            db.session.commit()

            assert unit.id is not None
            assert unit.uuid is not None
            assert len(unit.uuid) == 36  # UUID4 format
            assert unit.name == "Test Unit 101"
            assert unit.company_id == company_a.id

    def test_unit_creation_with_property(self, app, company_a, property_a):
        """Test creating a unit associated with a property."""
        with app.app_context():
            unit = Unit(
                name="Apt 202",
                company_id=company_a.id,
                property_id=property_a.id
            )
            db.session.add(unit)
            db.session.commit()

            assert unit.property_id == property_a.id
            assert unit.property == property_a

    def test_unit_basic_fields(self, app, company_a, property_a):
        """Test unit basic information fields."""
        with app.app_context():
            unit = Unit(
                name="Unit A1",
                company_id=company_a.id,
                property_id=property_a.id
            )

            # Set basic fields
            unit.bedrooms = 2
            unit.bathrooms = 1
            unit.sqft = 850
            unit.rent = 1200
            unit.description = "Cozy 2-bedroom apartment with modern amenities"

            db.session.add(unit)
            db.session.commit()

            assert unit.bedrooms == 2
            assert unit.bathrooms == 1
            assert unit.sqft == 850
            assert unit.rent == 1200
            assert unit.description == "Cozy 2-bedroom apartment with modern amenities"

    def test_unit_hvac_climate_fields(self, app, company_a):
        """Test HVAC and climate related fields."""
        with app.app_context():
            unit = Unit(name="HVAC Test Unit", company_id=company_a.id)

            unit.air_conditioning = True
            unit.heating_type = "heat_pump"
            unit.thermostat_type = "smart"

            db.session.add(unit)
            db.session.commit()

            assert unit.air_conditioning is True
            assert unit.heating_type == "heat_pump"
            assert unit.thermostat_type == "smart"

    def test_unit_appliances_fields(self, app, company_a):
        """Test appliance and kitchen related fields."""
        with app.app_context():
            unit = Unit(name="Appliance Test Unit", company_id=company_a.id)

            unit.appliances_included = "Refrigerator, Range, Dishwasher"
            unit.dishwasher = True
            unit.garbage_disposal = True
            unit.microwave = False
            unit.refrigerator = True
            unit.range_oven = True
            unit.washer_dryer = "in_unit"

            db.session.add(unit)
            db.session.commit()

            assert unit.appliances_included == "Refrigerator, Range, Dishwasher"
            assert unit.dishwasher is True
            assert unit.garbage_disposal is True
            assert unit.microwave is False
            assert unit.refrigerator is True
            assert unit.range_oven is True
            assert unit.washer_dryer == "in_unit"

    def test_unit_flooring_interior_fields(self, app, company_a):
        """Test flooring and interior design fields."""
        with app.app_context():
            unit = Unit(name="Interior Test Unit", company_id=company_a.id)

            unit.flooring_type = "Hardwood in living areas, carpet in bedrooms"
            unit.ceiling_height = 9
            unit.windows_type = "double_pane"
            unit.natural_light = "excellent"

            db.session.add(unit)
            db.session.commit()

            assert unit.flooring_type == "Hardwood in living areas, carpet in bedrooms"
            assert unit.ceiling_height == 9
            assert unit.windows_type == "double_pane"
            assert unit.natural_light == "excellent"

    def test_unit_storage_space_fields(self, app, company_a):
        """Test storage and space related fields."""
        with app.app_context():
            unit = Unit(name="Storage Test Unit", company_id=company_a.id)

            unit.closet_space = "excellent"
            unit.storage_units = 1
            unit.balcony_patio = True
            unit.balcony_sqft = 80

            db.session.add(unit)
            db.session.commit()

            assert unit.closet_space == "excellent"
            assert unit.storage_units == 1
            assert unit.balcony_patio is True
            assert unit.balcony_sqft == 80

    def test_unit_parking_access_fields(self, app, company_a):
        """Test parking and access related fields."""
        with app.app_context():
            unit = Unit(name="Parking Test Unit", company_id=company_a.id)

            unit.parking_type = "garage"
            unit.parking_spaces = 2
            unit.garage_type = "attached"

            db.session.add(unit)
            db.session.commit()

            assert unit.parking_type == "garage"
            assert unit.parking_spaces == 2
            assert unit.garage_type == "attached"

    def test_unit_bathroom_fields(self, app, company_a):
        """Test bathroom related fields."""
        with app.app_context():
            unit = Unit(name="Bathroom Test Unit", company_id=company_a.id)

            unit.bathroom_features = "Double vanity, jetted tub"
            unit.master_bath = True
            unit.bathtub = True
            unit.shower_type = "walk_in"

            db.session.add(unit)
            db.session.commit()

            assert unit.bathroom_features == "Double vanity, jetted tub"
            assert unit.master_bath is True
            assert unit.bathtub is True
            assert unit.shower_type == "walk_in"

    def test_unit_condition_maintenance_fields(self, app, company_a):
        """Test condition and maintenance related fields."""
        with app.app_context():
            unit = Unit(name="Maintenance Test Unit", company_id=company_a.id)

            unit.last_renovated = date(2023, 6, 15)
            unit.condition_rating = 4
            unit.recent_updates = "New flooring installed"
            unit.upcoming_maintenance = "HVAC servicing scheduled"

            db.session.add(unit)
            db.session.commit()

            assert unit.last_renovated == date(2023, 6, 15)
            assert unit.condition_rating == 4
            assert unit.recent_updates == "New flooring installed"
            assert unit.upcoming_maintenance == "HVAC servicing scheduled"

    def test_unit_accessibility_fields(self, app, company_a):
        """Test accessibility and compliance fields."""
        with app.app_context():
            unit = Unit(name="Accessibility Test Unit", company_id=company_a.id)

            unit.ada_compliant = True
            unit.wheelchair_accessible = True
            unit.accessibility_features = "Grab bars, ramps, wide doorways"

            db.session.add(unit)
            db.session.commit()

            assert unit.ada_compliant is True
            assert unit.wheelchair_accessible is True
            assert unit.accessibility_features == "Grab bars, ramps, wide doorways"

    def test_unit_utilities_energy_fields(self, app, company_a):
        """Test utilities and energy related fields."""
        with app.app_context():
            unit = Unit(name="Utilities Test Unit", company_id=company_a.id)

            unit.utilities_included = "Water, sewer, electric"
            unit.utility_cost_estimate = 150
            unit.energy_efficiency_rating = "A+"

            db.session.add(unit)
            db.session.commit()

            assert unit.utilities_included == "Water, sewer, electric"
            assert unit.utility_cost_estimate == 150
            assert unit.energy_efficiency_rating == "A+"

    def test_unit_pet_policy_fields(self, app, company_a):
        """Test pet policy related fields."""
        with app.app_context():
            unit = Unit(name="Pet Policy Test Unit", company_id=company_a.id)

            unit.pets_allowed = True
            unit.pet_restrictions = "Dogs under 50lbs, no aggressive breeds"
            unit.pet_fee_monthly = 25
            unit.pet_deposit = 200

            db.session.add(unit)
            db.session.commit()

            assert unit.pets_allowed is True
            assert unit.pet_restrictions == "Dogs under 50lbs, no aggressive breeds"
            assert unit.pet_fee_monthly == 25
            assert unit.pet_deposit == 200

    def test_unit_security_fields(self, app, company_a):
        """Test security related fields."""
        with app.app_context():
            unit = Unit(name="Security Test Unit", company_id=company_a.id)

            unit.security_features = "Security system, cameras"
            unit.alarm_system = True
            unit.secure_entry = True

            db.session.add(unit)
            db.session.commit()

            assert unit.security_features == "Security system, cameras"
            assert unit.alarm_system is True
            assert unit.secure_entry is True

    def test_unit_technology_fields(self, app, company_a):
        """Test technology and internet related fields."""
        with app.app_context():
            unit = Unit(name="Technology Test Unit", company_id=company_a.id)

            unit.internet_included = True
            unit.cable_ready = True
            unit.internet_speed = "100 Mbps"
            unit.smart_home_features = "Smart locks, thermostat"

            db.session.add(unit)
            db.session.commit()

            assert unit.internet_included is True
            assert unit.cable_ready is True
            assert unit.internet_speed == "100 Mbps"
            assert unit.smart_home_features == "Smart locks, thermostat"

    def test_unit_lease_status_vacant(self, app, company_a):
        """Test lease status for vacant unit."""
        with app.app_context():
            unit = Unit(name="Vacant Unit", company_id=company_a.id)
            db.session.add(unit)
            db.session.commit()

            status = unit.get_lease_status()
            assert status == 'Vacant'

    def test_unit_lease_status_occupied(self, app, company_a, unit, tenant, active_lease):
        """Test lease status for occupied unit."""
        with app.app_context():
            status = unit.get_lease_status()
            assert status == 'Occupied'

    def test_unit_lease_status_scheduled(self, app, company_a, property_a, tenant):
        """Test lease status for unit with future lease."""
        with app.app_context():
            unit = Unit(name="Future Lease Unit", company_id=company_a.id, property_id=property_a.id)
            db.session.add(unit)
            db.session.commit()

            # Create a future lease
            future_start = datetime.now().date() + timedelta(days=30)
            future_end = future_start + timedelta(days=365)

            future_lease = Lease(
                start=future_start,
                end=future_end,
                rent=Decimal('1400.00'),
                unit_id=unit.id,
                tenant_id=tenant.id,
                property_id=property_a.id,
                company_id=company_a.id
            )
            db.session.add(future_lease)
            db.session.commit()

            status = unit.get_lease_status()
            assert status == 'Scheduled'

    def test_unit_get_current_lease(self, app, unit, active_lease):
        """Test getting current active lease."""
        with app.app_context():
            current_lease = unit.get_current_lease()
            assert current_lease is not None
            assert current_lease.id == active_lease.id

    def test_unit_get_current_lease_none(self, app, company_a):
        """Test getting current lease when none exists."""
        with app.app_context():
            unit = Unit(name="No Lease Unit", company_id=company_a.id)
            db.session.add(unit)
            db.session.commit()

            current_lease = unit.get_current_lease()
            assert current_lease is None

    def test_unit_get_current_tenant(self, app, unit, tenant, active_lease):
        """Test getting current tenant through active lease."""
        with app.app_context():
            current_tenant = unit.get_current_tenant()
            assert current_tenant is not None
            assert current_tenant.id == tenant.id

    def test_unit_get_current_tenant_none(self, app, company_a):
        """Test getting current tenant when none exists."""
        with app.app_context():
            unit = Unit(name="No Tenant Unit", company_id=company_a.id)
            db.session.add(unit)
            db.session.commit()

            current_tenant = unit.get_current_tenant()
            assert current_tenant is None

    def test_unit_get_next_lease(self, app, company_a, property_a, tenant):
        """Test getting next upcoming lease."""
        with app.app_context():
            unit = Unit(name="Next Lease Unit", company_id=company_a.id, property_id=property_a.id)
            db.session.add(unit)
            db.session.commit()

            # Create a future lease
            future_start = datetime.now().date() + timedelta(days=30)
            future_end = future_start + timedelta(days=365)

            future_lease = Lease(
                start=future_start,
                end=future_end,
                rent=Decimal('1500.00'),
                unit_id=unit.id,
                tenant_id=tenant.id,
                property_id=property_a.id,
                company_id=company_a.id
            )
            db.session.add(future_lease)
            db.session.commit()

            next_lease = unit.get_next_lease()
            assert next_lease is not None
            assert next_lease.id == future_lease.id

    def test_unit_find_by_uuid(self, app, company_a):
        """Test finding unit by UUID."""
        with app.app_context():
            unit = Unit(name="UUID Test Unit", company_id=company_a.id)
            db.session.add(unit)
            db.session.commit()

            found_unit = Unit.find_by_uuid(unit.uuid, company_a.id)
            assert found_unit is not None
            assert found_unit.id == unit.id

    def test_unit_find_by_uuid_wrong_company(self, app, company_a, company_b):
        """Test that UUID lookup respects company isolation."""
        with app.app_context():
            unit = Unit(name="Company A Unit", company_id=company_a.id)
            db.session.add(unit)
            db.session.commit()

            # Try to find with wrong company ID
            found_unit = Unit.find_by_uuid(unit.uuid, company_b.id)
            assert found_unit is None

    def test_unit_find_by_uuid_no_company_filter(self, app, company_a):
        """Test finding unit by UUID without company filter."""
        with app.app_context():
            unit = Unit(name="No Filter Test Unit", company_id=company_a.id)
            db.session.add(unit)
            db.session.commit()

            found_unit = Unit.find_by_uuid(unit.uuid)
            assert found_unit is not None
            assert found_unit.id == unit.id

    def test_unit_company_isolation(self, app, company_a, company_b):
        """Test that units are properly isolated by company."""
        with app.app_context():
            # Create units for different companies
            unit_a = Unit(name="Company A Unit", company_id=company_a.id)
            unit_b = Unit(name="Company B Unit", company_id=company_b.id)

            db.session.add_all([unit_a, unit_b])
            db.session.commit()

            # Query units for company A
            company_a_units = Unit.query.filter_by(company_id=company_a.id).all()
            assert len(company_a_units) == 1
            assert company_a_units[0].id == unit_a.id

            # Query units for company B
            company_b_units = Unit.query.filter_by(company_id=company_b.id).all()
            assert len(company_b_units) == 1
            assert company_b_units[0].id == unit_b.id

    def test_unit_property_relationship(self, app, company_a, property_a):
        """Test unit-property relationship."""
        with app.app_context():
            unit = Unit(name="Property Relation Unit", company_id=company_a.id, property_id=property_a.id)
            db.session.add(unit)
            db.session.commit()

            # Test forward relationship
            assert unit.property is not None
            assert unit.property.id == property_a.id

            # Test backward relationship
            assert unit in property_a.units

    def test_unit_lease_relationship_cascade_delete(self, app, company_a, unit, tenant, active_lease):
        """Test that deleting unit cascades to leases."""
        with app.app_context():
            unit_id = unit.id
            lease_id = active_lease.id

            # Verify lease exists
            lease = Lease.query.get(lease_id)
            assert lease is not None

            # Delete unit
            db.session.delete(unit)
            db.session.commit()

            # Verify lease was also deleted (cascade)
            lease = Lease.query.get(lease_id)
            assert lease is None

    def test_unit_defaults(self, app, company_a):
        """Test default values for unit fields."""
        with app.app_context():
            unit = Unit(name="Defaults Test Unit", company_id=company_a.id)
            db.session.add(unit)
            db.session.commit()

            # Test boolean defaults
            assert unit.air_conditioning is False
            assert unit.dishwasher is False
            assert unit.garbage_disposal is False
            assert unit.microwave is False
            assert unit.refrigerator is False
            assert unit.range_oven is False
            assert unit.balcony_patio is False
            assert unit.master_bath is False
            assert unit.bathtub is False
            assert unit.ada_compliant is False
            assert unit.wheelchair_accessible is False
            assert unit.pets_allowed is False
            assert unit.alarm_system is False
            assert unit.secure_entry is False
            assert unit.internet_included is False
            assert unit.cable_ready is False

            # Test integer defaults
            assert unit.storage_units == 0
            assert unit.parking_spaces == 0
            assert unit.pet_fee_monthly == 0
            assert unit.pet_deposit == 0

    def test_unit_str_representation(self, app, company_a, property_a):
        """Test unit string representation."""
        with app.app_context():
            unit = Unit(name="Unit 301", company_id=company_a.id, property_id=property_a.id)
            db.session.add(unit)
            db.session.commit()

            # The model should have a meaningful string representation
            str_repr = str(unit)
            assert "Unit 301" in str_repr