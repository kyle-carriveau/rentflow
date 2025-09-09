from flask.app import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, RadioField, SelectMultipleField, PasswordField, BooleanField, TextAreaField, IntegerField, DateField
from wtforms.fields import EmailField
from wtforms.validators import InputRequired, DataRequired, Length, NoneOf, ValidationError
from website.models import User

# Form for login
class LoginForm(FlaskForm):
    email           = EmailField("Email", validators=[InputRequired("Email is required."), DataRequired("Email is required.")])
    password_hash   = PasswordField("Password",
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
    email               = EmailField("Email", validators=[InputRequired("Email is required."), DataRequired("Email is required.")])
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
    submit              = SubmitField("Register")

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if email:
            raise ValidationError("Email already exists.")
    
    def validate_password_confirm(self, field):
        if self.password.data != field.data:
            raise ValidationError("Passwords do not match.")