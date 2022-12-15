
from website.models import Portfolio, Tenant, Property, Unit
from flask_login import current_user

def get_tenants():
    tenants = Tenant.query.filter_by(landlord=current_user.id).order_by(Tenant.last_name.asc()).all()
    return tenants

def get_tenant(id):
    tenant = Tenant.query.filter_by(id=id).first()
    return tenant

def get_portfolios():
    portfolios = Portfolio.query.filter_by(owner=current_user.id).order_by(Portfolio.name.asc()).all()
    return portfolios

def get_properties():
    properties = Property.query.filter_by(owner=current_user.id).order_by(Property.name.asc()).all()
    return properties

def get_units(id):
    units = Unit.query.filter_by(owner=current_user.id, property=id).order_by(Unit.name.asc()).all()
    return units

def get_states():
    states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'PR', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'VI', 'WA', 'WV', 'WI', 'WY']
    return states
