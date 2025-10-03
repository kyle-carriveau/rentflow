from flask import render_template
from flask_login import current_user

# 404 Error Handler
def page_not_found(e):
    return render_template("errors/404.html", user=current_user), 404

# 403 Error Handler
def forbidden(e):
    return render_template("errors/403.html", user=current_user), 403

# 500 Error Handler
def internal_server_error(e):
    return render_template("errors/500.html", user=current_user), 500