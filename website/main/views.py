from flask import render_template, Blueprint
from website.auth.forms import LoginForm

main = Blueprint('main', __name__, template_folder='templates')

@main.route('/')
def landing():
    login_form = LoginForm()
    return render_template("landing.html", login_form=login_form)