from crypt import methods
from flask import render_template, Blueprint, redirect, url_for
from website.models import User
from website import db 
from flask_login import login_user, login_required, current_user
from werkzeug.security import generate_password_hash
from website.views import get_properties, get_tenants

profile = Blueprint('profile', __name__, template_folder='templates')

@profile.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

@profile.route('/')
@login_required
def home():
    return render_template("profile.html", user=current_user, properties=get_properties(), tenants=get_tenants()) 

@profile.route('/settings')
@login_required
def settings():
    return render_template("settings.html", user=current_user)

@profile.route('/create')
def check_user():
    user = User.query.filter_by(email="kyle.carriveau@gmail.com").first()
    if user:
        login_user(user, remember=True)
    else:
        new_user = User(first_name="Kyle", last_name="Carriveau", email="kyle.carriveau@gmail.com", password=generate_password_hash("password", method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
    return redirect(url_for('profile.home'))
