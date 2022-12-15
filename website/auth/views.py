from flask import Blueprint, render_template, request, flash, redirect, url_for
from website.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from website import db 
from flask_login import login_user, login_required, logout_user, current_user
from website.auth.forms import LoginForm, RegistrationForm
auth = Blueprint('auth', __name__, template_folder="templates")

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile.home"))

    login_form = LoginForm()
    if login_form.validate_on_submit():
        print('form is validated')
        user = User.query.filter_by(email=login_form.email.data).first()
        if user is None or not user.check_password(login_form.password_hash.data):
            flash("Invalid username or password", category="danger")
            return redirect(url_for("auth.login"))
        login_user(user, remember=login_form.remember_me.data)
        return redirect(url_for("profile.home"))
    
    return render_template("login.html", form=login_form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("profile.home"))
    register_form = RegistrationForm()
    print(register_form.validate_on_submit())
    if register_form.validate_on_submit():
        first_name      = register_form.first_name.data
        last_name       = register_form.last_name.data
        email           = register_form.email.data
        password        = register_form.password.data

        user = User(first_name, last_name, email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        flash('Profile created.', category="success")
        return redirect(url_for("profile.home"))

    return render_template("register.html", form=register_form)

@auth.route('/forgot', methods=['GET', 'POST'])
def forgot():
    return render_template('forgot-password.html', user=current_user)