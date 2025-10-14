from flask.app import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, RadioField, SelectMultipleField, PasswordField, BooleanField, TextAreaField, IntegerField, DateField
from wtforms.validators import InputRequired, DataRequired, Length, NoneOf, ValidationError, Email, Regexp, Optional
from website.models import User

# Form for login
class LoginForm(FlaskForm):
    email           = StringField("Email", validators=[InputRequired("Email is required."), DataRequired("Email is required."), Email("Please enter a valid email address.")])
    password        = PasswordField("Password",
                            validators=[
                                InputRequired("Please enter your password"),
                                DataRequired("Password is required"),
                                Length(min=8, max=40, message="Password must be between 8 and 40 characters long")
                            ])
    remember_me     = BooleanField("Remember me")
    login_submit          = SubmitField("Login")

# Form for user registration
class RegistrationForm(FlaskForm):
    first_name          = StringField("First Name", validators=[InputRequired("First Name is required."), DataRequired("First Name is required."), Length(min=1, max=20, message="First Name must be between 1 and 20 characters long")])
    last_name           = StringField("Last Name", validators=[InputRequired("Last Name is required."), DataRequired("Last Name is required."), Length(min=1, max=20, message="Last Name must be between 1 and 20 characters long")])
    company_name        = StringField("Company Name", validators=[InputRequired("Company Name is required."), DataRequired("Company Name is required."), Length(min=1, max=150, message="Company Name must be between 1 and 150 characters long")])
    company_size        = SelectField("Company Size", choices=[
                                ('', 'Select company size'),
                                ('1-10', '1-10 properties'),
                                ('11-50', '11-50 properties'),
                                ('51-100', '51-100 properties'),
                                ('100+', '100+ properties')
                            ], validators=[Optional()])
    email               = StringField("Email", validators=[InputRequired("Email is required."), DataRequired("Email is required."), Email("Please enter a valid email address.")])
    phone               = StringField("Phone Number", validators=[
                                InputRequired("Phone number is required."),
                                DataRequired("Phone number is required."),
                                Regexp(r'^[\+]?[1-9][\d]{0,15}$', message="Please enter a valid phone number.")
                            ])
    primary_role        = SelectField("Primary Role", choices=[
                                ('', 'Select your role'),
                                ('owner', 'Property Owner'),
                                ('manager', 'Property Manager'),
                                ('agent', 'Real Estate Agent'),
                                ('other', 'Other')
                            ], validators=[Optional()])
    password            = PasswordField("Password",
                                validators=[
                                    InputRequired("Please enter your password"),
                                    DataRequired("Password is required"),
                                    Length(min=8, max=40, message="Password must be between 8 and 40 characters long")
                                ])
    password_confirm    = PasswordField("Confirm Password *",
                                validators=[
                                    InputRequired("Input is required!"),
                                    DataRequired("Data is required!")
                                ])
    terms_accepted      = BooleanField("I accept the terms and privacy policy",
                                validators=[InputRequired("You must accept the terms and privacy policy to register.")])
    submit              = SubmitField("Register")

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if email:
            raise ValidationError("Email already exists.")
    
    def validate_password_confirm(self, field):
        if self.password.data != field.data:
            raise ValidationError("Passwords do not match.")