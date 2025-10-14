"""
Database seeding script - Creates fresh database with sample data

This script:
1. Deletes existing database
2. Creates fresh database with new schema
3. Creates user: kyle.carriveau@gmail.com / B0nehe@d1
4. Populates with portfolios, properties, units, tenants, and leases
"""

import os
import sys
from datetime import datetime, timedelta

# Clear any cached imports
if 'website' in sys.modules:
    del sys.modules['website']
if 'website.models' in sys.modules:
    del sys.modules['website.models']

# Now import fresh
from website import create_app, db
from website.models import Company, User, Portfolio, Property, Unit, Tenant, Lease, Payment, Expense

def seed_database():
    """Seed the database with sample data."""

    # Delete existing database files
    db_paths = ['instance/database.db', 'website/database.db', 'database.db']
    for db_path in db_paths:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✓ Deleted existing database: {db_path}")

    # Create Flask app
    app = create_app()

    with app.app_context():
        # Ensure all tables are created
        db.create_all()
        print("✓ Created fresh database with new schema")

        # Verify User table has new columns by adding them if missing
        import sqlite3
        conn = sqlite3.connect('instance/database.db')
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'bio' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN bio TEXT")
            print("✓ Added bio column to user table")

        if 'job_title' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN job_title VARCHAR(100)")
            print("✓ Added job_title column to user table")

        if 'department' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN department VARCHAR(100)")
            print("✓ Added department column to user table")

        if 'date_joined' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN date_joined DATETIME DEFAULT CURRENT_TIMESTAMP")
            print("✓ Added date_joined column to user table")

        conn.commit()
        conn.close()
        print("✓ Verified and updated user table schema")

        # Create Company
        company = Company(
            name="Carriveau Property Management",
            address="123 Main Street",
            city="San Francisco",
            state="CA",
            zip_code="94102",
            phone="(415) 555-0123",
            email="info@cariveaupm.com"
        )
        db.session.add(company)
        db.session.flush()  # Get company.id
        print(f"✓ Created company: {company.name}")

        # Create User
        user = User(
            first_name="Kyle",
            last_name="Carriveau",
            email="kyle.carriveau@gmail.com",
            password="B0nehe@d1",
            company_id=company.id,
            role="owner"
        )
        user.phone = "(415) 555-0100"
        user.address = "123 Main Street"
        user.city = "San Francisco"
        user.state = "CA"
        user.zip_code = "94102"
        user.bio = "Experienced property manager with over 10 years in real estate management. Specializing in multi-family residential properties."
        user.job_title = "CEO & Property Manager"
        user.department = "Executive"

        db.session.add(user)
        db.session.flush()
        print(f"✓ Created user: {user.email}")

        # Create Portfolios
        portfolios = []

        portfolio1 = Portfolio(
            name="Downtown Residential",
            company_id=company.id
        )
        portfolios.append(portfolio1)

        portfolio2 = Portfolio(
            name="Suburban Family Homes",
            company_id=company.id
        )
        portfolios.append(portfolio2)

        portfolio3 = Portfolio(
            name="Luxury Condos",
            company_id=company.id
        )
        portfolios.append(portfolio3)

        for portfolio in portfolios:
            db.session.add(portfolio)

        db.session.flush()
        print(f"✓ Created {len(portfolios)} portfolios")

        # Create Properties
        properties_data = [
            {
                "name": "Sunset Apartments",
                "address": "456 Sunset Blvd",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94122",
                "type": "Multi-Family",
                "units_count": 12,
                "portfolio": portfolio1
            },
            {
                "name": "Harbor View Residences",
                "address": "789 Harbor Drive",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94111",
                "type": "Multi-Family",
                "units_count": 8,
                "portfolio": portfolio1
            },
            {
                "name": "Maple Street Commons",
                "address": "321 Maple Street",
                "city": "Oakland",
                "state": "CA",
                "zip_code": "94601",
                "type": "Multi-Family",
                "units_count": 6,
                "portfolio": portfolio1
            },
            {
                "name": "Oak Ridge House",
                "address": "555 Oak Ridge Lane",
                "city": "San Mateo",
                "state": "CA",
                "zip_code": "94402",
                "type": "Single Family",
                "units_count": 1,
                "portfolio": portfolio2
            },
            {
                "name": "Willow Creek Home",
                "address": "777 Willow Creek Road",
                "city": "Palo Alto",
                "state": "CA",
                "zip_code": "94301",
                "type": "Single Family",
                "units_count": 1,
                "portfolio": portfolio2
            },
            {
                "name": "Bayview Luxury Towers",
                "address": "999 Bayview Plaza",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94105",
                "type": "Condo",
                "units_count": 10,
                "portfolio": portfolio3
            }
        ]

        properties = []
        for prop_data in properties_data:
            property = Property(
                name=prop_data["name"],
                company_id=company.id,
                portfolio_id=prop_data["portfolio"].id
            )
            # Set other fields as attributes
            property.address = prop_data["address"]
            property.city = prop_data["city"]
            property.state = prop_data["state"]
            property.zip_code = prop_data["zip_code"]
            property.type = prop_data["type"]
            property.description = f"Beautiful {prop_data['type'].lower()} property in {prop_data['city']}"

            properties.append((property, prop_data["units_count"]))
            db.session.add(property)

        db.session.flush()
        print(f"✓ Created {len(properties)} properties")

        # Create Units for each property
        unit_configs = [
            {"beds": 0, "baths": 1, "sqft": 450, "rent": 1800, "name_suffix": "Studio"},
            {"beds": 1, "baths": 1, "sqft": 650, "rent": 2200, "name_suffix": "1BR"},
            {"beds": 2, "baths": 1, "sqft": 850, "rent": 2800, "name_suffix": "2BR"},
            {"beds": 2, "baths": 2, "sqft": 1000, "rent": 3200, "name_suffix": "2BR/2BA"},
            {"beds": 3, "baths": 2, "sqft": 1200, "rent": 3800, "name_suffix": "3BR"},
        ]

        total_units = 0
        for property, units_count in properties:
            for i in range(units_count):
                config = unit_configs[i % len(unit_configs)]

                unit = Unit(
                    name=f"{property.name} - Unit {i+1}",
                    company_id=company.id,
                    property_id=property.id
                )

                # Basic details
                unit.bedrooms = config["beds"]
                unit.bathrooms = config["baths"]
                unit.sqft = config["sqft"]
                unit.rent = config["rent"]
                unit.description = f"{config['name_suffix']} unit with modern finishes"

                # Amenities
                unit.air_conditioning = True
                unit.heating_type = "Central"
                unit.dishwasher = True
                unit.microwave = True
                unit.refrigerator = True
                unit.washer_dryer = "In-unit" if config["beds"] >= 2 else "Shared"
                unit.parking_spaces = 1 if config["beds"] >= 2 else 0
                unit.parking_type = "Garage" if config["beds"] >= 2 else "Street"
                unit.balcony_patio = config["beds"] >= 2
                unit.pets_allowed = True
                unit.pet_deposit = 500
                unit.internet_included = True

                # Set some units as occupied, some available
                if i % 3 == 0:
                    unit.occupancy_status = "Available"
                elif i % 3 == 1:
                    unit.occupancy_status = "Occupied"
                else:
                    unit.occupancy_status = "Reserved"

                db.session.add(unit)
                total_units += 1

        db.session.flush()
        print(f"✓ Created {total_units} units")

        # Create Tenants
        tenants_data = [
            {"first": "Sarah", "last": "Johnson", "email": "sarah.j@email.com", "phone": "(415) 555-1001"},
            {"first": "Michael", "last": "Chen", "email": "mchen@email.com", "phone": "(415) 555-1002"},
            {"first": "Jessica", "last": "Williams", "email": "jwilliams@email.com", "phone": "(415) 555-1003"},
            {"first": "David", "last": "Martinez", "email": "david.m@email.com", "phone": "(415) 555-1004"},
            {"first": "Emily", "last": "Anderson", "email": "emily.a@email.com", "phone": "(415) 555-1005"},
            {"first": "James", "last": "Thompson", "email": "jthompson@email.com", "phone": "(415) 555-1006"},
            {"first": "Lisa", "last": "Garcia", "email": "lgarcia@email.com", "phone": "(415) 555-1007"},
            {"first": "Robert", "last": "Davis", "email": "rdavis@email.com", "phone": "(415) 555-1008"},
            {"first": "Jennifer", "last": "Wilson", "email": "jwilson@email.com", "phone": "(415) 555-1009"},
            {"first": "Daniel", "last": "Moore", "email": "dmoore@email.com", "phone": "(415) 555-1010"},
        ]

        tenants = []
        for tenant_data in tenants_data:
            tenant = Tenant(
                first_name=tenant_data["first"],
                last_name=tenant_data["last"],
                company_id=company.id
            )
            # Set other fields as attributes
            tenant.email = tenant_data["email"]
            tenant.phone = tenant_data["phone"]

            tenants.append(tenant)
            db.session.add(tenant)

        db.session.flush()
        print(f"✓ Created {len(tenants)} tenants")

        # Create Leases for occupied units
        occupied_units = Unit.query.filter_by(company_id=company.id, occupancy_status="Occupied").all()

        for i, unit in enumerate(occupied_units[:len(tenants)]):
            tenant = tenants[i]

            # Create lease starting 6 months ago, ending 6 months from now
            start_date = datetime.now() - timedelta(days=180)
            end_date = datetime.now() + timedelta(days=180)

            lease = Lease(
                tenant_id=tenant.id,
                property_id=unit.property_id,
                unit_id=unit.id,
                company_id=company.id,
                start=start_date,
                end=end_date,
                rent=unit.rent
            )
            # Set other fields as attributes
            lease.deposit = unit.rent * 2
            lease.lease_status = "active"
            lease.utilities_included = "Water, Trash"
            lease.pets_allowed = True
            lease.payment_due_day = 1

            db.session.add(lease)
            db.session.flush()  # Flush to get lease.id before creating payments

            # Create some payments for each lease
            for month_offset in range(-3, 1):  # Last 3 months + current month
                payment_date = datetime.now() + timedelta(days=30*month_offset)
                # Due on the 1st of the month
                due_date = payment_date.replace(day=1)
                payment = Payment(
                    lease_id=lease.id,
                    property_id=unit.property_id,
                    company_id=company.id,
                    amount=unit.rent,
                    payment_date=payment_date,
                    due_date=due_date,
                    status="completed",
                    payment_method="Bank Transfer",
                    user_id=user.id
                )
                db.session.add(payment)

        print(f"✓ Created {len(occupied_units[:len(tenants)])} leases with payment history")

        # Create some expenses
        expense_categories = [
            ("Maintenance", 450, "HVAC servicing"),
            ("Repairs", 1200, "Plumbing repair - Unit 3"),
            ("Landscaping", 300, "Monthly landscaping service"),
            ("Utilities", 850, "Common area utilities"),
            ("Insurance", 2400, "Property insurance premium"),
            ("Repairs", 750, "Roof leak repair"),
            ("Maintenance", 200, "Elevator inspection"),
            ("Property Tax", 5000, "Quarterly property tax"),
        ]

        for category, amount, description in expense_categories:
            expense_date = datetime.now() - timedelta(days=30)
            expense = Expense(
                description=description,
                amount=amount,
                expense_date=expense_date,
                category=category.lower(),
                company_id=company.id,
                property_id=properties[0][0].id,  # Assign to first property
                user_id=user.id
            )
            db.session.add(expense)

        print(f"✓ Created {len(expense_categories)} expense records")

        # Commit all changes
        db.session.commit()

        print("\n" + "="*60)
        print("✅ DATABASE SEEDED SUCCESSFULLY!")
        print("="*60)
        print(f"\nLogin Credentials:")
        print(f"  Email:    kyle.carriveau@gmail.com")
        print(f"  Password: B0nehe@d1")
        print(f"\nData Summary:")
        print(f"  Company:    1")
        print(f"  Users:      1 (Owner)")
        print(f"  Portfolios: {len(portfolios)}")
        print(f"  Properties: {len(properties)}")
        print(f"  Units:      {total_units}")
        print(f"  Tenants:    {len(tenants)}")
        print(f"  Leases:     {len(occupied_units[:len(tenants)])}")
        print(f"  Expenses:   {len(expense_categories)}")
        print("\n" + "="*60)

if __name__ == '__main__':
    seed_database()
