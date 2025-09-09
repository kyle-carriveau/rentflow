from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Unit, Property
from website import db 
from flask_login import login_required, current_user
from website.errors import page_not_found

unit = Blueprint('unit', __name__, template_folder='templates')

@unit.route('/')
@login_required
def list_units():
    """List all units for the current user."""
    units = Unit.query.filter_by(owner=current_user.id).all()
    return render_template("units.html", user=current_user, units=units)

@unit.route('/create/<int:id>', methods=['GET', 'POST'])
@login_required
def create(id):
    """Create a new unit for a property."""
    # Verify property ownership
    property = Property.query.filter_by(id=id, owner=current_user.id).first()
    if not property:
        return page_not_found(404)
    
    if request.method == "POST":
        name = request.form.get('name', '').strip()
        bedrooms = request.form.get('bedrooms', '').strip()
        bathrooms = request.form.get('bathrooms', '').strip()
        sqft = request.form.get('sqft', '').strip()
        rent = request.form.get('rent', '').strip()
        
        # Server-side validation
        if not name:
            flash('Unit name is required.', 'error')
            return render_template("create_unit.html", user=current_user, property=property)
        
        # Validate numeric fields
        try:
            bedrooms_int = int(bedrooms) if bedrooms else 0
            bathrooms_int = int(bathrooms) if bathrooms else 0
            sqft_int = int(sqft) if sqft else None
            rent_int = int(rent) if rent else None
            
            if bedrooms_int < 0 or bathrooms_int < 0:
                flash('Bedrooms and bathrooms must be non-negative.', 'error')
                return render_template("create_unit.html", user=current_user, property=property)
                
            if sqft_int is not None and sqft_int <= 0:
                flash('Square footage must be positive.', 'error')
                return render_template("create_unit.html", user=current_user, property=property)
                
            if rent_int is not None and rent_int < 0:
                flash('Rent must be non-negative.', 'error')
                return render_template("create_unit.html", user=current_user, property=property)
                
        except ValueError:
            flash('Please enter valid numbers for bedrooms, bathrooms, square footage, and rent.', 'error')
            return render_template("create_unit.html", user=current_user, property=property)
        
        new_unit = Unit(name=name, bedrooms=bedrooms_int, bathrooms=bathrooms_int, sqft=sqft_int, property=id, rent=rent_int, owner=current_user.id)
        db.session.add(new_unit)
        db.session.commit()
        flash('Unit created successfully!', 'success')
        return redirect(url_for('property.home', id=id))
        
    return render_template("create_unit.html", user=current_user, property=property)

@unit.route('/<int:id>')
@login_required
def show(id):
    """Show unit details."""
    unit = Unit.query.filter_by(id=id, owner=current_user.id).first()
    if not unit:
        return page_not_found(404)
    return render_template("unit.html", unit=unit, user=current_user)

@unit.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing unit."""
    unit = Unit.query.filter_by(id=id, owner=current_user.id).first()
    if not unit:
        return page_not_found(404)
    
    # Get the property for validation
    property = Property.query.filter_by(id=unit.property, owner=current_user.id).first()
    if not property:
        return page_not_found(404)
    
    if request.method == "POST":
        name = request.form.get('name', '').strip()
        bedrooms = request.form.get('bedrooms', '').strip()
        bathrooms = request.form.get('bathrooms', '').strip()
        sqft = request.form.get('sqft', '').strip()
        rent = request.form.get('rent', '').strip()
        description = request.form.get('description', '').strip()
        
        # Server-side validation
        if not name:
            flash('Unit name is required.', 'error')
            return render_template("edit_unit.html", user=current_user, unit=unit, property=property)
        
        # Validate numeric fields
        try:
            bedrooms_int = int(bedrooms) if bedrooms else 0
            bathrooms_int = int(bathrooms) if bathrooms else 0
            sqft_int = int(sqft) if sqft else None
            rent_int = int(rent) if rent else None
            
            if bedrooms_int < 0 or bathrooms_int < 0:
                flash('Bedrooms and bathrooms must be non-negative.', 'error')
                return render_template("edit_unit.html", user=current_user, unit=unit, property=property)
                
            if sqft_int is not None and sqft_int <= 0:
                flash('Square footage must be positive.', 'error')
                return render_template("edit_unit.html", user=current_user, unit=unit, property=property)
                
            if rent_int is not None and rent_int < 0:
                flash('Rent must be non-negative.', 'error')
                return render_template("edit_unit.html", user=current_user, unit=unit, property=property)
                
        except ValueError:
            flash('Please enter valid numbers for bedrooms, bathrooms, square footage, and rent.', 'error')
            return render_template("edit_unit.html", user=current_user, unit=unit, property=property)
        
        # Update unit
        unit.name = name
        unit.bedrooms = bedrooms_int
        unit.bathrooms = bathrooms_int
        unit.sqft = sqft_int
        unit.rent = rent_int
        unit.description = description
        
        db.session.commit()
        flash('Unit updated successfully!', 'success')
        return redirect(url_for('unit.show', id=id))
        
    return render_template("edit_unit.html", user=current_user, unit=unit, property=property)

@unit.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a unit."""
    unit = Unit.query.filter_by(id=id, owner=current_user.id).first()
    if not unit:
        return page_not_found(404)
    
    property_id = unit.property
    unit_name = unit.name
    
    try:
        db.session.delete(unit)
        db.session.commit()
        flash(f'Unit "{unit_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting unit. It may have associated leases.', 'error')
    
    return redirect(url_for('property.home', id=property_id))