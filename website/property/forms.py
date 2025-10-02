from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, Regexp, ValidationError
from wtforms.widgets import HiddenInput


class PropertyForm(FlaskForm):
    # Basic Information
    name = StringField('Property Name',
                      validators=[DataRequired(message="Property name is required."),
                                Length(max=200, message="Property name must be less than 200 characters.")],
                      render_kw={"placeholder": "Enter property name"})

    type = SelectField('Property Type',
                      choices=[
                          ('', 'Select Property Type'),
                          ('Apartment', 'Apartment'),
                          ('Single-Family Home', 'Single-Family Home'),
                          ('Duplex', 'Duplex'),
                          ('Townhouse', 'Townhouse'),
                          ('Condominium', 'Condominium'),
                          ('Commercial', 'Commercial'),
                          ('Mixed-Use', 'Mixed-Use'),
                          ('Other', 'Other')
                      ],
                      validators=[Optional()])

    portfolio_id = SelectField('Portfolio',
                              choices=[],  # Will be populated dynamically
                              validators=[Optional()])

    description = TextAreaField('Description',
                               validators=[Optional(), Length(max=1000, message="Description must be less than 1000 characters.")],
                               render_kw={"placeholder": "Brief description of the property", "rows": "3"})

    property_status = SelectField('Property Status',
                                 choices=[
                                     ('Active', 'Active'),
                                     ('Inactive', 'Inactive'),
                                     ('Under Maintenance', 'Under Maintenance'),
                                     ('Sold', 'Sold')
                                 ],
                                 default='Active',
                                 validators=[Optional()])

    maintenance_priority = SelectField('Maintenance Priority',
                                     choices=[
                                         ('Low', 'Low'),
                                         ('Medium', 'Medium'),
                                         ('High', 'High'),
                                         ('Critical', 'Critical')
                                     ],
                                     default='Medium',
                                     validators=[Optional()])

    # Location & Address
    address = StringField('Street Address',
                         validators=[Optional(), Length(max=200, message="Address must be less than 200 characters.")],
                         render_kw={"placeholder": "123 Main Street"})

    city = StringField('City',
                      validators=[Optional(), Length(max=100, message="City must be less than 100 characters.")],
                      render_kw={"placeholder": "City name"})

    state = SelectField('State',
                       choices=[
                           ('', 'Select State'),
                           ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
                           ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
                           ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
                           ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
                           ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
                           ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
                           ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
                           ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
                           ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
                           ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
                           ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
                           ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
                           ('WI', 'Wisconsin'), ('WY', 'Wyoming')
                       ],
                       validators=[Optional()])

    zip_code = StringField('ZIP Code',
                          validators=[Optional(),
                                    Regexp(r'^\d{5}(-\d{4})?$', message="ZIP code must be in format 12345 or 12345-6789.")],
                          render_kw={"placeholder": "12345"})

    neighborhood = StringField('Neighborhood',
                              validators=[Optional(), Length(max=100, message="Neighborhood must be less than 100 characters.")],
                              render_kw={"placeholder": "Neighborhood name"})

    latitude = FloatField('Latitude',
                         validators=[Optional(), NumberRange(min=-90, max=90, message="Latitude must be between -90 and 90.")],
                         render_kw={"placeholder": "e.g., 40.7128"})

    longitude = FloatField('Longitude',
                          validators=[Optional(), NumberRange(min=-180, max=180, message="Longitude must be between -180 and 180.")],
                          render_kw={"placeholder": "e.g., -74.0060"})

    # Property Details
    year_built = IntegerField('Year Built',
                             validators=[Optional(), NumberRange(min=1800, max=2030, message="Year built must be between 1800 and 2030.")],
                             render_kw={"placeholder": "e.g., 1995"})

    lot_size = IntegerField('Lot Size (sq ft)',
                           validators=[Optional(), NumberRange(min=1, message="Lot size must be positive.")],
                           render_kw={"placeholder": "e.g., 5000"})

    building_sqft = IntegerField('Building Square Feet',
                                validators=[Optional(), NumberRange(min=1, message="Building square feet must be positive.")],
                                render_kw={"placeholder": "e.g., 2000"})

    stories = IntegerField('Number of Stories',
                          validators=[Optional(), NumberRange(min=1, max=50, message="Stories must be between 1 and 50.")],
                          render_kw={"placeholder": "e.g., 2"})

    parking_spaces = IntegerField('Parking Spaces',
                                 validators=[Optional(), NumberRange(min=0, message="Parking spaces cannot be negative.")],
                                 render_kw={"placeholder": "e.g., 2"})

    # Financial Information
    purchase_price = FloatField('Purchase Price',
                               validators=[Optional(), NumberRange(min=0, message="Purchase price cannot be negative.")],
                               render_kw={"placeholder": "e.g., 250000.00"})

    purchase_date = DateField('Purchase Date',
                             validators=[Optional()],
                             render_kw={"placeholder": "YYYY-MM-DD"})

    current_market_value = FloatField('Current Market Value',
                                     validators=[Optional(), NumberRange(min=0, message="Market value cannot be negative.")],
                                     render_kw={"placeholder": "e.g., 300000.00"})

    annual_property_tax = FloatField('Annual Property Tax',
                                    validators=[Optional(), NumberRange(min=0, message="Property tax cannot be negative.")],
                                    render_kw={"placeholder": "e.g., 5000.00"})

    annual_insurance = FloatField('Annual Insurance',
                                 validators=[Optional(), NumberRange(min=0, message="Insurance cost cannot be negative.")],
                                 render_kw={"placeholder": "e.g., 1200.00"})

    monthly_hoa_fees = FloatField('Monthly HOA Fees',
                                 validators=[Optional(), NumberRange(min=0, message="HOA fees cannot be negative.")],
                                 render_kw={"placeholder": "e.g., 150.00"})

    acquisition_method = SelectField('Acquisition Method',
                                   choices=[
                                       ('', 'Select Method'),
                                       ('Purchase', 'Purchase'),
                                       ('Inheritance', 'Inheritance'),
                                       ('Gift', 'Gift'),
                                       ('Transfer', 'Transfer'),
                                       ('Development', 'Development'),
                                       ('Other', 'Other')
                                   ],
                                   validators=[Optional()])

    # Management & Operations
    property_manager = StringField('Property Manager',
                                  validators=[Optional(), Length(max=100, message="Property manager name must be less than 100 characters.")],
                                  render_kw={"placeholder": "Manager name or company"})

    def __init__(self, portfolios=None, *args, **kwargs):
        """Initialize form with dynamic portfolio choices."""
        super(PropertyForm, self).__init__(*args, **kwargs)
        if portfolios:
            self.portfolio_id.choices = [('', 'Select Portfolio')] + [(p.uuid, p.name) for p in portfolios]
        else:
            self.portfolio_id.choices = [('', 'Select Portfolio')]

    def validate_zip_code(self, field):
        """Custom validation for ZIP code to ensure it's numeric when provided."""
        if field.data:
            # Remove hyphen for validation
            zip_clean = field.data.replace('-', '')
            if not zip_clean.isdigit():
                raise ValidationError('ZIP code must contain only numbers and hyphens.')


class PropertyEditForm(PropertyForm):
    """Extended form for editing existing properties with additional validation."""
    pass