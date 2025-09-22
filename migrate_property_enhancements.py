#!/usr/bin/env python3
"""
Migration script to add enhanced property fields to existing database.
This script adds all the new columns to the Property model and creates
the PropertyPhoto and PropertyDocument tables.
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add new property enhancement columns and tables"""

    # Database path
    db_path = 'instance/database.db'

    if not os.path.exists(db_path):
        print("Database not found. No migration needed.")
        return

    print(f"Starting property enhancement migration at {datetime.now()}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Add new columns to Property table
        new_columns = [
            # Location enhancements
            ("neighborhood", "TEXT"),
            ("latitude", "REAL"),
            ("longitude", "REAL"),

            # Property details
            ("year_built", "INTEGER"),
            ("lot_size", "INTEGER"),
            ("building_sqft", "INTEGER"),
            ("stories", "INTEGER"),
            ("parking_spaces", "INTEGER"),
            ("description", "TEXT"),

            # Financial information
            ("purchase_price", "DECIMAL(12,2)"),
            ("purchase_date", "DATE"),
            ("current_market_value", "DECIMAL(12,2)"),
            ("annual_property_tax", "DECIMAL(10,2)"),
            ("annual_insurance", "DECIMAL(10,2)"),
            ("monthly_hoa_fees", "DECIMAL(8,2)"),

            # Management & operations
            ("property_manager", "TEXT"),
            ("acquisition_method", "TEXT"),
            ("property_status", "TEXT DEFAULT 'Active'"),
            ("maintenance_priority", "TEXT DEFAULT 'Medium'"),

            # Metadata
            ("created_date", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("updated_date", "DATETIME DEFAULT CURRENT_TIMESTAMP")
        ]

        print("Adding new columns to Property table...")
        for column_name, column_type in new_columns:
            try:
                cursor.execute(f"ALTER TABLE property ADD COLUMN {column_name} {column_type}")
                print(f"  ✓ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"  - Column {column_name} already exists, skipping")
                else:
                    print(f"  ✗ Error adding column {column_name}: {e}")

        # Create PropertyPhoto table
        print("Creating PropertyPhoto table...")
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS property_photo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT,
                    is_primary BOOLEAN DEFAULT 0,
                    caption TEXT,
                    uploaded_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (property_id) REFERENCES property (id)
                )
            ''')
            print("  ✓ PropertyPhoto table created successfully")
        except sqlite3.Error as e:
            print(f"  ✗ Error creating PropertyPhoto table: {e}")

        # Create PropertyDocument table
        print("Creating PropertyDocument table...")
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS property_document (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT,
                    document_type TEXT,
                    description TEXT,
                    uploaded_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (property_id) REFERENCES property (id)
                )
            ''')
            print("  ✓ PropertyDocument table created successfully")
        except sqlite3.Error as e:
            print(f"  ✗ Error creating PropertyDocument table: {e}")

        # Update existing properties with default values
        print("Setting default values for existing properties...")
        try:
            cursor.execute('''
                UPDATE property
                SET property_status = 'Active',
                    maintenance_priority = 'Medium',
                    created_date = CURRENT_TIMESTAMP,
                    updated_date = CURRENT_TIMESTAMP
                WHERE property_status IS NULL
            ''')
            updated_rows = cursor.rowcount
            print(f"  ✓ Updated {updated_rows} existing properties with default values")
        except sqlite3.Error as e:
            print(f"  ✗ Error updating existing properties: {e}")

        # Commit all changes
        conn.commit()
        print("✓ All changes committed successfully")

        # Verify the migration
        print("\nVerifying migration...")
        cursor.execute("PRAGMA table_info(property)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        required_columns = ['neighborhood', 'latitude', 'longitude', 'year_built', 'lot_size',
                          'building_sqft', 'description', 'purchase_price', 'property_status']

        missing_columns = [col for col in required_columns if col not in column_names]
        if missing_columns:
            print(f"  ⚠ Missing columns: {missing_columns}")
        else:
            print("  ✓ All required columns are present")

        # Check if new tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('property_photo', 'property_document')")
        tables = [row[0] for row in cursor.fetchall()]

        if 'property_photo' in tables and 'property_document' in tables:
            print("  ✓ All new tables created successfully")
        else:
            print(f"  ⚠ Missing tables: {set(['property_photo', 'property_document']) - set(tables)}")

        conn.close()
        print(f"\n🎉 Property enhancement migration completed successfully at {datetime.now()}")
        print("\nNew features available:")
        print("  • Enhanced property details (year built, square footage, etc.)")
        print("  • GPS coordinates for mapping")
        print("  • Financial tracking (purchase price, taxes, insurance)")
        print("  • Property management fields")
        print("  • Photo and document storage (tables created)")
        print("  • Property status and maintenance priority")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    migrate_database()