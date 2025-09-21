from flask import render_template, Blueprint
from flask_login import login_required, current_user
from website.views import get_properties, get_tenants

profile = Blueprint('profile', __name__, template_folder='templates')

@profile.route('/dashboard')
@login_required
def dashboard():
    from datetime import datetime
    from website.models import Property, Portfolio, Tenant
    
    # Get user's data
    company_id = current_user.get_company_id()
    properties = Property.query.filter_by(company_id=company_id).all()
    portfolios = Portfolio.query.filter_by(company_id=company_id).all()
    tenants = Tenant.query.filter_by(landlord=current_user.id).all()
    
    # Pass today's date for lease calculations
    today_date = datetime.now().date()
    
    return render_template("dashboard.html", 
                         user=current_user, 
                         properties=properties,
                         portfolios=portfolios,
                         tenants=tenants,
                         today_date=today_date)

@profile.route('/')
@login_required
def home():
    return render_template("profile.html", user=current_user, properties=get_properties(), tenants=get_tenants()) 

@profile.route('/settings')
@login_required
def settings():
    return render_template("settings.html", user=current_user)

