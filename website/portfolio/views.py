from flask import render_template, Blueprint, request, redirect, url_for, flash, jsonify
from website.models import Portfolio, Property, Unit, Lease
from website import db
from flask_login import login_required, current_user
from website.views import get_portfolios
from website.errors import page_not_found
from website.portfolio.forms import PortfolioForm, PortfolioEditForm, PropertyAssignmentForm, PropertyRemovalForm, PortfolioDeleteForm
from sqlalchemy import func, and_
from datetime import datetime

portfolio = Blueprint('portfolio', __name__, template_folder='templates')

@portfolio.route('/', methods=['GET', 'POST'])
@login_required
def portfolios():
    """Display all portfolios with enhanced metrics."""
    form = PortfolioForm()

    if form.validate_on_submit():
        # RBAC: Only Manager and Owner can create portfolios
        if current_user.role not in ['owner', 'manager']:
            flash('You do not have permission to create portfolios.', 'error')
            return redirect(url_for('portfolio.portfolios'))
        company_id = current_user.get_company_id()
        new_portfolio = Portfolio(name=form.name.data, company_id=company_id)
        db.session.add(new_portfolio)
        db.session.commit()
        flash('Portfolio created successfully!', 'success')
        return redirect(url_for('portfolio.portfolios'))

    return render_template("portfolios.html", user=current_user, portfolios=get_enhanced_portfolios(), form=form)

@portfolio.route('/<uuid:uuid>')
@login_required
def home(uuid):
    """View individual portfolio details."""
    company_id = current_user.get_company_id()
    portfolio = Portfolio.find_by_uuid(str(uuid), company_id)
    if not portfolio:
        return page_not_found(404)
    
    # Get portfolio properties with metrics
    properties = Property.query.filter_by(portfolio_id=portfolio.id, company_id=company_id).all()
    unassigned_properties = Property.query.filter_by(portfolio_id=None, company_id=company_id).all()
    
    # Calculate portfolio metrics
    metrics = calculate_portfolio_metrics(portfolio)
    
    return render_template("portfolio_detail.html", 
                         user=current_user, 
                         portfolio=portfolio, 
                         properties=properties,
                         unassigned_properties=unassigned_properties,
                         metrics=metrics)

@portfolio.route('/<uuid:uuid>/edit', methods=['GET', 'POST'])
@login_required
def edit(uuid):
    """Edit portfolio details."""
    company_id = current_user.get_company_id()
    portfolio = Portfolio.find_by_uuid(str(uuid), company_id)
    if not portfolio:
        return page_not_found(404)

    form = PortfolioEditForm(obj=portfolio)

    if form.validate_on_submit():
        portfolio.name = form.name.data
        db.session.commit()
        flash('Portfolio updated successfully!', 'success')
        return redirect(url_for('portfolio.home', uuid=uuid))

    return render_template("edit_portfolio.html", user=current_user, portfolio=portfolio, form=form)

@portfolio.route('/<uuid:uuid>/delete', methods=['POST'])
@login_required
def delete(uuid):
    """Delete a portfolio (moves properties to unassigned)."""
    company_id = current_user.get_company_id()
    portfolio = Portfolio.find_by_uuid(str(uuid), company_id)
    if not portfolio:
        return page_not_found(404)

    form = PortfolioDeleteForm()

    if form.validate_on_submit():
        portfolio_name = portfolio.name

        try:
            # Move all properties in this portfolio to unassigned
            Property.query.filter_by(portfolio_id=portfolio.id, company_id=company_id).update({'portfolio_id': None})
            db.session.delete(portfolio)
            db.session.commit()
            flash(f'Portfolio "{portfolio_name}" deleted. Properties moved to unassigned.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting portfolio.', 'error')

    return redirect(url_for('portfolio.portfolios'))

@portfolio.route('/<uuid:uuid>/assign-property', methods=['POST'])
@login_required
def assign_property(uuid):
    """Assign a property to this portfolio."""
    company_id = current_user.get_company_id()
    portfolio = Portfolio.find_by_uuid(str(uuid), company_id)
    if not portfolio:
        return page_not_found(404)

    form = PropertyAssignmentForm()

    if form.validate_on_submit():
        property_uuid = form.property_uuid.data
        property = Property.find_by_uuid(property_uuid, company_id) if property_uuid else None

        if not property:
            flash('Property not found.', 'error')
            return redirect(url_for('portfolio.home', uuid=uuid))

        property.portfolio_id = portfolio.id
        db.session.commit()
        flash(f'Property "{property.name}" assigned to portfolio "{portfolio.name}".', 'success')

    return redirect(url_for('portfolio.home', uuid=uuid))

@portfolio.route('/<uuid:uuid>/remove-property', methods=['POST'])
@login_required
def remove_property(uuid):
    """Remove a property from this portfolio."""
    company_id = current_user.get_company_id()
    portfolio = Portfolio.find_by_uuid(str(uuid), company_id)
    if not portfolio:
        return page_not_found(404)

    form = PropertyRemovalForm()

    if form.validate_on_submit():
        property_uuid = form.property_uuid.data
        property = Property.find_by_uuid(property_uuid, company_id) if property_uuid else None

        # Additional check to ensure property is in this portfolio
        if property and property.portfolio_id != portfolio.id:
            property = None

        if not property:
            flash('Property not found in this portfolio.', 'error')
            return redirect(url_for('portfolio.home', uuid=uuid))

        property.portfolio_id = None
        db.session.commit()
        flash(f'Property "{property.name}" removed from portfolio.', 'success')

    return redirect(url_for('portfolio.home', uuid=uuid))

def get_enhanced_portfolios():
    """Get portfolios with enhanced metrics."""
    company_id = current_user.get_company_id()
    portfolios = Portfolio.query.filter_by(company_id=company_id).all()
    enhanced_portfolios = []
    
    for portfolio in portfolios:
        metrics = calculate_portfolio_metrics(portfolio)
        enhanced_portfolio = {
            'id': portfolio.id,
            'uuid': portfolio.uuid,
            'name': portfolio.name,
            'property_count': metrics['property_count'],
            'total_units': metrics['total_units'],
            'total_revenue': metrics['total_revenue'],
            'occupancy_rate': metrics['occupancy_rate'],
            'properties': metrics['properties']
        }
        enhanced_portfolios.append(enhanced_portfolio)
    
    return enhanced_portfolios

def calculate_portfolio_metrics(portfolio):
    """Calculate comprehensive metrics for a portfolio."""
    company_id = current_user.get_company_id()
    properties = Property.query.filter_by(portfolio_id=portfolio.id, company_id=company_id).all()
    
    total_units = 0
    total_revenue = 0
    occupied_units = 0
    property_details = []
    
    for property in properties:
        units = Unit.query.filter_by(property_id=property.id, company_id=company_id).all()
        property_revenue = 0
        property_occupied = 0
        
        for unit in units:
            total_units += 1
            # Check for active leases
            active_lease = Lease.query.filter(
                and_(
                    Lease.unit_id == unit.id,
                    Lease.start <= datetime.now().date(),
                    Lease.end >= datetime.now().date()
                )
            ).first()
            
            if active_lease:
                occupied_units += 1
                property_occupied += 1
                total_revenue += active_lease.rent
                property_revenue += active_lease.rent
        
        property_details.append({
            'id': property.id,
            'name': property.name,
            'units': len(units),
            'occupied': property_occupied,
            'revenue': property_revenue,
            'occupancy_rate': (property_occupied / len(units) * 100) if units else 0
        })
    
    return {
        'property_count': len(properties),
        'total_units': total_units,
        'occupied_units': occupied_units,
        'total_revenue': total_revenue,
        'occupancy_rate': (occupied_units / total_units * 100) if total_units > 0 else 0,
        'properties': property_details
    }