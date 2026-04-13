from flask import render_template, Blueprint, request, redirect, url_for, flash, jsonify
from website.models import Company, CompanySettings
from website import db
from flask_login import login_required, current_user
from website.errors import page_not_found
from website.auth_utils import owner_required, manager_required
from website.company.forms import CompanyEditForm, BusinessSettingsForm, FinancialSettingsForm, CommunicationSettingsForm
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

    form = CompanyEditForm(obj=company_data)

    if form.validate_on_submit():
        # Update company with form data
        company_data.name = form.name.data
        company_data.email = form.email.data
        company_data.phone = form.phone.data if form.phone.data else None
        company_data.address = form.address.data if form.address.data else None
        company_data.city = form.city.data if form.city.data else None
        company_data.state = form.state.data if form.state.data else None
        company_data.zip_code = form.zip_code.data if form.zip_code.data else None
        company_data.website = form.website.data if form.website.data else None
        company_data.description = form.description.data if form.description.data else None
        company_data.industry = form.industry.data if form.industry.data else None
        company_data.company_size = form.company_size.data if form.company_size.data else None
        company_data.tax_id = form.tax_id.data if form.tax_id.data else None
        company_data.license_number = form.license_number.data if form.license_number.data else None
        company_data.established_date = form.established_date.data
        company_data.timezone = form.timezone.data
        company_data.currency = form.currency.data

        db.session.commit()
        flash('Company information updated successfully!', 'success')
        return redirect(url_for('company.profile'))

    return render_template("edit_company.html", user=current_user, company=company_data, form=form)

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

    # Load current settings for form pre-population
    form = BusinessSettingsForm(
        default_lease_term=get_company_setting(company_id, 'default_lease_term', 12),
        late_fee_amount=get_company_setting(company_id, 'late_fee_amount', 50),
        grace_period_days=get_company_setting(company_id, 'grace_period_days', 5),
        security_deposit_multiplier=get_company_setting(company_id, 'security_deposit_multiplier', '1'),
        application_fee=get_company_setting(company_id, 'application_fee', 25),
        pet_policy_enabled=get_company_setting(company_id, 'pet_policy_enabled', False),
        pet_deposit_amount=get_company_setting(company_id, 'pet_deposit_amount', 200)
    )

    if form.validate_on_submit():
        try:
            # Save settings from form
            set_company_setting(company_id, 'default_lease_term', form.default_lease_term.data, 'integer', 'business')
            set_company_setting(company_id, 'late_fee_amount', form.late_fee_amount.data, 'integer', 'business')
            set_company_setting(company_id, 'grace_period_days', form.grace_period_days.data, 'integer', 'business')
            set_company_setting(company_id, 'security_deposit_multiplier', form.security_deposit_multiplier.data, 'string', 'business')
            set_company_setting(company_id, 'application_fee', form.application_fee.data, 'integer', 'business')
            set_company_setting(company_id, 'pet_policy_enabled', form.pet_policy_enabled.data, 'boolean', 'business')
            set_company_setting(company_id, 'pet_deposit_amount', form.pet_deposit_amount.data, 'integer', 'business')

            flash('Business settings updated successfully!', 'success')
            return redirect(url_for('company.settings'))

        except Exception as e:
            flash('Error updating business settings.', 'error')
            return redirect(url_for('company.business_settings'))

    return render_template("business_settings.html", user=current_user, form=form)

@company.route('/settings/financial', methods=['GET', 'POST'])
@login_required
@owner_required
def financial_settings():
    """Manage financial settings (owner only)."""
    company_id = current_user.get_company_id()

    # Load current settings for form pre-population
    form = FinancialSettingsForm(
        accounting_period=get_company_setting(company_id, 'accounting_period', 'monthly'),
        tax_year_type=get_company_setting(company_id, 'tax_year_type', 'calendar'),
        late_payment_interest=get_company_setting(company_id, 'late_payment_interest', '0')
    )

    if form.validate_on_submit():
        try:
            # Save settings from form
            set_company_setting(company_id, 'accounting_period', form.accounting_period.data, 'string', 'financial')
            set_company_setting(company_id, 'tax_year_type', form.tax_year_type.data, 'string', 'financial')
            set_company_setting(company_id, 'late_payment_interest', form.late_payment_interest.data, 'string', 'financial')

            flash('Financial settings updated successfully!', 'success')
            return redirect(url_for('company.settings'))

        except Exception as e:
            flash('Error updating financial settings.', 'error')
            return redirect(url_for('company.financial_settings'))

    return render_template("financial_settings.html", user=current_user, form=form)

@company.route('/settings/communication', methods=['GET', 'POST'])
@login_required
@manager_required
def communication_settings():
    """Manage communication settings."""
    company_id = current_user.get_company_id()

    # Load current settings for form pre-population
    form = CommunicationSettingsForm(
        email_notifications=get_company_setting(company_id, 'email_notifications', True),
        sms_notifications=get_company_setting(company_id, 'sms_notifications', False),
        rent_reminder_days=get_company_setting(company_id, 'rent_reminder_days', 3),
        lease_expiry_notice_days=get_company_setting(company_id, 'lease_expiry_notice_days', 60)
    )

    if form.validate_on_submit():
        try:
            # Save settings from form
            set_company_setting(company_id, 'email_notifications', form.email_notifications.data, 'boolean', 'communication')
            set_company_setting(company_id, 'sms_notifications', form.sms_notifications.data, 'boolean', 'communication')
            set_company_setting(company_id, 'rent_reminder_days', form.rent_reminder_days.data, 'integer', 'communication')
            set_company_setting(company_id, 'lease_expiry_notice_days', form.lease_expiry_notice_days.data, 'integer', 'communication')

            flash('Communication settings updated successfully!', 'success')
            return redirect(url_for('company.settings'))

        except Exception as e:
            flash('Error updating communication settings.', 'error')
            return redirect(url_for('company.communication_settings'))

    return render_template("communication_settings.html", user=current_user, form=form)