from flask import Flask
from os import path
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from decouple import config

db = SQLAlchemy(session_options={"autoflush": False})

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = config('SECRET_KEY', default='keyissecret')
    app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL', default='sqlite:///database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = config('DEBUG', default=True, cast=bool)
    db.init_app(app)

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

    from website.portfolio.views import portfolio
    app.register_blueprint(portfolio, url_prefix='/portfolio')

    from website.financial.views import financial
    app.register_blueprint(financial, url_prefix='/financial')

    from website.user_management.views import user_management
    app.register_blueprint(user_management, url_prefix='/users')

    from website.company.views import company
    app.register_blueprint(company, url_prefix='/company')

    from website.errors import page_not_found
    app.register_error_handler(404, page_not_found)

    # Import all models to ensure they're registered with SQLAlchemy
    from website.models import (
        User, Company, Portfolio, Property, Unit, 
        Tenant, Lease, Payment, Expense
    )
    
    with app.app_context():
        create_database(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app

def create_database(app):
    # Always create tables (db.create_all() is safe to call multiple times)
    db.create_all()
    print('Created database and tables')

