from flask import render_template, Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from website.models import Payment, Expense, Lease, Property, Tenant
from website import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from decimal import Decimal

financial = Blueprint('financial', __name__, template_folder='templates')

@financial.route('/')
@login_required
def dashboard():
    """Financial dashboard with overview of income and expenses."""
    # Get current month data
    today = datetime.now()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Income summary
    monthly_payments = Payment.query.filter(
        Payment.user_id == current_user.id,
        Payment.status == 'completed',
        Payment.payment_date >= start_of_month,
        Payment.payment_date <= end_of_month
    ).all()
    
    monthly_income = sum(payment.amount for payment in monthly_payments)
    
    # Expense summary
    monthly_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= start_of_month,
        Expense.expense_date <= end_of_month
    ).all()
    
    monthly_expense_total = sum(expense.amount for expense in monthly_expenses)
    
    # Outstanding rent
    overdue_leases = []
    company_id = current_user.get_company_id()
    current_leases = Lease.query.join(Property).filter(
        Property.company_id == company_id,
        Lease.start <= today,
        Lease.end >= today
    ).all()
    
    total_outstanding = 0
    for lease in current_leases:
        balance = lease.get_outstanding_balance()
        if balance > 0:
            overdue_leases.append({
                'lease': lease,
                'balance': balance,
                'tenant': lease.tenant_ref,
                'property': lease.lease_property_ref
            })
            total_outstanding += balance
    
    # Recent transactions
    recent_payments = Payment.query.filter(
        Payment.user_id == current_user.id
    ).order_by(Payment.payment_date.desc()).limit(10).all()
    
    recent_expenses = Expense.query.filter(
        Expense.user_id == current_user.id
    ).order_by(Expense.expense_date.desc()).limit(10).all()
    
    return render_template('financial_dashboard.html',
                         user=current_user,
                         monthly_income=monthly_income,
                         monthly_expense_total=monthly_expense_total,
                         net_income=monthly_income - monthly_expense_total,
                         total_outstanding=total_outstanding,
                         overdue_leases=overdue_leases,
                         recent_payments=recent_payments,
                         recent_expenses=recent_expenses,
                         current_month=today.strftime('%B %Y'))

@financial.route('/payments')
@login_required
def payments():
    """View all payments."""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    property_filter = request.args.get('property', 'all')
    
    query = Payment.query.filter(Payment.user_id == current_user.id)
    
    if status_filter != 'all':
        query = query.filter(Payment.status == status_filter)
    
    if property_filter != 'all':
        query = query.filter(Payment.property_id == property_filter)
    
    payments = query.order_by(Payment.payment_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    company_id = current_user.get_company_id()
    properties = Property.query.filter_by(company_id=company_id).all()
    
    return render_template('payments.html',
                         user=current_user,
                         payments=payments,
                         properties=properties,
                         status_filter=status_filter,
                         property_filter=property_filter)

@financial.route('/payments/record', methods=['GET', 'POST'])
@login_required
def record_payment():
    """Record a new payment."""
    if request.method == 'POST':
        lease_id = request.form.get('lease_id')
        amount = request.form.get('amount')
        payment_date = request.form.get('payment_date')
        payment_method = request.form.get('payment_method', 'cash')
        reference_number = request.form.get('reference_number', '')
        notes = request.form.get('notes', '')
        
        # Enhanced validation with specific error messages
        errors = []
        
        if not lease_id:
            errors.append('Please select a lease.')
        if not amount:
            errors.append('Please enter a payment amount.')
        elif not amount.replace('.', '').isdigit() or float(amount) <= 0:
            errors.append('Please enter a valid payment amount greater than 0.')
        if not payment_date:
            errors.append('Please select a payment date.')
            
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('financial.record_payment'))
        
        try:
            # Validate lease exists and belongs to user
            lease = Lease.query.filter_by(id=lease_id).first()
            if not lease:
                flash('The selected lease could not be found.', 'error')
                return redirect(url_for('financial.record_payment'))
                
            if lease.lease_property_ref.company_id != current_user.get_company_id():
                flash('You do not have permission to record payments for this lease.', 'error')
                return redirect(url_for('financial.record_payment'))
            
            # Validate amount
            payment_amount = Decimal(amount)
            if payment_amount > 99999.99:
                flash('Payment amount cannot exceed $99,999.99.', 'error')
                return redirect(url_for('financial.record_payment'))
            
            # Validate date
            try:
                payment_date_obj = datetime.strptime(payment_date, '%Y-%m-%d')
            except ValueError:
                flash('Please enter a valid payment date.', 'error')
                return redirect(url_for('financial.record_payment'))
            
            # Create payment record
            payment = Payment(
                lease_id=lease_id,
                property_id=lease.property_id,
                user_id=current_user.id,
                amount=payment_amount,
                payment_date=payment_date_obj,
                due_date=payment_date_obj,  # Simplified for now
                payment_method=payment_method,
                reference_number=reference_number.strip() if reference_number else '',
                notes=notes.strip() if notes else '',
                status='completed'
            )
            
            db.session.add(payment)
            db.session.commit()
            
            # Success message with details
            tenant_name = f"{lease.tenant_ref.first_name} {lease.tenant_ref.last_name}"
            flash(f'Payment of ${payment_amount:,.2f} recorded successfully for {tenant_name}.', 'success')
            return redirect(url_for('financial.payments'))
            
        except ValueError as e:
            db.session.rollback()
            flash('Invalid payment amount format. Please enter a valid number.', 'error')
            return redirect(url_for('financial.record_payment'))
        except Exception as e:
            db.session.rollback()
            flash('An unexpected error occurred while recording the payment. Please try again.', 'error')
            return redirect(url_for('financial.record_payment'))
    
    # GET request - show form
    company_id = current_user.get_company_id()
    active_leases = Lease.query.join(Property).filter(
        Property.company_id == company_id,
        Lease.start <= datetime.now(),
        Lease.end >= datetime.now()
    ).all()
    
    return render_template('record_payment.html',
                         user=current_user,
                         leases=active_leases,
                         today=datetime.now().strftime('%Y-%m-%d'))

@financial.route('/expenses')
@login_required
def expenses():
    """View all expenses."""
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', 'all')
    property_filter = request.args.get('property', 'all')
    
    query = Expense.query.filter(Expense.user_id == current_user.id)
    
    if category_filter != 'all':
        query = query.filter(Expense.category == category_filter)
    
    if property_filter != 'all':
        if property_filter == 'general':
            query = query.filter(Expense.property_id.is_(None))
        else:
            query = query.filter(Expense.property_id == property_filter)
    
    expenses = query.order_by(Expense.expense_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    company_id = current_user.get_company_id()
    properties = Property.query.filter_by(company_id=company_id).all()
    categories = Expense.get_categories()
    
    return render_template('expenses.html',
                         user=current_user,
                         expenses=expenses,
                         properties=properties,
                         categories=categories,
                         category_filter=category_filter,
                         property_filter=property_filter)

@financial.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Add a new expense."""
    if request.method == 'POST':
        amount = request.form.get('amount')
        expense_date = request.form.get('expense_date')
        category = request.form.get('category')
        subcategory = request.form.get('subcategory', '')
        description = request.form.get('description')
        vendor = request.form.get('vendor', '')
        property_id = request.form.get('property_id')
        reference_number = request.form.get('reference_number', '')
        notes = request.form.get('notes', '')
        tax_deductible = bool(request.form.get('tax_deductible'))
        
        # Validation
        if not all([amount, expense_date, category, description]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('financial.add_expense'))
        
        try:
            expense = Expense(
                user_id=current_user.id,
                property_id=int(property_id) if property_id and property_id != 'general' else None,
                amount=Decimal(amount),
                expense_date=datetime.strptime(expense_date, '%Y-%m-%d'),
                category=category,
                subcategory=subcategory,
                description=description,
                vendor=vendor,
                reference_number=reference_number,
                notes=notes,
                tax_deductible=tax_deductible
            )
            
            db.session.add(expense)
            db.session.commit()
            flash('Expense added successfully!', 'success')
            return redirect(url_for('financial.expenses'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error adding expense. Please try again.', 'error')
            return redirect(url_for('financial.add_expense'))
    
    # GET request - show form
    company_id = current_user.get_company_id()
    properties = Property.query.filter_by(company_id=company_id).all()
    categories = Expense.get_categories()
    
    return render_template('add_expense.html',
                         user=current_user,
                         properties=properties,
                         categories=categories)

@financial.route('/reports')
@login_required
def reports():
    """Financial reports and analytics."""
    # Year-to-date summary
    year_start = datetime.now().replace(month=1, day=1)
    
    ytd_income = db.session.query(func.sum(Payment.amount)).filter(
        Payment.user_id == current_user.id,
        Payment.status == 'completed',
        Payment.payment_date >= year_start
    ).scalar() or 0
    
    ytd_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= year_start
    ).scalar() or 0
    
    # Monthly breakdown for chart
    monthly_data = []
    for month in range(1, 13):
        month_start = datetime.now().replace(month=month, day=1)
        if month == 12:
            month_end = datetime.now().replace(year=datetime.now().year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = datetime.now().replace(month=month + 1, day=1) - timedelta(days=1)
        
        if month_start > datetime.now():
            break
            
        income = db.session.query(func.sum(Payment.amount)).filter(
            Payment.user_id == current_user.id,
            Payment.status == 'completed',
            Payment.payment_date >= month_start,
            Payment.payment_date <= month_end
        ).scalar() or 0
        
        expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.expense_date >= month_start,
            Expense.expense_date <= month_end
        ).scalar() or 0
        
        monthly_data.append({
            'month': month_start.strftime('%B'),
            'income': float(income),
            'expenses': float(expenses),
            'net': float(income - expenses)
        })
    
    # Expense breakdown by category
    expense_categories = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == current_user.id,
        Expense.expense_date >= year_start
    ).group_by(Expense.category).all()
    
    return render_template('financial_reports.html',
                         user=current_user,
                         ytd_income=ytd_income,
                         ytd_expenses=ytd_expenses,
                         ytd_net=ytd_income - ytd_expenses,
                         monthly_data=monthly_data,
                         expense_categories=expense_categories)