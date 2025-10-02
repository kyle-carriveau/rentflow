from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, IntegerField, DecimalField, TextAreaField, StringField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange

class LeaseForm(FlaskForm):
    tenant = SelectField('Tenant', validators=[DataRequired()], render_kw={"data-placeholder": "Choose a tenant..."})
    unit = SelectField('Unit', validators=[DataRequired()], render_kw={"data-placeholder": "Choose a unit..."})
    start = DateField('Start Date', validators=[DataRequired()])
    end = DateField('End Date', validators=[DataRequired()])
    rent = DecimalField('Monthly Rent', validators=[DataRequired()], places=2)

    # Financial Fields
    security_deposit = DecimalField('Security Deposit', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    pet_deposit = DecimalField('Pet Deposit', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    late_fee = DecimalField('Late Fee Amount', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    payment_due_date = SelectField('Payment Due Date', choices=[
        (1, '1st of month'), (5, '5th of month'), (15, '15th of month'), (30, '30th of month')
    ], coerce=int, validators=[DataRequired()], default=1)
    grace_period_days = IntegerField('Grace Period (Days)', validators=[Optional(), NumberRange(min=0, max=30)], default=5)
    utilities_included = TextAreaField('Utilities Included', validators=[Optional()],
                                     render_kw={"placeholder": "e.g., Water, Sewer, Trash (separate by commas)"})
    parking_fee = DecimalField('Monthly Parking Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)

    # Additional Financial Fields for Comprehensive Tracking
    application_fee = DecimalField('Application Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    broker_fee = DecimalField('Broker/Agent Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    cleaning_fee = DecimalField('Cleaning Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    administrative_fee = DecimalField('Administrative Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    last_month_rent = DecimalField('Last Month Rent (Prepaid)', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    utility_deposits = DecimalField('Utility Deposits', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    storage_fee = DecimalField('Monthly Storage Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    concessions = DecimalField('Rent Concessions/Discounts', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    pet_fee = DecimalField('Monthly Pet Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)

    # Lease Terms Fields
    lease_type = SelectField('Lease Type', choices=[
        ('fixed', 'Fixed Term'), ('month_to_month', 'Month-to-Month'), ('periodic', 'Periodic')
    ], validators=[Optional()], default='fixed')
    auto_renewal = SelectField('Auto Renewal', choices=[
        ('no', 'No Auto Renewal'), ('month_to_month', 'Convert to Month-to-Month'), ('same_term', 'Renew Same Term')
    ], validators=[Optional()], default='no')
    notice_period_days = IntegerField('Notice Period (Days)', validators=[Optional(), NumberRange(min=0, max=365)], default=30)
    early_termination_fee = DecimalField('Early Termination Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    max_occupants = IntegerField('Maximum Occupants', validators=[Optional(), NumberRange(min=1, max=20)], default=2)
    renewal_terms = TextAreaField('Renewal Terms & Conditions', validators=[Optional()],
                                render_kw={"placeholder": "Enter specific terms for lease renewal, rent adjustments, etc."})

    # Operational Details Fields
    move_in_date = DateField('Actual Move-In Date', validators=[Optional()])
    move_out_date = DateField('Actual Move-Out Date', validators=[Optional()])
    key_deposit = DecimalField('Key/Access Deposit', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    move_in_inspection_notes = TextAreaField('Move-In Inspection Notes', validators=[Optional()],
                                           render_kw={"placeholder": "Document property condition at move-in"})
    move_out_inspection_notes = TextAreaField('Move-Out Inspection Notes', validators=[Optional()],
                                            render_kw={"placeholder": "Document property condition at move-out"})
    lease_status = SelectField('Lease Status', choices=[
        ('active', 'Active'), ('pending', 'Pending'), ('terminated', 'Terminated'), ('expired', 'Expired')
    ], validators=[Optional()], default='active')
    property_manager_notes = TextAreaField('Property Manager Notes', validators=[Optional()],
                                         render_kw={"placeholder": "Internal notes for property management team"})
    emergency_contact_name = StringField('Emergency Contact Name', validators=[Optional()],
                                         render_kw={"placeholder": "Full name of emergency contact"})
    emergency_contact_phone = StringField('Emergency Contact Phone', validators=[Optional()],
                                          render_kw={"placeholder": "Phone number for emergency contact"})

    # Advanced Features Fields
    lease_documents = TextAreaField('Lease Documents', validators=[Optional()],
                                  render_kw={"placeholder": "List or description of lease-related documents"})
    compliance_notes = TextAreaField('Compliance & Legal Notes', validators=[Optional()],
                                   render_kw={"placeholder": "Legal compliance requirements and notes"})
    insurance_required = BooleanField('Insurance Required', validators=[Optional()], default=False)
    insurance_verified = BooleanField('Insurance Verified', validators=[Optional()], default=False)
    insurance_expiry_date = DateField('Insurance Expiry Date', validators=[Optional()])
    background_check_status = SelectField('Background Check Status', choices=[
        ('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'), ('not_required', 'Not Required')
    ], validators=[Optional()], default='not_required')
    background_check_date = DateField('Background Check Date', validators=[Optional()])
    credit_score = IntegerField('Credit Score', validators=[Optional(), NumberRange(min=300, max=850)])
    # automatic_renewal_enabled removed - using auto_renewal field instead
    renewal_reminder_days = IntegerField('Renewal Reminder (Days)', validators=[Optional(), NumberRange(min=0, max=365)], default=60)
    violation_history = TextAreaField('Violation History', validators=[Optional()],
                                    render_kw={"placeholder": "Record of lease violations and resolutions"})
    maintenance_requests = TextAreaField('Maintenance Requests Log', validators=[Optional()],
                                       render_kw={"placeholder": "Log of maintenance requests and resolutions"})

class GeneralLeaseForm(FlaskForm):
    property = SelectField('Property', validators=[DataRequired()], render_kw={"data-placeholder": "Choose a property..."})
    tenant = SelectField('Tenant', validators=[DataRequired()], render_kw={"data-placeholder": "Choose a tenant..."})
    unit = SelectField('Unit', validators=[DataRequired()], render_kw={"data-placeholder": "Choose a unit..."})
    start = DateField('Start Date', validators=[DataRequired()])
    end = DateField('End Date', validators=[DataRequired()])
    rent = DecimalField('Monthly Rent', validators=[DataRequired()], places=2)

    # Financial Fields
    security_deposit = DecimalField('Security Deposit', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    pet_deposit = DecimalField('Pet Deposit', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    late_fee = DecimalField('Late Fee Amount', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    payment_due_date = SelectField('Payment Due Date', choices=[
        (1, '1st of month'), (5, '5th of month'), (15, '15th of month'), (30, '30th of month')
    ], coerce=int, validators=[DataRequired()], default=1)
    grace_period_days = IntegerField('Grace Period (Days)', validators=[Optional(), NumberRange(min=0, max=30)], default=5)
    utilities_included = TextAreaField('Utilities Included', validators=[Optional()],
                                     render_kw={"placeholder": "e.g., Water, Sewer, Trash (separate by commas)"})
    parking_fee = DecimalField('Monthly Parking Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)

    # Additional Financial Fields for Comprehensive Tracking
    application_fee = DecimalField('Application Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    broker_fee = DecimalField('Broker/Agent Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    cleaning_fee = DecimalField('Cleaning Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    administrative_fee = DecimalField('Administrative Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    last_month_rent = DecimalField('Last Month Rent (Prepaid)', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    utility_deposits = DecimalField('Utility Deposits', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    storage_fee = DecimalField('Monthly Storage Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    concessions = DecimalField('Rent Concessions/Discounts', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    pet_fee = DecimalField('Monthly Pet Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)

    # Lease Terms Fields
    lease_type = SelectField('Lease Type', choices=[
        ('fixed', 'Fixed Term'), ('month_to_month', 'Month-to-Month'), ('periodic', 'Periodic')
    ], validators=[Optional()], default='fixed')
    auto_renewal = SelectField('Auto Renewal', choices=[
        ('no', 'No Auto Renewal'), ('month_to_month', 'Convert to Month-to-Month'), ('same_term', 'Renew Same Term')
    ], validators=[Optional()], default='no')
    notice_period_days = IntegerField('Notice Period (Days)', validators=[Optional(), NumberRange(min=0, max=365)], default=30)
    early_termination_fee = DecimalField('Early Termination Fee', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    max_occupants = IntegerField('Maximum Occupants', validators=[Optional(), NumberRange(min=1, max=20)], default=2)
    renewal_terms = TextAreaField('Renewal Terms & Conditions', validators=[Optional()],
                                render_kw={"placeholder": "Enter specific terms for lease renewal, rent adjustments, etc."})

    # Operational Details Fields
    move_in_date = DateField('Actual Move-In Date', validators=[Optional()])
    move_out_date = DateField('Actual Move-Out Date', validators=[Optional()])
    key_deposit = DecimalField('Key/Access Deposit', validators=[Optional(), NumberRange(min=0)], default=0, places=2)
    move_in_inspection_notes = TextAreaField('Move-In Inspection Notes', validators=[Optional()],
                                           render_kw={"placeholder": "Document property condition at move-in"})
    move_out_inspection_notes = TextAreaField('Move-Out Inspection Notes', validators=[Optional()],
                                            render_kw={"placeholder": "Document property condition at move-out"})
    lease_status = SelectField('Lease Status', choices=[
        ('active', 'Active'), ('pending', 'Pending'), ('terminated', 'Terminated'), ('expired', 'Expired')
    ], validators=[Optional()], default='active')
    property_manager_notes = TextAreaField('Property Manager Notes', validators=[Optional()],
                                         render_kw={"placeholder": "Internal notes for property management team"})
    emergency_contact_name = StringField('Emergency Contact Name', validators=[Optional()],
                                         render_kw={"placeholder": "Full name of emergency contact"})
    emergency_contact_phone = StringField('Emergency Contact Phone', validators=[Optional()],
                                          render_kw={"placeholder": "Phone number for emergency contact"})

    # Advanced Features Fields
    lease_documents = TextAreaField('Lease Documents', validators=[Optional()],
                                  render_kw={"placeholder": "List or description of lease-related documents"})
    compliance_notes = TextAreaField('Compliance & Legal Notes', validators=[Optional()],
                                   render_kw={"placeholder": "Legal compliance requirements and notes"})
    insurance_required = BooleanField('Insurance Required', validators=[Optional()], default=False)
    insurance_verified = BooleanField('Insurance Verified', validators=[Optional()], default=False)
    insurance_expiry_date = DateField('Insurance Expiry Date', validators=[Optional()])
    background_check_status = SelectField('Background Check Status', choices=[
        ('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'), ('not_required', 'Not Required')
    ], validators=[Optional()], default='not_required')
    background_check_date = DateField('Background Check Date', validators=[Optional()])
    credit_score = IntegerField('Credit Score', validators=[Optional(), NumberRange(min=300, max=850)])
    # automatic_renewal_enabled removed - using auto_renewal field instead
    renewal_reminder_days = IntegerField('Renewal Reminder (Days)', validators=[Optional(), NumberRange(min=0, max=365)], default=60)
    violation_history = TextAreaField('Violation History', validators=[Optional()],
                                    render_kw={"placeholder": "Record of lease violations and resolutions"})
    maintenance_requests = TextAreaField('Maintenance Requests Log', validators=[Optional()],
                                       render_kw={"placeholder": "Log of maintenance requests and resolutions"})