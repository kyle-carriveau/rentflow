from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Lease, Unit, Tenant, Property
from website import db 
from flask_login import login_required, current_user
from datetime import datetime
from website.views import get_tenants, get_units, get_properties
from website.errors import page_not_found
from .forms import LeaseForm, GeneralLeaseForm

lease = Blueprint('lease', __name__, template_folder='templates')

@lease.route('/', methods=['GET', 'POST'])
@login_required
def leases():
    leases = get_all_leases_for_user()
    today_date = datetime.now()
    return render_template("leases.html", user=current_user, leases=leases, today_date=today_date)

@lease.route('/<uuid:uuid>', methods=['GET', 'POST'])
@login_required
def show(uuid):
    """View lease details."""
    # Only show leases for properties owned by current user
    company_id = current_user.get_company_id()
    lease = Lease.find_by_uuid(str(uuid), company_id)
    if not lease:
        return page_not_found(404)
    today_date = datetime.now()
    return render_template("lease.html", user=current_user, lease=lease, today_date=today_date)

@lease.route('/update/<uuid:uuid>', methods=['GET', 'POST'])
@login_required
def update(uuid):
    # Only allow updating leases for properties owned by current user
    company_id = current_user.get_company_id()
    lease = Lease.find_by_uuid(str(uuid), company_id)
    if not lease:
        return page_not_found(404)
    form = LeaseForm(obj=lease)
    form.tenant.choices = [('', 'Choose a tenant...')] + [(t.uuid, f"{t.first_name} {t.last_name}") for t in Tenant.query.filter_by(company_id=company_id)]
    form.unit.choices = [('', 'Choose a unit...')] + [(u.uuid, u.name) for u in Unit.query.filter_by(property_id=lease.property_id)]
    
    if form.validate_on_submit():
        # Get form data
        start_datetime = datetime.combine(form.start.data, datetime.min.time())
        end_datetime = datetime.combine(form.end.data, datetime.min.time())

        # Additional validation
        if start_datetime >= end_datetime:
            flash('Start date must be before end date.', 'error')
            return render_template("update_lease.html", user=current_user, form=form, lease=lease, properties=get_properties())

        # Check for tenant overlap (excluding current lease)
        if Lease.check_tenant_overlap(form.tenant.data, start_datetime, end_datetime, company_id, exclude_lease_id=lease.id):
            flash('This tenant already has an overlapping lease during this time period.', 'error')
            return render_template("update_lease.html", user=current_user, form=form, lease=lease, properties=get_properties())

        # Check for unit overlap (excluding current lease)
        if Lease.check_unit_overlap(form.unit.data, start_datetime, end_datetime, company_id, exclude_lease_id=lease.id):
            flash('This unit is already leased to another tenant during this time period.', 'error')
            return render_template("update_lease.html", user=current_user, form=form, lease=lease, properties=get_properties())

        form.populate_obj(lease)
        lease.start = start_datetime
        lease.end = end_datetime
        lease.company_id = company_id  # Ensure company_id is set
        db.session.commit()
        return redirect(url_for('property.show', uuid=lease.unit.property_ref.uuid))
    
    return render_template("update_lease.html", user=current_user, form=form, lease=lease, properties=get_properties())


@lease.route('/create', methods=['GET', 'POST'])
@login_required
def create_general():
    """Create a new lease with property selection."""
    from website.auth_utils import can_create_required

    # Check if user has create permissions
    if not current_user.can_create():
        flash('You do not have permission to create new records.', 'error')
        return redirect(url_for('lease.leases'))

    company_id = current_user.get_company_id()

    # Get user's properties for property selection
    properties = Property.query.filter_by(company_id=company_id).all()
    if not properties:
        flash('You need to create a property before creating a lease.', 'warning')
        return redirect(url_for('property.create'))

    form = GeneralLeaseForm()
    form.property.choices = [('', 'Select Property')] + [(p.uuid, p.name) for p in properties]
    form.tenant.choices = [('', 'Choose a tenant...')] + [(t.uuid, f"{t.first_name} {t.last_name}") for t in Tenant.query.filter_by(company_id=company_id)]
    form.unit.choices = [('', 'Choose a unit...')]  # Will be populated via JavaScript based on property selection

    # Handle pre-selected values from query parameters (for context-specific links)
    preselected_property = request.args.get('property')
    preselected_unit = request.args.get('unit')
    preselected_tenant = request.args.get('tenant')

    # Pre-select form values if provided and valid
    if preselected_property and not form.property.data:
        # Validate property belongs to company
        property_obj = Property.find_by_uuid(preselected_property, company_id)
        if property_obj:
            form.property.data = preselected_property

            # If property is pre-selected, populate units for that property
            units = Unit.query.filter_by(property_id=property_obj.id, company_id=company_id).all()
            form.unit.choices = [('', 'Choose a unit...')] + [(u.uuid, u.name) for u in units]

            # Pre-select unit if provided and belongs to the property
            if preselected_unit:
                unit_obj = Unit.find_by_uuid(preselected_unit, company_id)
                if unit_obj and unit_obj.property_id == property_obj.id:
                    form.unit.data = preselected_unit

    if preselected_tenant and not form.tenant.data:
        # Validate tenant belongs to company
        tenant_obj = Tenant.find_by_uuid(preselected_tenant, company_id)
        if tenant_obj:
            form.tenant.data = preselected_tenant

    # Handle form errors by ensuring unit dropdown is populated when property is selected
    if request.method == 'POST' and form.property.data:
        # Property is selected, populate units for that property even if form has other errors
        property_obj = Property.find_by_uuid(form.property.data, company_id)
        if property_obj:
            units = Unit.query.filter_by(property_id=property_obj.id, company_id=company_id).all()
            form.unit.choices = [('', 'Choose a unit...')] + [(u.uuid, u.name) for u in units]

    if form.validate_on_submit():
        property_uuid = form.property.data
        tenant_uuid = form.tenant.data
        unit_uuid = form.unit.data
        start = form.start.data
        end = form.end.data
        rent = form.rent.data

        # Additional validation
        if start >= end:
            flash('Start date must be before end date.', 'error')
            # Ensure unit dropdown is populated for error state
            if form.property.data:
                property_obj = Property.find_by_uuid(form.property.data, company_id)
                if property_obj:
                    units = Unit.query.filter_by(property_id=property_obj.id, company_id=company_id).all()
                    form.unit.choices = [('', 'Choose a unit...')] + [(u.uuid, u.name) for u in units]
            return render_template("create_general_lease.html", user=current_user, form=form)

        # Verify unit belongs to the selected property
        property = Property.find_by_uuid(property_uuid, company_id)
        unit = Unit.find_by_uuid(unit_uuid, company_id) if unit_uuid else None
        if not unit or not property or unit.property_id != property.id:
            flash('Invalid unit selected for the chosen property.', 'error')
            # Ensure unit dropdown is populated for error state
            if form.property.data:
                property_obj = Property.find_by_uuid(form.property.data, company_id)
                if property_obj:
                    units = Unit.query.filter_by(property_id=property_obj.id, company_id=company_id).all()
                    form.unit.choices = [('', 'Choose a unit...')] + [(u.uuid, u.name) for u in units]
            return render_template("create_general_lease.html", user=current_user, form=form)

        # Convert dates to datetime for comparison
        start_datetime = datetime.combine(start, datetime.min.time())
        end_datetime = datetime.combine(end, datetime.min.time())

        # Get tenant for validation
        tenant = Tenant.find_by_uuid(tenant_uuid, company_id) if tenant_uuid else None
        if not tenant:
            flash('Invalid tenant selected.', 'error')
            # Ensure unit dropdown is populated for error state
            if form.property.data:
                property_obj = Property.find_by_uuid(form.property.data, company_id)
                if property_obj:
                    units = Unit.query.filter_by(property_id=property_obj.id, company_id=company_id).all()
                    form.unit.choices = [('', 'Choose a unit...')] + [(u.uuid, u.name) for u in units]
            return render_template("create_general_lease.html", user=current_user, form=form)

        # Check for tenant overlap using integer IDs (internal method)
        if Lease.check_tenant_overlap(tenant.id, start_datetime, end_datetime, company_id):
            flash('This tenant already has an overlapping lease during this time period.', 'error')
            # Ensure unit dropdown is populated for error state
            if form.property.data:
                property_obj = Property.find_by_uuid(form.property.data, company_id)
                if property_obj:
                    units = Unit.query.filter_by(property_id=property_obj.id, company_id=company_id).all()
                    form.unit.choices = [('', 'Choose a unit...')] + [(u.uuid, u.name) for u in units]
            return render_template("create_general_lease.html", user=current_user, form=form)

        # Check for unit overlap using integer IDs (internal method)
        if Lease.check_unit_overlap(unit.id, start_datetime, end_datetime, company_id):
            flash('This unit is already leased to another tenant during this time period.', 'error')
            # Ensure unit dropdown is populated for error state
            if form.property.data:
                property_obj = Property.find_by_uuid(form.property.data, company_id)
                if property_obj:
                    units = Unit.query.filter_by(property_id=property_obj.id, company_id=company_id).all()
                    form.unit.choices = [('', 'Choose a unit...')] + [(u.uuid, u.name) for u in units]
            return render_template("create_general_lease.html", user=current_user, form=form)

        # Get financial field values
        security_deposit = form.security_deposit.data or 0
        pet_deposit = form.pet_deposit.data or 0
        late_fee = form.late_fee.data or 0
        payment_due_date = form.payment_due_date.data or 1
        grace_period_days = form.grace_period_days.data or 5
        utilities_included = form.utilities_included.data or ""
        parking_fee = form.parking_fee.data or 0

        # Get additional financial field values
        application_fee = form.application_fee.data or 0
        broker_fee = form.broker_fee.data or 0
        cleaning_fee = form.cleaning_fee.data or 0
        administrative_fee = form.administrative_fee.data or 0
        last_month_rent = form.last_month_rent.data or 0
        utility_deposits = form.utility_deposits.data or 0
        storage_fee = form.storage_fee.data or 0
        concessions = form.concessions.data or 0
        pet_fee = form.pet_fee.data or 0

        # Get lease terms field values
        lease_type = form.lease_type.data or 'fixed'
        auto_renewal = form.auto_renewal.data or 'no'
        notice_period_days = form.notice_period_days.data or 30
        early_termination_fee = form.early_termination_fee.data or 0
        max_occupants = form.max_occupants.data or 2
        renewal_terms = form.renewal_terms.data or ""

        # Get operational details field values
        move_in_date = form.move_in_date.data
        move_out_date = form.move_out_date.data
        key_deposit = form.key_deposit.data or 0
        move_in_inspection_notes = form.move_in_inspection_notes.data or ""
        move_out_inspection_notes = form.move_out_inspection_notes.data or ""
        lease_status = form.lease_status.data or 'active'
        property_manager_notes = form.property_manager_notes.data or ""
        emergency_contact_name = form.emergency_contact_name.data or ""
        emergency_contact_phone = form.emergency_contact_phone.data or ""

        # Get advanced features field values
        lease_documents = form.lease_documents.data or ""
        compliance_notes = form.compliance_notes.data or ""
        insurance_required = form.insurance_required.data or False
        insurance_verified = form.insurance_verified.data or False
        insurance_expiry_date = form.insurance_expiry_date.data
        background_check_status = form.background_check_status.data or 'not_required'
        background_check_date = form.background_check_date.data
        credit_score = form.credit_score.data
        # automatic_renewal_enabled removed - using auto_renewal field instead
        renewal_reminder_days = form.renewal_reminder_days.data or 60
        violation_history = form.violation_history.data or ""
        maintenance_requests = form.maintenance_requests.data or ""

        new_lease = Lease(
            tenant_id=tenant.id,
            unit_id=unit.id,
            property_id=property.id,
            company_id=company_id,
            start=start_datetime,
            end=end_datetime,
            rent=rent,
            security_deposit=security_deposit,
            pet_deposit=pet_deposit,
            late_fee=late_fee,
            payment_due_date=payment_due_date,
            grace_period_days=grace_period_days,
            utilities_included=utilities_included,
            parking_fee=parking_fee,
            # Additional financial fields
            application_fee=application_fee,
            broker_fee=broker_fee,
            cleaning_fee=cleaning_fee,
            administrative_fee=administrative_fee,
            last_month_rent=last_month_rent,
            utility_deposits=utility_deposits,
            storage_fee=storage_fee,
            concessions=concessions,
            pet_fee=pet_fee,
            lease_type=lease_type,
            auto_renewal=auto_renewal,
            notice_period_days=notice_period_days,
            early_termination_fee=early_termination_fee,
            max_occupants=max_occupants,
            renewal_terms=renewal_terms,
            move_in_date=move_in_date,
            move_out_date=move_out_date,
            key_deposit=key_deposit,
            move_in_inspection_notes=move_in_inspection_notes,
            move_out_inspection_notes=move_out_inspection_notes,
            lease_status=lease_status,
            property_manager_notes=property_manager_notes,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            lease_documents=lease_documents,
            compliance_notes=compliance_notes,
            insurance_required=insurance_required,
            insurance_verified=insurance_verified,
            insurance_expiry_date=insurance_expiry_date,
            background_check_status=background_check_status,
            background_check_date=background_check_date,
            credit_score=credit_score,
            renewal_reminder_days=renewal_reminder_days,
            violation_history=violation_history,
            maintenance_requests=maintenance_requests
        )
        db.session.add(new_lease)
        db.session.commit()

        # Get tenant and unit info for the success message (already have these objects)
        tenant_name = f"{tenant.first_name} {tenant.last_name}" if tenant else "Unknown"
        unit_name = unit.name if unit else "Unknown"

        flash(f'Lease created successfully! {tenant_name} is now assigned to {unit_name} starting {start.strftime("%m/%d/%Y")}.', 'success')
        return redirect(url_for('lease.show', uuid=new_lease.uuid))

    return render_template("create_general_lease.html", user=current_user, form=form)

@lease.route('/api/units/<uuid:property_uuid>')
@login_required
def get_units_for_property(property_uuid):
    """API endpoint to get units for a specific property."""
    from flask import jsonify

    company_id = current_user.get_company_id()

    # Verify property belongs to current user's company
    property = Property.find_by_uuid(str(property_uuid), company_id)
    if not property:
        return jsonify([])

    # Get units for this property
    units = Unit.query.filter_by(property_id=property.id).all()
    unit_choices = [{'id': u.uuid, 'name': u.name} for u in units]

    return jsonify(unit_choices)


@lease.route('/<uuid:uuid>/delete', methods=['POST'])
@login_required
def delete(uuid):
    """Delete a lease."""
    # Only allow deleting leases for properties owned by current user
    company_id = current_user.get_company_id()
    lease = Lease.find_by_uuid(str(uuid), company_id)

    if not lease:
        return page_not_found(404)
    
    property_uuid = lease.unit.property_ref.uuid
    tenant_name = f"{lease.tenant_ref.first_name} {lease.tenant_ref.last_name}" if lease.tenant_ref else "Unknown"
    unit_name = lease.unit_ref.name if lease.unit_ref else "Unknown"

    try:
        db.session.delete(lease)
        db.session.commit()
        flash(f'Lease for {tenant_name} in {unit_name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting lease.', 'error')

    return redirect(url_for('property.show', uuid=property_uuid))

def get_all_leases_for_user():
    """Get all leases for properties owned by current user, ordered by most recent first."""
    company_id = current_user.get_company_id()
    all_leases = db.session.query(Lease).join(Unit).join(Property).filter(
        Property.company_id == company_id
    ).order_by(Lease.end.desc(), Lease.start.desc()).all()
    return all_leases

def get_active_leases():
    today = datetime.now()
    # Only return leases for properties owned by current user
    company_id = current_user.get_company_id()
    active_leases = db.session.query(Lease).join(Unit).join(Property).filter(
        Property.company_id == company_id,
        Lease.start <= today,
        Lease.end >= today
    ).all()
    return active_leases

def get_active_leases_for_property(property_id):
    today = datetime.now()
    active_leases = Lease.query.join(Unit).join(Property).\
                    filter(Property.id == property_id, Lease.start <= today, Lease.end >= today).\
                    all()
    return active_leases