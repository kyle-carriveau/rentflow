# RE2 - Real Estate Management System

## Project Overview

RE2 is a Flask-based web application for real estate management and property rental operations. It provides a comprehensive platform for companies to manage their portfolios, properties, units, tenants, leases, and financial operations with full multi-tenant support.

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (with SQLAlchemy ORM)
- **Authentication**: Flask-Login with password hashing
- **Frontend**: HTML templates with Bootstrap UI framework
- **Architecture**: Modular Blueprint-based structure with role-based access control

## Multi-Tenant Architecture

The application uses a **company-only model** for clean multi-tenant isolation:
- All data is scoped by `company_id` for perfect tenant separation
- Role-based access control (Owner, Manager, Staff, Viewer)
- Company-level user management and permissions
- Automatic company creation for new users

## Core Models (`website/models.py`)

- **Company**: Multi-tenant companies with business information
- **User**: System users with roles and company association
- **Portfolio**: Collections of properties within a company
- **Property**: Individual real estate properties
- **Unit**: Rentable units within properties
- **Tenant**: Renter information and contact details
- **Lease**: Rental agreements linking tenants to units
- **Payment**: Payment tracking and rent collection
- **Expense**: Property and business expense management

## Application Modules

### 1. **Authentication** (`/auth`)
- Multi-tenant user registration with automatic company creation
- Role-based login and session management
- Password reset and security features

### 2. **Company Management** (`/company`)
- Company profile management (Owner role only)
- Business information and settings
- Company-wide configuration

### 3. **User Management** (`/user_management`)
- Team member invitation system
- Role assignment and permissions
- User directory and management

### 4. **Property Management** (`/property`)
- Create, view, edit properties with portfolio assignment
- Property listing and detailed views
- Property-specific financial tracking

### 5. **Unit Management** (`/unit`)
- Individual unit creation and management
- Unit specifications and availability tracking
- Lease status and occupancy management

### 6. **Tenant Management** (`/tenant`)
- Tenant registration and profiles
- Contact information and lease history
- Tenant communication tracking

### 7. **Lease Management** (`/lease`)
- Comprehensive lease creation and management
- Rental agreement tracking with automated calculations
- Lease status and renewal management

### 8. **Portfolio Management** (`/portfolio`)
- Property portfolio organization and metrics
- High-level portfolio performance views
- Investment analysis and reporting

### 9. **Financial Management** (`/financial`)
- Income and expense tracking
- Payment processing and rent collection
- Financial reporting and analytics
- Tax-deductible expense categorization

### 10. **Profile Management** (`/profile`)
- User dashboard and personal settings
- Individual user preferences
- Account management

## Key Features

### Multi-Tenant & Security
- **Company-level data isolation** with `company_id` filtering
- **Role-based access control** with four permission levels
- **Secure authentication** with password hashing
- **Session management** with Flask-Login

### Property & Portfolio Management
- **Hierarchical property organization** (Company → Portfolio → Property → Unit)
- **Portfolio performance metrics** and analytics
- **Property assignment** and reassignment capabilities
- **Unit occupancy tracking** and availability management

### Financial Operations
- **Comprehensive rent collection** with payment tracking
- **Expense management** with categorization and tax features
- **Financial reporting** with income/expense analytics
- **Outstanding balance tracking** and overdue notifications

### User Experience
- **Responsive design** with Bootstrap framework
- **Role-based navigation** and feature access
- **Form autosave functionality** for data preservation
- **Enhanced UI components** with modern styling

## Development Setup

### Prerequisites
- Python 3.12+
- Virtual environment (reenv312/ or similar)

### Running the Application
```bash
# Activate virtual environment
source reenv312/bin/activate  # Linux/Mac
# or
reenv312\Scripts\activate     # Windows

# Start the application
python main.py
```

The application runs in debug mode on `http://127.0.0.1:5000` and automatically creates the database schema on first run.

## Database

- **Development**: SQLite with auto-schema creation
- **Database file**: `website/database.db` (auto-created)
- **Migration strategy**: Clean company-only model (no legacy `owner` fields)
- **Multi-tenant isolation**: All queries filtered by `company_id`

## Security & Permissions

### Role Hierarchy (highest to lowest privilege)
1. **Owner**: Full access, company management, user management
2. **Manager**: Property and tenant management, financial operations
3. **Staff**: Property and tenant management, limited financial access
4. **Viewer**: Read-only access to assigned data

### Security Features
- **Password hashing** using Werkzeug security
- **Session security** with Flask-Login
- **Company-level data isolation** preventing cross-tenant access
- **Role-based decorators** for endpoint protection

## Development Guidelines

### Commit Standards
- Write clear, descriptive commit messages
- Focus on the "why" not just the "what"
- **Important**: Do not include "assisted by Claude" or similar attributions in commit messages
- Use present tense ("Add feature" not "Added feature")

### Code Conventions
- Follow existing patterns and file structure
- Use company_id for all multi-tenant queries
- Implement proper role-based access control
- Maintain consistent error handling and user feedback

### Testing Strategy
- Test multi-tenant isolation thoroughly
- Verify role-based permissions
- Validate financial calculations and reporting
- Test user management and invitation flows

## Architecture Benefits

- **Scalable multi-tenancy** with clean company separation
- **Flexible role system** supporting team collaboration
- **Comprehensive financial tracking** for property management
- **Modern responsive UI** with enhanced user experience
- **Secure by design** with proper access controls