#!/usr/bin/env python3
"""
Comprehensive database migration for Lease Management Enhancements.

This migration includes:
Phase 1: Lease Status Tracking
- Lease.status_updated_at
- Unit.occupancy_status, Unit.status_updated_at
- Property.occupancy_status, Property.status_updated_at

Phase 2: Lease Templates
- Creates lease_template table
- Adds Lease.template_id foreign key
- Inserts default system templates

Run with: python migrate_lease_enhancements.py
"""

import sqlite3
from datetime import datetime
import sys
import json

DATABASE_PATH = 'instance/database.db'

# Default lease template content
DEFAULT_RESIDENTIAL_TEMPLATE = """RESIDENTIAL LEASE AGREEMENT

This Lease Agreement ("Agreement") is entered into on {{current_date}} by and between:

LANDLORD: {{landlord_company}}
TENANT: {{tenant_name}}

PROPERTY INFORMATION:
Address: {{property_address}}
Unit: {{unit_number}}

LEASE TERMS:
1. TERM: This lease shall commence on {{start_date}} and end on {{end_date}}, for a total term of {{lease_term_months}} months.

2. RENT: Tenant agrees to pay ${{rent_amount}} per month, due on the {{payment_due_date}} day of each month.

3. SECURITY DEPOSIT: Tenant has paid a security deposit of {{security_deposit}}, which will be held in accordance with state law.

4. UTILITIES: The following utilities are included: {{utilities_included}}

5. LATE FEES: A late fee of {{late_fee}} will be charged if rent is not paid within the grace period.

6. PET POLICY: Pet deposit: {{pet_deposit}}

7. OCCUPANCY: This unit is leased to the tenant named above and immediate family only.

8. MAINTENANCE: Tenant agrees to maintain the premises in good condition and report needed repairs promptly.

9. TERMINATION: Either party may terminate this lease with proper notice as required by law and this agreement.

By signing below, both parties agree to the terms of this lease agreement.

LANDLORD: _____________________________ Date: __________

TENANT: _____________________________ Date: __________
"""

def add_column_if_not_exists(cursor, table_name, column_name, column_type, default=None):
    """Add a column to a table if it doesn't already exist."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]

    if column_name in columns:
        print(f"  ✓ Column {table_name}.{column_name} already exists")
        return False

    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
    if default is not None:
        alter_sql += f" DEFAULT {default}"

    cursor.execute(alter_sql)
    print(f"  ✓ Added {table_name}.{column_name}")
    return True

def table_exists(cursor, table_name):
    """Check if a table exists."""
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def create_lease_template_table(cursor):
    """Create the lease_template table."""
    if table_exists(cursor, 'lease_template'):
        print("  ✓ lease_template table already exists")
        return False

    cursor.execute("""
        CREATE TABLE lease_template (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid VARCHAR(36) UNIQUE NOT NULL,
            company_id INTEGER,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            template_type VARCHAR(50) DEFAULT 'residential',
            contract_text TEXT NOT NULL,
            header_text TEXT,
            footer_text TEXT,
            default_terms TEXT,
            is_default BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            is_system_template BOOLEAN DEFAULT 0,
            version INTEGER DEFAULT 1,
            parent_template_id INTEGER,
            available_merge_fields TEXT,
            required_fields TEXT,
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            FOREIGN KEY (company_id) REFERENCES company(id),
            FOREIGN KEY (parent_template_id) REFERENCES lease_template(id),
            FOREIGN KEY (created_by) REFERENCES user(id)
        )
    """)
    print("  ✓ Created lease_template table")
    return True

def insert_default_templates(cursor):
    """Insert default system templates."""
    import uuid

    # Check if default templates already exist
    cursor.execute("SELECT COUNT(*) FROM lease_template WHERE is_system_template = 1")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"  ✓ Default templates already exist ({count} templates)")
        return

    # Available merge fields
    merge_fields = json.dumps([
        'tenant_name', 'tenant_email', 'tenant_phone',
        'landlord_name', 'landlord_company',
        'property_address', 'unit_number',
        'rent_amount', 'security_deposit',
        'start_date', 'end_date', 'lease_term_months',
        'payment_due_date', 'late_fee', 'pet_deposit',
        'parking_spaces', 'utilities_included', 'current_date'
    ])

    required_fields = json.dumps([
        'tenant_name', 'property_address', 'unit_number',
        'rent_amount', 'start_date', 'end_date'
    ])

    # Insert default residential template
    cursor.execute("""
        INSERT INTO lease_template (
            uuid, company_id, name, description, template_type,
            contract_text, is_default, is_active, is_system_template,
            available_merge_fields, required_fields
        ) VALUES (?, NULL, ?, ?, ?, ?, 1, 1, 1, ?, ?)
    """, (
        str(uuid.uuid4()),
        'Standard Residential Lease',
        'Default template for residential lease agreements',
        'residential',
        DEFAULT_RESIDENTIAL_TEMPLATE,
        merge_fields,
        required_fields
    ))

    print("  ✓ Inserted default residential lease template")

def migrate_database():
    """Run the comprehensive migration."""
    print("=" * 70)
    print("RE2 Database Migration: Lease Management Enhancements")
    print("=" * 70)
    print()

    try:
        # Connect to database
        print(f"Connecting to database: {DATABASE_PATH}")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        print("  ✓ Connected successfully")
        print()

        # Backup recommendation
        print("⚠️  IMPORTANT: Backup your database before proceeding!")
        response = input("Have you backed up your database? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled. Please backup your database first.")
            return
        print()

        # === PHASE 1: STATUS FIELDS ===
        print("PHASE 1: Adding Lease Status Tracking Fields")
        print("-" * 70)

        print("\n1. Updating Lease table...")
        add_column_if_not_exists(cursor, 'lease', 'status_updated_at', 'DATETIME')

        print("\n2. Updating Unit table...")
        add_column_if_not_exists(cursor, 'unit', 'occupancy_status', 'VARCHAR(20)', "'Available'")
        add_column_if_not_exists(cursor, 'unit', 'status_updated_at', 'DATETIME')

        print("\n3. Updating Property table...")
        add_column_if_not_exists(cursor, 'property', 'occupancy_status', 'VARCHAR(20)', "'Vacant'")
        add_column_if_not_exists(cursor, 'property', 'status_updated_at', 'DATETIME')

        print("\n4. Initializing status values...")
        cursor.execute("""
            UPDATE unit SET occupancy_status = 'Available', status_updated_at = ?
            WHERE occupancy_status IS NULL
        """, (datetime.now(),))
        print(f"  ✓ Initialized {cursor.rowcount} unit records")

        cursor.execute("""
            UPDATE property SET occupancy_status = 'Vacant', status_updated_at = ?
            WHERE occupancy_status IS NULL
        """, (datetime.now(),))
        print(f"  ✓ Initialized {cursor.rowcount} property records")

        cursor.execute("""
            UPDATE lease SET status_updated_at = ?
            WHERE status_updated_at IS NULL
        """, (datetime.now(),))
        print(f"  ✓ Initialized {cursor.rowcount} lease records")

        # === PHASE 2: LEASE TEMPLATES ===
        print("\n" + "=" * 70)
        print("PHASE 2: Adding Lease Template System")
        print("-" * 70)

        print("\n5. Creating lease_template table...")
        create_lease_template_table(cursor)

        print("\n6. Adding template_id to Lease table...")
        add_column_if_not_exists(cursor, 'lease', 'template_id', 'INTEGER')

        print("\n7. Inserting default system templates...")
        insert_default_templates(cursor)

        # Commit changes
        conn.commit()

        print("\n" + "=" * 70)
        print("✅ Migration completed successfully!")
        print("=" * 70)
        print()
        print("Next Steps:")
        print("1. Restart your application")
        print("2. Run: python manage_tasks.py update_leases")
        print("3. Navigate to /lease-templates to manage templates")
        print("4. Test creating a new lease with a template")
        print()

    except sqlite3.Error as e:
        print(f"\n❌ ERROR: Database error occurred: {e}")
        conn.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    migrate_database()
