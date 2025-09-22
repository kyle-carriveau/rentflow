#!/usr/bin/env python3
"""
Migration script to add enhanced company fields and CompanySettings table.
This script adds all the new columns to the Company model and creates
the CompanySettings table for key-value configuration storage.
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add new company enhancement columns and CompanySettings table"""

    # Database path
    db_path = 'instance/database.db'

    if not os.path.exists(db_path):
        print("Database not found. No migration needed.")
        return

    print(f"Starting company enhancement migration at {datetime.now()}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Add new columns to Company table
        new_company_columns = [
            ("description", "TEXT"),
            ("industry", "VARCHAR(100)"),
            ("company_size", "VARCHAR(50)"),
            ("tax_id", "VARCHAR(50)"),
            ("license_number", "VARCHAR(100)"),
            ("established_date", "DATE"),
            ("timezone", "VARCHAR(50) DEFAULT 'America/New_York'"),
            ("currency", "VARCHAR(10) DEFAULT 'USD'"),
            ("logo_url", "VARCHAR(200)")
        ]

        print("Adding new columns to Company table...")
        for column_name, column_type in new_company_columns:
            try:
                cursor.execute(f"ALTER TABLE company ADD COLUMN {column_name} {column_type}")
                print(f"  ✓ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"  - Column {column_name} already exists, skipping")
                else:
                    print(f"  ✗ Error adding column {column_name}: {e}")

        # Create CompanySettings table
        print("Creating CompanySettings table...")
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS company_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    setting_key VARCHAR(100) NOT NULL,
                    setting_value TEXT,
                    setting_type VARCHAR(50) DEFAULT 'string',
                    category VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES company (id),
                    UNIQUE(company_id, setting_key)
                )
            ''')
            print("  ✓ CompanySettings table created successfully")
        except sqlite3.Error as e:
            print(f"  ✗ Error creating CompanySettings table: {e}")

        # Set default values for existing companies
        print("Setting default values for existing companies...")
        try:
            cursor.execute('''
                UPDATE company
                SET timezone = 'America/New_York',
                    currency = 'USD'
                WHERE timezone IS NULL OR currency IS NULL
            ''')
            updated_rows = cursor.rowcount
            print(f"  ✓ Updated {updated_rows} existing companies with default values")
        except sqlite3.Error as e:
            print(f"  ✗ Error updating existing companies: {e}")

        # Insert default company settings for existing companies
        print("Creating default settings for existing companies...")
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO company_settings (company_id, setting_key, setting_value, setting_type, category)
                SELECT
                    id as company_id,
                    'default_lease_term' as setting_key,
                    '12' as setting_value,
                    'integer' as setting_type,
                    'business' as category
                FROM company
            ''')

            cursor.execute('''
                INSERT OR IGNORE INTO company_settings (company_id, setting_key, setting_value, setting_type, category)
                SELECT
                    id as company_id,
                    'late_fee_amount' as setting_key,
                    '50' as setting_value,
                    'integer' as setting_type,
                    'financial' as category
                FROM company
            ''')

            cursor.execute('''
                INSERT OR IGNORE INTO company_settings (company_id, setting_key, setting_value, setting_type, category)
                SELECT
                    id as company_id,
                    'grace_period_days' as setting_key,
                    '5' as setting_value,
                    'integer' as setting_type,
                    'business' as category
                FROM company
            ''')

            settings_rows = cursor.rowcount
            print(f"  ✓ Created default settings for companies")
        except sqlite3.Error as e:
            print(f"  ✗ Error creating default settings: {e}")

        # Commit all changes
        conn.commit()
        print("✓ All changes committed successfully")

        # Verify the migration
        print("\nVerifying migration...")
        cursor.execute("PRAGMA table_info(company)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        required_columns = ['description', 'industry', 'company_size', 'tax_id', 'license_number',
                          'established_date', 'timezone', 'currency', 'logo_url']

        missing_columns = [col for col in required_columns if col not in column_names]
        if missing_columns:
            print(f"  ⚠ Missing columns: {missing_columns}")
        else:
            print("  ✓ All required company columns are present")

        # Check if CompanySettings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_settings'")
        table_exists = cursor.fetchone()

        if table_exists:
            print("  ✓ CompanySettings table created successfully")

            # Check settings count
            cursor.execute("SELECT COUNT(*) FROM company_settings")
            settings_count = cursor.fetchone()[0]
            print(f"  ✓ {settings_count} default settings created")
        else:
            print("  ⚠ CompanySettings table was not created")

        conn.close()
        print(f"\n🎉 Company enhancement migration completed successfully at {datetime.now()}")
        print("\nNew features available:")
        print("  • Enhanced company profile fields (industry, size, tax ID, etc.)")
        print("  • Company settings storage system")
        print("  • Business rule configuration")
        print("  • Financial settings management")
        print("  • Timezone and currency support")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    migrate_database()