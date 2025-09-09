import pytest
from datetime import datetime, timedelta
from website.models import User, Property, Unit, Tenant, Lease, Portfolio
from website import db

@pytest.mark.models
@pytest.mark.unit
class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation_with_all_fields(self, app):
        """Test creating user with all optional fields."""
        with app.app_context():
            user = User(
                first_name='John',
                last_name='Doe',
                email='john@example.com'
            )
            user.address = '123 Main St'
            user.city = 'Test City'
            user.state = 'CA'
            user.zip_code = 12345
            user.company = 'Test Company'
            user.set_password('password123')
            
            db.session.add(user)
            db.session.commit()
            
            saved_user = User.query.filter_by(email='john@example.com').first()
            assert saved_user.first_name == 'John'
            assert saved_user.last_name == 'Doe'
            assert saved_user.address == '123 Main St'
            assert saved_user.city == 'Test City'
            assert saved_user.state == 'CA'
            assert saved_user.zip_code == 12345
            assert saved_user.company == 'Test Company'
    
    def test_user_email_uniqueness(self, app):
        """Test that user emails must be unique."""
        with app.app_context():
            user1 = User(first_name='User', last_name='One', email='same@example.com')
            user1.set_password('password')
            db.session.add(user1)
            db.session.commit()
            
            user2 = User(first_name='User', last_name='Two', email='same@example.com')
            user2.set_password('password')
            db.session.add(user2)
            
            with pytest.raises(Exception):  # Should raise integrity error
                db.session.commit()

@pytest.mark.models
@pytest.mark.unit
class TestPropertyModel:
    """Test Property model functionality."""
    
    def test_property_creation(self, app, auth_user):
        """Test creating a property."""
        with app.app_context():
            property = Property(
                name='Test Property',
                owner=auth_user.id,
                address='456 Property Ave',
                city='Property City',
                state='NY',
                zip_code=54321,
                type='Single Family'
            )
            db.session.add(property)
            db.session.commit()
            
            saved_property = Property.query.filter_by(name='Test Property').first()
            assert saved_property.name == 'Test Property'
            assert saved_property.owner == auth_user.id
            assert saved_property.address == '456 Property Ave'
            assert saved_property.type == 'Single Family'
    
    def test_property_lease_status_vacant(self, app, auth_user, sample_property):
        """Test property lease status when vacant."""
        with app.app_context():
            status = sample_property.get_lease_status()
            assert status == "Vacant"
    
    def test_property_lease_status_leased(self, app, auth_user, sample_property, sample_unit, sample_tenant):
        """Test property lease status when leased."""
        with app.app_context():
            # Create an active lease
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now() + timedelta(days=300)
            
            lease = Lease(
                tenant_id=sample_tenant.id,
                unit_id=sample_unit.id,
                property_id=sample_property.id,
                start=start_date,
                end=end_date,
                rent=1500
            )
            db.session.add(lease)
            db.session.commit()
            
            status = sample_property.get_lease_status()
            assert status == "Leased"
    
    def test_property_relationships(self, app, auth_user, sample_property, sample_unit, sample_tenant):
        """Test property relationships with units, tenants, and leases."""
        with app.app_context():
            assert len(sample_property.units) == 1
            assert sample_property.units[0].id == sample_unit.id
            
            assert len(sample_property.tenants) == 1
            assert sample_property.tenants[0].id == sample_tenant.id

@pytest.mark.models
@pytest.mark.unit
class TestUnitModel:
    """Test Unit model functionality."""
    
    def test_unit_creation(self, app, auth_user, sample_property):
        """Test creating a unit."""
        with app.app_context():
            unit = Unit(
                name='Unit 2B',
                owner=auth_user.id,
                property=sample_property.id,
                bedrooms=3,
                bathrooms=2,
                rent=2000,
                sqft=1200,
                description='Spacious 3BR unit with balcony'
            )
            db.session.add(unit)
            db.session.commit()
            
            saved_unit = Unit.query.filter_by(name='Unit 2B').first()
            assert saved_unit.name == 'Unit 2B'
            assert saved_unit.bedrooms == 3
            assert saved_unit.bathrooms == 2
            assert saved_unit.rent == 2000
            assert saved_unit.sqft == 1200
    
    def test_unit_property_relationship(self, app, sample_unit, sample_property):
        """Test unit-property relationship."""
        with app.app_context():
            assert sample_unit.property == sample_property.id
            assert sample_unit in sample_property.units

@pytest.mark.models
@pytest.mark.unit
class TestTenantModel:
    """Test Tenant model functionality."""
    
    def test_tenant_creation_complete(self, app, auth_user, sample_property):
        """Test creating tenant with all fields."""
        with app.app_context():
            tenant = Tenant(
                landlord=auth_user.id,
                first_name='Jane',
                last_name='Smith',
                email='jane.smith@example.com',
                phone=5559876543,
                address='789 Tenant Blvd',
                city='Tenant City',
                state='FL',
                zip_code=33101,
                property=sample_property.id
            )
            db.session.add(tenant)
            db.session.commit()
            
            saved_tenant = Tenant.query.filter_by(email='jane.smith@example.com').first()
            assert saved_tenant.first_name == 'Jane'
            assert saved_tenant.last_name == 'Smith'
            assert saved_tenant.phone == 5559876543
            assert saved_tenant.address == '789 Tenant Blvd'
    
    def test_tenant_property_relationship(self, app, sample_tenant, sample_property):
        """Test tenant-property relationship."""
        with app.app_context():
            assert sample_tenant.property == sample_property.id
            assert sample_tenant in sample_property.tenants

@pytest.mark.models
@pytest.mark.unit
class TestLeaseModel:
    """Test Lease model functionality."""
    
    def test_lease_creation(self, app, sample_tenant, sample_unit, sample_property):
        """Test creating a lease."""
        with app.app_context():
            start_date = datetime.now()
            end_date = start_date + timedelta(days=365)
            
            lease = Lease(
                tenant_id=sample_tenant.id,
                unit_id=sample_unit.id,
                property_id=sample_property.id,
                start=start_date,
                end=end_date,
                rent=1800
            )
            db.session.add(lease)
            db.session.commit()
            
            saved_lease = Lease.query.filter_by(tenant_id=sample_tenant.id).first()
            assert saved_lease.tenant_id == sample_tenant.id
            assert saved_lease.unit_id == sample_unit.id
            assert saved_lease.property_id == sample_property.id
            assert saved_lease.rent == 1800
    
    def test_lease_relationships(self, app, sample_tenant, sample_unit, sample_property):
        """Test lease relationships with tenant, unit, and property."""
        with app.app_context():
            start_date = datetime.now()
            end_date = start_date + timedelta(days=365)
            
            lease = Lease(
                tenant_id=sample_tenant.id,
                unit_id=sample_unit.id,
                property_id=sample_property.id,
                start=start_date,
                end=end_date,
                rent=1600
            )
            db.session.add(lease)
            db.session.commit()
            
            # Test relationships through backref
            assert lease in sample_tenant.leases
            assert lease in sample_unit.leases
            assert lease in sample_property.leases
    
    def test_lease_date_validation(self, app, sample_tenant, sample_unit, sample_property):
        """Test lease date validation logic."""
        with app.app_context():
            start_date = datetime.now()
            end_date = start_date - timedelta(days=10)  # End before start
            
            lease = Lease(
                tenant_id=sample_tenant.id,
                unit_id=sample_unit.id,
                property_id=sample_property.id,
                start=start_date,
                end=end_date,
                rent=1500
            )
            db.session.add(lease)
            db.session.commit()
            
            # Note: The model doesn't enforce this validation at DB level
            # This test documents expected behavior for future validation logic
            assert lease.start > lease.end  # This should be prevented in business logic

@pytest.mark.models
@pytest.mark.unit
class TestPortfolioModel:
    """Test Portfolio model functionality."""
    
    def test_portfolio_creation(self, app, auth_user):
        """Test creating a portfolio."""
        with app.app_context():
            portfolio = Portfolio(
                name='My Real Estate Portfolio',
                owner=auth_user.id
            )
            db.session.add(portfolio)
            db.session.commit()
            
            saved_portfolio = Portfolio.query.filter_by(name='My Real Estate Portfolio').first()
            assert saved_portfolio.name == 'My Real Estate Portfolio'
            assert saved_portfolio.owner == auth_user.id
    
    def test_portfolio_property_relationship(self, app, auth_user):
        """Test portfolio-property relationship."""
        with app.app_context():
            portfolio = Portfolio(name='Test Portfolio', owner=auth_user.id)
            db.session.add(portfolio)
            db.session.commit()
            
            property = Property(
                name='Portfolio Property',
                owner=auth_user.id,
                portfolio=portfolio.id,
                address='Portfolio St',
                city='Portfolio City'
            )
            db.session.add(property)
            db.session.commit()
            
            assert property.portfolio == portfolio.id

@pytest.mark.models
@pytest.mark.integration
class TestModelRelationships:
    """Test complex model relationships and cascade behavior."""
    
    def test_property_cascade_deletion(self, app, auth_user):
        """Test that deleting property cascades to units, tenants, and leases."""
        with app.app_context():
            # Create property
            property = Property(name='Test Property', owner=auth_user.id, address='Test St')
            db.session.add(property)
            db.session.commit()
            
            # Create unit
            unit = Unit(name='Unit 1', owner=auth_user.id, property=property.id, rent=1000)
            db.session.add(unit)
            
            # Create tenant
            tenant = Tenant(
                landlord=auth_user.id, 
                first_name='Test', 
                last_name='Tenant',
                property=property.id
            )
            db.session.add(tenant)
            db.session.commit()
            
            # Create lease
            lease = Lease(
                tenant_id=tenant.id,
                unit_id=unit.id,
                property_id=property.id,
                start=datetime.now(),
                end=datetime.now() + timedelta(days=365),
                rent=1000
            )
            db.session.add(lease)
            db.session.commit()
            
            # Verify all created
            assert Unit.query.filter_by(property=property.id).count() == 1
            assert Tenant.query.filter_by(property=property.id).count() == 1
            assert Lease.query.filter_by(property_id=property.id).count() == 1
            
            # Delete property
            db.session.delete(property)
            db.session.commit()
            
            # Verify cascade deletion
            assert Unit.query.filter_by(property=property.id).count() == 0
            assert Tenant.query.filter_by(property=property.id).count() == 0
            assert Lease.query.filter_by(property_id=property.id).count() == 0
    
    def test_user_property_ownership(self, app):
        """Test that users can own multiple properties."""
        with app.app_context():
            user = User(first_name='Owner', last_name='Test', email='owner@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            property1 = Property(name='Property 1', owner=user.id, address='Address 1')
            property2 = Property(name='Property 2', owner=user.id, address='Address 2')
            db.session.add_all([property1, property2])
            db.session.commit()
            
            user_properties = Property.query.filter_by(owner=user.id).all()
            assert len(user_properties) == 2
            assert property1 in user_properties
            assert property2 in user_properties