from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, BooleanField, SelectField, DateField
from wtforms.validators import DataRequired, Optional, NumberRange

class UnitForm(FlaskForm):
    # Property Selection
    property_id = SelectField('Property', coerce=int, validators=[DataRequired()])

    # Basic Information
    name = StringField('Unit Name/Number', validators=[DataRequired()],
                      render_kw={"placeholder": "e.g., Apt 101, Unit A, etc."})
    bedrooms = IntegerField('Bedrooms', validators=[Optional(), NumberRange(min=0, max=20)], default=0)
    bathrooms = IntegerField('Bathrooms', validators=[Optional(), NumberRange(min=0, max=10)], default=0)
    sqft = IntegerField('Square Feet', validators=[Optional(), NumberRange(min=1, max=10000)])
    rent = IntegerField('Monthly Rent', validators=[Optional(), NumberRange(min=0)])
    description = TextAreaField('Description', validators=[Optional()],
                               render_kw={"placeholder": "General description of the unit", "rows": "3"})

    # HVAC & Climate
    air_conditioning = BooleanField('Air Conditioning', validators=[Optional()], default=False)
    heating_type = SelectField('Heating Type', choices=[
        ('', 'Select heating type'),
        ('gas', 'Gas'), ('electric', 'Electric'), ('heat_pump', 'Heat Pump'),
        ('radiant', 'Radiant'), ('baseboard', 'Baseboard'), ('forced_air', 'Forced Air'),
        ('other', 'Other')
    ], validators=[Optional()])
    thermostat_type = SelectField('Thermostat Type', choices=[
        ('', 'Select thermostat type'),
        ('manual', 'Manual'), ('programmable', 'Programmable'), ('smart', 'Smart')
    ], validators=[Optional()])

    # Appliances & Kitchen
    appliances_included = TextAreaField('Appliances Included', validators=[Optional()],
                                      render_kw={"placeholder": "List included appliances", "rows": "2"})
    dishwasher = BooleanField('Dishwasher', validators=[Optional()], default=False)
    garbage_disposal = BooleanField('Garbage Disposal', validators=[Optional()], default=False)
    microwave = BooleanField('Microwave', validators=[Optional()], default=False)
    refrigerator = BooleanField('Refrigerator', validators=[Optional()], default=False)
    range_oven = BooleanField('Range/Oven', validators=[Optional()], default=False)
    washer_dryer = SelectField('Washer/Dryer', choices=[
        ('', 'Select option'),
        ('in_unit', 'In-Unit'), ('hookups', 'Hook-ups Available'),
        ('shared', 'Shared Laundry'), ('none', 'None')
    ], validators=[Optional()])

    # Flooring & Interior
    flooring_type = TextAreaField('Flooring Types', validators=[Optional()],
                                render_kw={"placeholder": "e.g., Hardwood in living areas, carpet in bedrooms", "rows": "2"})
    ceiling_height = IntegerField('Ceiling Height (feet)', validators=[Optional(), NumberRange(min=6, max=20)])
    windows_type = SelectField('Window Type', choices=[
        ('', 'Select window type'),
        ('single_pane', 'Single-Pane'), ('double_pane', 'Double-Pane'),
        ('triple_pane', 'Triple-Pane'), ('energy_efficient', 'Energy Efficient')
    ], validators=[Optional()])
    natural_light = SelectField('Natural Light', choices=[
        ('', 'Select light level'),
        ('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('limited', 'Limited')
    ], validators=[Optional()])

    # Storage & Space
    closet_space = SelectField('Closet Space', choices=[
        ('', 'Select closet space'),
        ('excellent', 'Excellent'), ('good', 'Good'), ('limited', 'Limited')
    ], validators=[Optional()])
    storage_units = IntegerField('Additional Storage Units', validators=[Optional(), NumberRange(min=0)], default=0)
    balcony_patio = BooleanField('Balcony/Patio', validators=[Optional()], default=False)
    balcony_sqft = IntegerField('Balcony/Patio Sq Ft', validators=[Optional(), NumberRange(min=1)])

    # Parking & Access
    parking_type = SelectField('Parking Type', choices=[
        ('', 'Select parking type'),
        ('garage', 'Garage'), ('covered', 'Covered'), ('open', 'Open Lot'),
        ('street', 'Street Parking'), ('none', 'No Parking')
    ], validators=[Optional()])
    parking_spaces = IntegerField('Parking Spaces', validators=[Optional(), NumberRange(min=0)], default=0)
    garage_type = SelectField('Garage Type', choices=[
        ('', 'Select garage type'),
        ('attached', 'Attached'), ('detached', 'Detached'), ('carport', 'Carport'), ('none', 'None')
    ], validators=[Optional()])

    # Bathroom Features
    bathroom_features = TextAreaField('Bathroom Features', validators=[Optional()],
                                    render_kw={"placeholder": "e.g., Double vanity, jetted tub, walk-in shower", "rows": "2"})
    master_bath = BooleanField('Master Bathroom', validators=[Optional()], default=False)
    bathtub = BooleanField('Bathtub', validators=[Optional()], default=False)
    shower_type = SelectField('Shower Type', choices=[
        ('', 'Select shower type'),
        ('standup', 'Stand-up Shower'), ('combo', 'Shower/Tub Combo'), ('walk_in', 'Walk-in Shower')
    ], validators=[Optional()])

    # Condition & Maintenance
    last_renovated = DateField('Last Renovated', validators=[Optional()])
    condition_rating = SelectField('Condition Rating', choices=[
        ('', 'Select condition'),
        (1, 'Poor (1)'), (2, 'Fair (2)'), (3, 'Good (3)'), (4, 'Very Good (4)'), (5, 'Excellent (5)')
    ], coerce=lambda x: int(x) if x else None, validators=[Optional()])
    recent_updates = TextAreaField('Recent Updates', validators=[Optional()],
                                 render_kw={"placeholder": "Recent renovations or improvements", "rows": "2"})
    upcoming_maintenance = TextAreaField('Upcoming Maintenance', validators=[Optional()],
                                       render_kw={"placeholder": "Scheduled maintenance or repairs", "rows": "2"})

    # Accessibility & Compliance
    ada_compliant = BooleanField('ADA Compliant', validators=[Optional()], default=False)
    wheelchair_accessible = BooleanField('Wheelchair Accessible', validators=[Optional()], default=False)
    accessibility_features = TextAreaField('Accessibility Features', validators=[Optional()],
                                         render_kw={"placeholder": "Ramps, grab bars, wide doorways, etc.", "rows": "2"})

    # Utilities & Energy
    utilities_included = TextAreaField('Utilities Included', validators=[Optional()],
                                     render_kw={"placeholder": "Water, sewer, electric, gas, internet, etc.", "rows": "2"})
    utility_cost_estimate = IntegerField('Monthly Utility Cost Estimate', validators=[Optional(), NumberRange(min=0)])
    energy_efficiency_rating = StringField('Energy Efficiency Rating', validators=[Optional()],
                                         render_kw={"placeholder": "e.g., Energy Star, A+, etc."})

    # Pet Policy
    pets_allowed = BooleanField('Pets Allowed', validators=[Optional()], default=False)
    pet_restrictions = TextAreaField('Pet Restrictions', validators=[Optional()],
                                   render_kw={"placeholder": "Breed, size, number restrictions", "rows": "2"})
    pet_fee_monthly = IntegerField('Monthly Pet Fee', validators=[Optional(), NumberRange(min=0)], default=0)
    pet_deposit = IntegerField('Pet Deposit', validators=[Optional(), NumberRange(min=0)], default=0)

    # Security Features
    security_features = TextAreaField('Security Features', validators=[Optional()],
                                    render_kw={"placeholder": "Security system, cameras, lighting, etc.", "rows": "2"})
    alarm_system = BooleanField('Alarm System', validators=[Optional()], default=False)
    secure_entry = BooleanField('Secure Entry', validators=[Optional()], default=False)

    # Technology & Internet
    internet_included = BooleanField('Internet Included', validators=[Optional()], default=False)
    cable_ready = BooleanField('Cable Ready', validators=[Optional()], default=False)
    internet_speed = StringField('Internet Speed', validators=[Optional()],
                                render_kw={"placeholder": "e.g., 100 Mbps, Fiber, etc."})
    smart_home_features = TextAreaField('Smart Home Features', validators=[Optional()],
                                      render_kw={"placeholder": "Smart locks, thermostats, lighting, etc.", "rows": "2"})