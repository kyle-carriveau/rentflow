"""
Lease Template Forms

Forms for creating and editing lease templates.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Length, Optional


class LeaseTemplateForm(FlaskForm):
    """Form for creating and editing lease templates."""

    name = StringField(
        'Template Name',
        validators=[DataRequired(), Length(min=3, max=200)],
        render_kw={'placeholder': 'e.g., Standard Residential Lease'}
    )

    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=500)],
        render_kw={'placeholder': 'Brief description of when to use this template', 'rows': 2}
    )

    template_type = SelectField(
        'Template Type',
        choices=[
            ('residential', 'Residential Lease'),
            ('commercial', 'Commercial Lease'),
            ('month_to_month', 'Month-to-Month Agreement'),
            ('sublease', 'Sublease Agreement'),
            ('renewal', 'Lease Renewal'),
            ('custom', 'Custom')
        ],
        validators=[DataRequired()]
    )

    contract_text = TextAreaField(
        'Contract Template',
        validators=[DataRequired(), Length(min=100)],
        render_kw={
            'placeholder': 'Enter your lease contract template. Use {{field_name}} for merge fields like {{tenant_name}}, {{rent_amount}}, etc.',
            'rows': 20,
            'class': 'font-monospace'
        }
    )

    header_text = TextAreaField(
        'Header Text (Optional)',
        validators=[Optional(), Length(max=1000)],
        render_kw={'placeholder': 'Optional header text for the contract', 'rows': 3}
    )

    footer_text = TextAreaField(
        'Footer Text (Optional)',
        validators=[Optional(), Length(max=1000)],
        render_kw={'placeholder': 'Optional footer text for the contract', 'rows': 3}
    )

    default_terms = TextAreaField(
        'Default Terms & Conditions (Optional)',
        validators=[Optional(), Length(max=2000)],
        render_kw={'placeholder': 'Standard terms and conditions', 'rows': 5}
    )

    is_default = BooleanField(
        'Set as Default Template',
        default=False
    )

    is_active = BooleanField(
        'Active (Available for Use)',
        default=True
    )


class TemplatePreviewForm(FlaskForm):
    """Form for previewing templates with sample data."""

    tenant_name = StringField('Tenant Name', default='John Doe')
    tenant_email = StringField('Tenant Email', default='john.doe@example.com')
    tenant_phone = StringField('Tenant Phone', default='(555) 123-4567')
    landlord_name = StringField('Landlord Name', default='Property Owner')
    landlord_company = StringField('Company Name', default='ABC Properties LLC')
    property_address = StringField('Property Address', default='123 Main Street')
    unit_number = StringField('Unit Number', default='Apt 101')
    rent_amount = StringField('Monthly Rent', default='$1,500.00')
    security_deposit = StringField('Security Deposit', default='$1,500.00')
    start_date = StringField('Start Date', default='January 1, 2025')
    end_date = StringField('End Date', default='December 31, 2025')
    lease_term_months = StringField('Lease Term (months)', default='12')
    payment_due_date = StringField('Payment Due Date', default='1st')
    late_fee = StringField('Late Fee', default='$50.00')
    pet_deposit = StringField('Pet Deposit', default='$300.00')
    parking_spaces = StringField('Parking Spaces', default='1')
    utilities_included = StringField('Utilities Included', default='Water, Trash')
