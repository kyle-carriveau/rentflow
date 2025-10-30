"""
Forms for Super Admin authentication and operations.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length


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
