from flask import render_template, Blueprint, request, redirect, url_for, flash, jsonify
from website.models import Company, CompanySettings
from website import db
from flask_login import login_required, current_user
from website.errors import page_not_found
from website.auth_utils import owner_required, manager_required
from datetime import datetime
import json

company = Blueprint('company', __name__, template_folder='templates')

@company.route('/')
@login_required
def profile():
    """Display company profile information."""
    company_id = current_user.get_company_id()
    company_data = Company.query.filter_by(id=company_id).first()
    if not company_data:
        return page_not_found(404)
    
    return render_template("company_profile.html", user=current_user, company=company_data)

@company.route('/edit', methods=['GET', 'POST'])
@login_required
@owner_required
def edit():
    """Edit company profile information (owner only)."""
    company_id = current_user.get_company_id()
    company_data = Company.query.filter_by(id=company_id).first()
    if not company_data:
        return page_not_found(404)
    
    if request.method == 'POST':
        # Basic company information
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        website = request.form.get('website', '').strip()
        description = request.form.get('description', '').strip()

        # Enhanced company fields
        industry = request.form.get('industry', '').strip()
        company_size = request.form.get('company_size', '').strip()
        tax_id = request.form.get('tax_id', '').strip()
        license_number = request.form.get('license_number', '').strip()
        established_date = request.form.get('established_date')
        timezone = request.form.get('timezone', 'America/New_York').strip()
        currency = request.form.get('currency', 'USD').strip()

        # Server-side validation
        if not name:
            flash('Company name is required.', 'error')
            return render_template("edit_company.html", user=current_user, company=company_data)

        if not email:
            flash('Company email is required.', 'error')
            return render_template("edit_company.html", user=current_user, company=company_data)

        # Data conversion
        try:
            if established_date:
                established_date = datetime.strptime(established_date, '%Y-%m-%d').date()
            else:
                established_date = None
        except ValueError:
            flash('Invalid established date format.', 'error')
            return render_template("edit_company.html", user=current_user, company=company_data)

        # Update company
        company_data.name = name
        company_data.email = email
        company_data.phone = phone
        company_data.address = address
        company_data.city = city
        company_data.state = state
        company_data.zip_code = zip_code
        company_data.website = website
        company_data.description = description
        company_data.industry = industry
        company_data.company_size = company_size
        company_data.tax_id = tax_id
        company_data.license_number = license_number
        company_data.established_date = established_date
        company_data.timezone = timezone
        company_data.currency = currency

        db.session.commit()
        flash('Company information updated successfully!', 'success')
        return redirect(url_for('company.profile'))

    return render_template("edit_company.html", user=current_user, company=company_data)

# Helper functions for settings management
def get_company_setting(company_id, setting_key, default_value=None):
    """Get a company setting value by key."""
    setting = CompanySettings.query.filter_by(company_id=company_id, setting_key=setting_key).first()
    if setting:
        # Convert based on setting type
        if setting.setting_type == 'boolean':
            return setting.setting_value.lower() in ('true', '1', 'yes')
        elif setting.setting_type == 'integer':
            try:
                return int(setting.setting_value)
            except (ValueError, TypeError):
                return default_value
        elif setting.setting_type == 'json':
            try:
                return json.loads(setting.setting_value)
            except (ValueError, TypeError):
                return default_value
        else:
            return setting.setting_value
    return default_value

def set_company_setting(company_id, setting_key, setting_value, setting_type='string', category=None):
    """Set a company setting value."""
    setting = CompanySettings.query.filter_by(company_id=company_id, setting_key=setting_key).first()

    # Convert value to string for storage
    if setting_type == 'boolean':
        setting_value_str = str(setting_value).lower()
    elif setting_type == 'json':
        setting_value_str = json.dumps(setting_value)
    else:
        setting_value_str = str(setting_value)

    if setting:
        setting.setting_value = setting_value_str
        setting.setting_type = setting_type
        setting.category = category
        setting.updated_at = datetime.utcnow()
    else:
        setting = CompanySettings(
            company_id=company_id,
            setting_key=setting_key,
            setting_value=setting_value_str,
            setting_type=setting_type,
            category=category
        )
        db.session.add(setting)

    db.session.commit()
    return setting

@company.route('/settings')
@login_required
@manager_required
def settings():
    """Display company settings dashboard."""
    company_id = current_user.get_company_id()
    company_data = Company.query.filter_by(id=company_id).first()
    if not company_data:
        return page_not_found(404)

    # Get all settings grouped by category
    settings = CompanySettings.query.filter_by(company_id=company_id).all()
    settings_by_category = {}

    for setting in settings:
        category = setting.category or 'general'
        if category not in settings_by_category:
            settings_by_category[category] = {}
        settings_by_category[category][setting.setting_key] = {
            'value': setting.setting_value,
            'type': setting.setting_type
        }

    return render_template("company_settings.html",
                         user=current_user,
                         company=company_data,
                         settings=settings_by_category)

@company.route('/settings/business', methods=['GET', 'POST'])
@login_required
@manager_required
def business_settings():
    """Manage business settings."""
    company_id = current_user.get_company_id()

    if request.method == 'POST':
        try:
            # Business rule settings
            default_lease_term = request.form.get('default_lease_term', '12')
            late_fee_amount = request.form.get('late_fee_amount', '50')
            grace_period_days = request.form.get('grace_period_days', '5')
            security_deposit_multiplier = request.form.get('security_deposit_multiplier', '1')
            application_fee = request.form.get('application_fee', '25')
            pet_policy_enabled = 'pet_policy_enabled' in request.form
            pet_deposit_amount = request.form.get('pet_deposit_amount', '200')

            # Save settings
            set_company_setting(company_id, 'default_lease_term', default_lease_term, 'integer', 'business')
            set_company_setting(company_id, 'late_fee_amount', late_fee_amount, 'integer', 'business')
            set_company_setting(company_id, 'grace_period_days', grace_period_days, 'integer', 'business')
            set_company_setting(company_id, 'security_deposit_multiplier', security_deposit_multiplier, 'string', 'business')
            set_company_setting(company_id, 'application_fee', application_fee, 'integer', 'business')
            set_company_setting(company_id, 'pet_policy_enabled', pet_policy_enabled, 'boolean', 'business')
            set_company_setting(company_id, 'pet_deposit_amount', pet_deposit_amount, 'integer', 'business')

            flash('Business settings updated successfully!', 'success')
            return redirect(url_for('company.settings'))

        except Exception as e:
            flash('Error updating business settings.', 'error')
            return redirect(url_for('company.business_settings'))

    # Load current settings
    settings = {
        'default_lease_term': get_company_setting(company_id, 'default_lease_term', 12),
        'late_fee_amount': get_company_setting(company_id, 'late_fee_amount', 50),
        'grace_period_days': get_company_setting(company_id, 'grace_period_days', 5),
        'security_deposit_multiplier': get_company_setting(company_id, 'security_deposit_multiplier', '1'),
        'application_fee': get_company_setting(company_id, 'application_fee', 25),
        'pet_policy_enabled': get_company_setting(company_id, 'pet_policy_enabled', False),
        'pet_deposit_amount': get_company_setting(company_id, 'pet_deposit_amount', 200)
    }

    return render_template("business_settings.html",
                         user=current_user,
                         settings=settings)

@company.route('/settings/financial', methods=['GET', 'POST'])
@login_required
@owner_required
def financial_settings():
    """Manage financial settings (owner only)."""
    company_id = current_user.get_company_id()

    if request.method == 'POST':
        try:
            # Financial settings
            accounting_period = request.form.get('accounting_period', 'monthly')
            tax_year_type = request.form.get('tax_year_type', 'calendar')
            late_payment_interest = request.form.get('late_payment_interest', '0')

            # Save settings
            set_company_setting(company_id, 'accounting_period', accounting_period, 'string', 'financial')
            set_company_setting(company_id, 'tax_year_type', tax_year_type, 'string', 'financial')
            set_company_setting(company_id, 'late_payment_interest', late_payment_interest, 'string', 'financial')

            flash('Financial settings updated successfully!', 'success')
            return redirect(url_for('company.settings'))

        except Exception as e:
            flash('Error updating financial settings.', 'error')
            return redirect(url_for('company.financial_settings'))

    # Load current settings
    settings = {
        'accounting_period': get_company_setting(company_id, 'accounting_period', 'monthly'),
        'tax_year_type': get_company_setting(company_id, 'tax_year_type', 'calendar'),
        'late_payment_interest': get_company_setting(company_id, 'late_payment_interest', '0')
    }

    return render_template("financial_settings.html",
                         user=current_user,
                         settings=settings)

@company.route('/settings/communication', methods=['GET', 'POST'])
@login_required
@manager_required
def communication_settings():
    """Manage communication settings."""
    company_id = current_user.get_company_id()

    if request.method == 'POST':
        try:
            # Communication settings
            email_notifications = 'email_notifications' in request.form
            sms_notifications = 'sms_notifications' in request.form
            rent_reminder_days = request.form.get('rent_reminder_days', '3')
            lease_expiry_notice_days = request.form.get('lease_expiry_notice_days', '60')

            # Save settings
            set_company_setting(company_id, 'email_notifications', email_notifications, 'boolean', 'communication')
            set_company_setting(company_id, 'sms_notifications', sms_notifications, 'boolean', 'communication')
            set_company_setting(company_id, 'rent_reminder_days', rent_reminder_days, 'integer', 'communication')
            set_company_setting(company_id, 'lease_expiry_notice_days', lease_expiry_notice_days, 'integer', 'communication')

            flash('Communication settings updated successfully!', 'success')
            return redirect(url_for('company.settings'))

        except Exception as e:
            flash('Error updating communication settings.', 'error')
            return redirect(url_for('company.communication_settings'))

    # Load current settings
    settings = {
        'email_notifications': get_company_setting(company_id, 'email_notifications', True),
        'sms_notifications': get_company_setting(company_id, 'sms_notifications', False),
        'rent_reminder_days': get_company_setting(company_id, 'rent_reminder_days', 3),
        'lease_expiry_notice_days': get_company_setting(company_id, 'lease_expiry_notice_days', 60)
    }

    return render_template("communication_settings.html",
                         user=current_user,
                         settings=settings)