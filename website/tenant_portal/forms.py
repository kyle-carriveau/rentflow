"""
Tenant Portal Forms

All forms use Flask-WTF for CSRF protection.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional


class TenantLoginForm(FlaskForm):
    """Tenant portal login form."""
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.')
    ])
    remember_me = BooleanField('Remember me')


class TenantRegistrationForm(FlaskForm):
    """
    Tenant portal registration form (invitation-based).

    Only used when accepting an invitation - email is pre-filled from invitation.
    """
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])


class TenantForgotPasswordForm(FlaskForm):
    """Tenant password reset request form."""
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.')
    ])


class TenantResetPasswordForm(FlaskForm):
    """Tenant password reset form (with token)."""
    password = PasswordField('New Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])


class MaintenanceRequestForm(FlaskForm):
    """Maintenance request submission form."""
    category = SelectField('Category', validators=[
        DataRequired(message='Please select a category.')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low - Can wait a few days'),
        ('medium', 'Medium - Should be addressed soon'),
        ('high', 'High - Needs attention quickly'),
        ('emergency', 'Emergency - Requires immediate attention')
    ], default='medium', validators=[
        DataRequired(message='Please select a priority.')
    ])
    title = StringField('Brief Description', validators=[
        DataRequired(message='Please provide a brief description.'),
        Length(max=200, message='Description must be less than 200 characters.')
    ])
    description = TextAreaField('Detailed Description', validators=[
        DataRequired(message='Please provide details about the issue.'),
        Length(max=2000, message='Description must be less than 2000 characters.')
    ])
    permission_to_enter = BooleanField('Permission to enter if I\'m not home')
    preferred_entry_time = SelectField('Preferred Time', choices=[
        ('', '-- Select preferred time --'),
        ('morning', 'Morning (8 AM - 12 PM)'),
        ('afternoon', 'Afternoon (12 PM - 5 PM)'),
        ('evening', 'Evening (5 PM - 8 PM)'),
        ('anytime', 'Any time')
    ], validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(MaintenanceRequestForm, self).__init__(*args, **kwargs)
        # Set category choices dynamically
        from website.models import MaintenanceRequest
        self.category.choices = MaintenanceRequest.CATEGORIES


class MaintenanceFeedbackForm(FlaskForm):
    """Tenant feedback form for completed maintenance requests."""
    rating = SelectField('Rating', coerce=int, choices=[
        (5, '5 - Excellent'),
        (4, '4 - Good'),
        (3, '3 - Average'),
        (2, '2 - Poor'),
        (1, '1 - Very Poor')
    ], validators=[DataRequired(message='Please provide a rating.')])
    feedback = TextAreaField('Comments (Optional)', validators=[
        Optional(),
        Length(max=1000, message='Feedback must be less than 1000 characters.')
    ])
