"""
Unit tests for Unit forms functionality.

Tests the UnitForm validation, field constraints, choices,
and form rendering behavior.
"""

import pytest
from datetime import date
from website.unit.forms import UnitForm
from website.models import Property


@pytest.mark.unit
class TestUnitForm:
    """Test UnitForm validation and functionality."""

    def test_unit_form_required_fields(self, app):
        """Test that required fields are validated."""
        with app.app_context():
            form = UnitForm()

            # Property ID is required
            form.property_id.choices = [(1, 'Test Property')]

            # Test with empty required fields
            form.name.data = ""
            form.property_id.data = None

            assert not form.validate()

            # Name is required
            assert any('required' in str(error).lower() for error in form.name.errors)

            # Property is required
            assert any('required' in str(error).lower() for error in form.property_id.errors)

    def test_unit_form_valid_data(self, app, property_a):
        """Test form validation with valid data."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]

            # Set valid data
            form.name.data = "Unit 101"
            form.property_id.data = property_a.id
            form.bedrooms.data = 2
            form.bathrooms.data = 1
            form.sqft.data = 850
            form.rent.data = 1200

            assert form.validate()

    def test_unit_form_basic_fields_validation(self, app, property_a):
        """Test validation of basic unit information fields."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Test Unit"

            # Test valid ranges
            form.bedrooms.data = 3
            form.bathrooms.data = 2
            form.sqft.data = 1200
            form.rent.data = 1500

            assert form.validate()

            # Test invalid ranges
            form.bedrooms.data = -1  # Should be >= 0
            assert not form.validate()
            assert any('range' in str(error).lower() for error in form.bedrooms.errors)

    def test_unit_form_numeric_field_ranges(self, app, property_a):
        """Test numeric field range validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Range Test Unit"

            # Test bedrooms range (0-20)
            form.bedrooms.data = 25  # Too high
            assert not form.validate()

            form.bedrooms.data = 5  # Valid
            assert form.bedrooms.validate(form)

            # Test bathrooms range (0-10)
            form.bathrooms.data = 15  # Too high
            assert not form.validate()

            form.bathrooms.data = 3  # Valid
            assert form.bathrooms.validate(form)

            # Test square feet range (1-10000)
            form.sqft.data = 15000  # Too high
            assert not form.validate()

            form.sqft.data = 1200  # Valid
            assert form.sqft.validate(form)

            # Test rent range (>= 0)
            form.rent.data = -100  # Negative not allowed
            assert not form.validate()

            form.rent.data = 1500  # Valid
            assert form.rent.validate(form)

    def test_unit_form_hvac_climate_choices(self, app, property_a):
        """Test HVAC and climate field choices."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "HVAC Test Unit"

            # Test heating type choices
            valid_heating_types = ['gas', 'electric', 'heat_pump', 'radiant', 'baseboard', 'forced_air', 'other']
            for heating_type in valid_heating_types:
                form.heating_type.data = heating_type
                assert form.heating_type.validate(form)

            # Test thermostat type choices
            valid_thermostat_types = ['manual', 'programmable', 'smart']
            for thermostat_type in valid_thermostat_types:
                form.thermostat_type.data = thermostat_type
                assert form.thermostat_type.validate(form)

    def test_unit_form_appliances_fields(self, app, property_a):
        """Test appliance and kitchen field validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Appliances Test Unit"

            # Test washer/dryer choices
            valid_washer_dryer_options = ['in_unit', 'hookups', 'shared', 'none']
            for option in valid_washer_dryer_options:
                form.washer_dryer.data = option
                assert form.washer_dryer.validate(form)

            # Test boolean appliance fields
            form.dishwasher.data = True
            form.garbage_disposal.data = False
            form.microwave.data = True
            form.refrigerator.data = True
            form.range_oven.data = False

            assert form.validate()

    def test_unit_form_flooring_interior_fields(self, app, property_a):
        """Test flooring and interior field validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Interior Test Unit"

            # Test ceiling height range (6-20 feet)
            form.ceiling_height.data = 25  # Too high
            assert not form.validate()

            form.ceiling_height.data = 9  # Valid
            assert form.ceiling_height.validate(form)

            # Test window type choices
            valid_window_types = ['single_pane', 'double_pane', 'triple_pane', 'energy_efficient']
            for window_type in valid_window_types:
                form.windows_type.data = window_type
                assert form.windows_type.validate(form)

            # Test natural light choices
            valid_light_levels = ['excellent', 'good', 'fair', 'limited']
            for light_level in valid_light_levels:
                form.natural_light.data = light_level
                assert form.natural_light.validate(form)

    def test_unit_form_storage_space_fields(self, app, property_a):
        """Test storage and space field validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Storage Test Unit"

            # Test closet space choices
            valid_closet_space_options = ['excellent', 'good', 'limited']
            for option in valid_closet_space_options:
                form.closet_space.data = option
                assert form.closet_space.validate(form)

            # Test storage units range (>= 0)
            form.storage_units.data = -1  # Invalid
            assert not form.validate()

            form.storage_units.data = 2  # Valid
            assert form.storage_units.validate(form)

            # Test balcony square feet range (>= 1)
            form.balcony_sqft.data = 0  # Invalid (must be >= 1 if provided)
            assert not form.validate()

            form.balcony_sqft.data = 50  # Valid
            assert form.balcony_sqft.validate(form)

    def test_unit_form_parking_access_fields(self, app, property_a):
        """Test parking and access field validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Parking Test Unit"

            # Test parking type choices
            valid_parking_types = ['garage', 'covered', 'open', 'street', 'none']
            for parking_type in valid_parking_types:
                form.parking_type.data = parking_type
                assert form.parking_type.validate(form)

            # Test garage type choices
            valid_garage_types = ['attached', 'detached', 'carport', 'none']
            for garage_type in valid_garage_types:
                form.garage_type.data = garage_type
                assert form.garage_type.validate(form)

            # Test parking spaces range (>= 0)
            form.parking_spaces.data = -1  # Invalid
            assert not form.validate()

            form.parking_spaces.data = 1  # Valid
            assert form.parking_spaces.validate(form)

    def test_unit_form_bathroom_fields(self, app, property_a):
        """Test bathroom feature field validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Bathroom Test Unit"

            # Test shower type choices
            valid_shower_types = ['standup', 'combo', 'walk_in']
            for shower_type in valid_shower_types:
                form.shower_type.data = shower_type
                assert form.shower_type.validate(form)

            # Test boolean bathroom fields
            form.master_bath.data = True
            form.bathtub.data = False

            assert form.validate()

    def test_unit_form_condition_maintenance_fields(self, app, property_a):
        """Test condition and maintenance field validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Condition Test Unit"

            # Test last renovated date
            form.last_renovated.data = date(2023, 6, 15)
            assert form.last_renovated.validate(form)

            # Test condition rating choices (1-5)
            valid_ratings = [1, 2, 3, 4, 5]
            for rating in valid_ratings:
                form.condition_rating.data = rating
                assert form.condition_rating.validate(form)

    def test_unit_form_accessibility_fields(self, app, property_a):
        """Test accessibility and compliance field validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Accessibility Test Unit"

            # Test boolean accessibility fields
            form.ada_compliant.data = True
            form.wheelchair_accessible.data = True

            assert form.validate()

    def test_unit_form_utilities_energy_fields(self, app, property_a):
        """Test utilities and energy field validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Utilities Test Unit"

            # Test utility cost estimate range (>= 0)
            form.utility_cost_estimate.data = -50  # Invalid
            assert not form.validate()

            form.utility_cost_estimate.data = 150  # Valid
            assert form.utility_cost_estimate.validate(form)

    def test_unit_form_pet_policy_fields(self, app, property_a):
        """Test pet policy field validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Pet Policy Test Unit"

            # Test pet fee ranges (>= 0)
            form.pet_fee_monthly.data = -10  # Invalid
            assert not form.validate()

            form.pet_fee_monthly.data = 25  # Valid
            assert form.pet_fee_monthly.validate(form)

            form.pet_deposit.data = -100  # Invalid
            assert not form.validate()

            form.pet_deposit.data = 200  # Valid
            assert form.pet_deposit.validate(form)

    def test_unit_form_security_fields(self, app, property_a):
        """Test security feature field validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Security Test Unit"

            # Test boolean security fields
            form.alarm_system.data = True
            form.secure_entry.data = False

            assert form.validate()

    def test_unit_form_technology_fields(self, app, property_a):
        """Test technology and internet field validation."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Technology Test Unit"

            # Test boolean technology fields
            form.internet_included.data = True
            form.cable_ready.data = True

            assert form.validate()

    def test_unit_form_optional_fields(self, app, property_a):
        """Test that optional fields can be left empty."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]

            # Set only required fields
            form.name.data = "Minimal Unit"
            form.property_id.data = property_a.id

            # Leave all optional fields empty/default
            assert form.validate()

    def test_unit_form_text_field_placeholders(self, app):
        """Test that text fields have appropriate placeholders."""
        with app.app_context():
            form = UnitForm()

            # Check that key fields have helpful placeholders
            assert form.name.render_kw.get('placeholder') is not None
            assert 'e.g.' in form.name.render_kw['placeholder']

            assert form.description.render_kw.get('placeholder') is not None
            assert form.appliances_included.render_kw.get('placeholder') is not None
            assert form.flooring_type.render_kw.get('placeholder') is not None

    def test_unit_form_textarea_rows(self, app):
        """Test that textarea fields have appropriate row counts."""
        with app.app_context():
            form = UnitForm()

            # Check that textarea fields have row specifications for better UX
            textarea_fields = [
                'description', 'appliances_included', 'flooring_type',
                'bathroom_features', 'recent_updates', 'upcoming_maintenance',
                'accessibility_features', 'utilities_included', 'pet_restrictions',
                'security_features', 'smart_home_features'
            ]

            for field_name in textarea_fields:
                field = getattr(form, field_name)
                assert field.render_kw.get('rows') is not None
                assert int(field.render_kw['rows']) >= 2

    def test_unit_form_coercion_functions(self, app, property_a):
        """Test field data type coercion."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]

            # Test property_id coercion to int
            form.property_id.data = str(property_a.id)  # String input
            form.name.data = "Coercion Test"

            assert form.validate()
            assert isinstance(form.property_id.data, int)

            # Test condition_rating coercion
            form.condition_rating.data = "3"  # String input
            assert form.condition_rating.validate(form)

    def test_unit_form_field_counts(self, app):
        """Test that form has expected number of fields."""
        with app.app_context():
            form = UnitForm()

            # Count of major field categories (approximate, may change with updates)
            field_names = [field.name for field in form]

            # Should have 50+ fields for comprehensive unit details
            assert len(field_names) >= 50

            # Check presence of key field categories
            hvac_fields = [name for name in field_names if 'heating' in name or 'air_conditioning' in name or 'thermostat' in name]
            assert len(hvac_fields) >= 3

            appliance_fields = [name for name in field_names if any(appliance in name for appliance in ['dishwasher', 'microwave', 'refrigerator', 'range'])]
            assert len(appliance_fields) >= 4

            accessibility_fields = [name for name in field_names if 'ada' in name or 'wheelchair' in name or 'accessibility' in name]
            assert len(accessibility_fields) >= 3

    def test_unit_form_comprehensive_validation(self, app, property_a):
        """Test comprehensive form validation with all field types."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]

            # Set comprehensive valid data
            form.name.data = "Comprehensive Test Unit"
            form.property_id.data = property_a.id
            form.bedrooms.data = 2
            form.bathrooms.data = 2
            form.sqft.data = 1200
            form.rent.data = 1800
            form.description.data = "Luxury 2-bedroom apartment"

            # HVAC & Climate
            form.air_conditioning.data = True
            form.heating_type.data = "heat_pump"
            form.thermostat_type.data = "smart"

            # Appliances
            form.dishwasher.data = True
            form.refrigerator.data = True
            form.washer_dryer.data = "in_unit"

            # Interior
            form.ceiling_height.data = 9
            form.windows_type.data = "double_pane"
            form.natural_light.data = "excellent"

            # Storage & Space
            form.closet_space.data = "good"
            form.balcony_patio.data = True
            form.balcony_sqft.data = 60

            # Parking
            form.parking_type.data = "garage"
            form.parking_spaces.data = 1

            # Bathroom
            form.master_bath.data = True
            form.shower_type.data = "walk_in"

            # Condition
            form.condition_rating.data = 4
            form.last_renovated.data = date(2023, 1, 1)

            # Accessibility
            form.ada_compliant.data = False
            form.wheelchair_accessible.data = False

            # Utilities
            form.utility_cost_estimate.data = 120

            # Pet Policy
            form.pets_allowed.data = True
            form.pet_fee_monthly.data = 30
            form.pet_deposit.data = 250

            # Security
            form.alarm_system.data = True
            form.secure_entry.data = True

            # Technology
            form.internet_included.data = True
            form.cable_ready.data = True

            assert form.validate()

    def test_unit_form_edge_cases(self, app, property_a):
        """Test form validation edge cases."""
        with app.app_context():
            form = UnitForm()
            form.property_id.choices = [(property_a.id, property_a.name)]
            form.property_id.data = property_a.id
            form.name.data = "Edge Case Unit"

            # Test zero values where allowed
            form.bedrooms.data = 0  # Studio apartment
            form.bathrooms.data = 0  # Unusual but possible
            form.storage_units.data = 0
            form.parking_spaces.data = 0
            form.pet_fee_monthly.data = 0
            form.pet_deposit.data = 0
            form.utility_cost_estimate.data = 0

            assert form.validate()

            # Test maximum values
            form.bedrooms.data = 20  # Maximum allowed
            form.bathrooms.data = 10  # Maximum allowed
            form.sqft.data = 10000  # Maximum allowed
            form.ceiling_height.data = 20  # Maximum allowed

            assert form.validate()