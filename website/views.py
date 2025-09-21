
from website.models import Portfolio, Tenant, Property, Unit
from flask_login import current_user

def get_tenants():
    company_id = current_user.get_company_id()
    tenants = Tenant.query.filter_by(company_id=company_id).order_by(Tenant.last_name.asc()).all()
    return tenants

def get_tenant(id):
    company_id = current_user.get_company_id()
    tenant = Tenant.query.filter_by(id=id, company_id=company_id).first()
    return tenant

def get_portfolios():
    company_id = current_user.get_company_id()
    portfolios = Portfolio.query.filter_by(company_id=company_id).order_by(Portfolio.name.asc()).all()
    return portfolios

def get_properties():
    company_id = current_user.get_company_id()
    properties = Property.query.filter_by(company_id=company_id).order_by(Property.name.asc()).all()
    return properties

def get_units(id):
    company_id = current_user.get_company_id()
    units = Unit.query.filter_by(company_id=company_id, property_id=id).order_by(Unit.name.asc()).all()
    return units

def get_states():
    states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'PR', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'VI', 'WA', 'WV', 'WI', 'WY']
    return states
