#!/usr/bin/env python3
"""
UUID Migration Script for RE2 Real Estate Management System

This script adds UUID columns to the main entity tables and populates them
for existing records. This enhances security by replacing sequential IDs
with unguessable UUIDs in public-facing URLs.

IMPORTANT: Run this script BEFORE updating views and templates to use UUIDs.

Usage:
    python uuid_migration.py

The script will:
1. Add UUID columns to Portfolio, Property, Unit, Tenant, and Lease tables
2. Generate UUIDs for all existing records
3. Create indexes on the new UUID columns
4. Provide rollback instructions if needed
"""

import sqlite3
import uuid
import os
import sys
from datetime import datetime

# Database path
DB_PATH = 'instance/database.db'

def backup_database():
    """Create a backup of the database before migration."""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{DB_PATH}.backup_{timestamp}"

    try:
        # Copy database file
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to backup database: {e}")
        return False

def check_existing_columns(cursor):
    """Check if UUID columns already exist."""
    tables = ['user', 'portfolio', 'property', 'unit', 'tenant', 'lease']
    existing_uuids = []

    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if 'uuid' in columns:
            existing_uuids.append(table)

    return existing_uuids

def add_uuid_columns(cursor):
    """Add UUID columns to all target tables."""
    tables = ['user', 'portfolio', 'property', 'unit', 'tenant', 'lease']

    print("\n🔧 Adding UUID columns...")

    for table in tables:
        try:
            cursor.execute(f"""
                ALTER TABLE {table}
                ADD COLUMN uuid VARCHAR(36)
            """)
            print(f"   ✅ Added uuid column to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"   ⚠️  UUID column already exists in {table}")
            else:
                raise e

def populate_uuids(cursor):
    """Generate and populate UUIDs for existing records."""
    tables = ['user', 'portfolio', 'property', 'unit', 'tenant', 'lease']

    print("\n🎲 Generating UUIDs for existing records...")

    total_updated = 0

    for table in tables:
        # Get all records without UUIDs
        cursor.execute(f"SELECT id FROM {table} WHERE uuid IS NULL OR uuid = ''")
        records = cursor.fetchall()

        if not records:
            print(f"   ✅ All records in {table} already have UUIDs")
            continue

        updated = 0
        for record in records:
            record_id = record[0]
            new_uuid = str(uuid.uuid4())

            cursor.execute(f"""
                UPDATE {table}
                SET uuid = ?
                WHERE id = ?
            """, (new_uuid, record_id))
            updated += 1

        print(f"   ✅ Updated {updated} records in {table}")
        total_updated += updated

    print(f"\n📊 Total records updated: {total_updated}")

def create_uuid_indexes(cursor):
    """Create indexes on UUID columns for performance."""
    tables = ['user', 'portfolio', 'property', 'unit', 'tenant', 'lease']

    print("\n🔍 Creating indexes on UUID columns...")

    for table in tables:
        index_name = f"idx_{table}_uuid"
        try:
            cursor.execute(f"""
                CREATE UNIQUE INDEX {index_name}
                ON {table} (uuid)
            """)
            print(f"   ✅ Created index {index_name}")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e).lower():
                print(f"   ⚠️  Index {index_name} already exists")
            else:
                raise e

def verify_migration(cursor):
    """Verify the migration was successful."""
    tables = ['user', 'portfolio', 'property', 'unit', 'tenant', 'lease']

    print("\n🔍 Verifying migration...")

    all_good = True
    for table in tables:
        # Check if UUID column exists
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]

        if 'uuid' not in columns:
            print(f"   ❌ UUID column missing from {table}")
            all_good = False
            continue

        # Check for null UUIDs
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE uuid IS NULL OR uuid = ''")
        null_count = cursor.fetchone()[0]

        if null_count > 0:
            print(f"   ❌ {table} has {null_count} records without UUIDs")
            all_good = False
            continue

        # Check total record count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        total_count = cursor.fetchone()[0]

        print(f"   ✅ {table}: {total_count} records with UUIDs")

    return all_good

def main():
    """Main migration function."""
    print("🚀 Starting UUID Migration for RE2 Real Estate Management System")
    print("=" * 70)

    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        print("   Make sure you're running this script from the project root directory.")
        sys.exit(1)

    # Create backup
    backup_path = backup_database()
    if not backup_path:
        print("❌ Cannot proceed without database backup")
        sys.exit(1)

    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check existing columns
        existing = check_existing_columns(cursor)
        if existing:
            print(f"⚠️  UUID columns already exist in: {', '.join(existing)}")
            response = input("Continue with migration? (y/N): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                sys.exit(0)

        # Perform migration steps
        add_uuid_columns(cursor)
        populate_uuids(cursor)
        create_uuid_indexes(cursor)

        # Commit changes
        conn.commit()

        # Verify migration
        if verify_migration(cursor):
            print("\n🎉 Migration completed successfully!")
            print(f"📁 Database backup available at: {backup_path}")
            print("\n📋 Next steps:")
            print("   1. Update view routes to use UUID parameters")
            print("   2. Update templates to use UUIDs in URLs")
            print("   3. Test the application thoroughly")
            print("   4. Remove backup file once confident: rm", backup_path)
        else:
            print("\n❌ Migration verification failed!")
            print("   Check the errors above and fix them before proceeding.")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print(f"📁 Database backup available at: {backup_path}")
        print("   You can restore the backup if needed.")
        sys.exit(1)

    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()