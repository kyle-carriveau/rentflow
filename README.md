# RE2 - Real Estate Management System

A comprehensive Flask-based web application for real estate management and property rental operations. RE2 provides a complete platform for companies to manage portfolios, properties, units, tenants, leases, and financial operations with full multi-tenant support.

## Features

### Multi-Tenant Architecture
- **Company-level data isolation** with perfect tenant separation
- **Role-based access control** (Owner, Manager, Staff, Viewer)
- **Secure authentication** with password hashing and session management
- **Team collaboration** with user invitation and role assignment

### Property & Portfolio Management
- **Hierarchical organization**: Company → Portfolio → Property → Unit
- **Portfolio performance metrics** and analytics
- **Property assignment** and reassignment capabilities
- **Automated occupancy tracking** (Vacant, Partially Occupied, Fully Occupied)
- **Unit status management** (Available, Reserved, Occupied, Maintenance)

### Lease Management
- **Automated lease lifecycle tracking** (Pending, Active, Expiring, Expired, Terminated)
- **Template-based contract generation** with variable substitution
- **Lease status automation** based on dates and events
- **Comprehensive lease details** with deposit, utilities, and pet policy tracking
- **Renewal management** and expiration alerts

### Financial Operations
- **Rent collection** with payment tracking and history
- **Expense management** with categorization and tax features
- **Financial reporting** with income/expense analytics
- **Outstanding balance tracking** and overdue notifications
- **Property-specific financial views**

### User Management
- **Team member invitations** with role-based permissions
- **User directory** and profile management
- **Company profile** and settings (Owner access only)
- **Personal dashboards** with role-appropriate features

## Technology Stack

### Development
- **Backend**: Flask (Python 3.12+)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Flask-Login with Werkzeug password hashing
- **Frontend**: HTML/Jinja2 templates with Bootstrap UI framework
- **Architecture**: Modular Blueprint-based structure

### Production
- **Containerization**: Docker & Docker Compose
- **Web Server**: NGINX (reverse proxy & SSL termination)
- **App Server**: Gunicorn (WSGI HTTP server)
- **Database**: PostgreSQL 16
- **Caching**: Redis (rate limiting)
- **Deployment**: Automated CI/CD with GitHub Actions

## Installation

### Prerequisites
- Python 3.12 or higher
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/kyle-carriveau/rentflow.git
   cd re2
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv reenv312
   ```

3. **Activate the virtual environment**
   ```bash
   # On macOS/Linux
   source reenv312/bin/activate

   # On Windows
   reenv312\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   # Development (includes testing tools)
   pip install -r requirements/dev.txt

   # Or production only
   pip install -r requirements/prod.txt
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:5000`
   - The database schema will be created automatically on first run

## Project Structure

```
re2/
├── main.py                          # Application entry point
├── config/                          # Configuration module
│   ├── __init__.py                  # Environment-based configs
│   └── README.md
├── deployment/                      # Production deployment
│   ├── docker/                      # Docker configuration
│   │   ├── docker-compose.yml       # Multi-service orchestration
│   │   ├── Dockerfile               # Container image definition
│   │   └── README.md                # Deployment documentation
│   ├── nginx/                       # NGINX configuration
│   │   ├── nginx.conf               # Main config
│   │   └── conf.d/                  # Site configs
│   ├── scripts/                     # Deployment scripts
│   │   └── validate.sh              # Validation script
│   └── ssl/                         # SSL certificates
├── requirements/                    # Modular dependencies
│   ├── base.txt                     # Core requirements
│   ├── dev.txt                      # Development & testing
│   └── prod.txt                     # Production only
├── website/                         # Application code
│   ├── __init__.py                  # App factory
│   ├── models.py                    # Database models
│   ├── errors.py                    # Error handlers
│   ├── auth/                        # Authentication
│   ├── company/                     # Company management
│   ├── user_management/             # Team management
│   ├── property/                    # Property management
│   ├── unit/                        # Unit management
│   ├── tenant/                      # Tenant management
│   ├── lease/                       # Lease management
│   ├── lease_template/              # Templates
│   ├── portfolio/                   # Portfolio management
│   ├── financial/                   # Financial operations
│   ├── report/                      # Reporting
│   ├── profile/                     # User profiles
│   ├── tasks/                       # Scheduled tasks
│   ├── templates/                   # HTML templates
│   └── static/                      # Static assets
├── tests/                           # Test suite
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   └── views/                       # View tests
├── migrations/                      # Database migrations
├── instance/                        # Instance data
├── logs/                            # Application logs
└── deploy.sh                        # Deployment script
```

## Core Models

- **Company**: Multi-tenant companies with business information
- **User**: System users with roles and company association
- **Portfolio**: Collections of properties within a company
- **Property**: Individual real estate properties with occupancy tracking
- **Unit**: Rentable units with automated status management
- **Tenant**: Renter information and contact details
- **Lease**: Rental agreements with automated lifecycle management
- **LeaseTemplate**: Reusable contract templates
- **Payment**: Payment tracking and rent collection
- **Expense**: Property and business expense management

## Role-Based Permissions

### Owner (Highest Privilege)
- Full system access
- Company management and settings
- User management and role assignment
- All financial operations

### Manager
- Property and tenant management
- Lease creation and management
- Financial operations and reporting
- Portfolio management

### Staff
- Property and tenant management
- Limited financial access
- View reports and analytics

### Viewer (Read-Only)
- View assigned properties and units
- View tenant information
- View reports (no edit access)

## Security Features

- **Password hashing** using Werkzeug security
- **Session management** with Flask-Login
- **Company-level data isolation** preventing cross-tenant access
- **Role-based decorators** for endpoint protection
- **CSRF protection** on all forms
- **Secure password reset** functionality

## Testing

The project includes a comprehensive test suite with:
- **Unit tests** for models and utilities
- **Integration tests** for workflows
- **View tests** for endpoints
- **Security tests** for permissions and data isolation

Run tests with:
```bash
pytest --cov=website --cov-report=term-missing
```

## Deployment

### Production Deployment with Docker

The application includes a production-ready Docker setup with automated deployment.

#### Quick Start

```bash
# 1. Clone repository on your server
git clone https://github.com/kyle-carriveau/rentflow.git
cd re2

# 2. Configure environment
cp .env.example .env
# Edit .env with production values

# 3. Deploy
./deploy.sh
```

#### Docker Compose Deployment

```bash
# Local development
docker compose -f docker-compose.local.yml up -d

# Staging environment
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Production environment
docker compose -f docker-compose.production.yml --env-file .env up -d

# View logs (any environment)
docker compose -f docker-compose.local.yml logs -f

# Stop services
docker compose -f docker-compose.local.yml down
```

#### Services

The deployment includes:
- **PostgreSQL 16**: Production database
- **Redis 7**: Rate limiting and caching
- **Flask/Gunicorn**: Application server
- **NGINX**: Reverse proxy with SSL termination

#### Environment Variables

Required in `.env` file:
```bash
SECRET_KEY=your-secure-random-key
POSTGRES_PASSWORD=your-database-password
POSTGRES_DB=rentflow
POSTGRES_USER=rentflow_user
```

Optional configuration:
```bash
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120
```

#### Validation

Validate your deployment configuration:
```bash
./deployment/scripts/validate.sh
```

#### CI/CD with GitHub Actions

The repository includes automated deployment on push to `main` branch:
- Runs full test suite
- Deploys to production VPS
- Performs health checks
- Auto-rollback on failure

See `.github/workflows/deploy.yml` for configuration.

### Manual Deployment

For manual deployment without Docker:

1. Set up PostgreSQL database
2. Configure environment variables
3. Install production dependencies: `pip install -r requirements/prod.txt`
4. Run migrations: `flask db upgrade`
5. Start with Gunicorn: `gunicorn main:app`

For detailed deployment documentation, see `deployment/docker/README.md`.

## Development

### Running in Development Mode
The application runs in debug mode by default when using `python main.py`. This enables:
- Automatic reloading on code changes
- Detailed error messages
- Debug toolbar (if configured)

### Database Management
- Database schema is created automatically on first run
- Located at `website/database.db`
- Uses SQLAlchemy ORM for all database operations

### Adding New Features
1. Follow the existing Blueprint structure
2. Ensure multi-tenant isolation with `company_id` filtering
3. Implement role-based access control
4. Write tests for new functionality
5. Update documentation as needed

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Commit Guidelines
- Use clear, descriptive commit messages
- Focus on the "why" not just the "what"
- Use present tense ("Add feature" not "Added feature")
- Keep commits focused and atomic

## License

This project is proprietary software. All rights reserved.

## Support

For issues, questions, or contributions, please open an issue in the GitHub repository.

## Roadmap

- [ ] Implement scheduled tasks for lease status automation
- [ ] Add email notifications for lease expirations
- [ ] Enhanced reporting and analytics dashboards
- [ ] Mobile-responsive improvements
- [ ] API endpoints for third-party integrations
- [ ] Document management system
- [ ] Maintenance request tracking
- [ ] Tenant portal for self-service

## Acknowledgments

Built with Flask, SQLAlchemy, and Bootstrap to provide a modern, scalable real estate management solution.
