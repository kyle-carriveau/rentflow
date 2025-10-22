#!/usr/bin/env python3
"""
Database Seeding Script - Multi-Environment Support
Creates comprehensive test data for development and staging environments

Usage:
    python scripts/db-seed.py [environment] [size]

Arguments:
    environment: local, staging (default: local)
    size: small, medium, large (default: small)

Examples:
    python scripts/db-seed.py local small
    python scripts/db-seed.py staging medium

⚠️ WARNING: This will create test data in the target database!
Production environment is blocked for safety.

Data Size Guidelines:
    small:  2 companies, 5 users, 3 properties, 5 tenants, 8 leases
    medium: 5 companies, 15 users, 10 properties, 20 tenants, 30 leases
    large:  10 companies, 30 users, 25 properties, 50 tenants, 75 leases
"""

import sys
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    NC = '\033[0m'  # No Color

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.NC} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.NC} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.NC} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.NC} {msg}")

def print_create(msg):
    print(f"{Colors.MAGENTA}+{Colors.NC} {msg}")

# Parse arguments
environment = sys.argv[1] if len(sys.argv) > 1 else 'local'
size = sys.argv[2] if len(sys.argv) > 2 else 'small'

# Validate environment
if environment not in ['local', 'staging']:
    print_error(f"Invalid environment: {environment}")
    print("Valid environments: local, staging")
    sys.exit(1)

# Validate size
if size not in ['small', 'medium', 'large']:
    print_error(f"Invalid size: {size}")
    print("Valid sizes: small, medium, large")
    sys.exit(1)

# Production safety check
if os.environ.get('FLASK_ENV') == 'production':
    print_error("❌ ERROR: Cannot seed production database!")
    print_error("This script is for development and staging only.")
    sys.exit(1)

# Set environment-specific configuration
if environment == 'local':
    os.environ['FLASK_ENV'] = 'development'
    if not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'postgresql://rentflow_dev:rentflow_dev_password@localhost:5432/rentflow_dev'
elif environment == 'staging':
    os.environ['FLASK_ENV'] = 'staging'
    # Staging should already have DATABASE_URL set

print("")
print_warning("════════════════════════════════════════════════════════════")
print_warning(f"  Database Seeding - {environment.upper()} Environment")
print_warning("════════════════════════════════════════════════════════════")
print("")
print_info(f"Environment: {environment}")
print_info(f"Data Size:   {size}")
print("")

# Import Flask app and models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from website import create_app, db
    from website.models import Company, User, Portfolio, Property, Unit, Tenant, Lease, Payment, Expense
    from werkzeug.security import generate_password_hash
except ImportError as e:
    print_error(f"Failed to import Flask application: {e}")
    print_error("Make sure you're running from the project root directory")
    sys.exit(1)

# Create Flask app
app = create_app(environment if environment != 'local' else 'development')

# Define data sizes
DATA_SIZES = {
    'small': {
        'companies': 2,
        'users_per_company': 3,
        'portfolios_per_company': 2,
        'properties_per_portfolio': 2,
        'units_per_property': 2,
        'tenants_per_company': 3,
        'leases_per_company': 4,
        'payments_per_lease': 3,
        'expenses_per_company': 5
    },
    'medium': {
        'companies': 5,
        'users_per_company': 3,
        'portfolios_per_company': 2,
        'properties_per_portfolio': 3,
        'units_per_property': 3,
        'tenants_per_company': 4,
        'leases_per_company': 6,
        'payments_per_lease': 4,
        'expenses_per_company': 8
    },
    'large': {
        'companies': 10,
        'users_per_company': 4,
        'portfolios_per_company': 3,
        'properties_per_portfolio': 3,
        'units_per_property': 4,
        'tenants_per_company': 5,
        'leases_per_company': 8,
        'payments_per_lease': 5,
        'expenses_per_company': 12
    }
}

config = DATA_SIZES[size]

# Sample data
COMPANY_NAMES = ['Sunset Properties', 'Metro Real Estate', 'Bay Area Rentals', 'Pacific Property Group',
                 'Golden Gate Management', 'Cityview Realty', 'Harbor Property Co', 'Riverside Investments',
                 'Summit Real Estate', 'Coastal Properties']

FIRST_NAMES = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William',
               'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah']

LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez',
              'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore']

PORTFOLIO_TYPES = ['Residential', 'Commercial', 'Mixed-Use', 'Student Housing', 'Senior Living']

PROPERTY_TYPES = ['Apartment', 'House', 'Townhouse', 'Condo', 'Duplex']

STREETS = ['Main St', 'Oak Ave', 'Maple Dr', 'Pine St', 'Cedar Ln', 'Elm St', 'Washington Blvd',
           'Market St', 'Broadway', 'Park Ave', 'Lake Dr', 'River Rd', 'Hill St', 'Valley Way']

CITIES = ['San Francisco', 'Oakland', 'San Jose', 'Berkeley', 'Palo Alto', 'Mountain View',
          'Redwood City', 'Sunnyvale', 'Santa Clara', 'Fremont']

STATES = ['CA', 'NY', 'TX', 'FL', 'WA']

UNIT_TYPES = ['Studio', '1BR/1BA', '2BR/1BA', '2BR/2BA', '3BR/2BA', '3BR/3BA', '4BR/2BA']

EXPENSE_CATEGORIES = ['Maintenance', 'Utilities', 'Insurance', 'Property Tax', 'HOA Fees',
                      'Repairs', 'Landscaping', 'Legal Fees', 'Marketing', 'Supplies']

def generate_email(first_name, last_name, company_id):
    """Generate a unique test email"""
    return f"{first_name.lower()}.{last_name.lower()}{company_id}@test.example.com"

def random_date(start_days_ago, end_days_ago=0):
    """Generate random date between start_days_ago and end_days_ago"""
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)

# Main seeding logic
with app.app_context():
    print_info("═══════════════════════════════════════════════════════════")
    print_info("  Creating Test Data")
    print_info("═══════════════════════════════════════════════════════════")
    print("")

    created_counts = {
        'companies': 0,
        'users': 0,
        'portfolios': 0,
        'properties': 0,
        'units': 0,
        'tenants': 0,
        'leases': 0,
        'payments': 0,
        'expenses': 0
    }

    # Create companies
    print_create("Creating companies...")
    companies = []
    for i in range(config['companies']):
        company_name = COMPANY_NAMES[i % len(COMPANY_NAMES)]

        # Check if company already exists
        existing = Company.query.filter_by(name=f"{company_name} {i+1}").first()
        if existing:
            companies.append(existing)
            print_info(f"  Using existing: {existing.name}")
            continue

        company = Company(
            name=f"{company_name} {i+1}",
            email=f"info{i+1}@{company_name.lower().replace(' ', '')}.com",
            phone=f"555-{1000+i:04d}",
            address=f"{100*(i+1)} {random.choice(STREETS)}",
            city=random.choice(CITIES),
            state=random.choice(STATES),
            zip_code=f"{90000 + i:05d}",
            website=f"https://{company_name.lower().replace(' ', '')}{i+1}.example.com"
        )
        db.session.add(company)
        companies.append(company)
        created_counts['companies'] += 1
        print_success(f"  Created: {company.name}")

    db.session.flush()

    # Create users for each company
    print("")
    print_create("Creating users...")
    all_users = []
    roles = ['Owner', 'Manager', 'Staff', 'Viewer']

    for company in companies:
        company_users = []
        for i in range(config['users_per_company']):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            email = generate_email(first_name, last_name, company.id)

            # Check if user already exists
            existing = User.query.filter_by(email=email).first()
            if existing:
                company_users.append(existing)
                continue

            user = User(
                email=email,
                password_hash=generate_password_hash('TestPassword123!'),
                first_name=first_name,
                last_name=last_name,
                phone=f"555{2000 + len(all_users):04d}",
                role=roles[i % len(roles)],
                company_id=company.id
            )
            db.session.add(user)
            company_users.append(user)
            all_users.append(user)
            created_counts['users'] += 1
            print_success(f"  Created: {user.email} ({user.role}) for {company.name}")

        # Store users on company for later reference
        company._seed_users = company_users

    db.session.flush()

    # Create portfolios for each company
    print("")
    print_create("Creating portfolios...")

    for company in companies:
        company._seed_portfolios = []
        for i in range(config['portfolios_per_company']):
            portfolio_type = PORTFOLIO_TYPES[i % len(PORTFOLIO_TYPES)]

            portfolio = Portfolio(
                name=f"{portfolio_type} Portfolio {i+1}",
                description=f"{portfolio_type} properties managed by {company.name}",
                company_id=company.id
            )
            db.session.add(portfolio)
            company._seed_portfolios.append(portfolio)
            created_counts['portfolios'] += 1
            print_success(f"  Created: {portfolio.name} for {company.name}")

    db.session.flush()

    # Create properties for each portfolio
    print("")
    print_create("Creating properties...")
    all_properties = []

    for company in companies:
        for portfolio in company._seed_portfolios:
            for i in range(config['properties_per_portfolio']):
                property_type = random.choice(PROPERTY_TYPES)
                street_num = random.randint(100, 9999)
                street = random.choice(STREETS)

                prop = Property(
                    name=f"{street_num} {street}",
                    property_type=property_type,
                    street_address=f"{street_num} {street}",
                    city=random.choice(CITIES),
                    state=random.choice(STATES),
                    zip_code=f"{90000 + random.randint(0, 999):05d}",
                    year_built=random.randint(1970, 2023),
                    total_units=config['units_per_property'],
                    portfolio_id=portfolio.id,
                    company_id=company.id
                )
                db.session.add(prop)
                all_properties.append(prop)
                created_counts['properties'] += 1
                print_success(f"  Created: {prop.name} ({property_type})")

    db.session.flush()

    # Create units for each property
    print("")
    print_create("Creating units...")
    all_units = []

    for prop in all_properties:
        for i in range(config['units_per_property']):
            unit_type = random.choice(UNIT_TYPES)
            bedrooms = int(unit_type.split('BR')[0]) if 'BR' in unit_type else 0
            bathrooms = int(unit_type.split('BA')[0].split('/')[-1]) if 'BA' in unit_type else 1

            unit = Unit(
                unit_number=f"{100 * (i // 10 + 1) + (i % 10 + 1)}",
                bedrooms=bedrooms,
                bathrooms=Decimal(str(bathrooms)),
                square_feet=random.randint(500, 2000),
                rent_amount=Decimal(str(random.randint(1000, 4000))),
                status='Vacant',
                property_id=prop.id,
                company_id=prop.company_id
            )
            db.session.add(unit)
            all_units.append(unit)
            created_counts['units'] += 1

    db.session.flush()
    print_success(f"  Created {len(all_units)} units")

    # Create tenants for each company
    print("")
    print_create("Creating tenants...")

    for company in companies:
        company._seed_tenants = []
        for i in range(config['tenants_per_company']):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)

            tenant = Tenant(
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}{company.id}@tenant.example.com",
                phone=5553000 + len(company._seed_tenants),
                street_address=f"{random.randint(100, 9999)} {random.choice(STREETS)}",
                city=random.choice(CITIES),
                state=random.choice(STATES),
                zip_code=f"{90000 + random.randint(0, 999):05d}",
                emergency_contact_name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                emergency_contact_phone=5559000 + len(company._seed_tenants),
                company_id=company.id
            )
            db.session.add(tenant)
            company._seed_tenants.append(tenant)
            created_counts['tenants'] += 1
            print_success(f"  Created: {tenant.first_name} {tenant.last_name}")

    db.session.flush()

    # Create leases
    print("")
    print_create("Creating leases...")

    for company in companies:
        # Get units for this company
        company_units = [u for u in all_units if u.company_id == company.id]

        for i in range(min(config['leases_per_company'], len(company_units), len(company._seed_tenants))):
            unit = company_units[i]
            tenant = company._seed_tenants[i % len(company._seed_tenants)]

            start_date = random_date(365, 30)
            lease_term = random.choice([6, 12, 24])
            end_date = start_date + timedelta(days=lease_term * 30)

            # Determine lease status based on dates
            if start_date > datetime.now():
                status = 'Pending'
            elif end_date < datetime.now():
                status = 'Expired'
            else:
                status = 'Active'
                unit.status = 'Occupied'

            lease = Lease(
                unit_id=unit.id,
                tenant_id=tenant.id,
                start_date=start_date,
                end_date=end_date,
                rent_amount=unit.rent_amount,
                security_deposit=unit.rent_amount * Decimal('1.5'),
                payment_due_date=5,
                status=status,
                company_id=company.id
            )
            db.session.add(lease)
            created_counts['leases'] += 1
            print_success(f"  Created: Lease for Unit {unit.unit_number} - {tenant.first_name} {tenant.last_name} ({status})")

            # Create payments for active/expired leases
            if status in ['Active', 'Expired']:
                months = min(config['payments_per_lease'], (datetime.now() - start_date).days // 30)
                for month in range(months):
                    payment_date = start_date + timedelta(days=month * 30 + random.randint(1, 5))

                    payment = Payment(
                        lease_id=lease.id,
                        amount_paid=lease.rent_amount,
                        payment_date=payment_date,
                        payment_method=random.choice(['Check', 'ACH', 'Credit Card', 'Cash']),
                        notes=f"Rent payment for month {month + 1}",
                        company_id=company.id
                    )
                    db.session.add(payment)
                    created_counts['payments'] += 1

    db.session.flush()
    print_success(f"  Created {created_counts['payments']} payments")

    # Create expenses
    print("")
    print_create("Creating expenses...")

    for company in companies:
        company_properties = [p for p in all_properties if p.company_id == company.id]

        for i in range(config['expenses_per_company']):
            prop = random.choice(company_properties) if company_properties else None
            category = random.choice(EXPENSE_CATEGORIES)

            expense = Expense(
                date=random_date(365),
                category=category,
                amount=Decimal(str(random.randint(100, 5000))),
                vendor=f"{category} Services Inc",
                description=f"{category} expense for property maintenance",
                property_id=prop.id if prop else None,
                is_tax_deductible=random.choice([True, False]),
                company_id=company.id
            )
            db.session.add(expense)
            created_counts['expenses'] += 1

    db.session.flush()
    print_success(f"  Created {created_counts['expenses']} expenses")

    # Commit all changes
    print("")
    print_info("Committing changes to database...")
    try:
        db.session.commit()
        print_success("All changes committed successfully!")
    except Exception as e:
        db.session.rollback()
        print_error(f"Failed to commit changes: {e}")
        sys.exit(1)

    # Print summary
    print("")
    print_success("════════════════════════════════════════════════════════════")
    print_success("  Seeding Complete!")
    print_success("════════════════════════════════════════════════════════════")
    print("")
    print_info("Data Created:")
    print(f"  Companies:   {created_counts['companies']}")
    print(f"  Users:       {created_counts['users']}")
    print(f"  Portfolios:  {created_counts['portfolios']}")
    print(f"  Properties:  {created_counts['properties']}")
    print(f"  Units:       {created_counts['units']}")
    print(f"  Tenants:     {created_counts['tenants']}")
    print(f"  Leases:      {created_counts['leases']}")
    print(f"  Payments:    {created_counts['payments']}")
    print(f"  Expenses:    {created_counts['expenses']}")
    print("")
    print_info("Test Credentials:")
    print(f"  Email:    <any-user>@test.example.com")
    print(f"  Password: TestPassword123!")
    print("")
    print_success("Database seeded successfully!")

sys.exit(0)
