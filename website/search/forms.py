"""
Search Forms

WTForms for advanced filtering and search across the application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, BooleanField, IntegerField
from wtforms.validators import Optional, NumberRange
from wtforms.fields import DateField


class UnitSearchForm(FlaskForm):
    """Advanced unit search form with multiple filter criteria."""

    # Text search
    query = StringField('Search', validators=[Optional()])

    # Bedroom/Bathroom filters
    bedrooms = SelectField(
        'Bedrooms',
        choices=[
            ('', 'Any Bedrooms'),
            ('0', 'Studio'),
            ('1', '1 Bedroom'),
            ('2', '2 Bedrooms'),
            ('3', '3 Bedrooms'),
            ('4', '4+ Bedrooms')
        ],
        validators=[Optional()]
    )

    bathrooms = SelectField(
        'Bathrooms',
        choices=[
            ('', 'Any Bathrooms'),
            ('1', '1 Bath'),
            ('1.5', '1.5 Baths'),
            ('2', '2 Baths'),
            ('2.5', '2.5 Baths'),
            ('3', '3+ Baths')
        ],
        validators=[Optional()]
    )

    # Occupancy status
    occupancy_status = SelectField(
        'Availability',
        choices=[
            ('', 'All Statuses'),
            ('Available', 'Available'),
            ('Occupied', 'Occupied'),
            ('Reserved', 'Reserved'),
            ('Maintenance', 'Maintenance')
        ],
        validators=[Optional()]
    )

    # Property filter
    property_id = SelectField('Property', coerce=str, validators=[Optional()])

    # Rent range
    min_rent = DecimalField('Min Rent', validators=[Optional(), NumberRange(min=0)], places=2)
    max_rent = DecimalField('Max Rent', validators=[Optional(), NumberRange(min=0)], places=2)

    # Square footage
    min_sqft = IntegerField('Min Sq Ft', validators=[Optional(), NumberRange(min=0)])
    max_sqft = IntegerField('Max Sq Ft', validators=[Optional(), NumberRange(min=0)])

    # Amenities
    pets_allowed = BooleanField('Pet Friendly', validators=[Optional()])
    parking_available = BooleanField('Parking Available', validators=[Optional()])
    washer_dryer = BooleanField('Washer/Dryer', validators=[Optional()])
    dishwasher = BooleanField('Dishwasher', validators=[Optional()])
    air_conditioning = BooleanField('Air Conditioning', validators=[Optional()])


class PropertySearchForm(FlaskForm):
    """Property search form."""

    query = StringField('Search', validators=[Optional()])

    property_type = SelectField(
        'Property Type',
        choices=[
            ('', 'All Types'),
            ('Single Family', 'Single Family'),
            ('Multi-Family', 'Multi-Family'),
            ('Apartment', 'Apartment'),
            ('Condo', 'Condo'),
            ('Townhouse', 'Townhouse'),
            ('Commercial', 'Commercial')
        ],
        validators=[Optional()]
    )

    city = StringField('City', validators=[Optional()])
    state = StringField('State', validators=[Optional()])

    occupancy_status = SelectField(
        'Occupancy',
        choices=[
            ('', 'All'),
            ('Vacant', 'Vacant'),
            ('Partially Occupied', 'Partially Occupied'),
            ('Fully Occupied', 'Fully Occupied')
        ],
        validators=[Optional()]
    )

    portfolio_id = SelectField('Portfolio', coerce=str, validators=[Optional()])


class TenantSearchForm(FlaskForm):
    """Tenant search form."""

    query = StringField('Search Name, Email, or Phone', validators=[Optional()])

    lease_status = SelectField(
        'Status',
        choices=[
            ('', 'All Tenants'),
            ('Current', 'Current Tenants'),
            ('Former', 'Former Tenants'),
            ('Prospect', 'Prospects')
        ],
        validators=[Optional()]
    )

    property_id = SelectField('Property', coerce=str, validators=[Optional()])


class LeaseSearchForm(FlaskForm):
    """Lease search form."""

    query = StringField('Search', validators=[Optional()])

    lease_status = SelectField(
        'Status',
        choices=[
            ('', 'All Leases'),
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('terminated', 'Terminated')
        ],
        validators=[Optional()]
    )

    property_id = SelectField('Property', coerce=str, validators=[Optional()])

    start_date_from = DateField('Start Date From', validators=[Optional()], format='%Y-%m-%d')
    start_date_to = DateField('Start Date To', validators=[Optional()], format='%Y-%m-%d')

    end_date_from = DateField('End Date From', validators=[Optional()], format='%Y-%m-%d')
    end_date_to = DateField('End Date To', validators=[Optional()], format='%Y-%m-%d')

    expiring_within_days = SelectField(
        'Expiring Within',
        choices=[
            ('', 'Any Time'),
            ('30', '30 Days'),
            ('60', '60 Days'),
            ('90', '90 Days')
        ],
        validators=[Optional()]
    )


class GlobalSearchForm(FlaskForm):
    """Global search form for searching across all resources."""

    query = StringField('Search', validators=[Optional()])

    resource_type = SelectField(
        'Search In',
        choices=[
            ('all', 'All'),
            ('units', 'Units'),
            ('properties', 'Properties'),
            ('tenants', 'Tenants'),
            ('leases', 'Leases')
        ],
        default='all',
        validators=[Optional()]
    )
