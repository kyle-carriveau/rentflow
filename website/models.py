from . import db
from flask_login import UserMixin, AnonymousUserMixin
from sqlalchemy.sql import func
from sqlalchemy import and_
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import uuid

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

    # Enhanced company fields
    description = db.Column(db.Text)
    industry = db.Column(db.String(100))
    company_size = db.Column(db.String(50))  # Property count ranges: 1-10, 11-50, 51-100, 100+
    tax_id = db.Column(db.String(50))
    license_number = db.Column(db.String(100))
    established_date = db.Column(db.Date)
    timezone = db.Column(db.String(50), default='America/New_York')
    currency = db.Column(db.String(10), default='USD')
    logo_url = db.Column(db.String(200))

    # Relationships
    users = db.relationship('User', backref='company_ref', lazy=True)
    portfolios = db.relationship('Portfolio', backref='company_ref', lazy=True)
    properties = db.relationship('Property', backref='company_ref', lazy=True)
    units = db.relationship('Unit', backref='company_ref', lazy=True)
    tenants = db.relationship('Tenant', backref='company_ref', lazy=True)
    leases = db.relationship('Lease', backref='company_ref', lazy=True)
    payments = db.relationship('Payment', backref='company_ref', lazy=True)
    expenses = db.relationship('Expense', backref='company_ref', lazy=True)

class CompanySettings(db.Model):
    __tablename__ = 'company_settings'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    setting_key = db.Column(db.String(100), nullable=False)
    setting_value = db.Column(db.Text)
    setting_type = db.Column(db.String(50), default='string')  # string, integer, boolean, json
    category = db.Column(db.String(50))  # business, financial, communication, system
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('company_id', 'setting_key', name='unique_company_setting'),)

    # Relationship
    company = db.relationship('Company', backref='settings', lazy=True)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    # Role constants
    ROLE_OWNER = 'owner'
    ROLE_MANAGER = 'manager'
    ROLE_STAFF = 'staff'
    ROLE_VIEWER = 'viewer'
    
    ROLES = [ROLE_OWNER, ROLE_MANAGER, ROLE_STAFF, ROLE_VIEWER]
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.String(10))
    password_hash = db.Column(db.String(1500), nullable=False)
    company = db.Column(db.String(150))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_OWNER)
    primary_role = db.Column(db.String(50), nullable=True)  # Business role: owner, manager, agent, other

    # Email verification fields (disabled - always verified)
    email_verified = db.Column(db.Boolean, nullable=False, default=True)
    email_verified_at = db.Column(db.DateTime, nullable=True)

    # Two-Factor Authentication fields
    totp_secret = db.Column(db.String(32), nullable=True)  # Base32 encoded secret
    totp_enabled = db.Column(db.Boolean, nullable=False, default=False)
    totp_backup_codes = db.Column(db.Text, nullable=True)  # Comma-separated backup codes
    totp_enabled_at = db.Column(db.DateTime, nullable=True)

    # Profile fields
    bio = db.Column(db.Text, nullable=True)  # Professional bio/description
    job_title = db.Column(db.String(100), nullable=True)  # Job title (e.g., "Senior Property Manager")
    department = db.Column(db.String(100), nullable=True)  # Department name
    date_joined = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    # Relationships (tenants now managed at company level)

    def __init__(self, first_name="", last_name="", email="", password="", company_id=None, role=None):
        self.uuid = str(uuid.uuid4())
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.company_id = company_id
        self.role = role or self.ROLE_OWNER  # Default to owner role
        # Set email as verified by default (email verification disabled)
        self.email_verified = True
        self.email_verified_at = db.func.current_timestamp()
        if password:
            self.set_password(password, validate_policy=False)
        
    def set_password(self, password, validate_policy=True):
        """
        Set user password with optional policy validation.
        Returns (success, error_messages) tuple when validate_policy=True.
        """
        if validate_policy:
            from .password_policy import PasswordPolicy, PasswordHistory

            # Validate password strength
            is_valid, errors = PasswordPolicy.validate_password_strength(password)
            if not is_valid:
                return False, errors

            # Check password reuse (only for existing users with ID)
            if self.id and PasswordHistory.check_password_reuse(self.id, password):
                return False, ["Password has been used recently. Please choose a different password."]

        # Generate new password hash
        new_hash = generate_password_hash(password)

        # Save old password to history if this is a password change (user exists)
        if validate_policy and self.id and self.password_hash:
            from .password_policy import PasswordHistory
            PasswordHistory.add_password_to_history(self.id, self.password_hash)

        # Set new password
        self.password_hash = new_hash

        if validate_policy:
            return True, []
        return True

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Return the UUID for Flask-Login instead of the integer ID"""
        return self.uuid

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

    @property
    def properties(self):
        """Get all properties for user's company."""
        if self.company_ref:
            return self.company_ref.properties
        return []
    
    def can_delete(self):
        """Check if user can delete records."""
        return self.role in [self.ROLE_OWNER, self.ROLE_MANAGER]
    
    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role == self.ROLE_OWNER

    @classmethod
    def find_by_uuid(cls, user_uuid, company_id=None):
        """Find user by UUID with optional company_id filter for security."""
        query = cls.query.filter_by(uuid=user_uuid)
        if company_id:
            query = query.filter_by(company_id=company_id)
        return query.first()

class AnonymousUser(AnonymousUserMixin):
    """Anonymous user proxy for Flask-Login with role-checking methods."""

    # Add safe default attributes to prevent template errors
    @property
    def first_name(self):
        return "Guest"

    @property
    def last_name(self):
        return "User"

    @property
    def email(self):
        return ""

    @property
    def company_id(self):
        return None

    @property
    def role(self):
        return "anonymous"

    def is_owner(self):
        return False

    def is_manager(self):
        return False

    def is_staff(self):
        return False

    def can_create(self):
        return False

    def can_edit(self):
        return False

    def can_delete(self):
        return False

    def can_manage_users(self):
        return False

class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    # Relationships
    properties = db.relationship('Property', backref='portfolio_ref', lazy=True)

    def __init__(self, name="", company_id=None):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.company_id = company_id

    @classmethod
    def find_by_uuid(cls, portfolio_uuid, company_id=None):
        """Find portfolio by UUID with optional company_id filter for security."""
        query = cls.query.filter_by(uuid=portfolio_uuid)
        if company_id:
            query = query.filter_by(company_id=company_id)
        return query.first()

class Property(db.Model):
    __tablename__ = 'property'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=True)

    # Basic Address Information
    address = db.Column(db.String(150))
    city = db.Column(db.String(150))
    state = db.Column(db.String(150))
    zip_code = db.Column(db.String(10))
    neighborhood = db.Column(db.String(150))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # Property Details
    type = db.Column(db.String(150))
    year_built = db.Column(db.Integer)
    lot_size = db.Column(db.Integer)  # in square feet
    building_sqft = db.Column(db.Integer)
    stories = db.Column(db.Integer)
    parking_spaces = db.Column(db.Integer)
    description = db.Column(db.Text)

    # Financial Information
    purchase_price = db.Column(db.Numeric(12, 2))
    purchase_date = db.Column(db.Date)
    current_market_value = db.Column(db.Numeric(12, 2))
    annual_property_tax = db.Column(db.Numeric(10, 2))
    annual_insurance = db.Column(db.Numeric(10, 2))
    monthly_hoa_fees = db.Column(db.Numeric(8, 2))

    # Management & Operations
    property_manager = db.Column(db.String(150))
    acquisition_method = db.Column(db.String(50))  # Purchase, Inheritance, Gift, Other
    property_status = db.Column(db.String(50), default='Active')  # Active, Inactive, Under Renovation, For Sale
    maintenance_priority = db.Column(db.String(20), default='Medium')  # High, Medium, Low

    # Metadata (optional for existing properties)
    created_date = db.Column(db.DateTime, nullable=True)
    updated_date = db.Column(db.DateTime, nullable=True)

    # Occupancy Status (cached for performance)
    occupancy_status = db.Column(db.String(20), default='Vacant')  # Vacant, Partially Occupied, Fully Occupied
    status_updated_at = db.Column(db.DateTime)  # Timestamp of last status update

    # Relationships with cascade delete
    units = db.relationship('Unit', backref='property_ref', cascade='all, delete-orphan')
    tenants = db.relationship('Tenant', backref='tenant_property_ref', cascade='all, delete-orphan')
    leases = db.relationship('Lease', backref='lease_property_ref', cascade='all, delete-orphan')
    photos = db.relationship('PropertyPhoto', backref='property', cascade='all, delete-orphan')
    documents = db.relationship('PropertyDocument', backref='property', cascade='all, delete-orphan')

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

    def update_occupancy_status(self):
        """
        Update the cached occupancy status based on unit occupancy.

        Status Logic:
        - Fully Occupied: All units are occupied
        - Partially Occupied: Some units occupied, some available
        - Vacant: No units are occupied

        Returns:
            str: The new occupancy status
        """
        from datetime import datetime

        # If no units, property is vacant
        if not self.units or len(self.units) == 0:
            old_status = self.occupancy_status
            new_status = 'Vacant'

            if new_status != old_status:
                self.occupancy_status = new_status
                self.status_updated_at = datetime.now()

            return new_status

        # Count occupied units
        total_units = len(self.units)
        occupied_units = sum(1 for unit in self.units if unit.get_lease_status() == 'Occupied')

        old_status = self.occupancy_status

        # Determine new status
        if occupied_units == 0:
            new_status = 'Vacant'
        elif occupied_units == total_units:
            new_status = 'Fully Occupied'
        else:
            new_status = 'Partially Occupied'

        # Update if status changed
        if new_status != old_status:
            self.occupancy_status = new_status
            self.status_updated_at = datetime.now()

        return new_status

    def __init__(self, name="", company_id=None, portfolio_id=None):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.company_id = company_id
        self.portfolio_id = portfolio_id

    @classmethod
    def find_by_uuid(cls, property_uuid, company_id=None):
        """Find property by UUID with optional company_id filter for security."""
        query = cls.query.filter_by(uuid=property_uuid)
        if company_id:
            query = query.filter_by(company_id=company_id)
        return query.first()

class PropertyPhoto(db.Model):
    __tablename__ = 'property_photo'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    is_primary = db.Column(db.Boolean, default=False)
    caption = db.Column(db.String(500))
    uploaded_date = db.Column(db.DateTime, default=db.func.current_timestamp())

class PropertyDocument(db.Model):
    __tablename__ = 'property_document'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    document_type = db.Column(db.String(100))  # Deed, Permit, Insurance, etc.
    description = db.Column(db.String(500))
    uploaded_date = db.Column(db.DateTime, default=db.func.current_timestamp())

class Unit(db.Model):
    __tablename__ = 'unit'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    rent = db.Column(db.Integer)
    sqft = db.Column(db.Integer)
    description = db.Column(db.String(500))

    # Phase 1: Physical Details & Features
    # HVAC & Climate
    air_conditioning = db.Column(db.Boolean, default=False)  # Central AC, window units, etc.
    heating_type = db.Column(db.String(50))  # Gas, Electric, Heat Pump, Radiant, etc.
    thermostat_type = db.Column(db.String(50))  # Manual, Programmable, Smart

    # Appliances & Kitchen
    appliances_included = db.Column(db.Text)  # JSON or comma-separated list
    dishwasher = db.Column(db.Boolean, default=False)
    garbage_disposal = db.Column(db.Boolean, default=False)
    microwave = db.Column(db.Boolean, default=False)
    refrigerator = db.Column(db.Boolean, default=False)
    range_oven = db.Column(db.Boolean, default=False)
    washer_dryer = db.Column(db.String(50))  # In-unit, Hook-ups, Shared, None

    # Flooring & Interior
    flooring_type = db.Column(db.Text)  # JSON for different rooms
    ceiling_height = db.Column(db.Integer)  # in feet
    windows_type = db.Column(db.String(50))  # Single-pane, Double-pane, etc.
    natural_light = db.Column(db.String(20))  # Excellent, Good, Fair, Limited

    # Storage & Space
    closet_space = db.Column(db.String(50))  # Excellent, Good, Limited
    storage_units = db.Column(db.Integer, default=0)  # Number of additional storage units
    balcony_patio = db.Column(db.Boolean, default=False)
    balcony_sqft = db.Column(db.Integer)

    # Parking & Access
    parking_type = db.Column(db.String(50))  # Garage, Covered, Open, Street, None
    parking_spaces = db.Column(db.Integer, default=0)
    garage_type = db.Column(db.String(50))  # Attached, Detached, Carport, None

    # Bathroom Features
    bathroom_features = db.Column(db.Text)  # JSON array of features
    master_bath = db.Column(db.Boolean, default=False)
    bathtub = db.Column(db.Boolean, default=False)
    shower_type = db.Column(db.String(50))  # Stand-up, Shower/tub combo, Walk-in

    # Condition & Maintenance
    last_renovated = db.Column(db.Date)
    condition_rating = db.Column(db.Integer)  # 1-5 scale
    recent_updates = db.Column(db.Text)  # Recent renovations/updates
    upcoming_maintenance = db.Column(db.Text)  # Scheduled maintenance

    # Accessibility & Compliance
    ada_compliant = db.Column(db.Boolean, default=False)
    wheelchair_accessible = db.Column(db.Boolean, default=False)
    accessibility_features = db.Column(db.Text)  # JSON array of features

    # Utilities & Energy
    utilities_included = db.Column(db.Text)  # What utilities are included
    utility_cost_estimate = db.Column(db.Integer)  # Monthly estimate for tenant
    energy_efficiency_rating = db.Column(db.String(10))  # Energy Star rating

    # Pet Policy
    pets_allowed = db.Column(db.Boolean, default=False)
    pet_restrictions = db.Column(db.Text)  # Breed, size, number restrictions
    pet_fee_monthly = db.Column(db.Integer, default=0)
    pet_deposit = db.Column(db.Integer, default=0)

    # Security Features
    security_features = db.Column(db.Text)  # JSON array of security features
    alarm_system = db.Column(db.Boolean, default=False)
    secure_entry = db.Column(db.Boolean, default=False)

    # Technology & Internet
    internet_included = db.Column(db.Boolean, default=False)
    cable_ready = db.Column(db.Boolean, default=False)
    internet_speed = db.Column(db.String(50))  # Speed capabilities
    smart_home_features = db.Column(db.Text)  # JSON array of smart features

    # Occupancy Status (cached for performance)
    occupancy_status = db.Column(db.String(20), default='Available')  # Available, Reserved, Occupied, Maintenance
    status_updated_at = db.Column(db.DateTime)  # Timestamp of last status update

    # Relationships with cascade delete
    leases = db.relationship('Lease', backref='unit_ref', cascade='all, delete-orphan')

    # Database indexes for search performance
    __table_args__ = (
        db.Index('idx_unit_bedrooms', 'bedrooms'),
        db.Index('idx_unit_bathrooms', 'bathrooms'),
        db.Index('idx_unit_occupancy_status', 'occupancy_status'),
        db.Index('idx_unit_rent', 'rent'),
        db.Index('idx_unit_property_id', 'property_id'),
        db.Index('idx_unit_company_id', 'company_id'),
        db.Index('idx_unit_sqft', 'sqft'),
        db.Index('idx_unit_pets_allowed', 'pets_allowed'),
    )
    
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

    def update_occupancy_status(self):
        """
        Update the cached occupancy status based on current lease state.

        Status Priority:
        1. Maintenance - Unit is under maintenance (manual override)
        2. Occupied - Has an active lease
        3. Reserved - Has a future lease scheduled
        4. Available - No active or future leases

        Returns:
            str: The new occupancy status
        """
        from datetime import datetime

        # Don't override maintenance status automatically
        if self.occupancy_status == 'Maintenance':
            return self.occupancy_status

        old_status = self.occupancy_status
        new_status = self.get_lease_status()  # Calculate from leases

        # Update if status changed
        if new_status != old_status:
            self.occupancy_status = new_status
            self.status_updated_at = datetime.now()

        return new_status

    def __init__(self, name="", company_id=None, property_id=None):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.company_id = company_id
        self.property_id = property_id

    @classmethod
    def find_by_uuid(cls, unit_uuid, company_id=None):
        """Find unit by UUID with optional company_id filter for security."""
        query = cls.query.filter_by(uuid=unit_uuid)
        if company_id:
            query = query.filter_by(company_id=company_id)
        return query.first()

class Tenant(db.Model):
    __tablename__ = 'tenant'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
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

    def __init__(self, first_name="", last_name="", company_id=None):
        self.uuid = str(uuid.uuid4())
        self.first_name = first_name
        self.last_name = last_name
        self.company_id = company_id

    @classmethod
    def find_by_uuid(cls, tenant_uuid, company_id=None):
        """Find tenant by UUID with optional company_id filter for security."""
        query = cls.query.filter_by(uuid=tenant_uuid)
        if company_id:
            query = query.filter_by(company_id=company_id)
        return query.first()

class Lease(db.Model):
    __tablename__ = 'lease'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('lease_template.id'), nullable=True)  # Template used for this lease
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    rent = db.Column(db.Numeric(10, 2), nullable=False)

    # Phase 1: Financial Fields
    security_deposit = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    pet_deposit = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    late_fee = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    payment_due_date = db.Column(db.Integer, nullable=True, default=1)  # Day of month (1-31)
    grace_period_days = db.Column(db.Integer, nullable=True, default=5)  # Days before late fee applies
    utilities_included = db.Column(db.Text, nullable=True)  # Comma-separated list or text description
    parking_fee = db.Column(db.Numeric(10, 2), nullable=True, default=0)

    # Additional Financial Fields for Comprehensive Tracking
    application_fee = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # One-time application fee
    broker_fee = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # Broker/agent fee
    cleaning_fee = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # Move-out cleaning fee
    administrative_fee = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # Administrative/processing fee
    last_month_rent = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # Last month's rent (prepaid)
    utility_deposits = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # Utility connection deposits
    storage_fee = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # Monthly storage fee
    concessions = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # Rent discounts/concessions
    pet_fee = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # Monthly pet fee (different from deposit)

    # Phase 2: Lease Terms & Conditions
    lease_type = db.Column(db.String(50), nullable=True, default='fixed')  # fixed, month_to_month, periodic
    auto_renewal = db.Column(db.String(20), nullable=True, default='no')  # no, month_to_month, same_term
    notice_period_days = db.Column(db.Integer, nullable=True, default=30)  # Required notice for termination (days)
    early_termination_fee = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # Fee for breaking lease early
    max_occupants = db.Column(db.Integer, nullable=True, default=2)  # Maximum number of occupants
    renewal_terms = db.Column(db.Text, nullable=True)  # Conditions for lease renewal

    # Phase 3: Operational Details
    move_in_date = db.Column(db.Date, nullable=True)  # Actual move-in date (may differ from lease start)
    move_out_date = db.Column(db.Date, nullable=True)  # Actual move-out date (may differ from lease end)
    key_deposit = db.Column(db.Numeric(10, 2), nullable=True, default=0)  # Deposit for keys/access cards
    move_in_inspection_notes = db.Column(db.Text, nullable=True)  # Notes from move-in inspection
    move_out_inspection_notes = db.Column(db.Text, nullable=True)  # Notes from move-out inspection
    lease_status = db.Column(db.String(20), nullable=True, default='active')  # draft, pending, active, expiring, terminated, expired
    status_updated_at = db.Column(db.DateTime, nullable=True)  # Timestamp of last status update
    property_manager_notes = db.Column(db.Text, nullable=True)  # Internal notes for property management
    emergency_contact_name = db.Column(db.String(100), nullable=True)  # Emergency contact information
    emergency_contact_phone = db.Column(db.String(20), nullable=True)  # Emergency contact phone

    # Phase 4: Advanced Features
    lease_documents = db.Column(db.Text, nullable=True)  # JSON array of document metadata (filename, type, upload_date)
    compliance_notes = db.Column(db.Text, nullable=True)  # Compliance and regulatory notes
    insurance_required = db.Column(db.Boolean, nullable=True, default=False)  # Whether renter's insurance is required
    insurance_verified = db.Column(db.Boolean, nullable=True, default=False)  # Whether insurance has been verified
    insurance_expiry_date = db.Column(db.Date, nullable=True)  # Insurance policy expiration date
    background_check_status = db.Column(db.String(20), nullable=True, default='pending')  # pending, approved, rejected
    background_check_date = db.Column(db.Date, nullable=True)  # Date background check was completed
    credit_score = db.Column(db.Integer, nullable=True)  # Tenant credit score (if disclosed)
    # Removed: duplicate of auto_renewal field
    renewal_reminder_days = db.Column(db.Integer, nullable=True, default=60)  # Days before lease end to send renewal reminder
    violation_history = db.Column(db.Text, nullable=True)  # JSON array of lease violations
    maintenance_requests = db.Column(db.Text, nullable=True)  # JSON array of maintenance request references

    # Relationships (with overlaps to resolve backref conflicts)
    tenant = db.relationship('Tenant', foreign_keys=[tenant_id], overlaps="leases,tenant_ref")
    unit = db.relationship('Unit', foreign_keys=[unit_id], overlaps="leases,unit_ref")
    property_obj = db.relationship('Property', foreign_keys=[property_id], overlaps="lease_property_ref,leases")
    payments = db.relationship('Payment', backref='lease_ref', lazy=True, cascade='all, delete-orphan')
    template = db.relationship('LeaseTemplate', backref='leases_using_template', foreign_keys=[template_id])

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

    def days_until_next_payment(self):
        """Calculate days until next rent payment is due."""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        today = datetime.now().date()
        lease_start = self.start.date() if isinstance(self.start, datetime) else self.start
        lease_end = self.end.date() if isinstance(self.end, datetime) else self.end

        # If lease hasn't started or has ended, return None
        if today < lease_start or today > lease_end:
            return None

        # Get payment due date (default to 1st of month)
        due_day = self.payment_due_date or 1

        # Calculate next payment date
        current_month_due = today.replace(day=min(due_day, 28))  # Avoid day overflow

        try:
            current_month_due = today.replace(day=due_day)
        except ValueError:
            # Handle months with fewer days (e.g., Feb 30 -> Feb 28)
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            current_month_due = today.replace(day=min(due_day, last_day))

        if today <= current_month_due:
            # Next payment is this month
            next_payment_date = current_month_due
        else:
            # Next payment is next month
            next_month = today + relativedelta(months=1)
            try:
                next_payment_date = next_month.replace(day=due_day)
            except ValueError:
                import calendar
                last_day = calendar.monthrange(next_month.year, next_month.month)[1]
                next_payment_date = next_month.replace(day=min(due_day, last_day))

        # Don't report payments beyond lease end
        if next_payment_date > lease_end:
            return None

        return (next_payment_date - today).days

    def get_total_upfront_costs(self):
        """Calculate total upfront costs tenant pays at move-in."""
        upfront_costs = (
            float(self.security_deposit or 0) +
            float(self.pet_deposit or 0) +
            float(self.application_fee or 0) +
            float(self.broker_fee or 0) +
            float(self.cleaning_fee or 0) +
            float(self.administrative_fee or 0) +
            float(self.last_month_rent or 0) +
            float(self.utility_deposits or 0) +
            float(self.key_deposit or 0)
        )
        return upfront_costs

    def get_monthly_recurring_costs(self):
        """Calculate total monthly recurring costs."""
        monthly_costs = (
            float(self.rent or 0) +
            float(self.parking_fee or 0) +
            float(self.storage_fee or 0) +
            float(self.pet_fee or 0)
        )
        return monthly_costs

    def get_net_effective_rent(self):
        """Calculate net effective monthly rent after concessions."""
        base_rent = float(self.rent or 0)
        monthly_concessions = float(self.concessions or 0)
        return max(0, base_rent - monthly_concessions)

    def get_total_lease_value(self):
        """Calculate total financial value of the entire lease term."""
        from dateutil.relativedelta import relativedelta
        import calendar

        lease_start = self.start.date() if self.start else None
        lease_end = self.end.date() if self.end else None

        if not lease_start or not lease_end:
            return 0

        total_value = 0
        current_date = lease_start.replace(day=1)

        while current_date <= lease_end:
            if current_date.month == lease_start.month and current_date.year == lease_start.year:
                # Prorate first month
                days_in_month = calendar.monthrange(current_date.year, current_date.month)[1]
                days_occupied = days_in_month - lease_start.day + 1
                monthly_charge = self.get_monthly_recurring_costs()
                total_value += (monthly_charge * days_occupied) / days_in_month
            elif current_date <= lease_end:
                total_value += self.get_monthly_recurring_costs()
            current_date += relativedelta(months=1)

        # Add one-time fees and deposits
        total_value += self.get_total_upfront_costs()
        return total_value

    def get_move_in_costs(self):
        """Calculate what tenant needs to pay at move-in (first month + deposits)."""
        first_month_rent = float(self.rent or 0)
        upfront_costs = self.get_total_upfront_costs()
        return first_month_rent + upfront_costs

    def calculate_prorated_rent(self, start_date, end_date):
        """Calculate prorated rent for a specific date range."""
        import calendar
        from datetime import timedelta

        if start_date >= end_date:
            return 0

        # Get the month and year
        month = start_date.month
        year = start_date.year

        # Get days in the month
        days_in_month = calendar.monthrange(year, month)[1]

        # Calculate days occupied
        if start_date.month == end_date.month:
            days_occupied = (end_date - start_date).days + 1
        else:
            # For simplicity, calculate for the start month only
            days_occupied = days_in_month - start_date.day + 1

        # Calculate prorated amount
        daily_rate = float(self.rent or 0) / days_in_month
        return daily_rate * days_occupied

    def get_payment_schedule(self):
        """Generate expected payment schedule for the lease term."""
        from dateutil.relativedelta import relativedelta
        import calendar

        schedule = []
        if not self.start or not self.end:
            return schedule

        lease_start = self.start.date()
        lease_end = self.end.date()
        current_date = lease_start.replace(day=self.payment_due_date or 1)

        # Adjust first payment date if it's before lease start
        if current_date < lease_start:
            current_date = current_date + relativedelta(months=1)

        payment_number = 1
        while current_date <= lease_end:
            # Calculate amount (may be prorated for first/last month)
            if payment_number == 1 and lease_start.day != (self.payment_due_date or 1):
                # First month may be prorated
                amount = self.calculate_prorated_rent(lease_start,
                    min(lease_start.replace(day=calendar.monthrange(lease_start.year, lease_start.month)[1]), lease_end))
            else:
                amount = self.get_monthly_recurring_costs()

            schedule.append({
                'payment_number': payment_number,
                'due_date': current_date,
                'amount': amount,
                'description': f'Month {payment_number} Rent'
            })

            current_date += relativedelta(months=1)
            payment_number += 1

        return schedule

    def get_financial_summary(self):
        """Get comprehensive financial summary for the lease."""
        return {
            'total_upfront_costs': self.get_total_upfront_costs(),
            'monthly_recurring_costs': self.get_monthly_recurring_costs(),
            'net_effective_rent': self.get_net_effective_rent(),
            'total_lease_value': self.get_total_lease_value(),
            'move_in_costs': self.get_move_in_costs(),
            'total_paid': self.get_total_paid(),
            'outstanding_balance': self.get_outstanding_balance(),
            'is_overdue': self.is_overdue(),
            'payment_schedule_count': len(self.get_payment_schedule())
        }

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

    def update_status(self, force_update=False):
        """
        Automatically update lease status based on dates.

        Status Transitions:
        - draft: Lease created but not finalized
        - pending: Lease finalized, awaiting start date
        - active: Current date is between start and end
        - expiring: Within 30 days of end date
        - expired: Past end date
        - terminated: Manually terminated early

        Args:
            force_update: If True, update even if status is 'terminated'

        Returns:
            str: The new status
        """
        from datetime import datetime, timedelta

        # Don't auto-update terminated leases unless forced
        if self.lease_status == 'terminated' and not force_update:
            return self.lease_status

        today = datetime.now().date()
        start_date = self.start.date() if isinstance(self.start, datetime) else self.start
        end_date = self.end.date() if isinstance(self.end, datetime) else self.end

        old_status = self.lease_status
        new_status = old_status

        # Determine appropriate status
        if today < start_date:
            # Lease hasn't started yet
            new_status = 'pending'
        elif today > end_date:
            # Lease has ended
            new_status = 'expired'
        elif today >= start_date and today <= end_date:
            # Lease is currently active
            days_until_end = (end_date - today).days

            if days_until_end <= 30:
                # Within 30 days of expiration
                new_status = 'expiring'
            else:
                # Active and not close to expiration
                new_status = 'active'

        # Update status if it changed
        if new_status != old_status:
            self.lease_status = new_status
            self.status_updated_at = datetime.now()

        return new_status

    def sync_unit_property_status(self):
        """
        Synchronize the occupancy status of the associated unit and property
        after this lease's status changes.
        """
        # Update unit status - use direct relationship for consistency
        if self.unit:
            self.unit.update_occupancy_status()

        # Update property status - use direct relationship for consistency
        if self.property_obj:
            self.property_obj.update_occupancy_status()

    @staticmethod
    def update_all_statuses(company_id=None):
        """
        Batch update all lease statuses. Useful for scheduled tasks.

        Args:
            company_id: Optional company_id to limit updates to specific company

        Returns:
            dict: Summary of status updates
        """
        query = Lease.query
        if company_id:
            query = query.filter_by(company_id=company_id)

        leases = query.all()

        summary = {
            'total_processed': 0,
            'status_changed': 0,
            'by_status': {}
        }

        for lease in leases:
            summary['total_processed'] += 1
            old_status = lease.lease_status
            new_status = lease.update_status()

            if old_status != new_status:
                summary['status_changed'] += 1

                # Track status changes
                if new_status not in summary['by_status']:
                    summary['by_status'][new_status] = 0
                summary['by_status'][new_status] += 1

                # Sync unit and property statuses
                lease.sync_unit_property_status()

        # Commit all changes
        db.session.commit()

        return summary

    def generate_contract(self):
        """
        Generate a populated lease contract from the template.

        Returns:
            str: Populated contract text, or None if no template
        """
        if not self.template:
            return None

        # Calculate lease term in months
        from dateutil.relativedelta import relativedelta
        start_date = self.start.date() if hasattr(self.start, 'date') else self.start
        end_date = self.end.date() if hasattr(self.end, 'date') else self.end
        delta = relativedelta(end_date, start_date)
        lease_term_months = delta.years * 12 + delta.months

        # Prepare lease data for merge fields
        lease_data = {
            'tenant_name': f"{self.tenant_ref.first_name} {self.tenant_ref.last_name}" if self.tenant_ref else '',
            'tenant_email': self.tenant_ref.email if self.tenant_ref else '',
            'tenant_phone': self.tenant_ref.phone if self.tenant_ref else '',
            'landlord_name': self.company_ref.name if self.company_ref else '',
            'landlord_company': self.company_ref.name if self.company_ref else '',
            'property_address': self.property_obj.address if self.property_obj else '',
            'unit_number': self.unit_ref.name if self.unit_ref else '',
            'rent_amount': f"${self.rent:,.2f}",
            'security_deposit': f"${self.security_deposit:,.2f}" if self.security_deposit else '$0.00',
            'start_date': start_date.strftime('%B %d, %Y'),
            'end_date': end_date.strftime('%B %d, %Y'),
            'lease_term_months': str(lease_term_months),
            'payment_due_date': str(self.payment_due_date) if self.payment_due_date else '1',
            'late_fee': f"${self.late_fee:,.2f}" if self.late_fee else '$0.00',
            'pet_deposit': f"${self.pet_deposit:,.2f}" if self.pet_deposit else '$0.00',
            'parking_spaces': str(getattr(self.unit_ref, 'parking_spaces', 0)),
            'utilities_included': self.utilities_included if self.utilities_included else 'None',
        }

        # Generate populated contract
        return self.template.populate_template(lease_data)

    def __init__(self, tenant_id=None, unit_id=None, property_id=None, company_id=None, start=None, end=None, rent=None, **kwargs):
        self.uuid = str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.unit_id = unit_id
        self.property_id = property_id
        self.company_id = company_id
        self.start = start
        self.end = end
        self.rent = rent

        # Set any additional keyword arguments as attributes
        # This allows setting template_id and all other optional Lease fields at creation
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def find_by_uuid(cls, lease_uuid, company_id=None):
        """Find lease by UUID with optional company_id filter for security."""
        query = cls.query.filter_by(uuid=lease_uuid)
        if company_id:
            query = query.filter_by(company_id=company_id)
        return query.first()


class LeaseTemplate(db.Model):
    """
    Lease contract templates for generating standardized lease agreements.

    Templates support merge fields like {{tenant_name}}, {{rent_amount}}, etc.
    Companies can create custom templates or use system defaults.
    """
    __tablename__ = 'lease_template'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)  # NULL = system template

    # Template Identification
    name = db.Column(db.String(200), nullable=False)  # "Standard Residential Lease", "Commercial Lease"
    description = db.Column(db.Text)  # Description of when to use this template
    template_type = db.Column(db.String(50), default='residential')  # residential, commercial, month_to_month, sublease

    # Template Content
    contract_text = db.Column(db.Text, nullable=False)  # Rich text with merge fields
    header_text = db.Column(db.Text)  # Optional header/letterhead
    footer_text = db.Column(db.Text)  # Optional footer/signature block

    # Default Terms (JSON)
    default_terms = db.Column(db.Text)  # JSON: {security_deposit_months: 1, late_fee: 50, notice_period_days: 30}

    # Template Status
    is_default = db.Column(db.Boolean, default=False)  # Is this the default template for this company?
    is_active = db.Column(db.Boolean, default=True)  # Can this template be used?
    is_system_template = db.Column(db.Boolean, default=False)  # System-provided template (read-only)

    # Version Control
    version = db.Column(db.Integer, default=1)  # Template version number
    parent_template_id = db.Column(db.Integer, db.ForeignKey('lease_template.id'), nullable=True)  # For versioning

    # Merge Fields Configuration
    available_merge_fields = db.Column(db.Text)  # JSON array of available merge fields
    required_fields = db.Column(db.Text)  # JSON array of required merge fields

    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_count = db.Column(db.Integer, default=0)  # How many times used

    # Relationships
    creator = db.relationship('User', backref='created_templates', foreign_keys=[created_by])
    child_versions = db.relationship('LeaseTemplate', backref=db.backref('parent_template', remote_side=[id]))

    def __init__(self, name="", company_id=None, template_type='residential'):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.company_id = company_id
        self.template_type = template_type

    @classmethod
    def find_by_uuid(cls, template_uuid, company_id=None):
        """Find template by UUID with optional company_id filter for security."""
        query = cls.query.filter_by(uuid=template_uuid)
        if company_id:
            # Can access own templates or system templates
            query = query.filter(
                db.or_(
                    cls.company_id == company_id,
                    cls.is_system_template == True
                )
            )
        return query.first()

    @classmethod
    def get_default_for_company(cls, company_id, template_type='residential'):
        """Get the default template for a company."""
        # First try company-specific default
        template = cls.query.filter_by(
            company_id=company_id,
            template_type=template_type,
            is_default=True,
            is_active=True
        ).first()

        if not template:
            # Fall back to system default
            template = cls.query.filter_by(
                is_system_template=True,
                template_type=template_type,
                is_default=True,
                is_active=True
            ).first()

        return template

    @classmethod
    def get_available_templates(cls, company_id, template_type=None):
        """Get all available templates for a company (own + system)."""
        query = cls.query.filter(
            cls.is_active == True,
            db.or_(
                cls.company_id == company_id,
                cls.is_system_template == True
            )
        )

        if template_type:
            query = query.filter_by(template_type=template_type)

        return query.order_by(cls.is_default.desc(), cls.name).all()

    def populate_template(self, lease_data):
        """
        Replace merge fields with actual lease data.

        Args:
            lease_data: Dictionary containing lease information

        Returns:
            str: Populated contract text
        """
        import re

        populated_text = self.contract_text

        # Define merge field mappings
        merge_fields = {
            'tenant_name': lease_data.get('tenant_name', ''),
            'tenant_email': lease_data.get('tenant_email', ''),
            'tenant_phone': lease_data.get('tenant_phone', ''),
            'landlord_name': lease_data.get('landlord_name', ''),
            'landlord_company': lease_data.get('landlord_company', ''),
            'property_address': lease_data.get('property_address', ''),
            'unit_number': lease_data.get('unit_number', ''),
            'rent_amount': lease_data.get('rent_amount', ''),
            'security_deposit': lease_data.get('security_deposit', ''),
            'start_date': lease_data.get('start_date', ''),
            'end_date': lease_data.get('end_date', ''),
            'lease_term_months': lease_data.get('lease_term_months', ''),
            'payment_due_date': lease_data.get('payment_due_date', ''),
            'late_fee': lease_data.get('late_fee', ''),
            'pet_deposit': lease_data.get('pet_deposit', ''),
            'parking_spaces': lease_data.get('parking_spaces', ''),
            'utilities_included': lease_data.get('utilities_included', ''),
            'current_date': datetime.now().strftime('%B %d, %Y'),
        }

        # Replace merge fields
        for field_name, field_value in merge_fields.items():
            pattern = r'\{\{' + field_name + r'\}\}'
            populated_text = re.sub(pattern, str(field_value), populated_text, flags=re.IGNORECASE)

        return populated_text

    def increment_usage(self):
        """Increment the usage counter for this template."""
        self.usage_count += 1
        db.session.commit()


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


class PasswordHistoryModel(db.Model):
    """
    Store password history for users to prevent password reuse.
    Part of enhanced security implementation.
    """
    __tablename__ = 'password_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    password_hash = db.Column(db.String(1500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='password_history', lazy=True)

    def __repr__(self):
        return f'<PasswordHistory {self.user_id} - {self.created_at}>'


class AuditLogModel(db.Model):
    """
    Comprehensive audit logging for security and compliance.
    Tracks all significant events and user activities.
    """
    __tablename__ = 'audit_log'

    id = db.Column(db.String(36), primary_key=True)  # UUID
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Event information
    event_type = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, default='info', index=True)
    success = db.Column(db.Boolean, nullable=False, default=True)

    # User context
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    user_email = db.Column(db.String(150), nullable=True, index=True)
    user_role = db.Column(db.String(20), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True, index=True)

    # Request context
    session_id = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True, index=True)  # IPv6 compatible
    user_agent = db.Column(db.Text, nullable=True)
    endpoint = db.Column(db.String(200), nullable=True)
    http_method = db.Column(db.String(10), nullable=True)
    url = db.Column(db.Text, nullable=True)

    # Resource context
    resource_type = db.Column(db.String(100), nullable=True, index=True)
    resource_id = db.Column(db.String(100), nullable=True, index=True)

    # Additional details (JSON)
    details = db.Column(db.Text, nullable=True)

    # Relationships
    user = db.relationship('User', backref='audit_logs', lazy=True)
    company = db.relationship('Company', backref='audit_logs', lazy=True)

    def __repr__(self):
        return f'<AuditLog {self.event_type} - {self.user_email} - {self.timestamp}>'


class EmailVerificationAttempt(db.Model):
    """
    Track email verification attempts for rate limiting.
    Part of enhanced security implementation.
    """
    __tablename__ = 'email_verification_attempt'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='verification_attempts', lazy=True)

    def __repr__(self):
        return f'<EmailVerificationAttempt {self.user_id} - {self.email} - {self.created_at}>'


class PasswordResetToken(db.Model):
    """
    Password reset tokens for forgot password functionality.

    Tokens are hashed before storage and expire after 24 hours.
    Single-use tokens are invalidated after successful password reset.
    """
    __tablename__ = 'password_reset_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, unique=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.String(255))

    # Relationship
    user = db.relationship('User', backref='reset_tokens')

    def __repr__(self):
        return f'<PasswordResetToken {self.user_id} - expires: {self.expires_at} - used: {self.used}>'


class SubscriptionPlan(db.Model):
    """
    Subscription plan definitions (Free, Pro, Enterprise).

    Defines pricing tiers, feature limits, and billing options.
    Plans are system-wide and not tied to any specific company.
    """
    __tablename__ = 'subscription_plan'

    id = db.Column(db.Integer, primary_key=True)

    # Plan identification
    name = db.Column(db.String(50), nullable=False, unique=True)  # Free, Pro, Enterprise
    display_name = db.Column(db.String(100), nullable=False)  # "Professional Plan"
    description = db.Column(db.Text)  # Plan description for marketing

    # Pricing
    price_monthly = db.Column(db.Numeric(10, 2), nullable=False, default=0)  # Monthly price in USD
    price_annual = db.Column(db.Numeric(10, 2), nullable=False, default=0)  # Annual price in USD

    # Feature limits
    max_portfolios = db.Column(db.Integer, nullable=True)  # NULL = unlimited
    max_properties = db.Column(db.Integer, nullable=True)  # NULL = unlimited
    max_units = db.Column(db.Integer, nullable=True)  # NULL = unlimited
    max_tenants = db.Column(db.Integer, nullable=True)  # NULL = unlimited
    max_users = db.Column(db.Integer, nullable=True)  # NULL = unlimited

    # Feature flags
    advanced_reporting = db.Column(db.Boolean, default=False)
    priority_support = db.Column(db.Boolean, default=False)
    custom_branding = db.Column(db.Boolean, default=False)
    api_access = db.Column(db.Boolean, default=False)
    bulk_operations = db.Column(db.Boolean, default=False)

    # Stripe integration
    stripe_price_id_monthly = db.Column(db.String(100))  # Stripe Price ID for monthly billing
    stripe_price_id_annual = db.Column(db.String(100))  # Stripe Price ID for annual billing
    stripe_product_id = db.Column(db.String(100))  # Stripe Product ID

    # Plan status
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=True)  # Show on pricing page
    sort_order = db.Column(db.Integer, default=0)  # Display order on pricing page

    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions = db.relationship('CompanySubscription', backref='plan', lazy=True)

    def __repr__(self):
        return f'<SubscriptionPlan {self.name} - ${self.price_monthly}/mo>'

    def get_limit_display(self, limit_name):
        """Get human-readable display of a limit."""
        limit_value = getattr(self, limit_name, None)
        return "Unlimited" if limit_value is None else str(limit_value)

    def is_limit_unlimited(self, limit_name):
        """Check if a specific limit is unlimited."""
        limit_value = getattr(self, limit_name, None)
        return limit_value is None

    def get_annual_savings(self):
        """Calculate annual savings percentage."""
        if self.price_monthly == 0 or self.price_annual == 0:
            return 0
        monthly_total = float(self.price_monthly) * 12
        annual_price = float(self.price_annual)
        savings = ((monthly_total - annual_price) / monthly_total) * 100
        return round(savings, 1)


class CompanySubscription(db.Model):
    """
    Company's active subscription and usage tracking.

    Links a company to their subscription plan and tracks usage
    against limits with grace period support.
    """
    __tablename__ = 'company_subscription'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False, unique=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=False)

    # Billing information
    billing_cycle = db.Column(db.String(20), nullable=False, default='monthly')  # monthly, annual
    status = db.Column(db.String(20), nullable=False, default='active')  # active, past_due, canceled, trialing

    # Subscription dates
    subscribed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    current_period_start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    current_period_end = db.Column(db.DateTime)
    trial_start = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    canceled_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)  # When subscription fully ends after cancellation

    # Usage tracking (cached for performance)
    current_portfolios = db.Column(db.Integer, default=0)
    current_properties = db.Column(db.Integer, default=0)
    current_units = db.Column(db.Integer, default=0)
    current_tenants = db.Column(db.Integer, default=0)
    current_users = db.Column(db.Integer, default=0)
    usage_last_updated = db.Column(db.DateTime)

    # Grace period tracking
    is_over_limit = db.Column(db.Boolean, default=False)
    over_limit_since = db.Column(db.DateTime)  # When company first exceeded limits
    grace_period_ends = db.Column(db.DateTime)  # When enforcement begins
    limit_warning_sent = db.Column(db.Boolean, default=False)
    limit_final_warning_sent = db.Column(db.Boolean, default=False)

    # Stripe integration
    stripe_customer_id = db.Column(db.String(100))  # Stripe Customer ID
    stripe_subscription_id = db.Column(db.String(100))  # Stripe Subscription ID
    stripe_status = db.Column(db.String(50))  # Stripe subscription status

    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = db.relationship('Company', backref=db.backref('subscription', uselist=False, lazy=True))
    payment_history = db.relationship('PaymentHistory', backref='subscription', lazy=True, cascade='all, delete-orphan')
    usage_events = db.relationship('UsageEvent', backref='subscription', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CompanySubscription company_id={self.company_id} plan={self.plan.name} status={self.status}>'

    def is_active(self):
        """Check if subscription is currently active."""
        return self.status in ['active', 'trialing']

    def is_in_trial(self):
        """Check if subscription is in trial period."""
        if not self.trial_end:
            return False
        return datetime.utcnow() < self.trial_end

    def days_until_renewal(self):
        """Calculate days until next billing cycle."""
        if not self.current_period_end:
            return None
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)

    def is_in_grace_period(self):
        """Check if company is in grace period for overages."""
        if not self.is_over_limit or not self.grace_period_ends:
            return False
        return datetime.utcnow() < self.grace_period_ends

    def days_left_in_grace_period(self):
        """Calculate days remaining in grace period."""
        if not self.is_in_grace_period():
            return 0
        delta = self.grace_period_ends - datetime.utcnow()
        return max(0, delta.days)

    def update_usage(self):
        """Update cached usage counts from actual database records."""
        from datetime import datetime

        self.current_portfolios = Portfolio.query.filter_by(company_id=self.company_id).count()
        self.current_properties = Property.query.filter_by(company_id=self.company_id).count()
        self.current_units = Unit.query.filter_by(company_id=self.company_id).count()
        self.current_tenants = Tenant.query.filter_by(company_id=self.company_id).count()
        self.current_users = User.query.filter_by(company_id=self.company_id).count()
        self.usage_last_updated = datetime.utcnow()

        # Check if over limit
        self.check_limits()

    def check_limits(self):
        """Check if company has exceeded any limits and update grace period."""
        from datetime import datetime, timedelta

        plan = self.plan
        is_over = False

        # Check each limit (None = unlimited)
        if plan.max_portfolios is not None and self.current_portfolios > plan.max_portfolios:
            is_over = True
        if plan.max_properties is not None and self.current_properties > plan.max_properties:
            is_over = True
        if plan.max_units is not None and self.current_units > plan.max_units:
            is_over = True
        if plan.max_tenants is not None and self.current_tenants > plan.max_tenants:
            is_over = True
        if plan.max_users is not None and self.current_users > plan.max_users:
            is_over = True

        # Update grace period status
        if is_over and not self.is_over_limit:
            # Just went over limit - start grace period
            self.is_over_limit = True
            self.over_limit_since = datetime.utcnow()
            # Grace period is 14 days by default (can be configured via env var)
            grace_days = 14  # TODO: Load from config
            self.grace_period_ends = datetime.utcnow() + timedelta(days=grace_days)
            self.limit_warning_sent = False
            self.limit_final_warning_sent = False
        elif not is_over and self.is_over_limit:
            # Back within limits - clear grace period
            self.is_over_limit = False
            self.over_limit_since = None
            self.grace_period_ends = None
            self.limit_warning_sent = False
            self.limit_final_warning_sent = False

    def get_usage_summary(self):
        """Get dictionary of usage vs limits."""
        plan = self.plan
        return {
            'portfolios': {
                'current': self.current_portfolios,
                'limit': plan.max_portfolios,
                'unlimited': plan.max_portfolios is None,
                'over_limit': plan.max_portfolios is not None and self.current_portfolios > plan.max_portfolios
            },
            'properties': {
                'current': self.current_properties,
                'limit': plan.max_properties,
                'unlimited': plan.max_properties is None,
                'over_limit': plan.max_properties is not None and self.current_properties > plan.max_properties
            },
            'units': {
                'current': self.current_units,
                'limit': plan.max_units,
                'unlimited': plan.max_units is None,
                'over_limit': plan.max_units is not None and self.current_units > plan.max_units
            },
            'tenants': {
                'current': self.current_tenants,
                'limit': plan.max_tenants,
                'unlimited': plan.max_tenants is None,
                'over_limit': plan.max_tenants is not None and self.current_tenants > plan.max_tenants
            },
            'users': {
                'current': self.current_users,
                'limit': plan.max_users,
                'unlimited': plan.max_users is None,
                'over_limit': plan.max_users is not None and self.current_users > plan.max_users
            }
        }


class PaymentHistory(db.Model):
    """
    Stripe payment transaction history.

    Records all payment transactions from Stripe for audit,
    compliance, and financial tracking.
    """
    __tablename__ = 'payment_history'

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('company_subscription.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Amount in USD
    currency = db.Column(db.String(3), default='usd')
    status = db.Column(db.String(20), nullable=False)  # succeeded, failed, pending, refunded
    payment_method = db.Column(db.String(50))  # card, bank_transfer, etc.

    # Stripe references
    stripe_payment_intent_id = db.Column(db.String(100), unique=True)
    stripe_invoice_id = db.Column(db.String(100))
    stripe_charge_id = db.Column(db.String(100))

    # Billing period
    billing_period_start = db.Column(db.DateTime)
    billing_period_end = db.Column(db.DateTime)

    # Payment dates
    payment_date = db.Column(db.DateTime)  # When payment was processed
    due_date = db.Column(db.DateTime)  # When payment was due

    # Failure information
    failure_code = db.Column(db.String(100))  # Stripe failure code
    failure_message = db.Column(db.Text)  # Human-readable failure message

    # Invoice details
    invoice_url = db.Column(db.String(500))  # Stripe hosted invoice URL
    invoice_pdf_url = db.Column(db.String(500))  # PDF download URL
    receipt_url = db.Column(db.String(500))  # Receipt URL

    # Metadata
    description = db.Column(db.Text)  # Payment description
    payment_metadata = db.Column(db.Text)  # JSON string with additional data
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = db.relationship('Company', backref='subscription_payments', lazy=True)

    def __repr__(self):
        return f'<PaymentHistory ${self.amount} {self.status} for company_id={self.company_id}>'

    def is_successful(self):
        """Check if payment was successful."""
        return self.status == 'succeeded'

    def is_failed(self):
        """Check if payment failed."""
        return self.status == 'failed'

    def is_pending(self):
        """Check if payment is pending."""
        return self.status == 'pending'

    def is_refunded(self):
        """Check if payment was refunded."""
        return self.status == 'refunded'


class UsageEvent(db.Model):
    """
    Detailed usage event tracking (optional).

    Records individual usage events for analytics and debugging.
    Useful for understanding usage patterns and generating reports.
    """
    __tablename__ = 'usage_event'

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('company_subscription.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    # Event details
    event_type = db.Column(db.String(50), nullable=False, index=True)  # created, deleted, updated
    resource_type = db.Column(db.String(50), nullable=False, index=True)  # portfolio, property, unit, tenant, user
    resource_id = db.Column(db.Integer)  # ID of the resource

    # Usage snapshot (at time of event)
    portfolios_count = db.Column(db.Integer)
    properties_count = db.Column(db.Integer)
    units_count = db.Column(db.Integer)
    tenants_count = db.Column(db.Integer)
    users_count = db.Column(db.Integer)

    # User context
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_email = db.Column(db.String(150))

    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    event_metadata = db.Column(db.Text)  # JSON string with additional context

    # Relationships
    company = db.relationship('Company', backref='usage_events', lazy=True)
    user = db.relationship('User', backref='usage_events', lazy=True)

    # Database indexes for analytics queries
    __table_args__ = (
        db.Index('idx_usage_event_company_date', 'company_id', 'created_at'),
        db.Index('idx_usage_event_resource', 'resource_type', 'event_type'),
    )

    def __repr__(self):
        return f'<UsageEvent {self.event_type} {self.resource_type} company_id={self.company_id}>'

    @classmethod
    def track_event(cls, subscription_id, company_id, event_type, resource_type, resource_id=None, user_id=None):
        """
        Convenience method to track a usage event.

        Args:
            subscription_id: Company subscription ID
            company_id: Company ID
            event_type: Type of event (created, deleted, updated)
            resource_type: Type of resource (portfolio, property, unit, tenant, user)
            resource_id: Optional ID of the resource
            user_id: Optional ID of the user performing the action

        Returns:
            UsageEvent: The created event record
        """
        from flask_login import current_user

        # Get current usage counts
        subscription = CompanySubscription.query.get(subscription_id)
        if not subscription:
            return None

        # Create event record
        event = cls(
            subscription_id=subscription_id,
            company_id=company_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            portfolios_count=subscription.current_portfolios,
            properties_count=subscription.current_properties,
            units_count=subscription.current_units,
            tenants_count=subscription.current_tenants,
            users_count=subscription.current_users,
            user_id=user_id or (current_user.id if hasattr(current_user, 'id') else None),
            user_email=current_user.email if hasattr(current_user, 'email') else None
        )

        db.session.add(event)
        return event


class SuperAdmin(db.Model):
    """
    Super Administrator model for God View Dashboard.

    Exists completely outside the multi-tenant system - no company_id.
    Super admins can view all companies and their data but cannot modify anything.
    Separate from regular User model for complete security isolation.
    """
    __tablename__ = 'super_admin'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(1500), nullable=False)
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    email = db.Column(db.String(150))  # For notifications, not login
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    notes = db.Column(db.Text)  # Internal notes about this admin

    # Security fields
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)  # Force password change on next login
    created_by_admin_id = db.Column(db.Integer, db.ForeignKey('super_admin.id'), nullable=True)  # Tracks who created this admin
    password_changed_at = db.Column(db.DateTime, nullable=True)  # Last password change timestamp

    # Relationships
    audit_logs = db.relationship('SuperAdminAuditLog', backref='admin', lazy=True)
    created_by = db.relationship('SuperAdmin', remote_side=[id], backref='created_admins', foreign_keys=[created_by_admin_id])

    def set_password(self, password):
        """Set admin password with secure hashing and track change timestamp."""
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.now(timezone.utc)

    def check_password(self, password):
        """Verify admin password."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.now(timezone.utc)
        db.session.commit()

    def __repr__(self):
        return f'<SuperAdmin {self.username}>'


class SuperAdminAuditLog(db.Model):
    """
    Audit log for all super admin actions.

    Tracks every action taken by super admins for security and compliance.
    Logs what was viewed, when, by whom, and from where.
    """
    __tablename__ = 'super_admin_audit_log'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('super_admin.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 'viewed_dashboard', 'viewed_company', etc.
    target_company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)  # Which company was viewed
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    details = db.Column(db.Text)  # JSON string with additional context

    # Relationships
    target_company = db.relationship('Company', backref='admin_views', lazy=True)

    def __repr__(self):
        return f'<SuperAdminAuditLog {self.action} by admin_{self.admin_id} at {self.timestamp}>'