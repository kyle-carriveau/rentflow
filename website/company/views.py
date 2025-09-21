from flask import render_template, Blueprint, request, redirect, url_for, flash
from website.models import Company
from website import db 
from flask_login import login_required, current_user
from website.errors import page_not_found
from website.auth_utils import owner_required

company = Blueprint('company', __name__, template_folder='templates')

@company.route('/')
@login_required
def profile():
    """Display company profile information."""
    company_id = current_user.get_company_id()
    company_data = Company.query.filter_by(id=company_id).first()
    if not company_data:
        return page_not_found(404)
    
    return render_template("company_profile.html", user=current_user, company=company_data)

@company.route('/edit', methods=['GET', 'POST'])
@login_required
@owner_required
def edit():
    """Edit company profile information (owner only)."""
    company_id = current_user.get_company_id()
    company_data = Company.query.filter_by(id=company_id).first()
    if not company_data:
        return page_not_found(404)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        website = request.form.get('website', '').strip()
        description = request.form.get('description', '').strip()
        
        # Server-side validation
        if not name:
            flash('Company name is required.', 'error')
            return render_template("edit_company.html", user=current_user, company=company_data)
        
        if not email:
            flash('Company email is required.', 'error')
            return render_template("edit_company.html", user=current_user, company=company_data)
        
        # Update company
        company_data.name = name
        company_data.email = email
        company_data.phone = phone
        company_data.address = address
        company_data.city = city
        company_data.state = state
        company_data.zip_code = zip_code
        company_data.website = website
        company_data.description = description
        
        db.session.commit()
        flash('Company information updated successfully!', 'success')
        return redirect(url_for('company.profile'))
    
    return render_template("edit_company.html", user=current_user, company=company_data)