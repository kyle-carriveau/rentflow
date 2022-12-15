from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Unit
from website import db 
from flask_login import login_required, current_user

unit = Blueprint('unit', __name__, template_folder='templates')

@unit.route('/create/<int:id>', methods=['GET', 'POST'])
@login_required
def create(id):
    if request.method == "POST":
        name = request.form.get('name')
        bedrooms = request.form.get('bedrooms')
        bathrooms = request.form.get('bathrooms')
        sqft = request.form.get('sqft')
        property = id
        rent = request.form.get('rent')
        
        new_unit = Unit(name=name, bedrooms=bedrooms, bathrooms=bathrooms, sqft=sqft, property=property, rent=rent, owner=current_user.id)
        db.session.add(new_unit)
        db.session.commit()
        return redirect(url_for('property.home', id=id))
        
    return render_template("create_unit.html", user=current_user)

@unit.route('/<int:id>')
@login_required
def show(id):
    unit = Unit.query.filter_by(id=id, owner=current_user.id).first()
    return render_template("unit.html", unit=unit, user=current_user)