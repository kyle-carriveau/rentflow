from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Unit, Property
from website import db
from flask_login import login_required, current_user
from website.errors import page_not_found
from datetime import datetime
from .forms import UnitForm

unit = Blueprint('unit', __name__, template_folder='templates')

@unit.route('/')
@login_required
def list_units():
    """List all units for the current user's company."""
    company_id = current_user.get_company_id()
    units = Unit.query.filter_by(company_id=company_id).all()
    return render_template("units.html", user=current_user, units=units)

@unit.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new unit with property selection."""
    company_id = current_user.get_company_id()

    # Get all properties for the company for the form
    properties = Property.query.filter_by(company_id=company_id).all()
    if not properties:
        flash('You must create a property before adding units.', 'warning')
        return redirect(url_for('property.create'))

    form = UnitForm()

    # Populate property choices for the form
    form.property_id.choices = [(p.id, f"{p.name} - {p.address or 'No address'}") for p in properties]

    if form.validate_on_submit():
        # Create unit with only constructor parameters
        new_unit = Unit(
            name=form.name.data,
            company_id=company_id,
            property_id=form.property_id.data
        )

        # Set all other attributes after initialization
        # Basic Information
        new_unit.bedrooms = form.bedrooms.data
        new_unit.bathrooms = form.bathrooms.data
        new_unit.sqft = form.sqft.data
        new_unit.rent = form.rent.data
        new_unit.description = form.description.data

        # HVAC & Climate
        new_unit.air_conditioning = form.air_conditioning.data
        new_unit.heating_type = form.heating_type.data
        new_unit.thermostat_type = form.thermostat_type.data

        # Appliances & Kitchen
        new_unit.appliances_included = form.appliances_included.data
        new_unit.dishwasher = form.dishwasher.data
        new_unit.garbage_disposal = form.garbage_disposal.data
        new_unit.microwave = form.microwave.data
        new_unit.refrigerator = form.refrigerator.data
        new_unit.range_oven = form.range_oven.data
        new_unit.washer_dryer = form.washer_dryer.data

        # Flooring & Interior
        new_unit.flooring_type = form.flooring_type.data
        new_unit.ceiling_height = form.ceiling_height.data
        new_unit.windows_type = form.windows_type.data
        new_unit.natural_light = form.natural_light.data

        # Storage & Space
        new_unit.closet_space = form.closet_space.data
        new_unit.storage_units = form.storage_units.data
        new_unit.balcony_patio = form.balcony_patio.data
        new_unit.balcony_sqft = form.balcony_sqft.data

        # Parking & Access
        new_unit.parking_type = form.parking_type.data
        new_unit.parking_spaces = form.parking_spaces.data
        new_unit.garage_type = form.garage_type.data

        # Bathroom Features
        new_unit.bathroom_features = form.bathroom_features.data
        new_unit.master_bath = form.master_bath.data
        new_unit.bathtub = form.bathtub.data
        new_unit.shower_type = form.shower_type.data

        # Condition & Maintenance
        new_unit.last_renovated = form.last_renovated.data
        new_unit.condition_rating = form.condition_rating.data
        new_unit.recent_updates = form.recent_updates.data
        new_unit.upcoming_maintenance = form.upcoming_maintenance.data

        # Accessibility & Compliance
        new_unit.ada_compliant = form.ada_compliant.data
        new_unit.wheelchair_accessible = form.wheelchair_accessible.data
        new_unit.accessibility_features = form.accessibility_features.data

        # Utilities & Energy
        new_unit.utilities_included = form.utilities_included.data
        new_unit.utility_cost_estimate = form.utility_cost_estimate.data
        new_unit.energy_efficiency_rating = form.energy_efficiency_rating.data

        # Pet Policy
        new_unit.pets_allowed = form.pets_allowed.data
        new_unit.pet_restrictions = form.pet_restrictions.data
        new_unit.pet_fee_monthly = form.pet_fee_monthly.data
        new_unit.pet_deposit = form.pet_deposit.data

        # Security Features
        new_unit.security_features = form.security_features.data
        new_unit.alarm_system = form.alarm_system.data
        new_unit.secure_entry = form.secure_entry.data

        # Technology & Internet
        new_unit.internet_included = form.internet_included.data
        new_unit.cable_ready = form.cable_ready.data
        new_unit.internet_speed = form.internet_speed.data
        new_unit.smart_home_features = form.smart_home_features.data

        try:
            db.session.add(new_unit)
            db.session.commit()
            flash(f'Unit "{new_unit.name}" has been created successfully!', 'success')
            return redirect(url_for('unit.show', uuid=new_unit.uuid))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating unit: {str(e)}', 'error')

    return render_template("create_unit.html", form=form, user=current_user)

@unit.route('/create/<uuid:uuid>', methods=['GET', 'POST'])
@login_required
def create_for_property(uuid):
    """Create a new unit for a property."""
    # Verify property ownership within company
    company_id = current_user.get_company_id()
    property = Property.find_by_uuid(str(uuid), company_id)
    if not property:
        return page_not_found(404)

    form = UnitForm()

    # For property-specific creation, set the property choices and default value
    form.property_id.choices = [(property.id, property.name)]
    form.property_id.data = property.id

    if form.validate_on_submit():
        # Create unit with only constructor parameters
        new_unit = Unit(
            name=form.name.data,
            company_id=company_id,
            property_id=property.id
        )

        # Set all other attributes after initialization
        # Basic Information
        new_unit.bedrooms = form.bedrooms.data
        new_unit.bathrooms = form.bathrooms.data
        new_unit.sqft = form.sqft.data
        new_unit.rent = form.rent.data
        new_unit.description = form.description.data

        # HVAC & Climate
        new_unit.air_conditioning = form.air_conditioning.data
        new_unit.heating_type = form.heating_type.data
        new_unit.thermostat_type = form.thermostat_type.data

        # Appliances & Kitchen
        new_unit.appliances_included = form.appliances_included.data
        new_unit.dishwasher = form.dishwasher.data
        new_unit.garbage_disposal = form.garbage_disposal.data
        new_unit.microwave = form.microwave.data
        new_unit.refrigerator = form.refrigerator.data
        new_unit.range_oven = form.range_oven.data
        new_unit.washer_dryer = form.washer_dryer.data

        # Flooring & Interior
        new_unit.flooring_type = form.flooring_type.data
        new_unit.ceiling_height = form.ceiling_height.data
        new_unit.windows_type = form.windows_type.data
        new_unit.natural_light = form.natural_light.data

        # Storage & Space
        new_unit.closet_space = form.closet_space.data
        new_unit.storage_units = form.storage_units.data
        new_unit.balcony_patio = form.balcony_patio.data
        new_unit.balcony_sqft = form.balcony_sqft.data

        # Parking & Access
        new_unit.parking_type = form.parking_type.data
        new_unit.parking_spaces = form.parking_spaces.data
        new_unit.garage_type = form.garage_type.data

        # Bathroom Features
        new_unit.bathroom_features = form.bathroom_features.data
        new_unit.master_bath = form.master_bath.data
        new_unit.bathtub = form.bathtub.data
        new_unit.shower_type = form.shower_type.data

        # Condition & Maintenance
        new_unit.last_renovated = form.last_renovated.data
        new_unit.condition_rating = form.condition_rating.data
        new_unit.recent_updates = form.recent_updates.data
        new_unit.upcoming_maintenance = form.upcoming_maintenance.data

        # Accessibility & Compliance
        new_unit.ada_compliant = form.ada_compliant.data
        new_unit.wheelchair_accessible = form.wheelchair_accessible.data
        new_unit.accessibility_features = form.accessibility_features.data

        # Utilities & Energy
        new_unit.utilities_included = form.utilities_included.data
        new_unit.utility_cost_estimate = form.utility_cost_estimate.data
        new_unit.energy_efficiency_rating = form.energy_efficiency_rating.data

        # Pet Policy
        new_unit.pets_allowed = form.pets_allowed.data
        new_unit.pet_restrictions = form.pet_restrictions.data
        new_unit.pet_fee_monthly = form.pet_fee_monthly.data
        new_unit.pet_deposit = form.pet_deposit.data

        # Security Features
        new_unit.security_features = form.security_features.data
        new_unit.alarm_system = form.alarm_system.data
        new_unit.secure_entry = form.secure_entry.data

        # Technology & Internet
        new_unit.internet_included = form.internet_included.data
        new_unit.cable_ready = form.cable_ready.data
        new_unit.internet_speed = form.internet_speed.data
        new_unit.smart_home_features = form.smart_home_features.data

        db.session.add(new_unit)
        db.session.commit()
        flash('Unit created successfully!', 'success')
        return redirect(url_for('property.home', uuid=uuid))

    return render_template("create_unit.html", user=current_user, property=property, form=form)

@unit.route('/<uuid:uuid>')
@login_required
def show(uuid):
    """Show unit details."""
    company_id = current_user.get_company_id()
    unit = Unit.find_by_uuid(str(uuid), company_id)
    if not unit:
        return page_not_found(404)
    today_date = datetime.now().date()
    return render_template("unit.html", unit=unit, user=current_user, today_date=today_date)

@unit.route('/<uuid:uuid>/edit', methods=['GET', 'POST'])
@login_required
def edit(uuid):
    """Edit an existing unit."""
    company_id = current_user.get_company_id()
    unit = Unit.find_by_uuid(str(uuid), company_id)
    if not unit:
        return page_not_found(404)

    # Get the property for validation
    property = Property.query.filter_by(id=unit.property_id, company_id=company_id).first()
    if not property:
        return page_not_found(404)

    form = UnitForm(obj=unit)

    # Set property choices for the form
    form.property_id.choices = [(property.id, property.name)]

    if form.validate_on_submit():
        # Basic Information
        unit.name = form.name.data
        unit.bedrooms = form.bedrooms.data
        unit.bathrooms = form.bathrooms.data
        unit.sqft = form.sqft.data
        unit.rent = form.rent.data
        unit.description = form.description.data

        # HVAC & Climate
        unit.air_conditioning = form.air_conditioning.data
        unit.heating_type = form.heating_type.data
        unit.thermostat_type = form.thermostat_type.data

        # Appliances & Kitchen
        unit.appliances_included = form.appliances_included.data
        unit.dishwasher = form.dishwasher.data
        unit.garbage_disposal = form.garbage_disposal.data
        unit.microwave = form.microwave.data
        unit.refrigerator = form.refrigerator.data
        unit.range_oven = form.range_oven.data
        unit.washer_dryer = form.washer_dryer.data

        # Flooring & Interior
        unit.flooring_type = form.flooring_type.data
        unit.ceiling_height = form.ceiling_height.data
        unit.windows_type = form.windows_type.data
        unit.natural_light = form.natural_light.data

        # Storage & Space
        unit.closet_space = form.closet_space.data
        unit.storage_units = form.storage_units.data
        unit.balcony_patio = form.balcony_patio.data
        unit.balcony_sqft = form.balcony_sqft.data

        # Parking & Access
        unit.parking_type = form.parking_type.data
        unit.parking_spaces = form.parking_spaces.data
        unit.garage_type = form.garage_type.data

        # Bathroom Features
        unit.bathroom_features = form.bathroom_features.data
        unit.master_bath = form.master_bath.data
        unit.bathtub = form.bathtub.data
        unit.shower_type = form.shower_type.data

        # Condition & Maintenance
        unit.last_renovated = form.last_renovated.data
        unit.condition_rating = form.condition_rating.data
        unit.recent_updates = form.recent_updates.data
        unit.upcoming_maintenance = form.upcoming_maintenance.data

        # Accessibility & Compliance
        unit.ada_compliant = form.ada_compliant.data
        unit.wheelchair_accessible = form.wheelchair_accessible.data
        unit.accessibility_features = form.accessibility_features.data

        # Utilities & Energy
        unit.utilities_included = form.utilities_included.data
        unit.utility_cost_estimate = form.utility_cost_estimate.data
        unit.energy_efficiency_rating = form.energy_efficiency_rating.data

        # Pet Policy
        unit.pets_allowed = form.pets_allowed.data
        unit.pet_restrictions = form.pet_restrictions.data
        unit.pet_fee_monthly = form.pet_fee_monthly.data
        unit.pet_deposit = form.pet_deposit.data

        # Security Features
        unit.security_features = form.security_features.data
        unit.alarm_system = form.alarm_system.data
        unit.secure_entry = form.secure_entry.data

        # Technology & Internet
        unit.internet_included = form.internet_included.data
        unit.cable_ready = form.cable_ready.data
        unit.internet_speed = form.internet_speed.data
        unit.smart_home_features = form.smart_home_features.data

        db.session.commit()
        flash('Unit updated successfully!', 'success')
        return redirect(url_for('unit.show', uuid=uuid))

    return render_template("edit_unit.html", user=current_user, unit=unit, property=property, form=form)

@unit.route('/<uuid:uuid>/delete', methods=['POST'])
@login_required
def delete(uuid):
    """Delete a unit."""
    company_id = current_user.get_company_id()
    unit = Unit.find_by_uuid(str(uuid), company_id)
    if not unit:
        return page_not_found(404)
    
    property = Property.query.filter_by(id=unit.property_id, company_id=company_id).first()
    if not property:
        return page_not_found(404)

    unit_name = unit.name

    try:
        db.session.delete(unit)
        db.session.commit()
        flash(f'Unit "{unit_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting unit. It may have associated leases.', 'error')

    return redirect(url_for('property.home', uuid=property.uuid))