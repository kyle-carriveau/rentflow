from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Lease, Unit, Tenant, Property
from website import db 
from flask_login import login_required, current_user
from datetime import datetime
from website.views import get_tenants, get_units, get_properties
from .forms import LeaseForm

lease = Blueprint('lease', __name__, template_folder='templates')

@lease.route('/', methods=['GET', 'POST'])
@login_required
def leases():
    leases = get_active_leases()
    return render_template("leases.html", user=current_user, leases=leases)

@lease.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def show(id):
    lease = Lease.query.filter_by(id=id).first()
    return render_template("lease.html", user=current_user, lease=lease)

@lease.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    lease = Lease.query.get_or_404(id)
    form = LeaseForm(obj=lease)
    form.tenant.choices = [(t.id, f"{t.first_name} {t.last_name}") for t in Tenant.query.all()]
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
    form = LeaseForm()
    form.tenant.choices = [(t.id, f"{t.first_name} {t.last_name}") for t in Tenant.query.all()]
    form.unit.choices = [(u.id, u.name) for u in Unit.query.filter_by(property=id)]
    
    if form.validate_on_submit():
        tenant_id = form.tenant.data
        unit_id = form.unit.data
        start = form.start.data
        end = form.end.data
        rent = form.rent.data

        new_lease = Lease(tenant_id=tenant_id, unit_id=unit_id, start=start, end=end, rent=rent)
        db.session.add(new_lease)
        db.session.commit()
        return redirect(url_for('property.home', user=current_user, id=id))
    
    return render_template("create_lease.html", user=current_user, form=form, property=id)

def get_active_leases():
    today = datetime.now().date()
    active_leases = Lease.query.filter(Lease.start <= today, Lease.end >= today).all()
    return active_leases

def get_active_leases_for_property(property_id):
    today = datetime.now().date()
    active_leases = Lease.query.join(Unit).join(Property).\
                    filter(Property.id == property_id, Lease.start <= today, Lease.end >= today).\
                    all()
    return active_leases