"""
Migration script to add profile fields to User table.

Adds: bio, job_title, department, date_joined columns to existing database.
"""

import sqlite3
from datetime import datetime

def migrate_user_profile_fields():
    """Add new profile fields to User table."""

    db_path = 'website/database.db'

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("Starting migration: Adding user profile fields...")

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]

        # Add bio column if it doesn't exist
        if 'bio' not in columns:
            print("Adding 'bio' column...")
            cursor.execute("ALTER TABLE user ADD COLUMN bio TEXT")
            print("✓ Added 'bio' column")
        else:
            print("⊘ 'bio' column already exists")

        # Add job_title column if it doesn't exist
        if 'job_title' not in columns:
            print("Adding 'job_title' column...")
            cursor.execute("ALTER TABLE user ADD COLUMN job_title VARCHAR(100)")
            print("✓ Added 'job_title' column")
        else:
            print("⊘ 'job_title' column already exists")

        # Add department column if it doesn't exist
        if 'department' not in columns:
            print("Adding 'department' column...")
            cursor.execute("ALTER TABLE user ADD COLUMN department VARCHAR(100)")
            print("✓ Added 'department' column")
        else:
            print("⊘ 'department' column already exists")

        # Add date_joined column if it doesn't exist
        if 'date_joined' not in columns:
            print("Adding 'date_joined' column...")
            cursor.execute("ALTER TABLE user ADD COLUMN date_joined DATETIME")

            # Set default date_joined to current timestamp for existing users
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE user SET date_joined = ? WHERE date_joined IS NULL", (current_time,))
            print("✓ Added 'date_joined' column and set default values")
        else:
            print("⊘ 'date_joined' column already exists")

        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("Your database has been updated with new profile fields.")

    except sqlite3.Error as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_user_profile_fields()
