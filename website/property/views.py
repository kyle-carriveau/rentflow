from email.policy import default
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
        name = request.form.get('property_name')
        portfolio = request.form.get('portfolio')
        new_property = Property(name=name, owner=current_user.id, portfolio=portfolio)
        db.session.add(new_property)
        db.session.commit()
        return redirect(url_for("property.properties", user=current_user, properties=get_properties(), portfolios=get_portfolios()))
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
        name = request.form.get('name')
        type = request.form.get('type')
        portfolio = request.form.get('portfolio')
        address = request.form.get('address')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')

        new_property = Property(name=name, owner=current_user.id, portfolio=portfolio, type=type, address=address, city=city, state=state, zip_code=zip_code)
        db.session.add(new_property)
        db.session.commit()
        return redirect(url_for('property.properties'))

    return render_template("/create.html", user=current_user, states=get_states(), portfolios=get_portfolios())


@property.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    #property = db.session.query(Property).filter_by(id=id, owner=current_user.id).first()
    property = Property.query.filter_by(id=id, owner=current_user.id).first()
    if request.method == "POST":
        property.name = request.form.get('name')
        property.type = request.form.get('type')
        property.address = request.form.get('address')
        property.city = request.form.get('city')
        property.state = request.form.get('state')
        property.zip_code = request.form.get('zip_code')

        db.session.commit()
        return redirect(url_for('property.home', id=id))

    return render_template("/edit.html", user=current_user, property=property, states=get_states())


