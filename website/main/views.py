from flask import render_template, Blueprint
from website.auth.forms import LoginForm, RegistrationForm

main = Blueprint('main', __name__, template_folder='templates')

@main.route('/')
def landing():
    login_form = LoginForm()
    registration_form = RegistrationForm()
    return render_template("landing.html", registration_form=registration_form, login_form=login_form)