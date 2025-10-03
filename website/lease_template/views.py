"""
Lease Template Views

Handles all lease template management operations including CRUD,
preview, and template selection.
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import uuid as uuid_lib

from . import lease_template
from .forms import LeaseTemplateForm, TemplatePreviewForm
from website import db
from website.models import LeaseTemplate
from website.auth_utils import role_required


@lease_template.route('/')
@login_required
def index():
    """List all lease templates."""
    # Get all available templates (company templates + system templates)
    templates = LeaseTemplate.get_available_templates(current_user.company_id)

    # Separate system and company templates
    system_templates = [t for t in templates if t.is_system_template]
    company_templates = [t for t in templates if not t.is_system_template]

    return render_template(
        'templates.html',
        system_templates=system_templates,
        company_templates=company_templates,
        today_date=datetime.now().date()
    )


@lease_template.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def create():
    """Create a new lease template."""
    form = LeaseTemplateForm()

    if form.validate_on_submit():
        # Create new template
        new_template = LeaseTemplate(
            uuid=str(uuid_lib.uuid4()),
            company_id=current_user.company_id,
            name=form.name.data,
            description=form.description.data,
            template_type=form.template_type.data,
            contract_text=form.contract_text.data,
            header_text=form.header_text.data,
            footer_text=form.footer_text.data,
            default_terms=form.default_terms.data,
            is_default=form.is_default.data,
            is_active=form.is_active.data,
            created_by=current_user.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # If setting as default, unset other defaults
        if form.is_default.data:
            LeaseTemplate.query.filter_by(
                company_id=current_user.company_id,
                is_default=True
            ).update({'is_default': False})

        db.session.add(new_template)
        db.session.commit()

        flash('Lease template created successfully!', 'success')
        return redirect(url_for('lease_template.view', uuid=new_template.uuid))

    return render_template('create_edit.html', form=form, mode='create')


@lease_template.route('/<uuid>')
@login_required
def view(uuid):
    """View a specific lease template."""
    template = LeaseTemplate.find_by_uuid(uuid)

    if not template:
        flash('Template not found.', 'error')
        return redirect(url_for('lease_template.index'))

    # Check if user has access (system template or owns the template)
    if not template.is_system_template and template.company_id != current_user.company_id:
        flash('You do not have access to this template.', 'error')
        return redirect(url_for('lease_template.index'))

    # Get merge fields
    available_fields = [
        'tenant_name', 'tenant_email', 'tenant_phone',
        'landlord_name', 'landlord_company',
        'property_address', 'unit_number',
        'rent_amount', 'security_deposit',
        'start_date', 'end_date', 'lease_term_months',
        'payment_due_date', 'late_fee', 'pet_deposit',
        'parking_spaces', 'utilities_included', 'current_date'
    ]

    return render_template(
        'view.html',
        template=template,
        available_fields=available_fields
    )


@lease_template.route('/<uuid>/edit', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def edit(uuid):
    """Edit an existing lease template."""
    template = LeaseTemplate.find_by_uuid(uuid)

    if not template:
        flash('Template not found.', 'error')
        return redirect(url_for('lease_template.index'))

    # Only allow editing company templates (not system templates)
    if template.is_system_template:
        flash('System templates cannot be edited. Create a copy instead.', 'warning')
        return redirect(url_for('lease_template.view', uuid=uuid))

    # Check ownership
    if template.company_id != current_user.company_id:
        flash('You do not have permission to edit this template.', 'error')
        return redirect(url_for('lease_template.index'))

    form = LeaseTemplateForm(obj=template)

    if form.validate_on_submit():
        template.name = form.name.data
        template.description = form.description.data
        template.template_type = form.template_type.data
        template.contract_text = form.contract_text.data
        template.header_text = form.header_text.data
        template.footer_text = form.footer_text.data
        template.default_terms = form.default_terms.data
        template.is_active = form.is_active.data
        template.updated_at = datetime.now()

        # Handle default template setting
        if form.is_default.data and not template.is_default:
            # Unset other defaults
            LeaseTemplate.query.filter_by(
                company_id=current_user.company_id,
                is_default=True
            ).update({'is_default': False})
            template.is_default = True
        elif not form.is_default.data and template.is_default:
            template.is_default = False

        db.session.commit()

        flash('Template updated successfully!', 'success')
        return redirect(url_for('lease_template.view', uuid=template.uuid))

    return render_template('create_edit.html', form=form, mode='edit', template=template)


@lease_template.route('/<uuid>/delete', methods=['POST'])
@login_required
@role_required('manager')
def delete(uuid):
    """Delete a lease template."""
    template = LeaseTemplate.find_by_uuid(uuid)

    if not template:
        flash('Template not found.', 'error')
        return redirect(url_for('lease_template.index'))

    # Only allow deleting company templates
    if template.is_system_template:
        flash('System templates cannot be deleted.', 'error')
        return redirect(url_for('lease_template.index'))

    # Check ownership
    if template.company_id != current_user.company_id:
        flash('You do not have permission to delete this template.', 'error')
        return redirect(url_for('lease_template.index'))

    # Check if template is in use
    if template.usage_count > 0:
        flash(f'This template is currently used by {template.usage_count} lease(s) and cannot be deleted. You can deactivate it instead.', 'warning')
        return redirect(url_for('lease_template.view', uuid=uuid))

    db.session.delete(template)
    db.session.commit()

    flash('Template deleted successfully.', 'success')
    return redirect(url_for('lease_template.index'))


@lease_template.route('/<uuid>/preview', methods=['GET', 'POST'])
@login_required
def preview(uuid):
    """Preview a lease template with sample data."""
    template = LeaseTemplate.find_by_uuid(uuid)

    if not template:
        flash('Template not found.', 'error')
        return redirect(url_for('lease_template.index'))

    # Check access
    if not template.is_system_template and template.company_id != current_user.company_id:
        flash('You do not have access to this template.', 'error')
        return redirect(url_for('lease_template.index'))

    form = TemplatePreviewForm()
    preview_html = None

    if request.method == 'POST':
        # Generate preview with form data
        merge_data = {
            'tenant_name': form.tenant_name.data,
            'tenant_email': form.tenant_email.data,
            'tenant_phone': form.tenant_phone.data,
            'landlord_name': form.landlord_name.data,
            'landlord_company': form.landlord_company.data,
            'property_address': form.property_address.data,
            'unit_number': form.unit_number.data,
            'rent_amount': form.rent_amount.data,
            'security_deposit': form.security_deposit.data,
            'start_date': form.start_date.data,
            'end_date': form.end_date.data,
            'lease_term_months': form.lease_term_months.data,
            'payment_due_date': form.payment_due_date.data,
            'late_fee': form.late_fee.data,
            'pet_deposit': form.pet_deposit.data,
            'parking_spaces': form.parking_spaces.data,
            'utilities_included': form.utilities_included.data,
            'current_date': datetime.now().strftime('%B %d, %Y')
        }

        preview_html = template.populate_template(merge_data)

    return render_template(
        'preview.html',
        template=template,
        form=form,
        preview_html=preview_html
    )


@lease_template.route('/<uuid>/copy', methods=['POST'])
@login_required
@role_required('manager')
def copy_template(uuid):
    """Create a copy of an existing template."""
    original = LeaseTemplate.find_by_uuid(uuid)

    if not original:
        flash('Template not found.', 'error')
        return redirect(url_for('lease_template.index'))

    # Check access
    if not original.is_system_template and original.company_id != current_user.company_id:
        flash('You do not have access to this template.', 'error')
        return redirect(url_for('lease_template.index'))

    # Create copy
    new_template = LeaseTemplate(
        uuid=str(uuid_lib.uuid4()),
        company_id=current_user.company_id,
        name=f"{original.name} (Copy)",
        description=original.description,
        template_type=original.template_type,
        contract_text=original.contract_text,
        header_text=original.header_text,
        footer_text=original.footer_text,
        default_terms=original.default_terms,
        is_default=False,  # Copies are never default
        is_active=True,
        is_system_template=False,  # Copies are always company templates
        version=1,
        parent_template_id=original.id if original.is_system_template else None,
        created_by=current_user.id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.session.add(new_template)
    db.session.commit()

    flash(f'Template copied successfully! You can now edit your copy.', 'success')
    return redirect(url_for('lease_template.edit', uuid=new_template.uuid))


@lease_template.route('/api/available')
@login_required
def api_available_templates():
    """API endpoint to get available templates for lease creation."""
    templates = LeaseTemplate.get_available_templates(current_user.company_id)

    # Only return active templates
    active_templates = [t for t in templates if t.is_active]

    result = [{
        'id': t.id,
        'uuid': t.uuid,
        'name': t.name,
        'description': t.description,
        'template_type': t.template_type,
        'is_default': t.is_default,
        'is_system': t.is_system_template
    } for t in active_templates]

    return jsonify(result)
