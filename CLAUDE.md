# RE2 - Real Estate Management System (RentFlow)

## Project Overview

RE2 (RentFlow) is a production-ready Flask-based web application for real estate management and property rental operations. It provides a comprehensive platform for companies to manage their portfolios, properties, units, tenants, leases, and financial operations with full multi-tenant support.

## Technology Stack

### Development Environment
- **Backend**: Flask (Python 3.12+)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login with Werkzeug password hashing
- **Frontend**: HTML/Jinja2 templates with Bootstrap UI framework
- **Architecture**: Modular Blueprint-based structure with role-based access control
- **Development Server**: Flask development server (port 5000)

### Production Environment
- **Backend**: Flask (Python 3.12+) with Gunicorn WSGI server
- **Database**: PostgreSQL 16 (production) / SQLite (development)
- **Caching & Rate Limiting**: Redis 7
- **Web Server**: NGINX (reverse proxy, SSL termination, static file serving)
- **Containerization**: Docker & Docker Compose
- **Database Migrations**: Flask-Migrate with Alembic
- **SSL/TLS**: Cloudflare Origin Certificates with Authenticated Origin Pulls
- **CI/CD**: GitHub Actions with automated deployment

## Multi-Tenant Architecture

The application uses a **company-only model** for clean multi-tenant isolation:
- All data is scoped by `company_id` for perfect tenant separation
- Role-based access control (Owner, Manager, Staff, Viewer)
- Company-level user management and permissions
- Automatic company creation for new users

## Project Structure

```
re2/
├── main.py                           # Application entry point
├── .env.example                      # Environment template
├── .env                              # Environment config (not in git)
├── deploy.sh                         # Automated deployment script
├── pytest.ini                        # Pytest configuration
├── CLAUDE.md                         # Project documentation (this file)
├── README.md                         # User-facing documentation
├── DEPLOYMENT.md                     # Production deployment guide
├── DEPLOYMENT_CHECKLIST.md          # Pre-deployment checklist
│
├── config/                          # Configuration module
│   ├── __init__.py                  # Environment-based configs
│   └── README.md                    # Config documentation
│
├── deployment/                      # Production deployment files
│   ├── docker/
│   │   ├── docker-compose.yml       # Multi-service orchestration
│   │   ├── Dockerfile               # Flask container definition
│   │   └── README.md                # Docker documentation
│   ├── nginx/
│   │   ├── nginx.conf               # NGINX main config
│   │   └── conf.d/
│   │       ├── rentflow.conf        # Site configuration
│   │       └── locations.inc        # Location blocks
│   ├── scripts/
│   │   ├── validate.sh              # Deployment validation
│   │   └── rollback.sh              # Deployment rollback
│   └── ssl/                         # SSL certificates (not in git)
│       ├── cloudflare-origin.crt
│       ├── cloudflare-origin.key
│       └── cloudflare-origin-pull-ca.pem
│
├── requirements/                    # Modular dependencies
│   ├── base.txt                     # Core requirements
│   ├── dev.txt                      # Development & testing
│   └── prod.txt                     # Production only
│
├── docs/                            # Project documentation
│   └── TENANT_PORTAL_ARCHITECTURE.md # Tenant portal design docs
│
├── website/                         # Main application package
│   ├── __init__.py                  # App factory (create_app)
│   ├── models.py                    # SQLAlchemy models
│   ├── errors.py                    # Error handlers
│   ├── health.py                    # Health check endpoint
│   ├── auth_utils.py                # Authentication utilities
│   ├── session_security.py          # Session security middleware
│   ├── password_policy.py           # Password policy enforcement
│   ├── security_monitoring.py       # Security monitoring
│   ├── audit_logging.py             # Audit logging
│   ├── two_factor_auth.py           # 2FA implementation
│   │
│   ├── main/                        # Main/homepage blueprint
│   │   ├── __init__.py
│   │   └── views.py
│   ├── auth/                        # Authentication blueprint (staff)
│   │   ├── __init__.py
│   │   ├── views.py
│   │   └── forms.py
│   ├── tenant_portal/               # Tenant Portal (separate auth system)
│   │   ├── __init__.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── decorators.py            # @tenant_required decorator
│   │   └── templates/tenant_portal/ # Tenant-specific templates
│   ├── admin/                       # Super Admin (God View)
│   │   ├── __init__.py
│   │   ├── views.py
│   │   └── cli.py                   # Admin CLI commands
│   ├── company/                     # Company management
│   │   ├── __init__.py
│   │   └── views.py
│   ├── user_management/             # User & team management
│   │   ├── __init__.py
│   │   └── views.py
│   ├── property/                    # Property management
│   │   ├── __init__.py
│   │   ├── views.py
│   │   └── forms.py
│   ├── unit/                        # Unit management
│   │   ├── __init__.py
│   │   ├── views.py
│   │   └── forms.py
│   ├── tenant/                      # Tenant management (staff-side)
│   │   ├── __init__.py
│   │   └── views.py
│   ├── lease/                       # Lease management
│   │   ├── __init__.py
│   │   └── views.py
│   ├── lease_template/              # Lease templates
│   │   ├── __init__.py
│   │   └── views.py
│   ├── portfolio/                   # Portfolio management
│   │   ├── __init__.py
│   │   └── views.py
│   ├── financial/                   # Financial operations
│   │   ├── __init__.py
│   │   └── views.py
│   ├── report/                      # Reporting
│   │   ├── __init__.py
│   │   └── views.py
│   ├── search/                      # Search functionality
│   │   ├── __init__.py
│   │   └── views.py
│   ├── profile/                     # User profiles
│   │   ├── __init__.py
│   │   └── views.py
│   ├── tasks/                       # Background tasks
│   │   ├── __init__.py
│   │   └── lease_tasks.py
│   ├── templates/                   # Jinja2 templates
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── property/
│   │   ├── tenant/
│   │   └── ...
│   └── static/                      # Static assets
│       ├── css/
│       ├── js/
│       └── images/
│
├── tests/                           # Test suite
│   ├── conftest.py                  # Shared fixtures
│   ├── test_basic.py                # Basic smoke tests
│   ├── README.md                    # Testing documentation
│   ├── fixtures/                    # Test data fixtures
│   ├── unit/                        # Unit tests
│   │   ├── test_models.py
│   │   └── ...
│   ├── integration/                 # Integration tests
│   │   ├── test_workflows.py
│   │   └── ...
│   └── views/                       # View tests
│       ├── test_auth_views.py
│       └── ...
│
├── migrations/                      # Database migrations
│   ├── versions/                    # Migration files
│   ├── alembic.ini
│   └── env.py
│
├── instance/                        # Instance-specific data
│   └── database.db                  # SQLite DB (development)
│
├── logs/                            # Application logs
│   ├── access.log
│   ├── error.log
│   └── nginx/
│
├── uploads/                         # User uploads
│
├── backups/                         # Database backups
│
├── .github/                         # GitHub configuration
│   └── workflows/
│       └── deploy.yml               # CI/CD workflow
│
└── reenv312/                        # Virtual environment (not in git)
```

## Core Models (`website/models.py`)

### Primary Business Models
- **Company**: Multi-tenant companies with business information
- **User**: System users (staff) with roles and company association
- **Portfolio**: Collections of properties within a company
- **Property**: Individual real estate properties with automated occupancy tracking
- **Unit**: Rentable units within properties with status management
- **Tenant**: Renter information and contact details
- **Lease**: Rental agreements linking tenants to units with automated lifecycle
- **LeaseTemplate**: Reusable contract templates with variable substitution
- **Payment**: Payment tracking and rent collection (supports Stripe integration)
- **Expense**: Property and business expense management

### Tenant Portal Models
- **TenantUser**: Separate authentication model for tenant portal (completely isolated from User)
- **MaintenanceRequest**: Tenant-submitted maintenance requests with status tracking

### Subscription & Billing Models
- **SubscriptionPlan**: Tiered pricing plans (Starter, Professional, Enterprise)
- **CompanySubscription**: Company subscription status and usage tracking
- **PaymentHistory**: Stripe payment transaction history

### Security & Audit Models
- **PasswordHistoryModel**: Password history for security policy enforcement
- **AuditLogModel**: Comprehensive audit logging for compliance
- **EmailVerificationAttempt**: Email verification tracking for security
- **SuperAdmin**: Platform administrators (separate from company users)
- **SuperAdminAuditLog**: Audit trail for super admin actions
- **AnonymousUser**: Custom anonymous user for Flask-Login integration

## Application Modules

All modules are implemented as Flask Blueprints in `website/` with the following structure:
```
website/[module]/
├── __init__.py       # Blueprint registration
├── views.py          # Route handlers and business logic
└── forms.py          # WTForms form definitions (where applicable)
```

### 1. **Main** (`/` - `website/main/`)
- Landing page and dashboard
- Main navigation and homepage
- Core application entry points

### 2. **Authentication** (`/` - `website/auth/`)
- Multi-tenant user registration with automatic company creation
- Role-based login and session management
- Password reset and security features
- Two-factor authentication support
- Session security and CSRF protection

### 3. **Company Management** (`/company` - `website/company/`)
- Company profile management (Owner role only)
- Business information and settings
- Company-wide configuration

### 4. **User Management** (`/users` - `website/user_management/`)
- Team member invitation system
- Role assignment and permissions
- User directory and management
- User access control

### 5. **Property Management** (`/property` - `website/property/`)
- Create, view, edit properties with portfolio assignment
- Property listing and detailed views
- Property-specific financial tracking
- Automated occupancy status calculation

### 6. **Unit Management** (`/unit` - `website/unit/`)
- Individual unit creation and management
- Unit specifications and availability tracking
- Lease status and occupancy management
- Unit status automation (Available, Reserved, Occupied, Maintenance)

### 7. **Tenant Management** (`/tenant` - `website/tenant/`)
- Tenant registration and profiles
- Contact information and lease history
- Tenant communication tracking

### 8. **Lease Management** (`/lease` - `website/lease/`)
- Comprehensive lease creation and management
- Rental agreement tracking with automated calculations
- Lease status automation (Pending, Active, Expiring, Expired, Terminated)
- Renewal management and expiration alerts

### 9. **Lease Templates** (`/lease-templates` - `website/lease_template/`)
- Reusable contract template management
- Variable substitution system for dynamic content
- Template versioning and editing

### 10. **Portfolio Management** (`/portfolio` - `website/portfolio/`)
- Property portfolio organization and metrics
- High-level portfolio performance views
- Investment analysis and reporting
- Portfolio-level financial analytics

### 11. **Financial Management** (`/financial` - `website/financial/`)
- Income and expense tracking
- Payment processing and rent collection
- Financial reporting and analytics
- Tax-deductible expense categorization
- Outstanding balance tracking

### 12. **Reporting** (`/reports` - `website/report/`)
- Financial reports and analytics
- Property performance reports
- Occupancy and vacancy reports
- Custom report generation

### 13. **Search** (`/search` - `website/search/`)
- Global search functionality
- Search across properties, units, tenants
- Advanced filtering capabilities

### 14. **Profile Management** (`/profile` - `website/profile/`)
- User dashboard and personal settings
- Individual user preferences
- Account management and profile updates

### 15. **Health Monitoring** (`/health` - `website/health.py`)
- Application health check endpoint
- Database connectivity verification
- Used by Docker healthchecks and load balancers

### 16. **Tenant Portal** (`/portal` - `website/tenant_portal/`)
- **Separate authentication system** for tenants (TenantUser model)
- Invitation-based registration with secure tokens
- Tenant dashboard with lease and payment overview
- Online rent payment (Stripe integration - planned)
- Maintenance request submission and tracking
- Payment history and lease document viewing
- **Security**: Completely isolated from staff User model

### 17. **Super Admin** (`/admin` - `website/admin/`)
- Platform-wide administration ("God View")
- View all companies and their data (read-only)
- **Separate authentication** from company users
- Comprehensive audit logging
- No company_id association (platform-level access)

## Key Features

### Multi-Tenant & Security
- **Company-level data isolation** with `company_id` filtering
- **Role-based access control** with four permission levels (Owner, Manager, Staff, Viewer)
- **Secure authentication** with password hashing (Werkzeug pbkdf2:sha256)
- **Session management** with Flask-Login and session rotation
- **Timing attack prevention** on login and password reset
- **Account lockout** after failed login attempts

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
- **Stripe integration** for online payments (tenant portal)

### Tenant Portal (Self-Service)
- **Separate TenantUser authentication** (isolated from staff)
- **Invitation-based registration** with secure token flow
- **Dashboard** with lease info, payment status, and quick actions
- **Online rent payments** via Stripe (PCI compliant - no card data stored)
- **Maintenance requests** submission and tracking
- **Payment history** and lease document access

### User Experience
- **Responsive design** with Bootstrap 5 framework
- **Role-based navigation** and feature access
- **Form autosave functionality** for data preservation
- **Enhanced UI components** with modern styling
- **Separate tenant portal UI** with tenant-focused design

## Development Setup

### Prerequisites
- Python 3.12+
- Git
- Virtual environment tool (venv)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd re2
   ```

2. **Create and activate virtual environment**
   ```bash
   # Create virtual environment
   python3 -m venv reenv312

   # Activate virtual environment
   source reenv312/bin/activate  # Linux/Mac
   # or
   reenv312\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   # Install development dependencies (includes testing tools)
   pip install -r requirements/dev.txt

   # Or install only base dependencies
   pip install -r requirements/base.txt
   ```

4. **Configure environment (optional for development)**
   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit .env with development values (optional - has sensible defaults)
   nano .env
   ```

5. **Run database migrations**
   ```bash
   # Initialize database and run migrations
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

The application runs in debug mode on `http://127.0.0.1:5000` with:
- Auto-reload on code changes
- SQLite database at `instance/database.db` (auto-created)
- Debug mode enabled
- Detailed error pages

## Database

### Development
- **Database**: SQLite
- **Location**: `instance/database.db` (auto-created)
- **Migrations**: Flask-Migrate with Alembic
- **Configuration**: Default via `SQLALCHEMY_DATABASE_URI` in `create_app()`

### Production
- **Database**: PostgreSQL 16
- **Connection**: Via `DATABASE_URL` environment variable
- **Container**: Docker PostgreSQL image (`postgres:16-alpine`)
- **Data Persistence**: Docker volume (`postgres_data`)
- **Backups**: Automated via `deploy.sh` before each deployment

### Database Migrations
The application uses Flask-Migrate (Alembic) for schema management:

```bash
# Create a new migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Revert last migration
flask db downgrade

# View migration history
flask db history

# View current migration
flask db current
```

### Migration Files Location
- **Location**: `migrations/versions/`
- **Auto-generated**: Yes (from model changes)
- **Version Control**: Committed to git

### Multi-Tenant Data Isolation
- **Strategy**: Company-only model with `company_id` foreign keys
- **Enforcement**: All queries filtered by `company_id`
- **Security**: No cross-tenant data access possible
- **Database Level**: Enforced at application layer (SQLAlchemy queries)

## Security & Permissions

### Authentication Systems
The application has **three separate authentication systems** for security isolation:

1. **Staff Authentication** (`website/auth/`)
   - For property managers, owners, and staff
   - Uses `User` model with role-based permissions
   - Company-scoped access

2. **Tenant Portal Authentication** (`website/tenant_portal/`)
   - For tenants accessing their rental information
   - Uses `TenantUser` model (completely separate from User)
   - Tenant-scoped access (can only see own data)
   - **Cannot access any staff features**

3. **Super Admin Authentication** (`website/admin/`)
   - For platform administrators
   - Uses `SuperAdmin` model
   - Platform-wide read-only access
   - **No company association**

### Role Hierarchy (Staff Users - highest to lowest)
1. **Owner**: Full access, company management, user management
2. **Manager**: Property and tenant management, financial operations
3. **Staff**: Property and tenant management, limited financial access
4. **Viewer**: Read-only access to assigned data

### Security Features
- **Password hashing** using Werkzeug security (pbkdf2:sha256)
- **Session security** with Flask-Login and custom middleware (`website/session_security.py`)
- **Session rotation** on login to prevent session fixation
- **CSRF protection** on all forms via Flask-WTF
- **Company-level data isolation** preventing cross-tenant access
- **Tenant-level data isolation** in tenant portal (tenant_id + company_id)
- **Role-based decorators** for endpoint protection (`@manager_required`, `@role_required`, `@tenant_required`)
- **Rate limiting** via Flask-Limiter with Redis backend (production)
- **Account lockout** after 5 failed login attempts (15-minute lockout)
- **Timing attack prevention** on login and password reset (constant-time responses)
- **Audit logging** for compliance and security monitoring (`website/audit_logging.py`)
- **Security monitoring** with anomaly detection (`website/security_monitoring.py`)
- **Password policies** enforcing strong passwords (`website/password_policy.py`)
- **Two-factor authentication** support (`website/two_factor_auth.py`)
- **SSL/TLS** in production with Cloudflare Origin Certificates
- **Authenticated Origin Pulls** blocking direct IP access to origin server
- **PCI compliance** for payments via Stripe (no card data on our servers)

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
- Use Flask Blueprints for modular organization
- Keep business logic in views, data models in `models.py`
- Use WTForms for form validation and CSRF protection
- Follow Python PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings for complex functions and classes

### Dependency Management
The project uses a modular requirements structure:

- **`requirements/base.txt`**: Core dependencies required for all environments
  - Flask framework and extensions
  - Database and ORM (SQLAlchemy)
  - Security and authentication
  - Forms and validation

- **`requirements/dev.txt`**: Development and testing tools
  - pytest and testing frameworks
  - pytest-flask for Flask testing
  - pytest-cov for coverage reporting
  - factory-boy for test data generation
  - Flask-Testing utilities

- **`requirements/prod.txt`**: Production-only dependencies
  - Gunicorn WSGI server
  - psycopg2-binary for PostgreSQL
  - Includes base.txt dependencies

**Installing dependencies:**
```bash
# Development (recommended)
pip install -r requirements/dev.txt

# Production
pip install -r requirements/prod.txt
```

### Testing Strategy & Requirements

#### Testing Philosophy
- **Test-Driven Development**: Write unit tests for all new code before implementation
- **Multi-Tenant Testing**: Ensure complete data isolation between companies
- **Security-First**: Validate role-based permissions and access controls
- **Financial Accuracy**: Rigorous testing for all monetary calculations
- **Coverage Target**: Maintain minimum 80% test coverage

#### Test Organization Structure
```
tests/
├── conftest.py                 # Shared fixtures and setup
├── unit/                      # Unit tests (models, utilities)
│   ├── test_models.py
│   ├── test_auth.py
│   └── test_utils.py
├── integration/               # Integration tests (workflows)
│   ├── test_tenant_workflows.py
│   ├── test_financial_workflows.py
│   └── test_property_workflows.py
├── views/                     # View/endpoint tests
│   ├── test_auth_views.py
│   ├── test_property_views.py
│   ├── test_financial_views.py
│   └── test_report_views.py
└── fixtures/                  # Test data factories
    ├── user_fixtures.py
    └── property_fixtures.py
```

#### Testing Framework Stack
- **pytest**: Primary testing framework with fixtures
- **pytest-flask**: Flask application testing utilities
- **pytest-cov**: Code coverage reporting and enforcement
- **factory-boy**: Test data generation and factories
- **Flask-Testing**: Flask-specific testing helpers

#### Test Categories & Markers
Use pytest markers to categorize tests (configured in `pytest.ini`):
- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Multi-component integration tests (workflows)
- `@pytest.mark.views` - HTTP endpoint and view tests (HTTP requests)
- `@pytest.mark.auth` - Authentication and authorization tests
- `@pytest.mark.models` - Database model tests
- `@pytest.mark.financial` - Financial calculation tests
- `@pytest.mark.security` - Security and permission tests
- `@pytest.mark.property` - Property management tests
- `@pytest.mark.tenant` - Tenant management tests
- `@pytest.mark.performance` - Performance and load tests

#### Naming Conventions
- **Test files**: `test_[module_name].py`
- **Test classes**: `Test[ClassName]` (PascalCase)
- **Test methods**: `test_[specific_behavior]` (snake_case)
- **Fixtures**: `[fixture_name]_factory` or `[fixture_name]_fixture`

#### Multi-Tenant Testing Requirements
All tests involving data must ensure:
```python
# Example: Company isolation test
def test_property_query_respects_company_isolation(app, company_a, company_b):
    with app.app_context():
        # Create properties for each company
        property_a = create_property(company_id=company_a.id)
        property_b = create_property(company_id=company_b.id)

        # Verify company A only sees their data
        with login_as_company(company_a):
            properties = Property.query.filter_by(company_id=company_a.id).all()
            assert property_a in properties
            assert property_b not in properties
```

#### Security Testing Requirements
Every endpoint must be tested for:
- **Authentication**: Unauthenticated access blocked
- **Authorization**: Role-based access enforced
- **Data Isolation**: Company-level data separation
- **Input Validation**: XSS, CSRF, and injection prevention

#### Financial Testing Requirements
All monetary calculations require:
- **Decimal Precision**: Use `Decimal` for currency, test rounding
- **Edge Cases**: Zero amounts, negative values, large numbers
- **Currency Formatting**: Display and storage consistency
- **Audit Trails**: Payment and expense tracking validation

#### Running Tests
```bash
# Run all tests with coverage
pytest --cov=website --cov-report=term-missing --cov-report=html

# Run specific test categories
pytest -m unit                 # Fast unit tests only
pytest -m integration          # Integration tests only
pytest -m "unit or views"      # Multiple markers

# Run tests for specific modules
pytest tests/views/test_property_views.py
pytest tests/unit/test_models.py

# Run with verbose output
pytest -v -s
```

#### Test Database Setup
- **Isolation**: Each test gets fresh database state
- **Transactions**: Tests run in separate transactions (rolled back)
- **Fixtures**: Use factories for consistent test data
- **Performance**: In-memory SQLite for fast test execution

## Production Deployment

### Docker-Based Deployment Architecture

The application uses a **Docker Compose multi-container architecture** for production deployment:

#### Container Services

1. **PostgreSQL Database** (`db`)
   - Image: `postgres:16-alpine`
   - Container: `rentflow_db`
   - Purpose: Production database with persistent storage
   - Network: Internal only (not exposed to host)
   - Healthcheck: PostgreSQL `pg_isready` command
   - Volume: `postgres_data` for data persistence

2. **Redis Cache** (`redis`)
   - Image: `redis:7-alpine`
   - Container: `rentflow_redis`
   - Purpose: Rate limiting and caching
   - Network: Internal only (not exposed to host)
   - Healthcheck: Redis `ping` command
   - Volume: `redis_data` for persistence

3. **Flask Application** (`web`)
   - Build: Custom Dockerfile (`deployment/docker/Dockerfile`)
   - Container: `rentflow_web`
   - Base Image: `python:3.12-slim`
   - WSGI Server: Gunicorn (4 workers, 2 threads)
   - Port: 8000 (internal)
   - Healthcheck: HTTP request to `/health` endpoint
   - Non-root user: `rentflow` (UID 1000)
   - Volumes:
     - `instance/` - Application data
     - `logs/` - Application logs
     - `uploads/` - User uploads

4. **NGINX Reverse Proxy** (`nginx`)
   - Image: `nginx:alpine`
   - Container: `rentflow_nginx`
   - Purpose: SSL termination, static file serving, reverse proxy
   - Ports: 80 (HTTP), 443 (HTTPS)
   - Configuration:
     - `deployment/nginx/nginx.conf` - Main NGINX config
     - `deployment/nginx/conf.d/` - Site-specific configs
   - SSL Certificates: `deployment/ssl/` (Cloudflare Origin Certificates)
   - Static files: Direct serving from `website/static/`
   - Uploads: Direct serving from `uploads/`

### Deployment Files Structure

```
deployment/
├── docker/
│   ├── docker-compose.yml    # Multi-service orchestration
│   ├── Dockerfile             # Flask application image
│   └── README.md              # Docker deployment docs
├── nginx/
│   ├── nginx.conf             # NGINX main configuration
│   └── conf.d/
│       ├── rentflow.conf      # Site configuration
│       └── locations.inc      # Location blocks
├── scripts/
│   ├── validate.sh            # Pre-deployment validation
│   └── rollback.sh            # Rollback deployment
└── ssl/
    ├── cloudflare-origin.crt        # Cloudflare origin certificate
    ├── cloudflare-origin.key        # Private key
    └── cloudflare-origin-pull-ca.pem # Authenticated origin pulls CA
```

### Deployment Script

The automated deployment script `deploy.sh` performs:

1. **Pre-deployment checks**
   - Verify `.env` file exists
   - Check Docker and Docker Compose installation
   - Validate Docker Compose configuration

2. **Backup**
   - Create timestamped PostgreSQL backup to `backups/`
   - Backup format: `backup-YYYYMMDD-HHMMSS.sql`

3. **Build**
   - Build Docker images with caching
   - Pull latest code from git (if in repo)

4. **Database migrations**
   - Stop web application (keep DB running)
   - Run `flask db upgrade` in container
   - Apply all pending migrations

5. **Deployment**
   - Start all services with `docker compose up -d`
   - Wait for services to initialize
   - Verify service health

6. **Health checks**
   - Test `/health` endpoint
   - Display service status
   - Show logs if deployment fails

7. **Cleanup**
   - Remove old Docker images
   - Prune unused resources

**Usage:**
```bash
./deploy.sh
```

### Environment Configuration

Required environment variables in `.env` file:

```bash
# Database
POSTGRES_DB=rentflow
POSTGRES_USER=rentflow_user
POSTGRES_PASSWORD=<secure-password>

# Flask
SECRET_KEY=<generate-with-openssl-rand-hex-32>
FLASK_ENV=production
DEBUG=False

# Security
SESSION_COOKIE_SECURE=True

# Gunicorn (optional - has defaults)
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120
```

**Generate secure values:**
```bash
# SECRET_KEY
openssl rand -hex 32

# POSTGRES_PASSWORD
openssl rand -base64 32
```

### SSL/TLS Configuration

The application uses **Cloudflare for SSL** with the following setup:

1. **Cloudflare SSL Mode**: Full (strict)
2. **Origin Certificates**: 15-year certificates from Cloudflare
3. **Authenticated Origin Pulls**: Blocks direct IP access to origin
4. **TLS Version**: Minimum TLS 1.2
5. **Certificate Locations**:
   - Origin certificate: `deployment/ssl/cloudflare-origin.crt`
   - Private key: `deployment/ssl/cloudflare-origin.key`
   - CA certificate: `deployment/ssl/cloudflare-origin-pull-ca.pem`

### CI/CD with GitHub Actions

Automated deployment on push to `main` branch (`.github/workflows/deploy.yml`):

**Workflow steps:**
1. Checkout code
2. Run test suite
3. SSH to production server
4. Pull latest changes
5. Run `deploy.sh` script
6. Verify deployment health
7. Notify on failure

**Required GitHub Secrets:**
- `VPS_HOST` - Server IP or domain
- `VPS_USERNAME` - SSH username
- `VPS_SSH_KEY` - Private SSH key
- `VPS_PORT` - SSH port (default: 22)

### Database Management in Production

**Create migration:**
```bash
docker compose -f deployment/docker/docker-compose.yml run --rm web flask db migrate -m "Description"
```

**Apply migrations:**
```bash
docker compose -f deployment/docker/docker-compose.yml run --rm web flask db upgrade
```

**Manual backup:**
```bash
docker compose -f deployment/docker/docker-compose.yml exec db pg_dump -U rentflow_user rentflow > backup.sql
```

**Restore backup:**
```bash
cat backup.sql | docker compose -f deployment/docker/docker-compose.yml exec -T db psql -U rentflow_user rentflow
```

### Monitoring and Logs

**View logs:**
```bash
# All services
docker compose -f deployment/docker/docker-compose.yml logs -f

# Specific service
docker compose -f deployment/docker/docker-compose.yml logs -f web
docker compose -f deployment/docker/docker-compose.yml logs -f nginx
docker compose -f deployment/docker/docker-compose.yml logs -f db
```

**Service status:**
```bash
docker compose -f deployment/docker/docker-compose.yml ps
```

**Resource usage:**
```bash
docker stats
```

### Deployment Documentation

For comprehensive deployment documentation, see:
- **`DEPLOYMENT.md`**: Complete production deployment guide
- **`deployment/docker/README.md`**: Docker-specific documentation
- **`DEPLOYMENT_CHECKLIST.md`**: Pre-deployment validation checklist

## Architecture Benefits

### Development Benefits
- **Modular Blueprint Architecture**: Clean separation of concerns with Flask Blueprints
- **Comprehensive Testing**: pytest-based test suite with 80%+ coverage target
- **Modern Python**: Python 3.12+ with type hints and modern patterns
- **Development Ergonomics**: Hot reload, detailed error pages, SQLite for fast iteration
- **Dependency Management**: Modular requirements for different environments

### Production Benefits
- **Containerized Deployment**: Docker Compose for consistent, reproducible deployments
- **Production-Grade Stack**: PostgreSQL, Redis, Gunicorn, NGINX
- **High Availability**: Health checks, automatic restarts, container orchestration
- **Security Hardened**: SSL/TLS, rate limiting, Cloudflare protection, non-root containers
- **Automated Deployment**: One-command deployment with database migrations and backups
- **Monitoring Ready**: Health endpoints, structured logging, Docker stats

### Business Benefits
- **Scalable Multi-Tenancy**: Clean company separation for unlimited growth
- **Flexible Role System**: Four-tier permission model supporting team collaboration
- **Comprehensive Financial Tracking**: Full rent collection and expense management
- **Audit & Compliance**: Complete audit logging for regulatory compliance
- **Modern Responsive UI**: Bootstrap-based design for desktop and mobile
- **Secure by Design**: Multi-layer security with proper access controls

### Operational Benefits
- **Zero-Downtime Deployments**: Blue-green deployment capability
- **Automated Backups**: Database backups on every deployment
- **Easy Rollback**: Rollback scripts for quick recovery
- **CI/CD Integration**: GitHub Actions for automated testing and deployment
- **Environment Flexibility**: Works identically in development and production
- **Documentation**: Comprehensive docs for development, deployment, and operations

## Quick Reference

### Common Development Commands

```bash
# Development
python main.py                                    # Start development server
flask db migrate -m "message"                     # Create migration
flask db upgrade                                  # Apply migrations
pytest --cov=website                             # Run tests with coverage
pytest -m unit                                    # Run only unit tests

# Docker Development
docker compose -f deployment/docker/docker-compose.yml up -d
docker compose -f deployment/docker/docker-compose.yml logs -f web
docker compose -f deployment/docker/docker-compose.yml down

# Production Deployment
./deploy.sh                                       # Full deployment
./deployment/scripts/validate.sh                 # Validate setup
```

### Important File Locations

- **Application Code**: `website/`
- **Database Models**: `website/models.py`
- **Tenant Portal**: `website/tenant_portal/`
- **Super Admin**: `website/admin/`
- **Entry Point**: `main.py`
- **Environment Config**: `.env` (create from `.env.example`)
- **Docker Config**: `deployment/docker/docker-compose.yml`
- **NGINX Config**: `deployment/nginx/conf.d/rentflow.conf`
- **Migrations**: `migrations/versions/`
- **Tests**: `tests/`
- **Deployment Script**: `deploy.sh`
- **Deployment Docs**: `DEPLOYMENT.md`
- **Architecture Docs**: `docs/TENANT_PORTAL_ARCHITECTURE.md`

### Key Environment Variables

```bash
# Required for Production
SECRET_KEY                    # Flask secret (openssl rand -hex 32)
POSTGRES_PASSWORD            # Database password
DATABASE_URL                 # PostgreSQL connection string

# Stripe (for tenant portal payments)
STRIPE_SECRET_KEY            # Stripe API secret key
STRIPE_PUBLISHABLE_KEY       # Stripe publishable key (for frontend)
STRIPE_WEBHOOK_SECRET        # Stripe webhook signing secret

# SendGrid (for email notifications)
SENDGRID_API_KEY             # SendGrid API key
FROM_EMAIL                   # Default sender email address

# Optional (has defaults)
GUNICORN_WORKERS=4           # Number of worker processes
GUNICORN_THREADS=2           # Threads per worker
GUNICORN_TIMEOUT=120         # Request timeout in seconds
```

## Contributing & Development Workflow

1. **Set up development environment**
   ```bash
   python3 -m venv reenv312
   source reenv312/bin/activate
   pip install -r requirements/dev.txt
   ```

2. **Make changes**
   - Follow existing patterns and Blueprint structure
   - Ensure multi-tenant isolation with `company_id`
   - Add role-based access control decorators
   - Update or create tests

3. **Test changes**
   ```bash
   pytest --cov=website
   pytest -m unit -v
   ```

4. **Create database migration (if needed)**
   ```bash
   flask db migrate -m "Description of changes"
   flask db upgrade
   ```

5. **Commit changes**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

6. **Push to trigger deployment**
   ```bash
   git push origin main
   # GitHub Actions will automatically deploy to production
   ```

## Support & Documentation

### Primary Documentation
- **This File (CLAUDE.md)**: Complete development and architecture guide
- **README.md**: User-facing documentation and quick start
- **DEPLOYMENT.md**: Comprehensive production deployment guide
- **deployment/docker/README.md**: Docker-specific documentation
- **tests/README.md**: Testing documentation and guidelines
- **docs/TENANT_PORTAL_ARCHITECTURE.md**: Tenant portal design and security

### Getting Help
- Review existing code patterns in the codebase
- Check test files for usage examples
- Consult DEPLOYMENT.md for production issues
- Refer to Flask documentation for framework questions
- Review `docs/TENANT_PORTAL_ARCHITECTURE.md` for tenant portal design decisions

---

**Last Updated**: 2026-04-15
**Version**: Production-ready with Docker deployment + Tenant Portal
**Python Version**: 3.12+
**Framework**: Flask with SQLAlchemy
**Tenant Portal**: Phase 2 - Foundation complete (auth, dashboard, maintenance requests)
**Planned Integrations**: Stripe (payments), SendGrid (email)