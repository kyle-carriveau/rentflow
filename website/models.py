from . import db 
from flask_login import UserMixin
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.Integer)
    password_hash = db.Column(db.String(1500))
    company = db.Column(db.String(150))

    def __init__(self, first_name="", last_name="", email="", password=""):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = generate_password_hash(password)
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    owner = db.Column(db.Integer, db.ForeignKey('user.id'))

class Property(db.Model):
    __tablename__ = 'property'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    owner = db.Column(db.Integer, db.ForeignKey('user.id'))
    portfolio = db.Column(db.Integer, db.ForeignKey('portfolio.id'))
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.Integer)
    #bought = db.Column(db.Date)
    type = db.Column(db.String(150))

class Unit(db.Model):
    __tablename__ = 'unit'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    owner = db.Column(db.Integer, db.ForeignKey('user.id'))
    property = db.Column(db.Integer, db.ForeignKey('property.id'))
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    rent = db.Column(db.Integer)
    sqft = db.Column(db.Integer)
    description = db.Column(db.String(500))

class Tenant(db.Model):
    __tablename__ = 'tenant'
    id = db.Column(db.Integer, primary_key=True)
    landlord = db.Column(db.Integer, db.ForeignKey('user.id'))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.Integer)
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.Integer)
    property = db.Column(db.Integer, db.ForeignKey('property.id'))

class Lease(db.Model):
    __tablename__ = 'lease'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    rent = db.Column(db.Integer)