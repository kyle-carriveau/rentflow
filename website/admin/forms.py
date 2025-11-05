"""
Forms for Super Admin authentication and operations.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError, EqualTo


class AdminLoginForm(FlaskForm):
    """Login form for super administrators."""

    username = StringField(
        'Username',
        validators=[
            DataRequired(message="Username is required"),
            Length(min=3, max=50, message="Username must be between 3 and 50 characters")
        ]
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message="Password is required")
        ]
    )

    submit = SubmitField('Login as Admin')


class AdminPasswordChangeForm(FlaskForm):
    """Password change form for super administrators."""

    current_password = PasswordField(
        'Current Password',
        validators=[
            DataRequired(message="Current password is required")
        ]
    )

    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message="New password is required"),
            Length(min=12, message="Admin password must be at least 12 characters long")
        ]
    )

    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message="Please confirm your new password"),
            EqualTo('new_password', message="Passwords must match")
        ]
    )

    submit = SubmitField('Change Password')

    def validate_new_password(self, field):
        """
        Custom validator for new password using admin password policy.

        Requirements:
        - Minimum 12 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains digit
        - Contains special character
        """
        password = field.data

        if not password:
            return

        # Check length (already done by Length validator, but double-check)
        if len(password) < 12:
            raise ValidationError("Admin password must be at least 12 characters long")

        # Check for uppercase letter
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")

        # Check for lowercase letter
        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain at least one lowercase letter")

        # Check for digit
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one digit")

        # Check for special character
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            raise ValidationError("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")


class AdminUserCreateForm(FlaskForm):
    """Form for creating new super administrator accounts."""

    username = StringField(
        'Username',
        validators=[
            DataRequired(message="Username is required"),
            Length(min=3, max=50, message="Username must be between 3 and 50 characters")
        ]
    )

    first_name = StringField(
        'First Name',
        validators=[
            Length(max=100, message="First name cannot exceed 100 characters")
        ]
    )

    last_name = StringField(
        'Last Name',
        validators=[
            Length(max=100, message="Last name cannot exceed 100 characters")
        ]
    )

    email = StringField(
        'Email',
        validators=[
            Length(max=255, message="Email cannot exceed 255 characters")
        ]
    )

    password = PasswordField(
        'Initial Password',
        validators=[
            DataRequired(message="Initial password is required"),
            Length(min=12, message="Admin password must be at least 12 characters long")
        ]
    )

    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message="Please confirm the password"),
            EqualTo('password', message="Passwords must match")
        ]
    )

    notes = StringField(
        'Notes',
        validators=[
            Length(max=500, message="Notes cannot exceed 500 characters")
        ]
    )

    submit = SubmitField('Create Admin Account')

    def validate_password(self, field):
        """
        Custom validator for password using admin password policy.

        Requirements:
        - Minimum 12 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains digit
        - Contains special character
        """
        password = field.data

        if not password:
            return

        # Check length (already done by Length validator, but double-check)
        if len(password) < 12:
            raise ValidationError("Admin password must be at least 12 characters long")

        # Check for uppercase letter
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")

        # Check for lowercase letter
        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain at least one lowercase letter")

        # Check for digit
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one digit")

        # Check for special character
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            raise ValidationError("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
