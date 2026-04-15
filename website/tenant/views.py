from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import User, Tenant, Property
from website import db
from flask_login import login_required, current_user
from website.auth_utils import role_required
from website.views import get_tenant, get_properties, get_states
from website.errors import page_not_found
from website.tenant.forms import TenantCreateForm, TenantEditForm, TenantDeleteForm
import re

tenant = Blueprint('tenant', __name__, template_folder='templates')

@tenant.route('/', methods=['GET', 'POST'])
@login_required
def tenants(): 
    company_id = current_user.get_company_id()
    tenants = db.session.query(Tenant).filter_by(company_id=company_id).all()
    return render_template("tenants.html", user=current_user, tenants=tenants)

@tenant.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('staff')
def create():
    company_id = current_user.get_company_id()
    form = TenantCreateForm(properties=get_properties())

    if form.validate_on_submit():
        # Additional uniqueness validation (beyond WTForms)
        # Check if email is already in use by a system user (global check - users are unique across all companies)
        existing_user = User.query.filter_by(email=form.email.data).first()
        # Check if email is already in use by another tenant IN THIS COMPANY (company-scoped)
        existing_tenant = Tenant.query.filter_by(email=form.email.data, company_id=company_id).first()

        if existing_user:
            flash('Email is already in use by a system user.', 'error')
            return render_template("/create_tenant.html", user=current_user, form=form, properties=get_properties(), states=get_states())

        if existing_tenant:
            flash('Email is already in use by another tenant.', 'error')
            return render_template("/create_tenant.html", user=current_user, form=form, properties=get_properties(), states=get_states())

        # Check if phone number is already in use IN THIS COMPANY (company-scoped)
        # Note: phone is already cleaned by form validator
        existing_tenant_phone = Tenant.query.filter_by(phone=form.phone.data, company_id=company_id).first()
        if existing_tenant_phone:
            flash('Phone number is already in use by another tenant.', 'error')
            return render_template("/create_tenant.html", user=current_user, form=form, properties=get_properties(), states=get_states())

        # Validate property ownership if property is selected
        property_obj = None
        if form.property.data:
            property_obj = Property.find_by_uuid(form.property.data, company_id)
            if not property_obj:
                # If UUID lookup fails, try ID lookup for backwards compatibility
                property_obj = Property.query.filter_by(id=form.property.data, company_id=company_id).first()

            if not property_obj:
                flash('Invalid property selected.', 'error')
                return render_template("/create_tenant.html", user=current_user, form=form, properties=get_properties(), states=get_states())

        # Create tenant with only constructor parameters
        new_tenant = Tenant(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            company_id=company_id
        )

        # Set all other attributes after initialization
        new_tenant.email = form.email.data
        new_tenant.phone = form.phone.data
        new_tenant.property_id = property_obj.id if property_obj else None
        new_tenant.address = form.address.data if form.address.data else None
        new_tenant.city = form.city.data if form.city.data else None
        new_tenant.state = form.state.data if form.state.data else None
        new_tenant.zip_code = int(form.zip_code.data) if form.zip_code.data else None

        try:
            db.session.add(new_tenant)
            db.session.commit()

            # Create detailed success message
            tenant_name = f"{form.first_name.data} {form.last_name.data}"
            property_info = ""
            if property_obj:
                property_info = f" and assigned to {property_obj.name}"

            flash(f'Tenant "{tenant_name}" created successfully{property_info}!', 'success')
            return redirect(url_for('tenant.home', uuid=new_tenant.uuid))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating tenant: {str(e)}', 'error')
            return render_template("/create_tenant.html", user=current_user, form=form, properties=get_properties(), states=get_states())

    return render_template("/create_tenant.html", user=current_user, form=form, properties=get_properties(), states=get_states())

@tenant.route('/<uuid:uuid>', methods=['GET', 'POST'])
@login_required
def home(uuid):
    """View tenant details."""
    company_id = current_user.get_company_id()
    tenant = Tenant.find_by_uuid(str(uuid), company_id)
    if not tenant:
        return page_not_found(404)
    return render_template("/tenant.html", tenant=tenant, user=current_user)

@tenant.route('/edit/<uuid:uuid>', methods=['GET', 'POST'])
@login_required
def edit(uuid):
    """Edit tenant information."""
    company_id = current_user.get_company_id()
    tenant = Tenant.find_by_uuid(str(uuid), company_id)
    if not tenant:
        return page_not_found(404)

    form = TenantEditForm(properties=get_properties(), obj=tenant)

    # Pre-populate form with tenant's current property (by ID for dropdown)
    if request.method == 'GET' and tenant.property_id:
        form.property.data = str(tenant.property_id)

    if form.validate_on_submit():
        # Check if email is already in use (excluding current tenant)
        # Users are global, tenants are company-scoped
        existing_user = User.query.filter_by(email=form.email.data).first()
        existing_tenant = Tenant.query.filter_by(email=form.email.data, company_id=company_id).filter(Tenant.id != tenant.id).first()

        if existing_user or existing_tenant:
            flash('Email is already in use.', 'error')
            return render_template("edit_tenant.html", tenant=tenant, user=current_user, form=form, properties=get_properties(), states=get_states())

        # Check if phone number is already in use IN THIS COMPANY (excluding current tenant)
        # Note: phone is already cleaned by form validator
        existing_tenant_phone = Tenant.query.filter_by(phone=form.phone.data, company_id=company_id).filter(Tenant.id != tenant.id).first()
        if existing_tenant_phone:
            flash('Phone number is already in use by another tenant.', 'error')
            return render_template("edit_tenant.html", tenant=tenant, user=current_user, form=form, properties=get_properties(), states=get_states())

        # Validate property ownership if property is selected
        property_id = None
        if form.property.data:
            property_obj = Property.query.filter_by(id=form.property.data, company_id=company_id).first()
            if not property_obj:
                flash('Invalid property selected.', 'error')
                return render_template("edit_tenant.html", tenant=tenant, user=current_user, form=form, properties=get_properties(), states=get_states())
            property_id = property_obj.id

        # Update tenant
        tenant.first_name = form.first_name.data
        tenant.last_name = form.last_name.data
        tenant.email = form.email.data
        tenant.phone = form.phone.data
        tenant.property_id = property_id
        tenant.address = form.address.data if form.address.data else None
        tenant.city = form.city.data if form.city.data else None
        tenant.state = form.state.data if form.state.data else None
        tenant.zip_code = int(form.zip_code.data) if form.zip_code.data else None

        db.session.commit()
        flash('Tenant updated successfully!', 'success')
        return redirect(url_for('tenant.home', uuid=uuid))

    return render_template("edit_tenant.html", tenant=tenant, user=current_user, form=form, properties=get_properties(), states=get_states())

@tenant.route('/<uuid:uuid>/delete', methods=['POST'])
@login_required
def delete(uuid):
    """Delete a tenant."""
    company_id = current_user.get_company_id()
    tenant = Tenant.find_by_uuid(str(uuid), company_id)
    if not tenant:
        return page_not_found(404)

    form = TenantDeleteForm()

    if form.validate_on_submit():
        tenant_name = f"{tenant.first_name} {tenant.last_name}"

        try:
            db.session.delete(tenant)
            db.session.commit()
            flash(f'Tenant "{tenant_name}" deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting tenant. They may have associated leases.', 'error')

    return redirect(url_for('tenant.tenants'))