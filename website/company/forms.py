from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length, URL, NumberRange


class CompanyEditForm(FlaskForm):
    """Form for editing company profile information."""
    name = StringField('Company Name',
                      validators=[DataRequired(message="Company name is required."),
                                Length(max=200, message="Company name must be less than 200 characters.")],
                      render_kw={"class": "form-control"})

    email = StringField('Company Email',
                       validators=[DataRequired(message="Company email is required."),
                                 Email(message="Please enter a valid email address.")],
                       render_kw={"class": "form-control"})

    phone = StringField('Phone',
                       validators=[Optional(), Length(max=20)],
                       render_kw={"class": "form-control"})

    address = StringField('Address',
                         validators=[Optional(), Length(max=200)],
                         render_kw={"class": "form-control"})

    city = StringField('City',
                      validators=[Optional(), Length(max=100)],
                      render_kw={"class": "form-control"})

    state = StringField('State',
                       validators=[Optional(), Length(max=2)],
                       render_kw={"class": "form-control"})

    zip_code = StringField('ZIP Code',
                          validators=[Optional(), Length(max=10)],
                          render_kw={"class": "form-control"})

    website = StringField('Website',
                         validators=[Optional(), URL(message="Please enter a valid URL."), Length(max=200)],
                         render_kw={"class": "form-control"})

    description = TextAreaField('Description',
                               validators=[Optional(), Length(max=1000)],
                               render_kw={"class": "form-control", "rows": "4"})

    industry = StringField('Industry',
                          validators=[Optional(), Length(max=100)],
                          render_kw={"class": "form-control"})

    company_size = StringField('Company Size',
                              validators=[Optional(), Length(max=50)],
                              render_kw={"class": "form-control"})

    tax_id = StringField('Tax ID',
                        validators=[Optional(), Length(max=50)],
                        render_kw={"class": "form-control"})

    license_number = StringField('License Number',
                                validators=[Optional(), Length(max=100)],
                                render_kw={"class": "form-control"})

    established_date = DateField('Established Date',
                                 validators=[Optional()],
                                 format='%Y-%m-%d',
                                 render_kw={"class": "form-control"})

    timezone = SelectField('Timezone',
                          choices=[
                              ('America/New_York', 'Eastern Time'),
                              ('America/Chicago', 'Central Time'),
                              ('America/Denver', 'Mountain Time'),
                              ('America/Los_Angeles', 'Pacific Time'),
                              ('America/Anchorage', 'Alaska Time'),
                              ('Pacific/Honolulu', 'Hawaii Time')
                          ],
                          default='America/New_York',
                          render_kw={"class": "form-control"})

    currency = SelectField('Currency',
                          choices=[
                              ('USD', 'US Dollar (USD)'),
                              ('EUR', 'Euro (EUR)'),
                              ('GBP', 'British Pound (GBP)'),
                              ('CAD', 'Canadian Dollar (CAD)')
                          ],
                          default='USD',
                          render_kw={"class": "form-control"})

    submit = SubmitField('Update Company Information', render_kw={"class": "btn btn-primary"})


class BusinessSettingsForm(FlaskForm):
    """Form for managing business settings."""
    default_lease_term = IntegerField('Default Lease Term (months)',
                                     validators=[Optional(), NumberRange(min=1, max=120)],
                                     default=12,
                                     render_kw={"class": "form-control"})

    late_fee_amount = IntegerField('Late Fee Amount',
                                   validators=[Optional(), NumberRange(min=0)],
                                   default=50,
                                   render_kw={"class": "form-control"})

    grace_period_days = IntegerField('Grace Period (days)',
                                     validators=[Optional(), NumberRange(min=0, max=30)],
                                     default=5,
                                     render_kw={"class": "form-control"})

    security_deposit_multiplier = StringField('Security Deposit Multiplier',
                                             validators=[Optional()],
                                             default='1',
                                             render_kw={"class": "form-control"})

    application_fee = IntegerField('Application Fee',
                                   validators=[Optional(), NumberRange(min=0)],
                                   default=25,
                                   render_kw={"class": "form-control"})

    pet_policy_enabled = BooleanField('Enable Pet Policy',
                                     render_kw={"class": "form-check-input"})

    pet_deposit_amount = IntegerField('Pet Deposit Amount',
                                      validators=[Optional(), NumberRange(min=0)],
                                      default=200,
                                      render_kw={"class": "form-control"})

    submit = SubmitField('Save Business Settings', render_kw={"class": "btn btn-primary"})


class FinancialSettingsForm(FlaskForm):
    """Form for managing financial settings (owner only)."""
    accounting_period = SelectField('Accounting Period',
                                   choices=[
                                       ('monthly', 'Monthly'),
                                       ('quarterly', 'Quarterly'),
                                       ('annual', 'Annual')
                                   ],
                                   default='monthly',
                                   render_kw={"class": "form-control"})

    tax_year_type = SelectField('Tax Year Type',
                               choices=[
                                   ('calendar', 'Calendar Year'),
                                   ('fiscal', 'Fiscal Year')
                               ],
                               default='calendar',
                               render_kw={"class": "form-control"})

    late_payment_interest = StringField('Late Payment Interest Rate (%)',
                                        validators=[Optional()],
                                        default='0',
                                        render_kw={"class": "form-control"})

    submit = SubmitField('Save Financial Settings', render_kw={"class": "btn btn-primary"})


class CommunicationSettingsForm(FlaskForm):
    """Form for managing communication settings."""
    email_notifications = BooleanField('Enable Email Notifications',
                                       default=True,
                                       render_kw={"class": "form-check-input"})

    sms_notifications = BooleanField('Enable SMS Notifications',
                                     default=False,
                                     render_kw={"class": "form-check-input"})

    rent_reminder_days = IntegerField('Rent Reminder Days Before Due',
                                      validators=[Optional(), NumberRange(min=0, max=30)],
                                      default=3,
                                      render_kw={"class": "form-control"})

    lease_expiry_notice_days = IntegerField('Lease Expiry Notice Days',
                                            validators=[Optional(), NumberRange(min=0, max=180)],
                                            default=60,
                                            render_kw={"class": "form-control"})

    submit = SubmitField('Save Communication Settings', render_kw={"class": "btn btn-primary"})
