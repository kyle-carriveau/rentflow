from . import db 
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import and_
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    website = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='company_ref', lazy=True)
    portfolios = db.relationship('Portfolio', backref='company_ref', lazy=True)
    properties = db.relationship('Property', backref='company_ref', lazy=True)
    units = db.relationship('Unit', backref='company_ref', lazy=True)
    tenants = db.relationship('Tenant', backref='company_ref', lazy=True)
    leases = db.relationship('Lease', backref='company_ref', lazy=True)
    payments = db.relationship('Payment', backref='company_ref', lazy=True)
    expenses = db.relationship('Expense', backref='company_ref', lazy=True)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    # Role constants
    ROLE_OWNER = 'owner'
    ROLE_MANAGER = 'manager'
    ROLE_STAFF = 'staff'
    ROLE_VIEWER = 'viewer'
    
    ROLES = [ROLE_OWNER, ROLE_MANAGER, ROLE_STAFF, ROLE_VIEWER]
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.String(10))
    password_hash = db.Column(db.String(1500), nullable=False)
    company = db.Column(db.String(150))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_OWNER)
    
    # Relationships (tenants now managed at company level)

    def __init__(self, first_name="", last_name="", email="", password="", company_id=None, role=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.company_id = company_id
        self.role = role or self.ROLE_OWNER  # Default to owner role
        if password:
            self.password_hash = generate_password_hash(password)
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_or_create_company(self):
        """Get user's company or create a default one for backward compatibility."""
        if self.company_id:
            return self.company_ref
        
        # Create a default company for users without one
        from . import db
        default_company = Company(
            name=self.company or f"{self.first_name} {self.last_name} Properties",
            email=self.email
        )
        db.session.add(default_company)
        db.session.flush()  # Get the ID without committing
        
        # Assign user to the company
        self.company_id = default_company.id
        db.session.commit()
        
        return default_company
    
    def get_company_id(self):
        """Get user's company_id, creating one if necessary."""
        if self.company_id:
            return self.company_id
        company = self.get_or_create_company()
        return company.id
    
    def has_role(self, role):
        """Check if user has a specific role."""
        return self.role == role
    
    def is_owner(self):
        """Check if user is a company owner."""
        return self.role == self.ROLE_OWNER
    
    def is_manager(self):
        """Check if user is a manager or higher."""
        return self.role in [self.ROLE_OWNER, self.ROLE_MANAGER]
    
    def is_staff(self):
        """Check if user is staff or higher."""
        return self.role in [self.ROLE_OWNER, self.ROLE_MANAGER, self.ROLE_STAFF]
    
    def can_create(self):
        """Check if user can create new records."""
        return self.role in [self.ROLE_OWNER, self.ROLE_MANAGER, self.ROLE_STAFF]
    
    def can_edit(self):
        """Check if user can edit records."""
        return self.role in [self.ROLE_OWNER, self.ROLE_MANAGER, self.ROLE_STAFF]
    
    def can_delete(self):
        """Check if user can delete records."""
        return self.role in [self.ROLE_OWNER, self.ROLE_MANAGER]
    
    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role == self.ROLE_OWNER

class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    # Relationships
    properties = db.relationship('Property', backref='portfolio_ref', lazy=True)

class Property(db.Model):
    __tablename__ = 'property'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=True)
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.String(10))
    type = db.Column(db.String(150))
    
    # Relationships with cascade delete
    units = db.relationship('Unit', backref='property_ref', cascade='all, delete-orphan')
    tenants = db.relationship('Tenant', backref='tenant_property_ref', cascade='all, delete-orphan')
    leases = db.relationship('Lease', backref='lease_property_ref', cascade='all, delete-orphan')
    
    def get_lease_status(self):
        """Returns the lease status of this property"""
        from datetime import datetime
        current_date = datetime.now()
        
        # Check if property has any active leases through its units
        active_leases = db.session.query(Lease).join(Unit).filter(
            and_(
                Unit.property_id == self.id,
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
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
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
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.String(10))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    
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
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    rent = db.Column(db.Integer, nullable=False)
    
    # Relationships
    payments = db.relationship('Payment', backref='lease_ref', lazy=True, cascade='all, delete-orphan')
    
    def get_total_paid(self):
        """Calculate total amount paid for this lease."""
        return sum(payment.amount for payment in self.payments if payment.status == 'completed')
    
    def get_outstanding_balance(self):
        """Calculate outstanding balance for this lease."""
        from datetime import datetime
        
        # Calculate total rent due up to today
        today = datetime.now().date()
        lease_start = self.start.date()
        lease_end = min(self.end.date(), today)
        
        if lease_start > today:
            return 0
            
        # Simple monthly calculation (could be enhanced for daily proration)
        import calendar
        from dateutil.relativedelta import relativedelta
        
        total_due = 0
        current_date = lease_start.replace(day=1)  # Start from first of month
        
        while current_date <= lease_end:
            if current_date.month == lease_start.month and current_date.year == lease_start.year:
                # Prorate first month if needed
                days_in_month = calendar.monthrange(current_date.year, current_date.month)[1]
                days_occupied = days_in_month - lease_start.day + 1
                total_due += (self.rent * days_occupied) / days_in_month
            elif current_date <= lease_end:
                total_due += self.rent
            current_date += relativedelta(months=1)
        
        return max(0, total_due - self.get_total_paid())
    
    def is_overdue(self):
        """Check if rent payment is overdue."""
        return self.get_outstanding_balance() > 0

    @staticmethod
    def check_tenant_overlap(tenant_id, start_date, end_date, company_id, exclude_lease_id=None):
        """Check if a tenant has overlapping leases."""
        from sqlalchemy import and_, or_

        query = db.session.query(Lease).filter(
            Lease.tenant_id == tenant_id,
            Lease.company_id == company_id,
            or_(
                and_(Lease.start <= start_date, Lease.end >= start_date),  # New lease starts during existing lease
                and_(Lease.start <= end_date, Lease.end >= end_date),      # New lease ends during existing lease
                and_(Lease.start >= start_date, Lease.end <= end_date)     # Existing lease is within new lease
            )
        )

        if exclude_lease_id:
            query = query.filter(Lease.id != exclude_lease_id)

        return query.first() is not None

    @staticmethod
    def check_unit_overlap(unit_id, start_date, end_date, company_id, exclude_lease_id=None):
        """Check if a unit has overlapping leases."""
        from sqlalchemy import and_, or_

        query = db.session.query(Lease).filter(
            Lease.unit_id == unit_id,
            Lease.company_id == company_id,
            or_(
                and_(Lease.start <= start_date, Lease.end >= start_date),  # New lease starts during existing lease
                and_(Lease.start <= end_date, Lease.end >= end_date),      # New lease ends during existing lease
                and_(Lease.start >= start_date, Lease.end <= end_date)     # Existing lease is within new lease
            )
        )

        if exclude_lease_id:
            query = query.filter(Lease.id != exclude_lease_id)

        return query.first() is not None


class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('lease.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    
    # Payment method and status
    payment_method = db.Column(db.String(50), nullable=False, default='cash')  # cash, check, bank_transfer, credit_card
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed, refunded
    
    # References and notes
    reference_number = db.Column(db.String(100))  # Check number, transaction ID, etc.
    notes = db.Column(db.Text)
    
    # Late fee tracking
    late_fee = db.Column(db.Numeric(10, 2), default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    property_ref = db.relationship('Property', backref='payments')
    user_ref = db.relationship('User', backref='payments')
    
    def __repr__(self):
        return f'<Payment {self.id}: ${self.amount} for Lease {self.lease_id}>'
    
    def is_late(self):
        """Check if payment is late."""
        return self.payment_date.date() > self.due_date.date() if self.status == 'completed' else datetime.now().date() > self.due_date.date()


class Expense(db.Model):
    __tablename__ = 'expense'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=True)  # Nullable for general expenses
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    
    # Expense details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    expense_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Categorization
    category = db.Column(db.String(50), nullable=False)  # maintenance, utilities, insurance, taxes, etc.
    subcategory = db.Column(db.String(50))  # plumbing, electrical, water, electric, etc.
    
    # Description and details
    description = db.Column(db.String(255), nullable=False)
    vendor = db.Column(db.String(100))
    receipt_url = db.Column(db.String(255))  # Path to uploaded receipt
    
    # Tax and business categorization
    tax_deductible = db.Column(db.Boolean, default=True)
    recurring = db.Column(db.Boolean, default=False)
    recurring_frequency = db.Column(db.String(20))  # monthly, quarterly, yearly
    
    # References
    reference_number = db.Column(db.String(100))  # Invoice number, receipt number
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    property_ref = db.relationship('Property', backref='expenses')
    user_ref = db.relationship('User', backref='expenses')
    
    def __repr__(self):
        return f'<Expense {self.id}: ${self.amount} - {self.category}>'
    
    @staticmethod
    def get_categories():
        """Get list of expense categories."""
        return [
            'maintenance', 'repairs', 'utilities', 'insurance', 'taxes', 
            'management_fees', 'legal_fees', 'advertising', 'cleaning',
            'landscaping', 'mortgage_interest', 'depreciation', 'other'
        ]