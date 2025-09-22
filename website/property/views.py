from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Tenant, Property, Unit, Lease
from website import db 
from flask_login import login_required, current_user
from website.views import get_properties, get_portfolios, get_states, get_units
from website.errors import page_not_found
from website.auth_utils import can_create_required, can_edit_required, can_delete_required
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
        
        company_id = current_user.get_company_id()
        new_property = Property(name=name, company_id=company_id, portfolio_id=portfolio)
        db.session.add(new_property)
        db.session.commit()
        flash('Property created successfully!', 'success')
        return redirect(url_for("property.properties"))
    return render_template("properties.html", user=current_user, properties=get_properties(), portfolios=get_portfolios())

@property.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def home(id):
    company_id = current_user.get_company_id()
    property = Property.query.filter_by(id=id, company_id=company_id).first()
    today = datetime.today()
    if property:
        tenants = Tenant.query.filter_by(property_id=id, company_id=company_id)
        leases = db.session.query(Unit, Lease, Tenant).filter_by(company_id=company_id, property_id=id).join(Lease, Lease.unit_id==Unit.id).join(Tenant, Tenant.id==Lease.tenant_id).all()     
        return render_template("property.html", user=current_user, property=property, leases=leases, tenants=tenants, units=get_units(property.id), today=today)
    return page_not_found(404)

@property.route('/create', methods=['GET', 'POST'])
@login_required
@can_create_required
def create():
    if request.method == "POST":
        # Basic Information
        name = request.form.get('name', '').strip()
        type = request.form.get('type')
        portfolio_id = request.form.get('portfolio_id')
        description = request.form.get('description', '').strip()
        property_status = request.form.get('property_status', 'Active')
        maintenance_priority = request.form.get('maintenance_priority', 'Medium')

        # Location & Address
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state')
        zip_code = request.form.get('zip_code', '').strip()
        neighborhood = request.form.get('neighborhood', '').strip()
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        # Property Details
        year_built = request.form.get('year_built')
        lot_size = request.form.get('lot_size')
        building_sqft = request.form.get('building_sqft')
        stories = request.form.get('stories')
        parking_spaces = request.form.get('parking_spaces')

        # Financial Information
        purchase_price = request.form.get('purchase_price')
        purchase_date = request.form.get('purchase_date')
        current_market_value = request.form.get('current_market_value')
        annual_property_tax = request.form.get('annual_property_tax')
        annual_insurance = request.form.get('annual_insurance')
        monthly_hoa_fees = request.form.get('monthly_hoa_fees')
        acquisition_method = request.form.get('acquisition_method')

        # Management & Operations
        property_manager = request.form.get('property_manager', '').strip()

        # Server-side validation
        if not name:
            flash('Property name is required.', 'error')
            return render_template("/create_enhanced.html", user=current_user, states=get_states(), portfolios=get_portfolios())

        if zip_code and not zip_code.isdigit():
            flash('Zip code must contain only numbers.', 'error')
            return render_template("/create_enhanced.html", user=current_user, states=get_states(), portfolios=get_portfolios())

        if zip_code and len(zip_code) != 5:
            flash('Zip code must be exactly 5 digits.', 'error')
            return render_template("/create_enhanced.html", user=current_user, states=get_states(), portfolios=get_portfolios())

        if year_built and (int(year_built) < 1800 or int(year_built) > 2030):
            flash('Year built must be between 1800 and 2030.', 'error')
            return render_template("/create_enhanced.html", user=current_user, states=get_states(), portfolios=get_portfolios())

        # Data conversion and validation
        try:
            # Convert empty strings to None for optional fields
            portfolio_id = int(portfolio_id) if portfolio_id else None
            year_built = int(year_built) if year_built else None
            lot_size = int(lot_size) if lot_size else None
            building_sqft = int(building_sqft) if building_sqft else None
            stories = int(stories) if stories else None
            parking_spaces = int(parking_spaces) if parking_spaces else None

            # Convert coordinates
            latitude = float(latitude) if latitude else None
            longitude = float(longitude) if longitude else None

            # Convert financial fields
            purchase_price = float(purchase_price) if purchase_price else None
            current_market_value = float(current_market_value) if current_market_value else None
            annual_property_tax = float(annual_property_tax) if annual_property_tax else None
            annual_insurance = float(annual_insurance) if annual_insurance else None
            monthly_hoa_fees = float(monthly_hoa_fees) if monthly_hoa_fees else None

            # Convert date
            from datetime import datetime
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date() if purchase_date else None

        except ValueError as e:
            flash('Invalid numeric value provided. Please check your inputs.', 'error')
            return render_template("/create_enhanced.html", user=current_user, states=get_states(), portfolios=get_portfolios())

        # Create property with all fields
        try:
            from datetime import datetime
            company_id = current_user.get_company_id()
            new_property = Property(
                # Basic Information
                name=name,
                company_id=company_id,
                portfolio_id=portfolio_id,
                type=type,
                description=description,
                property_status=property_status,
                maintenance_priority=maintenance_priority,

                # Location & Address
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                neighborhood=neighborhood,
                latitude=latitude,
                longitude=longitude,

                # Property Details
                year_built=year_built,
                lot_size=lot_size,
                building_sqft=building_sqft,
                stories=stories,
                parking_spaces=parking_spaces,

                # Financial Information
                purchase_price=purchase_price,
                purchase_date=purchase_date,
                current_market_value=current_market_value,
                annual_property_tax=annual_property_tax,
                annual_insurance=annual_insurance,
                monthly_hoa_fees=monthly_hoa_fees,
                acquisition_method=acquisition_method,

                # Management & Operations
                property_manager=property_manager,

                # Metadata
                created_date=datetime.now(),
                updated_date=datetime.now()
            )

            db.session.add(new_property)
            db.session.commit()

            flash(f'Property "{name}" created successfully with enhanced details!', 'success')
            return redirect(url_for('property.properties'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating property: {str(e)}', 'error')
            return render_template("/create_enhanced.html", user=current_user, states=get_states(), portfolios=get_portfolios())

    # GET request - show the enhanced form
    return render_template("/create_enhanced.html", user=current_user, states=get_states(), portfolios=get_portfolios())

@property.route('/create/enhanced', methods=['GET', 'POST'])
@login_required
@can_create_required
def create_enhanced():
    """Enhanced property creation with wizard interface"""
    return create()  # Use the same logic, just different template route

@property.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@can_edit_required
def edit(id):
    company_id = current_user.get_company_id()
    property = Property.query.filter_by(id=id, company_id=company_id).first()
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
@can_delete_required
def delete(id):
    """Delete a property and all associated data."""
    company_id = current_user.get_company_id()
    property = Property.query.filter_by(id=id, company_id=company_id).first()
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
