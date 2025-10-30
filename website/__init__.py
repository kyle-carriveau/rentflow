from flask import Flask
from os import path
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from decouple import config as env_config

# Import configuration management
from config import get_config

db = SQLAlchemy(session_options={"autoflush": False})
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()

def create_app(config_name=None):
    """
    Application factory pattern.

    Args:
        config_name: Environment name (development, staging, production, testing)
                    If None, reads from FLASK_ENV environment variable

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load environment-specific configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Initialize config (runs environment-specific setup)
    config_class.init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    mail.init_app(app)

    # Configure session security
    from website.session_security import SessionSecurity, CSRFProtection, SessionMiddleware
    SessionSecurity.configure_session_security(app)
    CSRFProtection.init_csrf_protection(app)
    SessionMiddleware(app)

    # Email verification disabled - no configuration needed

    with app.app_context():
        from website.main.views import main
        app.register_blueprint(main, url_prefix='/')
        
    from website.property.views import property
    app.register_blueprint(property, url_prefix='/property')

    from website.auth.views import auth
    app.register_blueprint(auth, url_prefix='/')

    from website.unit.views import unit
    app.register_blueprint(unit, url_prefix='/unit')

    from website.profile.views import profile
    app.register_blueprint(profile, url_prefix='/profile')

    from website.tenant.views import tenant
    app.register_blueprint(tenant, url_prefix='/tenant')

    from website.lease.views import lease
    app.register_blueprint(lease, url_prefix='/lease')

    from website.lease_template.views import lease_template
    app.register_blueprint(lease_template, url_prefix='/lease-templates')

    from website.portfolio.views import portfolio
    app.register_blueprint(portfolio, url_prefix='/portfolio')

    from website.financial.views import financial
    app.register_blueprint(financial, url_prefix='/financial')

    from website.user_management.views import user_management
    app.register_blueprint(user_management, url_prefix='/users')

    from website.company.views import company
    app.register_blueprint(company, url_prefix='/company')

    from website.report.views import report
    app.register_blueprint(report, url_prefix='/reports')

    from website.search.views import search
    app.register_blueprint(search, url_prefix='/search')

    from website.health import health_bp
    app.register_blueprint(health_bp)

    # Super Admin Blueprint (separate authentication system)
    from website.admin import admin
    app.register_blueprint(admin)

    from website.errors import page_not_found, forbidden, internal_server_error
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(500, internal_server_error)

    # Import all models to ensure they're registered with SQLAlchemy
    from website.models import (
        User, Company, Portfolio, Property, Unit,
        Tenant, Lease, LeaseTemplate, Payment, Expense,
        PasswordHistoryModel, AuditLogModel, EmailVerificationAttempt,
        SuperAdmin, SuperAdminAuditLog
    )
    
    # with app.app_context():
    #     create_database(app)
    
    # Register template filters for consistent number formatting
    @app.template_filter('currency')
    def currency_filter(value):
        """Format a number as currency with comma separators"""
        if value is None or value == '':
            return '$0'
        try:
            # Convert to float if it's a string
            if isinstance(value, str):
                value = float(value)
            return f"${value:,.0f}"
        except (ValueError, TypeError):
            return '$0'

    @app.template_filter('number')
    def number_filter(value):
        """Format a number with comma separators"""
        if value is None or value == '':
            return '0'
        try:
            # Convert to float if it's a string
            if isinstance(value, str):
                value = float(value)
            return f"{value:,.0f}"
        except (ValueError, TypeError):
            return '0'

    @app.template_filter('percentage')
    def percentage_filter(value, decimals=1):
        """Format a number as a percentage with specified decimal places"""
        if value is None or value == '':
            return '0.0%'
        try:
            # Convert to float if it's a string
            if isinstance(value, str):
                value = float(value)
            return f"{value:.{decimals}f}%"
        except (ValueError, TypeError):
            return '0.0%'

    # Import models here to avoid circular import
    from website.models import AnonymousUser, User

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.anonymous_user = AnonymousUser
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        try:
            # For Flask-Login, we need to handle both UUID strings and potential integer IDs for backward compatibility
            # Try UUID lookup first (secure method)
            user = User.query.filter_by(uuid=str(id)).first()
            if user:
                return user
            # Fallback to integer ID lookup for existing sessions (temporary compatibility)
            try:
                return User.query.get(int(id))
            except ValueError:
                return None
        except Exception:
            return None
    
    return app

# def create_database(app):
#     # Always create tables (db.create_all() is safe to call multiple times)
#     db.create_all()
#     print('Created database and tables')

