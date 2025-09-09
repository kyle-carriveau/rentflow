# RE2 - Real Estate Management System

## Project Overview

RE2 is a Flask-based web application for real estate management and property rental operations. It provides a comprehensive platform for landlords to manage their portfolios, properties, units, tenants, and leases.

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (with SQLAlchemy ORM)
- **Authentication**: Flask-Login with password hashing
- **Frontend**: HTML templates with TinyMCE editor integration
- **Architecture**: Modular Blueprint-based structure

## Application Structure

The application follows a modular Flask blueprint architecture with the following main components:

### Core Models (`website/models.py`)
- **User**: System users (landlords) with authentication
- **Portfolio**: Collections of properties owned by users
- **Property**: Individual real estate properties
- **Unit**: Rentable units within properties
- **Tenant**: Renter information and contact details
- **Lease**: Rental agreements linking tenants to units

### Application Modules

1. **Authentication** (`/auth`)
   - User registration, login, logout
   - Password reset functionality
   - User session management

2. **Property Management** (`/property`) 
   - Create, view, edit properties
   - Property listing and details

3. **Unit Management** (`/unit`)
   - Individual unit creation and management
   - Unit details and specifications

4. **Tenant Management** (`/tenant`)
   - Tenant registration and profiles
   - Tenant information management

5. **Lease Management** (`/lease`)
   - Lease creation and management
   - Rental agreement tracking

6. **Portfolio Management** (`/portfolio`)
   - Property portfolio organization
   - High-level portfolio views

7. **User Profile** (`/profile`)
   - User settings and dashboard
   - Personal information management

## Key Features

- Multi-tenant architecture supporting multiple landlords
- Property and unit hierarchy management
- Tenant and lease tracking
- User authentication and authorization
- Responsive web interface
- Database-driven data persistence

## Development Setup

To run the application:

```bash
python main.py
```

The application runs in debug mode and uses SQLite database stored in `website/database.db`.

## Database

- Uses SQLite for development
- Database file: `website/database.db`
- Commented SQL Server configuration available for production
- Auto-creates database schema on first run

## Security Considerations

- Passwords are hashed using Werkzeug security
- Flask-Login handles user session management
- Secret key configured for session security