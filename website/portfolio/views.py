from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Portfolio
from website import db 
from flask_login import login_required, current_user
from website.views import get_portfolios

portfolio = Blueprint('portfolio', __name__, template_folder='templates')

@portfolio.route('/', methods=['GET', 'POST']) 
@login_required 
def portfolios():
    if request.method == "POST":
        name = request.form.get('portfolio_name')
        new_portfolio = Portfolio(name=name, owner=current_user.id)
        db.session.add(new_portfolio)
        db.session.commit()
        return redirect(url_for('portfolio.portfolios', user=current_user))
    return render_template("portfolios.html", user=current_user, portfolios=get_portfolios())