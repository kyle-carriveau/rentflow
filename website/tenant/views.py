from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import User, Tenant, Property
from website import db 
from flask_login import login_required, current_user
from website.views import get_tenant, get_properties, get_states
from website.errors import page_not_found
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
def create():
    if request.method == "POST":
        print(f"DEBUG: Tenant creation attempt by user {current_user.email}")  # Debug logging
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        property = request.form.get('property')
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state')
        zip_code = request.form.get('zip_code', '').strip()

        print(f"DEBUG: Form data - first_name: '{first_name}', last_name: '{last_name}', email: '{email}', phone: '{phone}'")  # Debug logging

        # Server-side validation
        if not first_name:
            print("DEBUG: Validation failed - First name is required")
            flash('First name is required.', 'error')
            return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())

        if not last_name:
            print("DEBUG: Validation failed - Last name is required")
            flash('Last name is required.', 'error')
            return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())

        # Email validation
        if email:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                flash('Please enter a valid email address.', 'error')
                return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())

        # Zip code validation
        if zip_code and not zip_code.isdigit():
            flash('Zip code must contain only numbers.', 'error')
            return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())
        
        if zip_code and len(zip_code) != 5:
            flash('Zip code must be exactly 5 digits.', 'error')
            return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())

        # Check if email is already in use (check both users and tenants)
        if email:
            existing_user = User.query.filter_by(email=email).first()
            existing_tenant = Tenant.query.filter_by(email=email).first()
            if existing_user:
                flash('Email is already in use by a system user.', 'error')
                return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())
            if existing_tenant:
                flash('Email is already in use by another tenant.', 'error')
                return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())

        # Validate property ownership if property is selected
        if property:
            company_id = current_user.get_company_id()
            property_obj = Property.query.filter_by(id=property, company_id=company_id).first()
            if not property_obj:
                flash('Invalid property selected.', 'error')
                return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())

        # Convert empty strings to None for optional fields
        property = property if property else None
        zip_code = int(zip_code) if zip_code else None

        # Clean and validate phone number
        if phone:
            phone_digits = ''.join(filter(str.isdigit, phone))
            if phone_digits:
                if len(phone_digits) != 10:
                    flash('Phone number must be exactly 10 digits.', 'error')
                    return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())

                # Check if phone number is already in use
                existing_tenant_phone = Tenant.query.filter_by(phone=int(phone_digits)).first()
                if existing_tenant_phone:
                    flash('Phone number is already in use by another tenant.', 'error')
                    return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())

                phone = int(phone_digits)
            else:
                phone = None
        else:
            phone = None

        company_id = current_user.get_company_id()
        print(f"DEBUG: All validations passed, creating tenant with company_id: {company_id}")
        new_tenant = Tenant(first_name=first_name, last_name=last_name, email=email, phone=phone, property_id=property, address=address, city=city, state=state, zip_code=zip_code, company_id=company_id)

        try:
            db.session.add(new_tenant)
            db.session.commit()

            # Create detailed success message
            tenant_name = f"{first_name} {last_name}"
            property_info = ""
            if property:
                property_obj = Property.query.get(property)
                if property_obj:
                    property_info = f" and assigned to {property_obj.name}"

            print(f"DEBUG: Tenant {tenant_name} created successfully with ID {new_tenant.id}")  # Debug logging
            flash(f'Tenant "{tenant_name}" created successfully{property_info}!', 'success')
            return redirect(url_for('tenant.home', id=new_tenant.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating tenant: {str(e)}', 'error')
            return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())

    return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())

@tenant.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def home(id):
    """View tenant details."""
    company_id = current_user.get_company_id()
    tenant = Tenant.query.filter_by(id=id, company_id=company_id).first()
    if not tenant:
        return page_not_found(404)
    return render_template("/tenant.html", tenant=tenant, user=current_user)

@tenant.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit tenant information."""
    company_id = current_user.get_company_id()
    tenant = Tenant.query.filter_by(id=id, company_id=company_id).first()
    if not tenant:
        return page_not_found(404)
    
    if request.method == "POST":
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        property_id = request.form.get('property')
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state')
        zip_code = request.form.get('zip_code', '').strip()

        # Server-side validation
        if not first_name:
            flash('First name is required.', 'error')
            return render_template("edit_tenant.html", tenant=tenant, user=current_user, properties=get_properties(), states=get_states())
            
        if not last_name:
            flash('Last name is required.', 'error')
            return render_template("edit_tenant.html", tenant=tenant, user=current_user, properties=get_properties(), states=get_states())

        # Email validation
        if email:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                flash('Please enter a valid email address.', 'error')
                return render_template("edit_tenant.html", tenant=tenant, user=current_user, properties=get_properties(), states=get_states())

        # Zip code validation
        if zip_code and not zip_code.isdigit():
            flash('Zip code must contain only numbers.', 'error')
            return render_template("edit_tenant.html", tenant=tenant, user=current_user, properties=get_properties(), states=get_states())
        
        if zip_code and len(zip_code) != 5:
            flash('Zip code must be exactly 5 digits.', 'error')
            return render_template("edit_tenant.html", tenant=tenant, user=current_user, properties=get_properties(), states=get_states())

        # Check if email is already in use (excluding current tenant)
        if email:
            existing_user = User.query.filter_by(email=email).first()
            existing_tenant = Tenant.query.filter_by(email=email).filter(Tenant.id != id).first()
            if existing_user or existing_tenant:
                flash('Email is already in use.', 'error')
                return render_template("edit_tenant.html", tenant=tenant, user=current_user, properties=get_properties(), states=get_states())

        # Validate property ownership if property is selected
        if property_id:
            property_obj = Property.query.filter_by(id=property_id, company_id=company_id).first()
            if not property_obj:
                flash('Invalid property selected.', 'error')
                return render_template("edit_tenant.html", tenant=tenant, user=current_user, properties=get_properties(), states=get_states())

        # Convert empty strings to None for optional fields
        property_id = property_id if property_id else None
        zip_code = int(zip_code) if zip_code else None
        
        # Clean phone number: remove all non-digit characters and convert to int
        if phone:
            phone_digits = ''.join(filter(str.isdigit, phone))
            phone = int(phone_digits) if phone_digits else None
        else:
            phone = None

        # Update tenant
        tenant.first_name = first_name
        tenant.last_name = last_name
        tenant.email = email
        tenant.phone = phone
        tenant.property_id = property_id
        tenant.address = address
        tenant.city = city
        tenant.state = state
        tenant.zip_code = zip_code

        db.session.commit()
        flash('Tenant updated successfully!', 'success')
        return redirect(url_for('tenant.home', id=id))

    return render_template("edit_tenant.html", tenant=tenant, user=current_user, properties=get_properties(), states=get_states())

@tenant.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a tenant."""
    company_id = current_user.get_company_id()
    tenant = Tenant.query.filter_by(id=id, company_id=company_id).first()
    if not tenant:
        return page_not_found(404)
    
    tenant_name = f"{tenant.first_name} {tenant.last_name}"
    
    try:
        db.session.delete(tenant)
        db.session.commit()
        flash(f'Tenant "{tenant_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting tenant. They may have associated leases.', 'error')
    
    return redirect(url_for('tenant.tenants'))