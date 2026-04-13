from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp, Optional, ValidationError


class TenantForm(FlaskForm):
    """Form for creating and editing tenants."""
    first_name = StringField('First Name',
                            validators=[DataRequired(message="First name is required."),
                                      Length(max=100, message="First name must be less than 100 characters.")],
                            render_kw={"placeholder": "First name", "class": "form-control"})

    last_name = StringField('Last Name',
                          validators=[DataRequired(message="Last name is required."),
                                    Length(max=100, message="Last name must be less than 100 characters.")],
                          render_kw={"placeholder": "Last name", "class": "form-control"})

    email = StringField('Email',
                       validators=[DataRequired(message="Email is required."),
                                 Email(message="Please enter a valid email address."),
                                 Length(max=200, message="Email must be less than 200 characters.")],
                       render_kw={"placeholder": "email@example.com", "class": "form-control"})

    phone = StringField('Phone',
                       validators=[DataRequired(message="Phone number is required."),
                                 Regexp(r'^\d{10}$|^[\d\s\-\(\)]+$', message="Please enter a valid 10-digit phone number.")],
                       render_kw={"placeholder": "(555) 123-4567", "class": "form-control"})

    property = SelectField('Property',
                          choices=[],  # Will be populated dynamically
                          validators=[Optional()],
                          render_kw={"class": "form-control"})

    address = StringField('Address',
                         validators=[Optional(), Length(max=200, message="Address must be less than 200 characters.")],
                         render_kw={"placeholder": "Street address", "class": "form-control"})

    city = StringField('City',
                      validators=[Optional(), Length(max=100, message="City must be less than 100 characters.")],
                      render_kw={"placeholder": "City", "class": "form-control"})

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
                       validators=[Optional()],
                       render_kw={"class": "form-control"})

    zip_code = StringField('ZIP Code',
                          validators=[Optional(),
                                    Regexp(r'^\d{5}$', message="ZIP code must be exactly 5 digits.")],
                          render_kw={"placeholder": "12345", "class": "form-control"})

    submit = SubmitField('Save Tenant', render_kw={"class": "btn btn-primary"})

    def __init__(self, properties=None, *args, **kwargs):
        """Initialize form with dynamic property choices."""
        super(TenantForm, self).__init__(*args, **kwargs)
        if properties:
            self.property.choices = [('', 'Select Property')] + [(str(p.id), p.name) for p in properties]
        else:
            self.property.choices = [('', 'Select Property')]

    def validate_phone(self, field):
        """Custom validation to clean and validate phone number."""
        if field.data:
            # Extract only digits
            phone_digits = ''.join(filter(str.isdigit, field.data))
            if len(phone_digits) != 10:
                raise ValidationError('Phone number must be exactly 10 digits.')
            # Update field data to cleaned phone number
            field.data = phone_digits


class TenantCreateForm(TenantForm):
    """Form for creating a new tenant."""
    submit = SubmitField('Create Tenant', render_kw={"class": "btn btn-primary"})


class TenantEditForm(TenantForm):
    """Form for editing an existing tenant."""
    submit = SubmitField('Update Tenant', render_kw={"class": "btn btn-primary"})


class TenantDeleteForm(FlaskForm):
    """Form for deleting a tenant."""
    submit = SubmitField('Delete Tenant', render_kw={"class": "btn btn-danger"})
