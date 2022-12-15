from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import User, Tenant
from website import db 
from flask_login import login_required, current_user
from website.views import get_tenant, get_properties, get_states

tenant = Blueprint('tenant', __name__, template_folder='templates')

@tenant.route('/', methods=['GET', 'POST'])
@login_required
def tenants(): 
    tenants = db.session.query(Tenant).filter_by(landlord=current_user.id).all()
    return render_template("tenants.html", user=current_user, tenants=tenants)

@tenant.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == "POST":
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        property = request.form.get('property')
        address = request.form.get('address')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')

        # Check if email is already in use
        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email is already in use.', category='info')
            return redirect(url_for('tenant.create'))

        new_tenant = Tenant(first_name=first_name, last_name=last_name, email=email, phone=phone, property=property, address=address, city=city, state=state, zip_code=zip_code, landlord=current_user.id)

        db.session.add(new_tenant)
        db.session.commit()
        return redirect(url_for('tenant.tenants'))

    return render_template("/create_tenant.html", user=current_user, properties=get_properties(), states=get_states())

@tenant.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def home(id):
    return render_template("/tenant.html",tenant=get_tenant(id), user=current_user)

@tenant.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    tenant = Tenant.query.filter_by(id=id, landlord=current_user.id)
    return render_template("edit_tenant.html",tenant=tenant, user=current_user, states=get_states())