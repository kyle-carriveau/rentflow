"""
Shared test fixtures and configuration for RE2 application testing.

This module provides:
- Flask application factory with test configuration
- Database setup and teardown fixtures
- Multi-tenant company and user fixtures
- Authentication helpers for testing
- Common test data factories
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from decimal import Decimal
from flask import url_for
from flask_login import login_user, logout_user

from website import create_app, db
from website.models import (
    User, Company, Property, Unit, Tenant, Lease,
    Payment, Expense, Portfolio
)
from sqlalchemy import text


@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application."""
    # Create a temporary file for the test database
    db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')

    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{temp_db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SECRET_KEY': 'test-secret-key',
        'LOGIN_DISABLED': False,
    })

    with app.app_context():
        # Create all database tables
        db.create_all()
        yield app

        # Cleanup
        db.session.remove()
        db.drop_all()

    # Close and remove the temporary database file
    os.close(db_fd)
    os.unlink(temp_db_path)


@pytest.fixture
def client(app):
    """Create a test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Automatically clean database before each test."""
    with app.app_context():
        # Clean up all tables in reverse dependency order
        db.session.execute(text('DELETE FROM payment'))
        db.session.execute(text('DELETE FROM expense'))
        db.session.execute(text('DELETE FROM lease'))
        db.session.execute(text('DELETE FROM tenant'))
        db.session.execute(text('DELETE FROM unit'))
        db.session.execute(text('DELETE FROM property'))
        db.session.execute(text('DELETE FROM portfolio'))
        db.session.execute(text('DELETE FROM user'))
        db.session.execute(text('DELETE FROM company'))
        db.session.commit()


# Company Fixtures
@pytest.fixture
def company_a(app):
    """Create test company A for multi-tenant testing."""
    with app.app_context():
        company = Company(
            name='Test Company A',
            email='contact@companya.com',
            phone='555-0001',
            address='123 Company A St',
            city='Test City A',
            state='CA',
            zip_code='90001'
        )
        db.session.add(company)
        db.session.commit()
        return company


@pytest.fixture
def company_b(app):
    """Create test company B for multi-tenant testing."""
    with app.app_context():
        company = Company(
            name='Test Company B',
            email='contact@companyb.com',
            phone='555-0002',
            address='456 Company B Ave',
            city='Test City B',
            state='NY',
            zip_code='10001'
        )
        db.session.add(company)
        db.session.commit()
        return company


# User Fixtures
@pytest.fixture
def owner_user(app, company_a):
    """Create an owner user for company A."""
    with app.app_context():
        user = User(
            first_name='Alice',
            last_name='Owner',
            email='alice@companya.com',
            role='Owner',
            company_id=company_a.id
        )
        user.set_password('test_password')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def manager_user(app, company_a):
    """Create a manager user for company A."""
    with app.app_context():
        user = User(
            first_name='Bob',
            last_name='Manager',
            email='bob@companya.com',
            role='Manager',
            company_id=company_a.id
        )
        user.set_password('test_password')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def staff_user(app, company_a):
    """Create a staff user for company A."""
    with app.app_context():
        user = User(
            first_name='Carol',
            last_name='Staff',
            email='carol@companya.com',
            role='Staff',
            company_id=company_a.id
        )
        user.set_password('test_password')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def viewer_user(app, company_a):
    """Create a viewer user for company A."""
    with app.app_context():
        user = User(
            first_name='Dave',
            last_name='Viewer',
            email='dave@companya.com',
            role='Viewer',
            company_id=company_a.id
        )
        user.set_password('test_password')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def user_company_b(app, company_b):
    """Create a user for company B (for isolation testing)."""
    with app.app_context():
        user = User(
            first_name='Eve',
            last_name='CompanyB',
            email='eve@companyb.com',
            role='Owner',
            company_id=company_b.id
        )
        user.set_password('test_password')
        db.session.add(user)
        db.session.commit()
        return user


# Authentication Helpers
@pytest.fixture
def authenticated_client(app, client, owner_user):
    """Create a client with authenticated owner user."""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = str(owner_user.id)
            sess['_fresh'] = True
    return client


class AuthContextManager:
    """Context manager for user authentication in tests."""

    def __init__(self, app, user):
        self.app = app
        self.user = user

    def __enter__(self):
        with self.app.test_request_context():
            login_user(self.user)
        return self.user

    def __exit__(self, *args):
        with self.app.test_request_context():
            logout_user()


def login_as_user(app, user):
    """Helper to login as a specific user in tests."""
    return AuthContextManager(app, user)


# Property and Portfolio Fixtures
@pytest.fixture
def portfolio(app, company_a):
    """Create a test portfolio for company A."""
    with app.app_context():
        portfolio = Portfolio(
            name='Test Portfolio A',
            description='Test portfolio for company A',
            company_id=company_a.id
        )
        db.session.add(portfolio)
        db.session.commit()
        return portfolio


@pytest.fixture
def property_a(app, company_a, portfolio):
    """Create a test property for company A."""
    with app.app_context():
        property_obj = Property(
            name='Test Property A',
            address='123 Property St',
            city='Test City',
            state='CA',
            zip_code='90210',
            property_type='Apartment',
            company_id=company_a.id,
            portfolio_id=portfolio.id
        )
        db.session.add(property_obj)
        db.session.commit()
        return property_obj


@pytest.fixture
def property_b(app, company_b):
    """Create a test property for company B (isolation testing)."""
    with app.app_context():
        property_obj = Property(
            name='Test Property B',
            address='456 Property Ave',
            city='Test City B',
            state='NY',
            zip_code='10001',
            property_type='Condo',
            company_id=company_b.id
        )
        db.session.add(property_obj)
        db.session.commit()
        return property_obj


@pytest.fixture
def unit(app, property_a):
    """Create a test unit for property A."""
    with app.app_context():
        unit = Unit(
            unit_number='101',
            bedrooms=2,
            bathrooms=1,
            square_feet=1000,
            rent=Decimal('1500.00'),
            property_id=property_a.id
        )
        db.session.add(unit)
        db.session.commit()
        return unit


# Tenant Fixtures
@pytest.fixture
def tenant(app, company_a):
    """Create a test tenant for company A."""
    with app.app_context():
        tenant = Tenant(
            first_name='John',
            last_name='Tenant',
            email='john.tenant@example.com',
            phone='555-0123',
            company_id=company_a.id
        )
        db.session.add(tenant)
        db.session.commit()
        return tenant


# Lease Fixtures
@pytest.fixture
def active_lease(app, unit, tenant):
    """Create an active lease for testing."""
    with app.app_context():
        start_date = datetime.now().date() - timedelta(days=30)
        end_date = datetime.now().date() + timedelta(days=335)  # ~11 months from now

        lease = Lease(
            start=start_date,
            end=end_date,
            rent=Decimal('1500.00'),
            deposit=Decimal('1500.00'),
            unit_id=unit.id,
            tenant_id=tenant.id
        )
        db.session.add(lease)
        db.session.commit()
        return lease


@pytest.fixture
def expiring_lease(app, unit, tenant):
    """Create a lease expiring soon for testing alerts."""
    with app.app_context():
        start_date = datetime.now().date() - timedelta(days=330)
        end_date = datetime.now().date() + timedelta(days=30)  # Expires in 30 days

        lease = Lease(
            start=start_date,
            end=end_date,
            rent=Decimal('1500.00'),
            deposit=Decimal('1500.00'),
            unit_id=unit.id,
            tenant_id=tenant.id
        )
        db.session.add(lease)
        db.session.commit()
        return lease


# Financial Fixtures
@pytest.fixture
def payment(app, active_lease):
    """Create a test payment."""
    with app.app_context():
        payment = Payment(
            amount=Decimal('1500.00'),
            payment_date=datetime.now().date(),
            payment_method='Check',
            status='completed',
            lease_id=active_lease.id
        )
        db.session.add(payment)
        db.session.commit()
        return payment


@pytest.fixture
def expense(app, company_a, property_a):
    """Create a test expense."""
    with app.app_context():
        expense = Expense(
            amount=Decimal('250.00'),
            description='Maintenance repair',
            category='maintenance',
            expense_date=datetime.now().date(),
            company_id=company_a.id,
            property_id=property_a.id
        )
        db.session.add(expense)
        db.session.commit()
        return expense


# Test Data Factories
class TestDataFactory:
    """Factory class for creating test data with realistic values."""

    @staticmethod
    def create_company(app, **kwargs):
        """Create a company with default values."""
        defaults = {
            'name': 'Test Company',
            'email': 'test@company.com',
            'phone': '555-0000',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'CA',
            'zip_code': '90000'
        }
        defaults.update(kwargs)

        with app.app_context():
            company = Company(**defaults)
            db.session.add(company)
            db.session.commit()
            return company

    @staticmethod
    def create_user(app, company, **kwargs):
        """Create a user with default values."""
        defaults = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@user.com',
            'role': 'Staff',
            'company_id': company.id
        }
        defaults.update(kwargs)

        with app.app_context():
            user = User(**defaults)
            user.set_password('test_password')
            db.session.add(user)
            db.session.commit()
            return user

    @staticmethod
    def create_property(app, company, portfolio=None, **kwargs):
        """Create a property with default values."""
        defaults = {
            'name': 'Test Property',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'CA',
            'zip_code': '90000',
            'property_type': 'Apartment',
            'company_id': company.id
        }
        if portfolio:
            defaults['portfolio_id'] = portfolio.id
        defaults.update(kwargs)

        with app.app_context():
            property_obj = Property(**defaults)
            db.session.add(property_obj)
            db.session.commit()
            return property_obj


@pytest.fixture
def test_factory():
    """Provide the test data factory."""
    return TestDataFactory