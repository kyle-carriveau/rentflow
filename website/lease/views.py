from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Lease, Unit, Tenant, Property
from website import db 
from flask_login import login_required, current_user
from datetime import datetime
from website.views import get_tenants, get_units, get_properties
from website.errors import page_not_found
from .forms import LeaseForm

lease = Blueprint('lease', __name__, template_folder='templates')

@lease.route('/', methods=['GET', 'POST'])
@login_required
def leases():
    leases = get_all_leases_for_user()
    today_date = datetime.now().date()
    return render_template("leases.html", user=current_user, leases=leases, today_date=today_date)

@lease.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def show(id):
    """View lease details."""
    # Only show leases for properties owned by current user
    lease = db.session.query(Lease).join(Unit).join(Property).filter(
        Lease.id == id,
        Property.owner == current_user.id
    ).first()
    if not lease:
        return page_not_found(404)
    today_date = datetime.now().date()
    return render_template("lease.html", user=current_user, lease=lease, today_date=today_date)

@lease.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    # Only allow updating leases for properties owned by current user
    lease = db.session.query(Lease).join(Unit).join(Property).filter(
        Lease.id == id,
        Property.owner == current_user.id
    ).first_or_404()
    form = LeaseForm(obj=lease)
    form.tenant.choices = [(t.id, f"{t.first_name} {t.last_name}") for t in Tenant.query.filter_by(landlord=current_user.id)]
    form.unit.choices = [(u.id, u.name) for u in Unit.query.filter_by(property_id=lease.unit.property_id)]
    
    if form.validate_on_submit():
        form.populate_obj(lease)
        lease.start = datetime.combine(form.start.data, datetime.min.time())
        lease.end = datetime.combine(form.end.data, datetime.min.time())
        db.session.commit()
        return redirect(url_for('property.home', user=current_user, id=lease.unit.property_id))
    
    return render_template("update_lease.html", user=current_user, form=form, lease=lease, properties=get_properties())


@lease.route('/create/<int:id>', methods=['GET', 'POST'])
@login_required
def create(id):
    """Create a new lease for a property."""
    # Verify property ownership
    property = Property.query.filter_by(id=id, owner=current_user.id).first()
    if not property:
        return page_not_found(404)
    
    form = LeaseForm()
    form.tenant.choices = [(t.id, f"{t.first_name} {t.last_name}") for t in Tenant.query.filter_by(landlord=current_user.id)]
    form.unit.choices = [(u.id, u.name) for u in Unit.query.filter_by(property=id)]
    
    if form.validate_on_submit():
        tenant_id = form.tenant.data
        unit_id = form.unit.data
        start = form.start.data
        end = form.end.data
        rent = form.rent.data

        # Additional validation
        if start >= end:
            flash('Start date must be before end date.', 'error')
            return render_template("create_lease.html", user=current_user, form=form, property=property)

        # Verify unit belongs to this property
        unit = Unit.query.filter_by(id=unit_id, property=id).first()
        if not unit:
            flash('Invalid unit selected.', 'error')
            return render_template("create_lease.html", user=current_user, form=form, property=property)

        new_lease = Lease(tenant_id=tenant_id, unit_id=unit_id, property_id=id, start=start, end=end, rent=rent)
        db.session.add(new_lease)
        db.session.commit()
        flash('Lease created successfully!', 'success')
        return redirect(url_for('property.home', id=id))
    
    return render_template("create_lease.html", user=current_user, form=form, property=property)

@lease.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a lease."""
    # Only allow deleting leases for properties owned by current user
    lease = db.session.query(Lease).join(Unit).join(Property).filter(
        Lease.id == id,
        Property.owner == current_user.id
    ).first()
    
    if not lease:
        return page_not_found(404)
    
    property_id = lease.property_id
    tenant_name = f"{lease.tenant_ref.first_name} {lease.tenant_ref.last_name}" if lease.tenant_ref else "Unknown"
    unit_name = lease.unit_ref.name if lease.unit_ref else "Unknown"
    
    try:
        db.session.delete(lease)
        db.session.commit()
        flash(f'Lease for {tenant_name} in {unit_name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting lease.', 'error')
    
    return redirect(url_for('property.home', id=property_id))

def get_all_leases_for_user():
    """Get all leases for properties owned by current user, ordered by most recent first."""
    all_leases = db.session.query(Lease).join(Unit).join(Property).filter(
        Property.owner == current_user.id
    ).order_by(Lease.end.desc(), Lease.start.desc()).all()
    return all_leases

def get_active_leases():
    today = datetime.now().date()
    # Only return leases for properties owned by current user
    active_leases = db.session.query(Lease).join(Unit).join(Property).filter(
        Property.owner == current_user.id,
        Lease.start <= today,
        Lease.end >= today
    ).all()
    return active_leases

def get_active_leases_for_property(property_id):
    today = datetime.now().date()
    active_leases = Lease.query.join(Unit).join(Property).\
                    filter(Property.id == property_id, Lease.start <= today, Lease.end >= today).\
                    all()
    return active_leases