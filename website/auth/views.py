from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from website.models import User, Company
from werkzeug.security import generate_password_hash, check_password_hash
from website import db, limiter
from flask_login import login_user, login_required, logout_user, current_user
from website.auth.forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
auth = Blueprint('auth', __name__, template_folder="templates")

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile.dashboard"))

    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user is None or not user.check_password(login_form.password.data):
            # Log failed login attempt
            from website.session_security import SessionSecurity
            SessionSecurity.log_security_event('login_failed', {'email': login_form.email.data})
            flash("Invalid username or password", category="danger")
            return redirect(url_for("auth.login"))

        # Email verification disabled - skip verification check

        # Successful login
        from flask import session
        from website.session_security import SessionSecurity

        # Set remember me flag in session
        session['remember_me'] = login_form.remember_me.data

        # Rotate session ID for security
        SessionSecurity.rotate_session_id()

        # Log successful login
        SessionSecurity.log_security_event('login_success', {
            'user_id': user.id,
            'remember_me': login_form.remember_me.data
        })

        login_user(user, remember=login_form.remember_me.data)
        return redirect(url_for("profile.dashboard"))
    
    return render_template("login.html", form=login_form)

@auth.route('/logout')
@login_required
def logout():
    from website.session_security import SessionSecurity

    # Log logout event
    SessionSecurity.log_security_event('logout')

    # Clear session data securely
    logout_user()
    SessionSecurity.invalidate_session()

    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("profile.dashboard"))
    register_form = RegistrationForm()
    if register_form.validate_on_submit():
        first_name      = register_form.first_name.data
        last_name       = register_form.last_name.data
        company_name    = register_form.company_name.data
        company_size    = register_form.company_size.data
        email           = register_form.email.data
        phone           = register_form.phone.data
        primary_role    = register_form.primary_role.data
        password        = register_form.password.data

        # Create company with user-provided name and size
        company = Company(name=company_name, email=email)
        if company_size:
            company.company_size = company_size
        db.session.add(company)
        db.session.flush()  # Get company ID without committing

        # Create user with owner role and assign to company
        user = User(first_name=first_name, last_name=last_name, email=email,
                   company_id=company.id, role=User.ROLE_OWNER)

        # Set additional user fields
        if phone:
            user.phone = phone
        if primary_role:
            user.primary_role = primary_role

        # Validate and set password with enhanced policy
        success, errors = user.set_password(password, validate_policy=True)
        if not success:
            # Combine password errors into a single user-friendly message
            if len(errors) == 1:
                flash(errors[0], 'danger')
            else:
                # Create a single consolidated message for multiple errors
                flash('Password does not meet security requirements. Please ensure your password is at least 8 characters long and includes uppercase letters, numbers, and special characters.', 'danger')
            return render_template("register.html", form=register_form)

        db.session.add(user)
        db.session.commit()

        # Email verification disabled - log user in immediately after registration
        flash(f'Account created successfully for {company_name}! Welcome to RE2, {user.first_name}.', 'success')

        # Log successful registration
        from website.session_security import SessionSecurity
        SessionSecurity.log_security_event('user_registration', {
            'user_id': user.id,
            'email': user.email,
            'company_id': user.company_id,
            'auto_login': True
        })

        # Log the user in immediately
        login_user(user, remember=False)
        return redirect(url_for("profile.dashboard"))

    return render_template("register.html", form=register_form)


# Email verification routes removed - verification disabled

@auth.route('/verify-email/<token>')
def verify_email(token):
    """Email verification disabled - redirect to login."""
    flash('Email verification is disabled. You can log in directly.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/verification-sent')
def verification_sent():
    """Email verification disabled - redirect to login."""
    flash('Email verification is disabled. You can log in directly.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Email verification disabled - redirect to login."""
    flash('Email verification is disabled. You can log in directly.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/forgot', methods=['GET', 'POST'])
@limiter.limit("5 per hour")  # Prevent abuse
def forgot():
    """Handle forgot password requests."""
    if current_user.is_authenticated:
        return redirect(url_for('profile.dashboard'))

    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        # Always show success message (prevent email enumeration)
        flash('If an account exists with that email, you will receive password reset instructions.', 'info')

        if user:
            try:
                # Generate secure token
                from website.password_reset import PasswordResetManager
                token = PasswordResetManager.generate_token(user)

                # Send reset email
                from website.email_utils import send_password_reset_email
                send_password_reset_email(user, token)

                # Log password reset request
                from website.audit_logging import AuditLogger
                AuditLogger.log_event(
                    event_type=AuditLogger.EVENT_PASSWORD_RESET_REQUESTED,
                    category=AuditLogger.CATEGORY_SECURITY,
                    resource_type='user',
                    resource_id=user.id,
                    details={'email': user.email},
                    severity='info',
                    company_id=user.company_id
                )

            except Exception as e:
                # Log error but still show success message to user
                import logging
                logging.error(f"Failed to send password reset email: {str(e)}")

        return redirect(url_for('auth.forgot_password_sent'))

    return render_template('forgot-password.html', form=form, user=current_user)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def reset_password(token):
    """Handle password reset with token."""
    if current_user.is_authenticated:
        return redirect(url_for('profile.dashboard'))

    # Verify token
    from website.password_reset import PasswordResetManager
    user, error = PasswordResetManager.verify_token(token)

    if error:
        flash(error, 'danger')
        return redirect(url_for('auth.forgot'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        # Set new password with policy validation
        success, errors = user.set_password(form.password.data, validate_policy=True)

        if not success:
            for err in errors:
                flash(err, 'danger')
            return render_template('reset-password.html', form=form, token=token, user=current_user)

        # Mark token as used
        PasswordResetManager.mark_token_used(token)

        # Save password change
        db.session.commit()

        # Log password reset
        from website.audit_logging import AuditLogger
        AuditLogger.log_event(
            event_type=AuditLogger.EVENT_PASSWORD_CHANGE,
            category=AuditLogger.CATEGORY_SECURITY,
            resource_type='user',
            resource_id=user.id,
            details={'method': 'password_reset_token'},
            severity='warning',
            company_id=user.company_id
        )

        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset-password.html', form=form, token=token, user=current_user)


@auth.route('/forgot-password-sent')
def forgot_password_sent():
    """Confirmation page after requesting password reset."""
    return render_template('forgot-password-sent.html', user=current_user)


@auth.route('/csrf-token', methods=['GET'])
@login_required
def get_csrf_token():
    """Return a fresh CSRF token for AJAX requests."""
    from flask_wtf.csrf import generate_csrf
    return jsonify({'csrf_token': generate_csrf()})