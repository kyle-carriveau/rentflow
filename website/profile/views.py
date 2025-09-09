from flask import render_template, Blueprint
from flask_login import login_required, current_user
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

