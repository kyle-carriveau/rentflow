#!/usr/bin/env python3
"""
Database Migration Script - Fix Column Names
This script updates the database schema to match the new model structure.
"""

import sqlite3
import os
import shutil
from datetime import datetime

# Paths
DB_PATH = "instance/database.db"
BACKUP_PATH = f"instance/database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def backup_database():
    """Create a backup of the current database."""
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"✅ Database backed up to: {BACKUP_PATH}")
        return True
    else:
        print(f"❌ Database not found at: {DB_PATH}")
        return False

def migrate_database():
    """Migrate the database schema to match new models."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("🔄 Starting database migration...")

        # Check current schema
        cursor.execute("PRAGMA table_info(property)")
        property_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Current property columns: {property_columns}")

        # 1. Rename portfolio to portfolio_id in property table
        if 'portfolio' in property_columns and 'portfolio_id' not in property_columns:
            print("🔧 Renaming property.portfolio to property.portfolio_id...")
            cursor.execute("ALTER TABLE property RENAME COLUMN portfolio TO portfolio_id")

        # Check unit table
        cursor.execute("PRAGMA table_info(unit)")
        unit_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Current unit columns: {unit_columns}")

        # 2. Rename property to property_id in unit table
        if 'property' in unit_columns and 'property_id' not in unit_columns:
            print("🔧 Renaming unit.property to unit.property_id...")
            cursor.execute("ALTER TABLE unit RENAME COLUMN property TO property_id")

        # Check tenant table
        cursor.execute("PRAGMA table_info(tenant)")
        tenant_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Current tenant columns: {tenant_columns}")

        # 3. Rename property to property_id in tenant table
        if 'property' in tenant_columns and 'property_id' not in tenant_columns:
            print("🔧 Renaming tenant.property to tenant.property_id...")
            cursor.execute("ALTER TABLE tenant RENAME COLUMN property TO property_id")

        # 4. Drop landlord column from tenant table if it exists
        if 'landlord' in tenant_columns:
            print("🔧 Removing tenant.landlord column...")
            # SQLite doesn't support DROP COLUMN directly, need to recreate table
            recreate_tenant_table(cursor)

        # 5. Update data types for phone and zip_code (SQLite is flexible with types)
        print("ℹ️  Note: Phone and zip_code data types will be handled by SQLAlchemy")

        # 6. Make company_id non-nullable where needed
        print("ℹ️  Note: company_id nullable constraints will be enforced by SQLAlchemy")

        conn.commit()
        print("✅ Database migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def recreate_tenant_table(cursor):
    """Recreate tenant table without landlord column."""
    print("🔄 Recreating tenant table without landlord column...")

    # Create new table structure
    cursor.execute("""
        CREATE TABLE tenant_new (
            id INTEGER PRIMARY KEY,
            company_id INTEGER NOT NULL,
            first_name VARCHAR(150) NOT NULL,
            last_name VARCHAR(150) NOT NULL,
            email VARCHAR(150),
            phone VARCHAR(20),
            address VARCHAR(150),
            city VARCHAR(150),
            state VARCHAR(150),
            zip_code VARCHAR(10),
            property_id INTEGER,
            FOREIGN KEY (company_id) REFERENCES company(id),
            FOREIGN KEY (property_id) REFERENCES property(id)
        )
    """)

    # Copy data (excluding landlord column)
    cursor.execute("""
        INSERT INTO tenant_new (
            id, company_id, first_name, last_name, email, phone,
            address, city, state, zip_code, property_id
        )
        SELECT
            id,
            COALESCE(company_id, 1) as company_id,  -- Default to company 1 if null
            first_name,
            last_name,
            email,
            phone,
            address,
            city,
            state,
            zip_code,
            CASE WHEN property_id IS NOT NULL THEN property_id ELSE NULL END as property_id
        FROM tenant
    """)

    # Drop old table and rename new one
    cursor.execute("DROP TABLE tenant")
    cursor.execute("ALTER TABLE tenant_new RENAME TO tenant")

    print("✅ Tenant table recreated successfully")

def main():
    """Main migration function."""
    print("🚀 RE2 Database Migration Tool")
    print("=" * 40)

    # Create backup
    if not backup_database():
        return

    # Run migration
    try:
        migrate_database()
        print("\n✅ Migration completed successfully!")
        print(f"📁 Backup saved at: {BACKUP_PATH}")
        print("\n🎯 You can now restart your Flask application.")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print(f"📁 Your original database is backed up at: {BACKUP_PATH}")
        print("💡 You can restore it by copying the backup over the current database.")

if __name__ == "__main__":
    main()