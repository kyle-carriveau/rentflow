"""
Email Utility Functions

Provides email sending functionality for the application, including
password reset emails, notifications, and other transactional emails.

Features:
- Asynchronous email sending (non-blocking)
- HTML and plain text email support
- Template rendering with Jinja2
- Error handling and logging
- Flask-Mail integration
"""
from flask import render_template, current_app, url_for
from flask_mail import Message
from website import mail
from threading import Thread
import logging

logger = logging.getLogger(__name__)


def send_async_email(app, msg):
    """
    Send email in background thread to avoid blocking requests.

    Args:
        app: Flask application instance (needed for app context)
        msg: Flask-Mail Message object

    Note:
        This function runs in a separate thread and requires its own
        application context since Flask contexts are thread-local.
    """
    with app.app_context():
        try:
            mail.send(msg)
            logger.info(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            logger.error(f"Failed to send email to {msg.recipients}: {str(e)}")


def send_email(subject, recipients, text_body, html_body, sender=None):
    """
    Send email with both plain text and HTML versions.

    Args:
        subject: Email subject line
        recipients: Email address(es) - str or list of str
        text_body: Plain text email content (fallback)
        html_body: HTML email content (preferred)
        sender: Sender email address (optional, uses config default)

    Returns:
        bool: True if email queued successfully, False on error

    Example:
        send_email(
            subject='Welcome to RentFlow',
            recipients='user@example.com',
            text_body='Welcome!',
            html_body='<h1>Welcome!</h1>'
        )
    """
    try:
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            sender=sender or current_app.config['MAIL_DEFAULT_SENDER']
        )
        msg.body = text_body
        msg.html = html_body

        # Send asynchronously to avoid blocking the request
        Thread(
            target=send_async_email,
            args=(current_app._get_current_object(), msg)
        ).start()

        return True

    except Exception as e:
        logger.error(f"Failed to queue email: {str(e)}")
        return False


def send_password_reset_email(user, token):
    """
    Send password reset email with secure reset link.

    Args:
        user: User instance requesting password reset
        token: Secure reset token (plaintext, for URL)

    Returns:
        bool: True if email queued successfully, False on error

    Security:
        - Uses _external=True for absolute URLs
        - Token is only sent via email, never logged
        - Email templates are in website/templates/emails/

    Example:
        token = PasswordResetManager.generate_token(user)
        if send_password_reset_email(user, token):
            flash('Password reset instructions sent to your email', 'info')
    """
    try:
        # Generate absolute URL for reset link
        reset_url = url_for('auth.reset_password', token=token, _external=True)

        # Render email templates
        text_body = render_template(
            'emails/password_reset.txt',
            user=user,
            reset_url=reset_url
        )
        html_body = render_template(
            'emails/password_reset.html',
            user=user,
            reset_url=reset_url
        )

        # Send email
        return send_email(
            subject='RentFlow - Password Reset Request',
            recipients=user.email,
            text_body=text_body,
            html_body=html_body
        )

    except Exception as e:
        logger.error(f"Failed to send password reset email to user {user.id}: {str(e)}")
        return False


def send_welcome_email(user):
    """
    Send welcome email to newly registered user.

    Args:
        user: User instance who just registered

    Returns:
        bool: True if email queued successfully, False on error

    Note:
        This is a placeholder for future implementation.
        Requires welcome email templates to be created.
    """
    # TODO: Implement welcome email templates
    pass


def send_notification_email(user, subject, message):
    """
    Send generic notification email to user.

    Args:
        user: User instance
        subject: Email subject
        message: Email message (plain text)

    Returns:
        bool: True if email queued successfully, False on error

    Usage:
        send_notification_email(
            user=user,
            subject='Lease Expiring Soon',
            message='Your lease at 123 Main St expires in 30 days.'
        )
    """
    try:
        # Simple plain text email for notifications
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>{subject}</h2>
            <p>Hello {user.first_name},</p>
            <p>{message}</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated notification from RentFlow.
            </p>
        </body>
        </html>
        """

        return send_email(
            subject=f'RentFlow - {subject}',
            recipients=user.email,
            text_body=message,
            html_body=html_body
        )

    except Exception as e:
        logger.error(f"Failed to send notification email to user {user.id}: {str(e)}")
        return False
