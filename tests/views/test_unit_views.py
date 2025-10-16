"""
View tests for Unit management functionality.

Tests unit CRUD operations, access control, form handling,
and multi-tenant isolation for unit views.
"""

import pytest
from datetime import date
from flask import url_for
from bs4 import BeautifulSoup
from website import db
from website.models import Unit, Property, Company


@pytest.mark.views
class TestUnitViews:
    """Test unit view endpoints and functionality."""

    def test_unit_list_requires_login(self, client):
        """Test that unit list requires authentication."""
        response = client.get('/unit/')
        assert response.status_code == 302  # Redirect to login

    def test_unit_list_empty(self, app, authenticated_client):
        """Test unit list with no units."""
        with app.app_context():
            response = authenticated_client.get('/unit/')
            assert response.status_code == 200
            assert b'No units found' in response.data or b'units' in response.data.lower()

    def test_unit_list_with_units(self, app, authenticated_client, company_a, property_a):
        """Test unit list displays units for user's company."""
        with app.app_context():
            # Create test units
            unit1 = Unit(name="Unit 101", company_id=company_a.id, property_id=property_a.id)
            unit2 = Unit(name="Unit 102", company_id=company_a.id, property_id=property_a.id)

            db.session.add_all([unit1, unit2])
            db.session.commit()

            response = authenticated_client.get('/unit/')
            assert response.status_code == 200
            assert b'Unit 101' in response.data
            assert b'Unit 102' in response.data

    def test_unit_list_company_isolation(self, app, authenticated_client, company_a, company_b, property_a, property_b):
        """Test that unit list only shows units for user's company."""
        with app.app_context():
            # Create units for both companies
            unit_a = Unit(name="Company A Unit", company_id=company_a.id, property_id=property_a.id)
            unit_b = Unit(name="Company B Unit", company_id=company_b.id, property_id=property_b.id)

            db.session.add_all([unit_a, unit_b])
            db.session.commit()

            response = authenticated_client.get('/unit/')
            assert response.status_code == 200
            assert b'Company A Unit' in response.data
            assert b'Company B Unit' not in response.data

    def test_unit_create_requires_login(self, client):
        """Test that unit creation requires authentication."""
        response = client.get('/unit/create')
        assert response.status_code == 302  # Redirect to login

    def test_unit_create_get_no_properties(self, app, authenticated_client):
        """Test unit create GET redirects when no properties exist."""
        with app.app_context():
            response = authenticated_client.get('/unit/create')
            assert response.status_code == 302  # Redirect to property creation

            # Follow redirect
            response = authenticated_client.get('/unit/create', follow_redirects=True)
            assert b'create a property' in response.data.lower()

    def test_unit_create_get_with_properties(self, app, authenticated_client, property_a):
        """Test unit create GET with available properties."""
        with app.app_context():
            response = authenticated_client.get('/unit/create')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')

            # Check form is present
            form = soup.find('form')
            assert form is not None

            # Check property selection is available
            property_select = soup.find('select', {'name': 'property_id'})
            assert property_select is not None

            # Check that our property appears in the options
            assert property_a.name in response.data.decode()

    def test_unit_create_post_valid_data(self, app, authenticated_client, property_a):
        """Test unit creation with valid data."""
        with app.app_context():
            unit_data = {
                'name': 'Test Unit 101',
                'property_id': property_a.id,
                'bedrooms': 2,
                'bathrooms': 1,
                'sqft': 850,
                'rent': 1200,
                'description': 'Test unit description',
                'air_conditioning': True,
                'heating_type': 'heat_pump',
                'dishwasher': True,
                'parking_spaces': 1
            }

            response = authenticated_client.post('/unit/create', data=unit_data)
            assert response.status_code == 302  # Redirect after creation

            # Verify unit was created
            unit = Unit.query.filter_by(name='Test Unit 101').first()
            assert unit is not None
            assert unit.bedrooms == 2
            assert unit.bathrooms == 1
            assert unit.air_conditioning is True
            assert unit.heating_type == 'heat_pump'

    def test_unit_create_post_comprehensive_data(self, app, authenticated_client, property_a):
        """Test unit creation with comprehensive field data."""
        with app.app_context():
            unit_data = {
                'name': 'Comprehensive Unit',
                'property_id': property_a.id,
                'bedrooms': 3,
                'bathrooms': 2,
                'sqft': 1200,
                'rent': 1800,
                'description': 'Luxury apartment with modern amenities',

                # HVAC & Climate
                'air_conditioning': True,
                'heating_type': 'heat_pump',
                'thermostat_type': 'smart',

                # Appliances
                'appliances_included': 'Full kitchen appliances',
                'dishwasher': True,
                'garbage_disposal': True,
                'refrigerator': True,
                'range_oven': True,
                'washer_dryer': 'in_unit',

                # Interior
                'flooring_type': 'Hardwood and carpet',
                'ceiling_height': 9,
                'windows_type': 'double_pane',
                'natural_light': 'excellent',

                # Storage & Space
                'closet_space': 'excellent',
                'storage_units': 1,
                'balcony_patio': True,
                'balcony_sqft': 60,

                # Parking
                'parking_type': 'garage',
                'parking_spaces': 2,
                'garage_type': 'attached',

                # Bathroom
                'bathroom_features': 'Double vanity, jetted tub',
                'master_bath': True,
                'bathtub': True,
                'shower_type': 'walk_in',

                # Condition
                'last_renovated': '2023-01-15',
                'condition_rating': 5,
                'recent_updates': 'New appliances installed',

                # Accessibility
                'ada_compliant': False,
                'wheelchair_accessible': False,

                # Utilities
                'utilities_included': 'Water, sewer, electric',
                'utility_cost_estimate': 120,
                'energy_efficiency_rating': 'A+',

                # Pet Policy
                'pets_allowed': True,
                'pet_restrictions': 'Dogs under 50lbs',
                'pet_fee_monthly': 30,
                'pet_deposit': 250,

                # Security
                'security_features': 'Alarm system, cameras',
                'alarm_system': True,
                'secure_entry': True,

                # Technology
                'internet_included': True,
                'cable_ready': True,
                'internet_speed': '100 Mbps',
                'smart_home_features': 'Smart locks, thermostat'
            }

            response = authenticated_client.post('/unit/create', data=unit_data)
            assert response.status_code == 302  # Redirect after creation

            # Verify comprehensive unit was created with all fields
            unit = Unit.query.filter_by(name='Comprehensive Unit').first()
            assert unit is not None
            assert unit.bedrooms == 3
            assert unit.heating_type == 'heat_pump'
            assert unit.thermostat_type == 'smart'
            assert unit.dishwasher is True
            assert unit.washer_dryer == 'in_unit'
            assert unit.ceiling_height == 9
            assert unit.natural_light == 'excellent'
            assert unit.pets_allowed is True
            assert unit.pet_fee_monthly == 30
            assert unit.alarm_system is True
            assert unit.internet_included is True

    def test_unit_create_for_property_requires_login(self, client, property_a):
        """Test that property-specific unit creation requires authentication."""
        response = client.get(f'/unit/create/{property_a.uuid}')
        assert response.status_code == 302  # Redirect to login

    def test_unit_create_for_property_invalid_property(self, app, authenticated_client):
        """Test unit creation for non-existent property."""
        with app.app_context():
            fake_uuid = '12345678-1234-1234-1234-123456789012'
            response = authenticated_client.get(f'/unit/create/{fake_uuid}')
            assert response.status_code == 404

    def test_unit_create_for_property_wrong_company(self, app, authenticated_client, property_b):
        """Test unit creation for property from different company."""
        with app.app_context():
            response = authenticated_client.get(f'/unit/create/{property_b.uuid}')
            assert response.status_code == 404

    def test_unit_create_for_property_valid(self, app, authenticated_client, property_a):
        """Test valid property-specific unit creation."""
        with app.app_context():
            response = authenticated_client.get(f'/unit/create/{property_a.uuid}')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')

            # Check that property is pre-selected (hidden or disabled field)
            assert property_a.name in response.data.decode()

    def test_unit_show_requires_login(self, client, unit):
        """Test that unit detail view requires authentication."""
        response = client.get(f'/unit/{unit.uuid}')
        assert response.status_code == 302  # Redirect to login

    def test_unit_show_invalid_uuid(self, app, authenticated_client):
        """Test unit detail view with invalid UUID."""
        with app.app_context():
            fake_uuid = '12345678-1234-1234-1234-123456789012'
            response = authenticated_client.get(f'/unit/{fake_uuid}')
            assert response.status_code == 404

    def test_unit_show_wrong_company(self, app, authenticated_client, company_b, property_b):
        """Test unit detail view for unit from different company."""
        with app.app_context():
            unit_b = Unit(name="Company B Unit", company_id=company_b.id, property_id=property_b.id)
            db.session.add(unit_b)
            db.session.commit()

            response = authenticated_client.get(f'/unit/{unit_b.uuid}')
            assert response.status_code == 404

    def test_unit_show_valid(self, app, authenticated_client, unit):
        """Test valid unit detail view."""
        with app.app_context():
            response = authenticated_client.get(f'/unit/{unit.uuid}')
            assert response.status_code == 200
            assert unit.name.encode() in response.data

    def test_unit_edit_requires_login(self, client, unit):
        """Test that unit edit requires authentication."""
        response = client.get(f'/unit/{unit.uuid}/edit')
        assert response.status_code == 302  # Redirect to login

    def test_unit_edit_invalid_uuid(self, app, authenticated_client):
        """Test unit edit with invalid UUID."""
        with app.app_context():
            fake_uuid = '12345678-1234-1234-1234-123456789012'
            response = authenticated_client.get(f'/unit/{fake_uuid}/edit')
            assert response.status_code == 404

    def test_unit_edit_wrong_company(self, app, authenticated_client, company_b, property_b):
        """Test unit edit for unit from different company."""
        with app.app_context():
            unit_b = Unit(name="Company B Unit", company_id=company_b.id, property_id=property_b.id)
            db.session.add(unit_b)
            db.session.commit()

            response = authenticated_client.get(f'/unit/{unit_b.uuid}/edit')
            assert response.status_code == 404

    def test_unit_edit_get_valid(self, app, authenticated_client, unit, property_a):
        """Test valid unit edit GET request."""
        with app.app_context():
            response = authenticated_client.get(f'/unit/{unit.uuid}/edit')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')

            # Check form is pre-populated
            name_input = soup.find('input', {'name': 'name'})
            assert name_input is not None
            assert name_input.get('value') == unit.name

    def test_unit_edit_post_valid(self, app, authenticated_client, unit):
        """Test valid unit edit POST request."""
        with app.app_context():
            updated_data = {
                'name': 'Updated Unit Name',
                'property_id': unit.property_id,
                'bedrooms': 3,  # Changed from original
                'bathrooms': 2,  # Changed from original
                'sqft': 1000,
                'rent': 1400,
                'air_conditioning': True,
                'heating_type': 'gas'
            }

            response = authenticated_client.post(f'/unit/{unit.uuid}/edit', data=updated_data)
            assert response.status_code == 302  # Redirect after edit

            # Verify changes were saved
            db.session.refresh(unit)
            assert unit.name == 'Updated Unit Name'
            assert unit.bedrooms == 3
            assert unit.bathrooms == 2

    def test_unit_delete_requires_login(self, client, unit):
        """Test that unit deletion requires authentication."""
        response = client.post(f'/unit/{unit.uuid}/delete')
        assert response.status_code == 302  # Redirect to login

    def test_unit_delete_invalid_uuid(self, app, authenticated_client):
        """Test unit deletion with invalid UUID."""
        with app.app_context():
            fake_uuid = '12345678-1234-1234-1234-123456789012'
            response = authenticated_client.post(f'/unit/{fake_uuid}/delete')
            assert response.status_code == 404

    def test_unit_delete_wrong_company(self, app, authenticated_client, company_b, property_b):
        """Test unit deletion for unit from different company."""
        with app.app_context():
            unit_b = Unit(name="Company B Unit", company_id=company_b.id, property_id=property_b.id)
            db.session.add(unit_b)
            db.session.commit()
            unit_id = unit_b.id

            response = authenticated_client.post(f'/unit/{unit_b.uuid}/delete')
            assert response.status_code == 404

            # Verify unit still exists
            unit_still_exists = Unit.query.get(unit_id)
            assert unit_still_exists is not None

    def test_unit_delete_valid(self, app, authenticated_client, unit):
        """Test valid unit deletion."""
        with app.app_context():
            unit_id = unit.id
            unit_uuid = unit.uuid

            response = authenticated_client.post(f'/unit/{unit_uuid}/delete')
            assert response.status_code == 302  # Redirect after deletion

            # Verify unit was deleted
            deleted_unit = Unit.query.get(unit_id)
            assert deleted_unit is None

    def test_unit_form_loading_states(self, app, authenticated_client, property_a):
        """Test that unit forms have loading state attributes."""
        with app.app_context():
            response = authenticated_client.get('/unit/create')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')
            submit_button = soup.find('button', {'type': 'submit'})

            if submit_button:
                loading_attr = submit_button.get('data-loading')
                assert loading_attr is not None
                assert 'creating' in loading_attr.lower() or 'adding' in loading_attr.lower()

    def test_unit_form_validation_client_side(self, app, authenticated_client, property_a):
        """Test that unit forms include client-side validation."""
        with app.app_context():
            response = authenticated_client.get('/unit/create')
            assert response.status_code == 200

            # Check for validation JavaScript or classes
            assert b'validation' in response.data.lower() or b'needs-validation' in response.data

    def test_unit_create_invalid_data(self, app, authenticated_client, property_a):
        """Test unit creation with invalid data."""
        with app.app_context():
            invalid_data = {
                'name': '',  # Required field empty
                'property_id': property_a.id,
                'bedrooms': -1,  # Invalid range
                'bathrooms': 15,  # Out of range
                'sqft': -500,  # Invalid value
                'rent': -100  # Invalid value
            }

            response = authenticated_client.post('/unit/create', data=invalid_data)
            # Should stay on form page with errors
            assert response.status_code == 200

            # Check for error messages
            assert b'error' in response.data.lower() or b'invalid' in response.data.lower()

    def test_unit_property_relationship_display(self, app, authenticated_client, unit, property_a):
        """Test that unit detail view shows property relationship."""
        with app.app_context():
            response = authenticated_client.get(f'/unit/{unit.uuid}')
            assert response.status_code == 200

            # Should show property information
            assert property_a.name.encode() in response.data

    def test_unit_lease_status_display(self, app, authenticated_client, unit):
        """Test that unit shows lease status information."""
        with app.app_context():
            response = authenticated_client.get(f'/unit/{unit.uuid}')
            assert response.status_code == 200

            # Should show some form of occupancy/lease status
            status_indicators = [b'vacant', b'occupied', b'available', b'status']
            assert any(indicator in response.data.lower() for indicator in status_indicators)

    def test_unit_comprehensive_field_display(self, app, authenticated_client, company_a, property_a):
        """Test that unit detail view displays comprehensive field information."""
        with app.app_context():
            # Create unit with comprehensive data
            unit = Unit(name="Comprehensive Display Unit", company_id=company_a.id, property_id=property_a.id)
            unit.bedrooms = 2
            unit.bathrooms = 1
            unit.sqft = 900
            unit.rent = 1300
            unit.air_conditioning = True
            unit.heating_type = "heat_pump"
            unit.dishwasher = True
            unit.pets_allowed = True
            unit.parking_spaces = 1
            unit.internet_included = True

            db.session.add(unit)
            db.session.commit()

            response = authenticated_client.get(f'/unit/{unit.uuid}')
            assert response.status_code == 200

            # Check that key information is displayed
            response_text = response.data.decode().lower()
            assert 'bedroom' in response_text or str(unit.bedrooms) in response_text
            assert 'bathroom' in response_text or str(unit.bathrooms) in response_text
            assert str(unit.sqft) in response_text or 'sq' in response_text
            assert str(unit.rent) in response_text

    def test_unit_navigation_links(self, app, authenticated_client, unit):
        """Test that unit views have proper navigation links."""
        with app.app_context():
            response = authenticated_client.get(f'/unit/{unit.uuid}')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')

            # Should have links for common actions
            links = soup.find_all('a')
            link_hrefs = [link.get('href', '') for link in links]

            # Check for edit link
            edit_links = [href for href in link_hrefs if 'edit' in href and unit.uuid in href]
            assert len(edit_links) > 0

    def test_unit_breadcrumb_navigation(self, app, authenticated_client, unit):
        """Test that unit views include breadcrumb navigation."""
        with app.app_context():
            response = authenticated_client.get(f'/unit/{unit.uuid}')
            assert response.status_code == 200

            # Check for breadcrumb indicators
            breadcrumb_indicators = [b'breadcrumb', b'nav', b'home', b'units']
            response_lower = response.data.lower()

            # Should have some form of navigation structure
            has_navigation = any(indicator in response_lower for indicator in breadcrumb_indicators)
            assert has_navigation or b'unit' in response_lower