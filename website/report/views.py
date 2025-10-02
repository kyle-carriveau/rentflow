from flask import render_template, Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from website.models import Payment, Expense, Lease, Property, Tenant, Unit, Portfolio
from website import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, extract
from decimal import Decimal
import calendar

report = Blueprint('report', __name__, template_folder='templates')

@report.route('/')
@login_required
def dashboard():
    """Main reporting dashboard with overview analytics."""
    company_id = current_user.get_company_id()

    # Get date range (default to current year)
    year = request.args.get('year', datetime.now().year, type=int)
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)

    # Portfolio performance data
    portfolios = Portfolio.query.filter_by(company_id=company_id).all()
    portfolio_data = []

    for portfolio in portfolios:
        properties_count = Property.query.filter_by(portfolio_id=portfolio.id).count()
        units_count = db.session.query(Unit).join(Property).filter(
            Property.portfolio_id == portfolio.id
        ).count()

        # Calculate portfolio revenue
        revenue = db.session.query(func.sum(Payment.amount)).join(Lease).join(Unit).join(Property).filter(
            Property.portfolio_id == portfolio.id,
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date,
            Payment.status == 'completed'
        ).scalar() or 0

        portfolio_data.append({
            'portfolio': portfolio,
            'properties_count': properties_count,
            'units_count': units_count,
            'revenue': float(revenue)
        })

    # Monthly revenue and expense trends
    monthly_data = []
    for month in range(1, 13):
        month_start = datetime(year, month, 1)
        month_end = datetime(year, month, calendar.monthrange(year, month)[1])

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
            'month': calendar.month_abbr[month],
            'revenue': float(monthly_revenue),
            'expenses': float(monthly_expenses),
            'profit': float(monthly_revenue) - float(monthly_expenses)
        })

    # Occupancy rate calculation
    total_units = db.session.query(Unit).join(Property).filter(Property.company_id == company_id).count()
    occupied_units = 0
    if total_units > 0:
        all_units = db.session.query(Unit).join(Property).filter(Property.company_id == company_id).all()
        occupied_units = sum(1 for unit in all_units if unit.get_lease_status() == 'Occupied')

    occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

    # Top performing properties
    property_performance = db.session.query(
        Property,
        func.sum(Payment.amount).label('total_revenue')
    ).join(Unit).join(Lease).join(Payment).filter(
        Property.company_id == company_id,
        Payment.payment_date >= start_date,
        Payment.payment_date <= end_date,
        Payment.status == 'completed'
    ).group_by(Property.id).order_by(func.sum(Payment.amount).desc()).limit(5).all()

    return render_template(
        'reports/dashboard.html',
        year=year,
        portfolio_data=portfolio_data,
        monthly_data=monthly_data,
        occupancy_rate=occupancy_rate,
        total_units=total_units,
        occupied_units=occupied_units,
        property_performance=property_performance
    )

@report.route('/portfolio-performance')
@login_required
def portfolio_performance():
    """Detailed portfolio performance analysis."""
    company_id = current_user.get_company_id()

    # Get date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    portfolios = Portfolio.query.filter_by(company_id=company_id).all()
    portfolio_analysis = []

    for portfolio in portfolios:
        # Properties and units
        properties = Property.query.filter_by(portfolio_id=portfolio.id).all()
        total_units = sum(len(prop.units) for prop in properties)
        occupied_units = sum(1 for prop in properties for unit in prop.units if unit.get_lease_status() == 'Occupied')

        # Financial performance
        revenue = db.session.query(func.sum(Payment.amount)).join(Lease).join(Unit).join(Property).filter(
            Property.portfolio_id == portfolio.id,
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date,
            Payment.status == 'completed'
        ).scalar() or 0

        expenses = db.session.query(func.sum(Expense.amount)).join(Property).filter(
            Property.portfolio_id == portfolio.id,
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        ).scalar() or 0

        # Calculate metrics
        occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
        net_income = float(revenue) - float(expenses)
        roi = (net_income / float(revenue) * 100) if revenue > 0 else 0

        portfolio_analysis.append({
            'portfolio': portfolio,
            'properties_count': len(properties),
            'total_units': total_units,
            'occupied_units': occupied_units,
            'occupancy_rate': round(occupancy_rate, 1),
            'revenue': float(revenue),
            'expenses': float(expenses),
            'net_income': net_income,
            'roi': round(roi, 1)
        })

    return render_template(
        'reports/portfolio_performance.html',
        portfolio_analysis=portfolio_analysis,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )

@report.route('/financial-trends')
@login_required
def financial_trends():
    """Revenue and expense trend analysis."""
    company_id = current_user.get_company_id()

    # Get parameters
    period = request.args.get('period', 'monthly')  # monthly, quarterly, yearly
    year = request.args.get('year', datetime.now().year, type=int)

    trends_data = []

    if period == 'monthly':
        for month in range(1, 13):
            month_start = datetime(year, month, 1)
            month_end = datetime(year, month, calendar.monthrange(year, month)[1])

            revenue = db.session.query(func.sum(Payment.amount)).join(Lease).join(Unit).join(Property).filter(
                Property.company_id == company_id,
                Payment.payment_date >= month_start,
                Payment.payment_date <= month_end,
                Payment.status == 'completed'
            ).scalar() or 0

            expenses = db.session.query(func.sum(Expense.amount)).filter(
                Expense.company_id == company_id,
                Expense.expense_date >= month_start,
                Expense.expense_date <= month_end
            ).scalar() or 0

            trends_data.append({
                'period': f"{calendar.month_name[month]} {year}",
                'revenue': float(revenue),
                'expenses': float(expenses),
                'profit': float(revenue) - float(expenses)
            })

    elif period == 'quarterly':
        quarters = [(1, 3), (4, 6), (7, 9), (10, 12)]
        for q, (start_month, end_month) in enumerate(quarters, 1):
            quarter_start = datetime(year, start_month, 1)
            quarter_end = datetime(year, end_month, calendar.monthrange(year, end_month)[1])

            revenue = db.session.query(func.sum(Payment.amount)).join(Lease).join(Unit).join(Property).filter(
                Property.company_id == company_id,
                Payment.payment_date >= quarter_start,
                Payment.payment_date <= quarter_end,
                Payment.status == 'completed'
            ).scalar() or 0

            expenses = db.session.query(func.sum(Expense.amount)).filter(
                Expense.company_id == company_id,
                Expense.expense_date >= quarter_start,
                Expense.expense_date <= quarter_end
            ).scalar() or 0

            trends_data.append({
                'period': f"Q{q} {year}",
                'revenue': float(revenue),
                'expenses': float(expenses),
                'profit': float(revenue) - float(expenses)
            })

    return render_template(
        'reports/financial_trends.html',
        trends_data=trends_data,
        period=period,
        year=year
    )

@report.route('/occupancy-tracking')
@login_required
def occupancy_tracking():
    """Occupancy rate tracking over time."""
    company_id = current_user.get_company_id()

    # Get all properties with their units
    properties = Property.query.filter_by(company_id=company_id).all()

    property_occupancy = []
    for property in properties:
        total_units = len(property.units)
        occupied_units = sum(1 for unit in property.units if unit.get_lease_status() == 'Occupied')
        vacancy_rate = ((total_units - occupied_units) / total_units * 100) if total_units > 0 else 0
        occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

        # Calculate average rent for occupied units
        occupied_unit_rents = []
        for unit in property.units:
            if unit.get_lease_status() == 'Occupied':
                current_lease = unit.get_current_lease()
                if current_lease and current_lease.rent:
                    occupied_unit_rents.append(float(current_lease.rent))

        avg_rent = sum(occupied_unit_rents) / len(occupied_unit_rents) if occupied_unit_rents else 0

        property_occupancy.append({
            'property': property,
            'total_units': total_units,
            'occupied_units': occupied_units,
            'vacancy_rate': round(vacancy_rate, 1),
            'occupancy_rate': round(occupancy_rate, 1),
            'avg_rent': round(avg_rent, 2),
            'potential_revenue': round(avg_rent * total_units, 2),
            'actual_revenue': round(avg_rent * occupied_units, 2)
        })

    # Calculate overall occupancy
    total_all_units = sum(data['total_units'] for data in property_occupancy)
    total_occupied_units = sum(data['occupied_units'] for data in property_occupancy)
    overall_occupancy = (total_occupied_units / total_all_units * 100) if total_all_units > 0 else 0

    return render_template(
        'reports/occupancy_tracking.html',
        property_occupancy=property_occupancy,
        overall_occupancy=round(overall_occupancy, 1),
        total_all_units=total_all_units,
        total_occupied_units=total_occupied_units
    )

@report.route('/tenant-payments')
@login_required
def tenant_payments():
    """Tenant payment history and analysis."""
    company_id = current_user.get_company_id()

    # Get date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # Last 3 months
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # Payment analysis by tenant
    payment_analysis = db.session.query(
        Tenant,
        func.sum(Payment.amount).label('total_paid'),
        func.count(Payment.id).label('payment_count'),
        func.max(Payment.payment_date).label('last_payment')
    ).join(Lease).join(Payment).filter(
        Tenant.company_id == company_id,
        Payment.payment_date >= start_date,
        Payment.payment_date <= end_date,
        Payment.status == 'completed'
    ).group_by(Tenant.id).all()

    # Late payments analysis
    late_payments = db.session.query(Payment).join(Lease).join(Tenant).filter(
        Tenant.company_id == company_id,
        Payment.payment_date >= start_date,
        Payment.payment_date <= end_date,
        Payment.status.in_(['late', 'overdue'])
    ).all()

    # Outstanding balances
    outstanding_balances = []
    active_leases = db.session.query(Lease).join(Unit).join(Property).filter(
        Property.company_id == company_id,
        Lease.start <= datetime.now(),
        Lease.end >= datetime.now()
    ).all()

    for lease in active_leases:
        balance = lease.get_outstanding_balance()
        if balance > 0:
            outstanding_balances.append({
                'tenant': lease.tenant,
                'lease': lease,
                'balance': balance,
                'property': lease.unit.property_ref.name if lease.unit.property_ref else 'Unknown',
                'unit': lease.unit.unit_number
            })

    return render_template(
        'reports/tenant_payments.html',
        payment_analysis=payment_analysis,
        late_payments=late_payments,
        outstanding_balances=outstanding_balances,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )

@report.route('/api/revenue-chart')
@login_required
def revenue_chart_api():
    """API endpoint for revenue chart data."""
    company_id = current_user.get_company_id()
    year = request.args.get('year', datetime.now().year, type=int)

    chart_data = []
    for month in range(1, 13):
        month_start = datetime(year, month, 1)
        month_end = datetime(year, month, calendar.monthrange(year, month)[1])

        revenue = db.session.query(func.sum(Payment.amount)).join(Lease).join(Unit).join(Property).filter(
            Property.company_id == company_id,
            Payment.payment_date >= month_start,
            Payment.payment_date <= month_end,
            Payment.status == 'completed'
        ).scalar() or 0

        chart_data.append({
            'month': calendar.month_abbr[month],
            'revenue': float(revenue)
        })

    return jsonify(chart_data)

@report.route('/api/occupancy-chart')
@login_required
def occupancy_chart_api():
    """API endpoint for occupancy chart data."""
    company_id = current_user.get_company_id()

    properties = Property.query.filter_by(company_id=company_id).all()
    chart_data = []

    for property in properties:
        total_units = len(property.units)
        occupied_units = sum(1 for unit in property.units if unit.get_lease_status() == 'Occupied')
        occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

        chart_data.append({
            'property': property.name,
            'occupancy_rate': round(occupancy_rate, 1),
            'occupied_units': occupied_units,
            'total_units': total_units
        })

    return jsonify(chart_data)