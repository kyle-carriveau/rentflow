#!/usr/bin/env python3
"""
Create Default System Lease Template

This script creates a comprehensive default residential lease template
that all users can access and use as a starting point.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from website import create_app, db
from website.models import LeaseTemplate
import uuid
import json

def create_default_template():
    """Create the default system lease template."""

    app = create_app()

    with app.app_context():
        # Check if default template already exists
        existing = LeaseTemplate.query.filter_by(
            is_system_template=True,
            name="Standard Residential Lease Agreement"
        ).first()

        if existing:
            print("Default template already exists. Updating...")
            template = existing
        else:
            print("Creating new default system template...")
            template = LeaseTemplate()
            template.uuid = str(uuid.uuid4())
            template.company_id = None  # System template
            template.is_system_template = True

        # Template details
        template.name = "Standard Residential Lease Agreement"
        template.description = "Comprehensive residential lease template with standard clauses for rental properties. Includes terms for rent, security deposit, utilities, maintenance responsibilities, and termination conditions."
        template.template_type = "residential"
        template.is_active = True
        template.is_default = False  # Users can make it their default
        template.version = 1

        # Default terms as JSON
        default_terms = {
            "security_deposit_months": 1,
            "late_fee": 50,
            "late_fee_grace_days": 5,
            "notice_period_days": 30,
            "pet_deposit": 0,
            "parking_spaces": 0
        }
        template.default_terms = json.dumps(default_terms)

        # Header text
        template.header_text = """
<div style="text-align: center; margin-bottom: 30px;">
    <h1>RESIDENTIAL LEASE AGREEMENT</h1>
    <p><strong>{{landlord_company}}</strong></p>
</div>
""".strip()

        # Main contract text with comprehensive clauses
        template.contract_text = """
<div style="max-width: 800px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6;">

<p><strong>Date:</strong> {{current_date}}</p>

<h2>1. PARTIES</h2>
<p>This Lease Agreement ("Agreement") is entered into between:</p>
<p><strong>LANDLORD:</strong> {{landlord_name}}, {{landlord_company}}<br>
<strong>TENANT:</strong> {{tenant_name}}<br>
<strong>Email:</strong> {{tenant_email}}<br>
<strong>Phone:</strong> {{tenant_phone}}</p>

<h2>2. PROPERTY</h2>
<p>The Landlord agrees to lease to the Tenant the following residential property:</p>
<p><strong>Property Address:</strong> {{property_address}}<br>
<strong>Unit Number:</strong> {{unit_number}}</p>

<h2>3. LEASE TERM</h2>
<p>The lease term shall commence on <strong>{{start_date}}</strong> and end on <strong>{{end_date}}</strong>, for a total term of <strong>{{lease_term_months}} months</strong>.</p>

<h2>4. RENT</h2>
<p>The monthly rent for the property is <strong>${{rent_amount}}</strong>, payable in advance on the <strong>{{payment_due_date}}</strong> day of each month.</p>
<p>Payment shall be made to the Landlord at the address specified above or via other payment methods designated by the Landlord.</p>

<h2>5. LATE FEES</h2>
<p>If rent is not paid within 5 days of the due date, a late fee of <strong>${{late_fee}}</strong> will be assessed.</p>

<h2>6. SECURITY DEPOSIT</h2>
<p>Upon execution of this Agreement, Tenant shall pay a security deposit of <strong>${{security_deposit}}</strong> to be held by Landlord as security for the performance of Tenant's obligations under this Agreement.</p>
<p>The security deposit shall be returned to Tenant within 30 days after the termination of this Agreement, less any deductions for:</p>
<ul>
    <li>Unpaid rent or other charges</li>
    <li>Cleaning costs to restore the property to move-in condition</li>
    <li>Repairs for damages beyond normal wear and tear</li>
</ul>

<h2>7. UTILITIES AND SERVICES</h2>
<p><strong>Utilities Included:</strong> {{utilities_included}}</p>
<p>Tenant is responsible for all utilities and services not specifically included above, including but not limited to electricity, gas, water, sewer, trash collection, internet, and cable television.</p>

<h2>8. PARKING</h2>
<p>Tenant is allocated <strong>{{parking_spaces}}</strong> parking space(s) at the property. All vehicles must be properly registered and display valid license plates.</p>

<h2>9. PETS</h2>
<p>Pet Deposit: <strong>${{pet_deposit}}</strong></p>
<p>Pets are only permitted with prior written consent from the Landlord. If authorized, an additional pet deposit may be required. Tenant is responsible for any damage caused by pets and must comply with all applicable pet policies.</p>

<h2>10. USE OF PREMISES</h2>
<p>The property shall be used solely as a private residential dwelling. No commercial activities, illegal activities, or activities that disturb the peaceful enjoyment of neighboring residents are permitted.</p>

<h2>11. MAINTENANCE AND REPAIRS</h2>
<p><strong>Landlord's Responsibilities:</strong></p>
<ul>
    <li>Maintain the structural integrity of the property</li>
    <li>Ensure all major systems (plumbing, heating, electrical) are in working order</li>
    <li>Comply with all building and housing codes</li>
    <li>Make necessary repairs in a timely manner when notified</li>
</ul>

<p><strong>Tenant's Responsibilities:</strong></p>
<ul>
    <li>Keep the property clean and sanitary</li>
    <li>Dispose of all garbage and waste properly</li>
    <li>Use appliances and fixtures in a reasonable manner</li>
    <li>Promptly notify Landlord of any maintenance issues or needed repairs</li>
    <li>Replace light bulbs and HVAC filters as needed</li>
    <li>Pay for repairs necessitated by Tenant's negligence or misuse</li>
</ul>

<h2>12. ALTERATIONS</h2>
<p>Tenant shall not make any alterations, additions, or improvements to the property without prior written consent from the Landlord. Any approved alterations become the property of the Landlord upon termination of this Agreement.</p>

<h2>13. ENTRY AND INSPECTION</h2>
<p>Landlord may enter the property for inspection, repairs, or to show the property to prospective tenants or buyers, provided reasonable notice of at least 24 hours is given, except in cases of emergency.</p>

<h2>14. SUBLETTING AND ASSIGNMENT</h2>
<p>Tenant shall not sublet the property or assign this Agreement without the prior written consent of the Landlord. Any unauthorized subletting or assignment is grounds for termination of this Agreement.</p>

<h2>15. INSURANCE</h2>
<p>Tenant is strongly encouraged to obtain renter's insurance to cover personal property and liability. Landlord's insurance does not cover Tenant's personal belongings or liability.</p>

<h2>16. QUIET ENJOYMENT</h2>
<p>Landlord agrees that Tenant, upon payment of rent and performance of all obligations under this Agreement, shall peacefully and quietly have, hold, and enjoy the property during the term of this Agreement.</p>

<h2>17. TERMINATION AND RENEWAL</h2>
<p>This Agreement shall terminate on the end date specified in Section 3 unless:</p>
<ul>
    <li>Both parties agree in writing to renew or extend the lease</li>
    <li>The lease converts to a month-to-month tenancy as permitted by applicable law</li>
    <li>Either party terminates as provided in this Agreement</li>
</ul>

<h2>18. NOTICE TO TERMINATE</h2>
<p>Either party may terminate this Agreement by providing written notice at least 30 days prior to the intended termination date. Early termination by Tenant without proper notice may result in penalties as outlined in applicable law.</p>

<h2>19. ABANDONMENT</h2>
<p>If Tenant abandons the property before the end of the lease term, Landlord may re-rent the property and hold Tenant liable for any unpaid rent, costs of re-renting, and other damages as permitted by law.</p>

<h2>20. DEFAULT AND REMEDIES</h2>
<p>If Tenant fails to pay rent or violates any other term of this Agreement, Landlord may:</p>
<ul>
    <li>Terminate this Agreement and pursue eviction</li>
    <li>Recover unpaid rent and other charges</li>
    <li>Recover damages and legal fees as permitted by law</li>
</ul>

<h2>21. ATTORNEY'S FEES</h2>
<p>If either party brings legal action to enforce this Agreement, the prevailing party shall be entitled to recover reasonable attorney's fees and court costs.</p>

<h2>22. SMOKE-FREE POLICY</h2>
<p>Smoking is prohibited inside the property and within 25 feet of entrances, windows, and ventilation systems. Violation of this policy may result in additional cleaning fees and/or termination of this Agreement.</p>

<h2>23. COMPLIANCE WITH LAWS</h2>
<p>Tenant agrees to comply with all applicable federal, state, and local laws, ordinances, and regulations, including but not limited to housing codes, health and safety regulations, and noise ordinances.</p>

<h2>24. SEVERABILITY</h2>
<p>If any provision of this Agreement is found to be invalid or unenforceable, the remaining provisions shall continue in full force and effect.</p>

<h2>25. ENTIRE AGREEMENT</h2>
<p>This Agreement constitutes the entire agreement between the parties and supersedes all prior negotiations, representations, or agreements. This Agreement may only be modified in writing signed by both parties.</p>

<h2>26. BINDING EFFECT</h2>
<p>This Agreement shall be binding upon and inure to the benefit of the parties and their respective heirs, executors, administrators, successors, and assigns.</p>

<h2>27. GOVERNING LAW</h2>
<p>This Agreement shall be governed by and construed in accordance with the laws of the state in which the property is located.</p>

</div>
""".strip()

        # Footer with signature blocks
        template.footer_text = """
<div style="margin-top: 50px;">
    <h2>SIGNATURES</h2>
    <p>By signing below, the parties acknowledge that they have read, understood, and agree to be bound by all terms and conditions of this Lease Agreement.</p>

    <div style="margin-top: 40px;">
        <p><strong>LANDLORD:</strong></p>
        <p>_________________________________<br>
        {{landlord_name}}<br>
        Date: ________________</p>
    </div>

    <div style="margin-top: 40px;">
        <p><strong>TENANT:</strong></p>
        <p>_________________________________<br>
        {{tenant_name}}<br>
        Date: ________________</p>
    </div>
</div>
""".strip()

        # Available merge fields
        available_fields = [
            'tenant_name', 'tenant_email', 'tenant_phone',
            'landlord_name', 'landlord_company',
            'property_address', 'unit_number',
            'rent_amount', 'security_deposit',
            'start_date', 'end_date', 'lease_term_months',
            'payment_due_date', 'late_fee', 'pet_deposit',
            'parking_spaces', 'utilities_included', 'current_date'
        ]
        template.available_merge_fields = json.dumps(available_fields)

        # Required fields
        required_fields = [
            'tenant_name', 'landlord_name', 'property_address',
            'rent_amount', 'security_deposit', 'start_date', 'end_date'
        ]
        template.required_fields = json.dumps(required_fields)

        # Save to database
        if not existing:
            db.session.add(template)

        db.session.commit()

        print(f"✓ Default lease template created successfully!")
        print(f"  Template UUID: {template.uuid}")
        print(f"  Template Name: {template.name}")
        print(f"  Template Type: {template.template_type}")
        print(f"  System Template: {template.is_system_template}")
        print(f"  Available to all companies: Yes")
        print(f"\nUsers can now access this template when creating leases.")

if __name__ == '__main__':
    create_default_template()
