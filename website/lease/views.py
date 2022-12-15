from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Lease
from website import db 
from flask_login import login_required, current_user
from datetime import datetime
from website.views import get_tenants, get_units, get_properties

lease = Blueprint('lease', __name__, template_folder='templates')

@lease.route('/', methods=['GET', 'POST'])
@login_required
def leases():
    l = Lease.query.all()
    for lease in l:
        print(lease.property_id)
    return render_template("leases.html", user=current_user, leases=l)

@lease.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def show(id):
    lease = Lease.query.filter_by(id=id).first()
    return render_template("lease.html", user=current_user, lease=lease)

@lease.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    return render_template("edit_lease.html", user=current_user)

@lease.route('/create/<int:id>', methods=['GET', 'POST'])
@login_required
def create(id):
    if request.method == "POST":
        tenant = request.form.get('tenant')
        unit = request.form.get('unit')
        start = request.form.get('start')
        end = request.form.get('end')
        rent = request.form.get('rent')

        new_lease = Lease(tenant_id=tenant, unit_id=unit, start=datetime.strptime(start, '%Y-%m-%d'), end=datetime.strptime(end, '%Y-%m-%d'), rent=rent)
        db.session.add(new_lease)
        db.session.commit()
        return redirect(url_for('property.home', user=current_user, id=id))
        
    return render_template("create_lease.html", user=current_user, tenants=get_tenants(), units=get_units(id), properties=get_properties())
