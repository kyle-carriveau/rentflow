from flask import render_template, Blueprint, jsonify
from flask_login import login_required, current_user
from website.views import get_properties, get_tenants
from website import db
from datetime import datetime, timedelta
from sqlalchemy import func
import calendar

profile = Blueprint('profile', __name__, template_folder='templates')

@profile.route('/dashboard')
@login_required
def dashboard():
    from website.models import Property, Portfolio, Tenant, Lease, Payment, Expense, Unit

    # Get user's data
    company_id = current_user.get_company_id()
    properties = Property.query.filter_by(company_id=company_id).all()
    portfolios = Portfolio.query.filter_by(company_id=company_id).all()
    tenants = Tenant.query.filter_by(company_id=company_id).all()
    today_date = datetime.now().date()
    today = datetime.now()

    # Financial Performance Data (Last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):  # Last 6 months
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Monthly revenue
        monthly_revenue = db.session.query(func.sum(Payment.amount)).join(Lease).join(Unit).join(Property).filter(
            Property.company_id == company_id,
            Payment.payment_date >= month_start,
            Payment.payment_date <= month_end,
            Payment.status == 'completed'
        ).scalar() or 0

        # Monthly expenses
        monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.company_id == company_id,
            Expense.expense_date >= month_start,
            Expense.expense_date <= month_end
        ).scalar() or 0

        monthly_data.append({
            'month': month_date.strftime('%b'),
            'revenue': float(monthly_revenue),
            'expenses': float(monthly_expenses),
            'profit': float(monthly_revenue) - float(monthly_expenses)
        })

    # Lease Expiration Alerts (Next 90 days)
    expiring_soon = today + timedelta(days=90)
    expiring_leases = db.session.query(Lease).join(Unit).join(Property).filter(
        Property.company_id == company_id,
        Lease.end >= today.date(),
        Lease.end <= expiring_soon.date()
    ).order_by(Lease.end).all()

    # Recent Activity (Last 10 actions)
    recent_payments = db.session.query(Payment).join(Lease).join(Unit).join(Property).filter(
        Property.company_id == company_id
    ).order_by(Payment.payment_date.desc()).limit(5).all()

    recent_expenses = db.session.query(Expense).filter(
        Expense.company_id == company_id
    ).order_by(Expense.expense_date.desc()).limit(5).all()

    # Revenue Forecast (Next 6 months based on current leases)
    forecast_data = []
    for i in range(6):
        forecast_month = today + timedelta(days=30*i)
        forecast_start = forecast_month.replace(day=1)
        forecast_end = (forecast_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Get active leases for this period
        active_leases = db.session.query(Lease).join(Unit).join(Property).filter(
            Property.company_id == company_id,
            Lease.start <= forecast_end.date(),
            Lease.end >= forecast_start.date()
        ).all()

        projected_revenue = sum(lease.rent or 0 for lease in active_leases)

        forecast_data.append({
            'month': forecast_month.strftime('%b %Y'),
            'projected_revenue': float(projected_revenue)
        })

    # Occupancy and financial metrics
    total_units = db.session.query(Unit).join(Property).filter(Property.company_id == company_id).count()
    occupied_units = 0
    total_monthly_revenue = 0

    if total_units > 0:
        all_units = db.session.query(Unit).join(Property).filter(Property.company_id == company_id).all()
        for unit in all_units:
            if unit.get_lease_status() == 'Occupied':
                occupied_units += 1
                current_lease = unit.get_current_lease()
                if current_lease and current_lease.rent:
                    total_monthly_revenue += float(current_lease.rent)

    occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

    # Outstanding balance total
    outstanding_total = 0
    active_leases = db.session.query(Lease).join(Unit).join(Property).filter(
        Property.company_id == company_id,
        Lease.start <= today.date(),
        Lease.end >= today.date()
    ).all()

    for lease in active_leases:
        outstanding_total += lease.get_outstanding_balance()

    # Enhanced Financial Analytics using new lease methods
    total_upfront_costs = sum(lease.get_total_upfront_costs() for lease in active_leases)
    total_monthly_recurring = sum(lease.get_monthly_recurring_costs() for lease in active_leases)
    total_net_effective_rent = sum(lease.get_net_effective_rent() for lease in active_leases)

    # Revenue per unit metrics
    revenue_per_unit = (total_monthly_recurring / occupied_units) if occupied_units > 0 else 0

    # Collection rate calculation
    expected_monthly_rent = sum(lease.rent or 0 for lease in active_leases)
    collected_this_month = db.session.query(func.sum(Payment.amount)).join(Lease).join(Unit).join(Property).filter(
        Property.company_id == company_id,
        Payment.payment_date >= today.replace(day=1),
        Payment.payment_date <= today,
        Payment.status == 'completed'
    ).scalar() or 0
    collection_rate = (float(collected_this_month) / float(expected_monthly_rent) * 100) if expected_monthly_rent > 0 else 0

    # Portfolio performance comparison
    portfolio_metrics = []
    for portfolio in portfolios:
        portfolio_properties = [p for p in properties if p.portfolio_id == portfolio.id]
        portfolio_units = db.session.query(Unit).join(Property).filter(
            Property.portfolio_id == portfolio.id,
            Property.company_id == company_id
        ).all()

        portfolio_occupied = sum(1 for unit in portfolio_units if unit.get_lease_status() == 'Occupied')
        portfolio_total_units = len(portfolio_units)
        portfolio_occupancy = (portfolio_occupied / portfolio_total_units * 100) if portfolio_total_units > 0 else 0

        portfolio_leases = db.session.query(Lease).join(Unit).join(Property).filter(
            Property.portfolio_id == portfolio.id,
            Property.company_id == company_id,
            Lease.start <= today.date(),
            Lease.end >= today.date()
        ).all()

        portfolio_revenue = sum(lease.get_monthly_recurring_costs() for lease in portfolio_leases)
        portfolio_net_revenue = sum(lease.get_net_effective_rent() for lease in portfolio_leases)

        portfolio_metrics.append({
            'portfolio': portfolio,
            'properties_count': len(portfolio_properties),
            'total_units': portfolio_total_units,
            'occupied_units': portfolio_occupied,
            'occupancy_rate': portfolio_occupancy,
            'monthly_revenue': portfolio_revenue,
            'net_effective_rent': portfolio_net_revenue,
            'revenue_per_unit': (portfolio_revenue / portfolio_occupied) if portfolio_occupied > 0 else 0
        })

    # Renewal risk assessment
    renewal_risk_leases = []
    for lease in expiring_leases[:10]:  # Top 10 expiring leases
        days_to_expiry = (lease.end - today_date).days
        risk_level = 'high' if days_to_expiry <= 30 else 'medium' if days_to_expiry <= 60 else 'low'

        renewal_risk_leases.append({
            'lease': lease,
            'days_to_expiry': days_to_expiry,
            'risk_level': risk_level,
            'monthly_value': lease.get_monthly_recurring_costs(),
            'total_value': lease.get_total_lease_value()
        })

    # Market insights (comparing to internal averages)
    all_active_rents = [lease.rent for lease in active_leases if lease.rent]
    avg_market_rent = sum(all_active_rents) / len(all_active_rents) if all_active_rents else 0

    # Property performance insights
    property_insights = []
    for property_obj in properties[:5]:  # Top 5 properties
        property_leases = [lease for lease in active_leases if lease.property_id == property_obj.id]
        property_units = db.session.query(Unit).filter_by(property_id=property_obj.id).all()

        if property_leases:
            property_revenue = sum(lease.get_monthly_recurring_costs() for lease in property_leases)
            property_occupied = len(property_leases)
            property_total_units = len(property_units)
            property_occupancy = (property_occupied / property_total_units * 100) if property_total_units > 0 else 0

            # Calculate maintenance costs for this property (last 3 months)
            three_months_ago = today - timedelta(days=90)
            property_maintenance_costs = db.session.query(func.sum(Expense.amount)).filter(
                Expense.company_id == company_id,
                Expense.property_id == property_obj.id,
                Expense.category.in_(['maintenance', 'repairs']),
                Expense.expense_date >= three_months_ago.date()
            ).scalar() or 0

            property_insights.append({
                'property': property_obj,
                'monthly_revenue': property_revenue,
                'occupancy_rate': property_occupancy,
                'maintenance_costs_3m': float(property_maintenance_costs),
                'revenue_per_unit': (property_revenue / property_occupied) if property_occupied > 0 else 0,
                'occupied_units': property_occupied,
                'total_units': property_total_units
            })

    # Sort by revenue for top performers
    property_insights.sort(key=lambda x: x['monthly_revenue'], reverse=True)

    # Maintenance tracking data
    maintenance_items = []
    # Get units with upcoming maintenance
    units_with_maintenance = db.session.query(Unit).join(Property).filter(
        Property.company_id == company_id,
        Unit.upcoming_maintenance.isnot(None),
        Unit.upcoming_maintenance != ''
    ).all()

    for unit in units_with_maintenance:
        maintenance_items.append({
            'type': 'Unit Maintenance',
            'description': unit.upcoming_maintenance,
            'location': f"{unit.property.name} - {unit.unit_number}",
            'priority': 'Medium',
            'property_id': unit.property.id,
            'unit_id': unit.id
        })

    # Get recent maintenance expenses (last 30 days)
    recent_maintenance_expenses = db.session.query(Expense).filter(
        Expense.company_id == company_id,
        Expense.category.in_(['maintenance', 'repairs']),
        Expense.expense_date >= (today - timedelta(days=30)).date()
    ).order_by(Expense.expense_date.desc()).limit(10).all()

    return render_template("dashboard.html",
                         user=current_user,
                         properties=properties,
                         portfolios=portfolios,
                         tenants=tenants,
                         today_date=today_date,
                         monthly_data=monthly_data,
                         expiring_leases=expiring_leases,
                         recent_payments=recent_payments,
                         recent_expenses=recent_expenses,
                         forecast_data=forecast_data,
                         occupancy_rate=occupancy_rate,
                         total_monthly_revenue=total_monthly_revenue,
                         outstanding_total=outstanding_total,
                         maintenance_items=maintenance_items,
                         recent_maintenance_expenses=recent_maintenance_expenses,
                         # Enhanced Analytics
                         total_upfront_costs=total_upfront_costs,
                         total_monthly_recurring=total_monthly_recurring,
                         total_net_effective_rent=total_net_effective_rent,
                         revenue_per_unit=revenue_per_unit,
                         collection_rate=collection_rate,
                         portfolio_metrics=portfolio_metrics,
                         renewal_risk_leases=renewal_risk_leases,
                         avg_market_rent=avg_market_rent,
                         property_insights=property_insights,
                         occupied_units=occupied_units,
                         total_units=total_units)

@profile.route('/')
@login_required
def home():
    return render_template("profile.html", user=current_user, properties=get_properties(), tenants=get_tenants()) 

@profile.route('/settings')
@login_required
def settings():
    return render_template("settings.html", user=current_user)

