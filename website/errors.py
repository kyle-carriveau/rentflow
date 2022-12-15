from flask import render_template
from flask_login import current_user

# 404 Error Handler
def page_not_found(e):
    return render_template("errors/404.html", user=current_user)