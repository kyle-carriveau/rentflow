from . import db 
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import and_
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.Integer)
    password_hash = db.Column(db.String(1500), nullable=False)
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
    name = db.Column(db.String(150), nullable=False)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    portfolio = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=True)
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.Integer)
    #bought = db.Column(db.Date)
    type = db.Column(db.String(150))
    
    # Relationships with cascade delete
    units = db.relationship('Unit', backref='property_ref', cascade='all, delete-orphan')
    tenants = db.relationship('Tenant', backref='property_ref', cascade='all, delete-orphan')
    leases = db.relationship('Lease', backref='property_ref', cascade='all, delete-orphan')
    
    def get_lease_status(self):
        """Returns the lease status of this property"""
        from datetime import datetime
        current_date = datetime.now()
        
        # Check if property has any active leases through its units
        active_leases = db.session.query(Lease).join(Unit).filter(
            and_(
                Unit.property == self.id,
                Lease.start <= current_date,
                Lease.end >= current_date
            )
        ).count()
        
        if active_leases > 0:
            return "Leased"
        else:
            return "Vacant"

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
    
    # Relationships with cascade delete
    leases = db.relationship('Lease', backref='unit_ref', cascade='all, delete-orphan')
    
    def get_lease_status(self):
        """Get unit's current lease status based on active leases."""
        from datetime import datetime
        today = datetime.now().date()
        
        active_leases = [lease for lease in self.leases 
                        if lease.start.date() <= today <= lease.end.date()]
        
        if active_leases:
            return 'Occupied'
        
        future_leases = [lease for lease in self.leases 
                        if lease.start.date() > today]
        
        if future_leases:
            return 'Reserved'
            
        return 'Available'
    
    def get_current_lease(self):
        """Get the unit's current active lease, if any."""
        from datetime import datetime
        today = datetime.now().date()
        
        for lease in self.leases:
            if lease.start.date() <= today <= lease.end.date():
                return lease
        return None
    
    def get_current_tenant(self):
        """Get the current tenant for this unit."""
        current_lease = self.get_current_lease()
        if current_lease:
            return current_lease.tenant_ref
        return None
    
    def get_next_lease(self):
        """Get the next upcoming lease for this unit."""
        from datetime import datetime
        today = datetime.now().date()
        
        future_leases = [lease for lease in self.leases 
                        if lease.start.date() > today]
        
        if future_leases:
            return min(future_leases, key=lambda x: x.start.date())
        return None

class Tenant(db.Model):
    __tablename__ = 'tenant'
    id = db.Column(db.Integer, primary_key=True)
    landlord = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.Integer)
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.Integer)
    property = db.Column(db.Integer, db.ForeignKey('property.id'))
    
    # Relationships with cascade delete
    leases = db.relationship('Lease', backref='tenant_ref', cascade='all, delete-orphan')
    
    def get_lease_status(self):
        """Get tenant's current lease status based on active leases."""
        from datetime import datetime
        today = datetime.now().date()
        
        active_leases = [lease for lease in self.leases 
                        if lease.start.date() <= today <= lease.end.date()]
        
        if active_leases:
            return 'Active'
        
        future_leases = [lease for lease in self.leases 
                        if lease.start.date() > today]
        
        if future_leases:
            return 'Future'
            
        past_leases = [lease for lease in self.leases 
                      if lease.end.date() < today]
        
        if past_leases:
            return 'Former'
            
        return 'Prospect'
    
    def get_current_lease(self):
        """Get the tenant's current active lease, if any."""
        from datetime import datetime
        today = datetime.now().date()
        
        for lease in self.leases:
            if lease.start.date() <= today <= lease.end.date():
                return lease
        return None
    
    def get_current_property(self):
        """Get the property for the tenant's current lease."""
        current_lease = self.get_current_lease()
        if current_lease and current_lease.unit_ref:
            return current_lease.unit_ref.property_ref
        return None
    
    def get_current_unit(self):
        """Get the unit for the tenant's current lease."""
        current_lease = self.get_current_lease()
        if current_lease:
            return current_lease.unit_ref
        return None

class Lease(db.Model):
    __tablename__ = 'lease'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    rent = db.Column(db.Integer, nullable=False)