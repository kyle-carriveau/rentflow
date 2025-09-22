#!/usr/bin/env python3

from website import create_app, db

def create_database():
    app = create_app()
    
    with app.app_context():
        # Import all models to ensure they're registered with SQLAlchemy
        from website.models import (
            User, Company, Portfolio, Property, Unit, 
            Tenant, Lease, Payment, Expense
        )
        
        # Create all tables
        db.create_all()
        print("Database and all tables created successfully!")
        
        # Print table names to verify
        tables = db.engine.table_names()
        print(f"Created tables: {tables}")

if __name__ == "__main__":
    create_database()