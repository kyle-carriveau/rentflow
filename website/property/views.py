from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Tenant, Property, Unit, Lease, Portfolio
from website import db
from flask_login import login_required, current_user
from website.views import get_properties, get_portfolios, get_states, get_units
from website.errors import page_not_found
from website.auth_utils import can_create_required, can_edit_required, can_delete_required
from website.property.forms import PropertyForm, PropertyEditForm
from datetime import datetime

property = Blueprint('property', __name__, template_folder='templates')

@property.route('/finances/<uuid:uuid>', methods=['GET', 'POST'])
@login_required
def finances(uuid):
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
        
        company_id = current_user.get_company_id()
        new_property = Property(name=name, company_id=company_id, portfolio_id=portfolio)
        db.session.add(new_property)
        db.session.commit()
        flash('Property created successfully!', 'success')
        return redirect(url_for("property.properties"))
    return render_template("properties.html", user=current_user, properties=get_properties(), portfolios=get_portfolios())

@property.route('/<uuid:uuid>', methods=['GET', 'POST'])
@login_required
def home(uuid):
    company_id = current_user.get_company_id()
    property = Property.find_by_uuid(str(uuid), company_id)
    today = datetime.today()
    if property:
        tenants = Tenant.query.filter_by(property_id=property.id, company_id=company_id)
        leases = db.session.query(Unit, Lease, Tenant).filter_by(company_id=company_id, property_id=property.id).join(Lease, Lease.unit_id==Unit.id).join(Tenant, Tenant.id==Lease.tenant_id).all()     
        return render_template("property.html", user=current_user, property=property, leases=leases, tenants=tenants, units=get_units(property.id), today=today)
    return page_not_found(404)

@property.route('/create', methods=['GET', 'POST'])
@login_required
@can_create_required
def create():
    company_id = current_user.get_company_id()
    portfolios = Portfolio.query.filter_by(company_id=company_id).all()
    form = PropertyForm(portfolios=portfolios)

    if form.validate_on_submit():
        try:
            # Convert portfolio UUID to database ID if provided
            portfolio_db_id = None
            if form.portfolio_id.data:
                portfolio = Portfolio.find_by_uuid(form.portfolio_id.data, company_id)
                if portfolio:
                    portfolio_db_id = portfolio.id
                else:
                    flash('Selected portfolio not found.', 'error')
                    return render_template("/create_enhanced.html", user=current_user, form=form)

            # Create new property with only constructor parameters
            new_property = Property(
                name=form.name.data,
                company_id=company_id,
                portfolio_id=portfolio_db_id
            )

            # Set all other attributes after initialization
            new_property.type = form.type.data
            new_property.description = form.description.data
            new_property.property_status = form.property_status.data
            new_property.maintenance_priority = form.maintenance_priority.data
            new_property.address = form.address.data
            new_property.city = form.city.data
            new_property.state = form.state.data
            new_property.zip_code = form.zip_code.data
            new_property.neighborhood = form.neighborhood.data
            new_property.latitude = form.latitude.data
            new_property.longitude = form.longitude.data
            new_property.year_built = form.year_built.data
            new_property.lot_size = form.lot_size.data
            new_property.building_sqft = form.building_sqft.data
            new_property.stories = form.stories.data
            new_property.parking_spaces = form.parking_spaces.data
            new_property.purchase_price = form.purchase_price.data
            new_property.purchase_date = form.purchase_date.data
            new_property.current_market_value = form.current_market_value.data
            new_property.annual_property_tax = form.annual_property_tax.data
            new_property.annual_insurance = form.annual_insurance.data
            new_property.monthly_hoa_fees = form.monthly_hoa_fees.data
            new_property.acquisition_method = form.acquisition_method.data
            new_property.property_manager = form.property_manager.data
            new_property.created_date = datetime.now()
            new_property.updated_date = datetime.now()

            db.session.add(new_property)
            db.session.commit()

            flash(f'Property "{form.name.data}" created successfully!', 'success')
            return redirect(url_for('property.properties'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating property: {str(e)}', 'error')

    # Display form errors if validation failed
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')

    return render_template("/create_enhanced.html", user=current_user, form=form)


@property.route('/<uuid:uuid>/edit', methods=['GET', 'POST'])
@login_required
@can_edit_required
def edit(uuid):
    company_id = current_user.get_company_id()
    property_obj = Property.find_by_uuid(str(uuid), company_id)
    if not property_obj:
        return page_not_found(404)

    portfolios = Portfolio.query.filter_by(company_id=company_id).all()
    form = PropertyEditForm(portfolios=portfolios, obj=property_obj)

    # Convert portfolio database ID to UUID for the form
    if property_obj.portfolio_id and portfolios:
        for portfolio in portfolios:
            if portfolio.id == property_obj.portfolio_id:
                form.portfolio_id.data = portfolio.uuid
                break

    if form.validate_on_submit():
        try:
            # Convert portfolio UUID to database ID if provided
            portfolio_db_id = None
            if form.portfolio_id.data:
                portfolio = Portfolio.find_by_uuid(form.portfolio_id.data, company_id)
                if portfolio:
                    portfolio_db_id = portfolio.id
                else:
                    flash('Selected portfolio not found.', 'error')
                    return render_template("/edit.html", user=current_user, form=form, property=property_obj)

            # Update property with form data
            form.populate_obj(property_obj)
            property_obj.portfolio_id = portfolio_db_id
            property_obj.updated_date = datetime.now()

            db.session.commit()
            flash('Property updated successfully!', 'success')
            return redirect(url_for('property.home', uuid=uuid))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating property: {str(e)}', 'error')

    # Display form errors if validation failed
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')

    return render_template("/edit.html", user=current_user, form=form, property=property_obj)

@property.route('/<uuid:uuid>/delete', methods=['POST'])
@login_required
@can_delete_required
def delete(uuid):
    """Delete a property and all associated data."""
    company_id = current_user.get_company_id()
    property = Property.find_by_uuid(str(uuid), company_id)
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
