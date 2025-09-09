from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Tenant, Property, Unit, Lease
from website import db 
from flask_login import login_required, current_user
from website.views import get_properties, get_portfolios, get_states, get_units
from website.errors import page_not_found
from datetime import datetime

property = Blueprint('property', __name__, template_folder='templates')

@property.route('/finances/<int:id>', methods=['GET', 'POST'])
@login_required
def finances(id):
    return render_template("finances.html", user=current_user)

@property.route('/', methods=['GET', 'POST'])
@login_required
def properties():
    if request.method == "POST":
        name = request.form.get('property_name', '').strip()
        portfolio = request.form.get('portfolio')
        
        # Server-side validation
        if not name:
            flash('Property name is required.', 'error')
            return render_template("properties.html", user=current_user, properties=get_properties(), portfolios=get_portfolios())
        
        # Convert empty strings to None for optional fields
        portfolio = portfolio if portfolio else None
        
        new_property = Property(name=name, owner=current_user.id, portfolio=portfolio)
        db.session.add(new_property)
        db.session.commit()
        flash('Property created successfully!', 'success')
        return redirect(url_for("property.properties"))
    return render_template("properties.html", user=current_user, properties=get_properties(), portfolios=get_portfolios())

@property.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def home(id):
    property = Property.query.filter_by(id=id, owner=current_user.id).first()
    today = datetime.today()
    if property:
        tenants = Tenant.query.filter_by(property=id, landlord=current_user.id)
        leases = db.session.query(Unit, Lease, Tenant).filter_by(owner=current_user.id, property=id).join(Lease, Lease.unit_id==Unit.id).join(Tenant, Tenant.id==Lease.tenant_id).all()     
        return render_template("property.html", user=current_user, property=property, leases=leases, tenants=tenants, units=get_units(property.id), today=today)
    return page_not_found(404)

@property.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get('name', '').strip()
        type = request.form.get('type')
        portfolio = request.form.get('portfolio')
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state')
        zip_code = request.form.get('zip_code', '').strip()

        # Server-side validation
        if not name:
            flash('Property name is required.', 'error')
            return render_template("/create.html", user=current_user, states=get_states(), portfolios=get_portfolios())
        
        if zip_code and not zip_code.isdigit():
            flash('Zip code must contain only numbers.', 'error')
            return render_template("/create.html", user=current_user, states=get_states(), portfolios=get_portfolios())
        
        if zip_code and (len(zip_code) < 5 or len(zip_code) > 5):
            flash('Zip code must be exactly 5 digits.', 'error')
            return render_template("/create.html", user=current_user, states=get_states(), portfolios=get_portfolios())

        # Convert empty strings to None for optional fields
        portfolio = portfolio if portfolio else None
        zip_code = int(zip_code) if zip_code else None

        new_property = Property(name=name, owner=current_user.id, portfolio=portfolio, type=type, address=address, city=city, state=state, zip_code=zip_code)
        db.session.add(new_property)
        db.session.commit()
        flash('Property created successfully!', 'success')
        return redirect(url_for('property.properties'))

    return render_template("/create.html", user=current_user, states=get_states(), portfolios=get_portfolios())


@property.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    property = Property.query.filter_by(id=id, owner=current_user.id).first()
    if not property:
        return page_not_found(404)
        
    if request.method == "POST":
        name = request.form.get('name', '').strip()
        type = request.form.get('type')
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state')
        zip_code = request.form.get('zip_code', '').strip()
        
        # Server-side validation
        if not name:
            flash('Property name is required.', 'error')
            return render_template("/edit.html", user=current_user, property=property, states=get_states())
        
        if zip_code and not zip_code.isdigit():
            flash('Zip code must contain only numbers.', 'error')
            return render_template("/edit.html", user=current_user, property=property, states=get_states())
        
        if zip_code and len(zip_code) != 5:
            flash('Zip code must be exactly 5 digits.', 'error')
            return render_template("/edit.html", user=current_user, property=property, states=get_states())

        # Update property with validated data
        property.name = name
        property.type = type
        property.address = address
        property.city = city
        property.state = state
        property.zip_code = int(zip_code) if zip_code else None

        db.session.commit()
        flash('Property updated successfully!', 'success')
        return redirect(url_for('property.home', id=id))

    return render_template("/edit.html", user=current_user, property=property, states=get_states())

@property.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a property and all associated data."""
    property = Property.query.filter_by(id=id, owner=current_user.id).first()
    if not property:
        return page_not_found(404)
    
    property_name = property.name
    
    try:
        # The cascade relationships in the models will handle automatic deletion
        # of associated units, tenants, and leases
        db.session.delete(property)
        db.session.commit()
        flash(f'Property "{property_name}" and all associated data deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting property. Please try again.', 'error')
    
    return redirect(url_for('property.properties'))
