# Tenant Portal Architecture

## Security-First Design for RE2/RentFlow

**Version:** 1.0
**Author:** RE2 Development Team
**Date:** April 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Security Architecture](#security-architecture)
3. [Data Model Design](#data-model-design)
4. [Authentication System](#authentication-system)
5. [Authorization & Access Control](#authorization-access-control)
6. [Payment Integration (Stripe)](#payment-integration)
7. [Email Integration (SendGrid)](#email-integration)
8. [User Flows](#user-flows)
9. [API Design](#api-design)
10. [Security Checklist](#security-checklist)

---

## 1. Overview <a name="overview"></a>

### Purpose

The Tenant Portal provides a secure, self-service platform for tenants to:
- View their lease information and payment history
- Make online rent payments via Stripe
- Submit and track maintenance requests
- Access lease documents
- Communicate with property management

### Architecture Decision: Separate TenantUser Model

**Decision:** Create a separate `TenantUser` model rather than extending the existing `User` model.

**Rationale:**
1. **Security Isolation**: Tenants should NEVER have access to landlord-side features
2. **Clean Permission Model**: No risk of role escalation vulnerabilities
3. **Simplified Auditing**: Clear audit trail separation between staff and tenants
4. **Future Scalability**: Tenant-specific features without affecting staff user model
5. **Reduced Attack Surface**: Separate authentication flows reduce lateral movement risk

### Blueprint Structure

```
website/
├── tenant_portal/                    # New blueprint for tenant-facing features
│   ├── __init__.py                   # Blueprint registration
│   ├── views.py                      # Route handlers
│   ├── forms.py                      # WTForms definitions
│   ├── decorators.py                 # Tenant-specific auth decorators
│   ├── utils.py                      # Helper functions
│   └── templates/
│       └── tenant_portal/
│           ├── base.html             # Tenant portal base template
│           ├── login.html
│           ├── register.html
│           ├── dashboard.html
│           ├── pay_rent.html
│           ├── payment_history.html
│           ├── lease_details.html
│           ├── maintenance/
│           │   ├── submit.html
│           │   ├── list.html
│           │   └── detail.html
│           └── documents.html
│
├── webhooks/                         # Stripe webhook handlers
│   ├── __init__.py
│   └── stripe_webhook.py
│
└── services/                         # Business logic services
    ├── __init__.py
    ├── payment_service.py            # Stripe payment processing
    ├── email_service.py              # SendGrid email handling
    └── notification_service.py       # In-app + email notifications
```

---

## 2. Security Architecture <a name="security-architecture"></a>

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────────┐
│                        LAYER 1: NETWORK                        │
│  - HTTPS/TLS 1.3 only (via Cloudflare)                        │
│  - Authenticated Origin Pulls                                  │
│  - Rate limiting at edge                                       │
├─────────────────────────────────────────────────────────────────┤
│                     LAYER 2: APPLICATION                       │
│  - CSRF protection on all forms (Flask-WTF)                   │
│  - Rate limiting (Flask-Limiter with Redis)                   │
│  - Session security (rotation, secure cookies)                 │
│  - Input validation and sanitization                          │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 3: AUTHENTICATION                     │
│  - Secure password hashing (Werkzeug pbkdf2:sha256)           │
│  - Password policy enforcement (8+ chars, complexity)          │
│  - Timing attack prevention                                    │
│  - Brute force protection (rate limits + account lockout)      │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 4: AUTHORIZATION                      │
│  - Tenant-only decorator (blocks staff users)                  │
│  - Data scoping by tenant_id + company_id                     │
│  - Resource ownership validation                               │
│  - No cross-tenant data access                                │
├─────────────────────────────────────────────────────────────────┤
│                       LAYER 5: DATA                            │
│  - Query-level isolation (WHERE tenant_id = ?)                │
│  - No raw SQL (SQLAlchemy ORM only)                           │
│  - Audit logging for sensitive operations                     │
│  - PCI compliance via Stripe (no card data storage)           │
└─────────────────────────────────────────────────────────────────┘
```

### Security Requirements

| Requirement | Implementation | Priority |
|-------------|----------------|----------|
| Authentication | Separate TenantUser model with Flask-Login | CRITICAL |
| Password Security | Same policy as staff (8+ chars, complexity) | CRITICAL |
| Session Management | Secure cookies, rotation, timeout | CRITICAL |
| CSRF Protection | Flask-WTF tokens on all forms | CRITICAL |
| Rate Limiting | Login: 5/min, API: 60/min, Payments: 10/hour | HIGH |
| Input Validation | WTForms + server-side validation | HIGH |
| Data Isolation | tenant_id + company_id scoping | CRITICAL |
| PCI Compliance | Stripe.js (no server-side card handling) | CRITICAL |
| Audit Logging | All payment and auth events | HIGH |
| Error Handling | No stack traces, generic error messages | MEDIUM |

---

## 3. Data Model Design <a name="data-model-design"></a>

### TenantUser Model

```python
class TenantUser(db.Model, UserMixin):
    """
    Separate user model for tenant portal authentication.

    SECURITY NOTES:
    - Completely separate from staff User model
    - Linked to Tenant record via tenant_id
    - No role/permission escalation possible
    - Company-scoped for multi-tenant isolation
    """
    __tablename__ = 'tenant_user'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)

    # Link to existing Tenant record (1:1 relationship)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'),
                          unique=True, nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'),
                           nullable=False, index=True)

    # Authentication
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(1500), nullable=False)

    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verified_at = db.Column(db.DateTime, nullable=True)

    # Security tracking
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)  # IPv6 compatible

    # Invitation tracking
    invitation_token = db.Column(db.String(100), unique=True, nullable=True)
    invitation_sent_at = db.Column(db.DateTime, nullable=True)
    invitation_accepted_at = db.Column(db.DateTime, nullable=True)
    invited_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Stripe customer ID (for saved payment methods)
    stripe_customer_id = db.Column(db.String(100), unique=True, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = db.relationship('Tenant', backref=db.backref('user_account', uselist=False))
    company = db.relationship('Company', backref='tenant_users')
    invited_by = db.relationship('User', foreign_keys=[invited_by_user_id])

    # Table indexes for performance
    __table_args__ = (
        db.Index('idx_tenant_user_email', 'email'),
        db.Index('idx_tenant_user_company', 'company_id'),
        db.Index('idx_tenant_user_active', 'company_id', 'is_active'),
    )
```

### Tenant Model Updates

Add portal access fields to existing Tenant model:

```python
# Add to existing Tenant model
has_portal_access = db.Column(db.Boolean, default=False)
portal_invitation_sent = db.Column(db.DateTime, nullable=True)
portal_invitation_accepted = db.Column(db.DateTime, nullable=True)
```

### MaintenanceRequest Model

```python
class MaintenanceRequest(db.Model):
    """
    Maintenance requests submitted by tenants.

    SECURITY NOTES:
    - Always scoped by company_id AND tenant_id
    - Photo uploads validated and sanitized
    - Internal notes NOT visible to tenants
    """
    __tablename__ = 'maintenance_request'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)

    # Multi-tenant scoping (CRITICAL)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'),
                           nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'),
                          nullable=False, index=True)
    tenant_user_id = db.Column(db.Integer, db.ForeignKey('tenant_user.id'),
                               nullable=False)

    # Property/Unit association
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)

    # Request details
    category = db.Column(db.String(50), nullable=False)  # plumbing, electrical, HVAC, etc.
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, emergency
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Photo attachments (stored as JSON array of secure URLs)
    photos = db.Column(db.JSON, nullable=True)

    # Status tracking
    status = db.Column(db.String(20), default='submitted')
    # Statuses: submitted, acknowledged, assigned, in_progress, completed, closed, cancelled

    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)
    scheduled_date = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)

    # Staff-only fields (NOT exposed to tenant)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)  # NEVER expose to tenant
    estimated_cost = db.Column(db.Numeric(10, 2), nullable=True)
    actual_cost = db.Column(db.Numeric(10, 2), nullable=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=True)

    # Tenant feedback (after completion)
    tenant_feedback = db.Column(db.Text, nullable=True)
    tenant_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars

    # Indexes
    __table_args__ = (
        db.Index('idx_maint_company_status', 'company_id', 'status'),
        db.Index('idx_maint_tenant', 'tenant_id'),
        db.Index('idx_maint_property', 'property_id'),
        db.Index('idx_maint_submitted', 'submitted_at'),
    )
```

### Database Migration Strategy

```sql
-- Migration: Add tenant portal tables
-- Order matters for foreign key constraints

1. Add portal fields to tenant table
2. Create tenant_user table
3. Create maintenance_request table
4. Create vendor table (if not exists)
5. Add indexes for performance
```

---

## 4. Authentication System <a name="authentication-system"></a>

### Flask-Login Integration

Separate user loader for tenant users:

```python
# website/tenant_portal/__init__.py

from flask_login import LoginManager

# Separate login manager for tenant portal
tenant_login_manager = LoginManager()
tenant_login_manager.login_view = 'tenant_portal.login'
tenant_login_manager.login_message = 'Please log in to access the tenant portal.'
tenant_login_manager.login_message_category = 'info'

@tenant_login_manager.user_loader
def load_tenant_user(user_uuid):
    """Load tenant user by UUID."""
    return TenantUser.query.filter_by(uuid=user_uuid, is_active=True).first()
```

### Authentication Endpoints

| Endpoint | Method | Rate Limit | Description |
|----------|--------|------------|-------------|
| `/portal/login` | GET, POST | 5/min | Tenant login |
| `/portal/logout` | GET | - | Logout and session cleanup |
| `/portal/register/<token>` | GET, POST | 10/hour | Accept invitation |
| `/portal/forgot-password` | GET, POST | 3/hour | Request password reset |
| `/portal/reset-password/<token>` | GET, POST | 5/hour | Reset password |

### Security Implementation

```python
# website/tenant_portal/views.py

@tenant_portal.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Tenant portal login with security protections."""
    if current_tenant_user.is_authenticated:
        return redirect(url_for('tenant_portal.dashboard'))

    form = TenantLoginForm()

    if form.validate_on_submit():
        # SECURITY: Timing attack prevention
        DUMMY_HASH = 'pbkdf2:sha256:600000$dummy$hash'

        user = TenantUser.query.filter_by(
            email=form.email.data.lower().strip()
        ).first()

        # Always perform hash check (timing attack prevention)
        if user:
            # Check account lockout
            if user.locked_until and user.locked_until > datetime.utcnow():
                flash('Account temporarily locked. Try again later.', 'error')
                return render_template('tenant_portal/login.html', form=form)

            password_valid = check_password_hash(user.password_hash, form.password.data)
        else:
            check_password_hash(DUMMY_HASH, form.password.data)
            password_valid = False

        if not user or not password_valid:
            # Increment failed attempts
            if user:
                user.failed_login_attempts += 1
                # Lock after 5 failed attempts for 15 minutes
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                db.session.commit()

            # Log failed attempt
            AuditLogger.log_event(
                event_type='tenant_login_failed',
                category='security',
                details={'email': form.email.data},
                severity='warning'
            )

            flash('Invalid email or password.', 'error')
            return redirect(url_for('tenant_portal.login'))

        # Check if account is active
        if not user.is_active:
            flash('Your account has been deactivated. Contact your landlord.', 'error')
            return redirect(url_for('tenant_portal.login'))

        # Successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        user.last_login_ip = request.remote_addr
        db.session.commit()

        # Rotate session ID
        SessionSecurity.rotate_session_id()

        # Log successful login
        AuditLogger.log_event(
            event_type='tenant_login_success',
            category='security',
            resource_type='tenant_user',
            resource_id=user.id,
            details={'ip': request.remote_addr},
            company_id=user.company_id
        )

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        # SECURITY: Validate redirect URL (prevent open redirect)
        if next_page and not is_safe_url(next_page):
            next_page = None

        return redirect(next_page or url_for('tenant_portal.dashboard'))

    return render_template('tenant_portal/login.html', form=form)
```

### Invitation Flow

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Landlord      │      │   System     │      │    Tenant       │
│   (Staff User)  │      │              │      │                 │
└────────┬────────┘      └──────┬───────┘      └────────┬────────┘
         │                      │                       │
         │  1. Invite Tenant    │                       │
         │─────────────────────>│                       │
         │  (email, tenant_id)  │                       │
         │                      │                       │
         │                      │  2. Generate Token    │
         │                      │     (secure random)   │
         │                      │                       │
         │                      │  3. Send Email        │
         │                      │─────────────────────>│
         │                      │  (invitation link)    │
         │                      │                       │
         │                      │  4. Click Link        │
         │                      │<─────────────────────│
         │                      │                       │
         │                      │  5. Validate Token    │
         │                      │     - Not expired     │
         │                      │     - Not used        │
         │                      │     - Tenant exists   │
         │                      │                       │
         │                      │  6. Registration Form │
         │                      │─────────────────────>│
         │                      │  (set password)       │
         │                      │                       │
         │                      │  7. Submit Password   │
         │                      │<─────────────────────│
         │                      │                       │
         │                      │  8. Create TenantUser │
         │                      │     - Hash password   │
         │                      │     - Mark verified   │
         │                      │     - Log event       │
         │                      │                       │
         │                      │  9. Auto-Login        │
         │                      │─────────────────────>│
         │                      │  (redirect dashboard) │
```

---

## 5. Authorization & Access Control <a name="authorization-access-control"></a>

### Decorator Pattern

```python
# website/tenant_portal/decorators.py

from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def tenant_required(f):
    """
    Decorator to ensure request is from authenticated tenant user.

    SECURITY: Blocks all staff users from tenant portal routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated as TenantUser
        if not current_user.is_authenticated:
            return redirect(url_for('tenant_portal.login'))

        # CRITICAL: Block staff users (they use different User model)
        if not isinstance(current_user._get_current_object(), TenantUser):
            abort(403)  # Forbidden - wrong user type

        # Check account is active
        if not current_user.is_active:
            logout_user()
            flash('Your account has been deactivated.', 'error')
            return redirect(url_for('tenant_portal.login'))

        return f(*args, **kwargs)
    return decorated_function


def owns_resource(resource_type):
    """
    Decorator factory to verify tenant owns the requested resource.

    SECURITY: Prevents cross-tenant data access.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            resource_id = kwargs.get('uuid') or kwargs.get('id')

            if resource_type == 'lease':
                resource = Lease.query.filter_by(
                    uuid=resource_id,
                    tenant_id=current_user.tenant_id,
                    company_id=current_user.company_id
                ).first()
            elif resource_type == 'maintenance_request':
                resource = MaintenanceRequest.query.filter_by(
                    uuid=resource_id,
                    tenant_id=current_user.tenant_id,
                    company_id=current_user.company_id
                ).first()
            elif resource_type == 'payment':
                # Payments are linked via lease
                resource = Payment.query.join(Lease).filter(
                    Payment.id == resource_id,
                    Lease.tenant_id == current_user.tenant_id,
                    Payment.company_id == current_user.company_id
                ).first()
            else:
                abort(500)  # Unknown resource type

            if not resource:
                abort(404)  # Resource not found or not owned

            # Inject resource into kwargs
            kwargs[resource_type] = resource
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### Data Access Patterns

**CRITICAL: ALL tenant portal queries MUST include these filters:**

```python
# CORRECT - Always scope by tenant_id AND company_id
leases = Lease.query.filter_by(
    tenant_id=current_user.tenant_id,
    company_id=current_user.company_id
).all()

# WRONG - Missing tenant isolation
leases = Lease.query.filter_by(company_id=current_user.company_id).all()

# WRONG - Missing company isolation
leases = Lease.query.filter_by(tenant_id=current_user.tenant_id).all()

# WRONG - No isolation at all
leases = Lease.query.all()
```

### Access Control Matrix

| Resource | Tenant Can View | Tenant Can Modify | Notes |
|----------|-----------------|-------------------|-------|
| Own Lease Details | Yes | No | Read-only |
| Own Payment History | Yes | No | Read-only |
| Make Payment | Yes | Create only | Via Stripe |
| Own Maintenance Requests | Yes | Create, Update (limited) | Can't delete |
| Request Status | Yes | No | Read-only |
| Lease Documents | Yes | No | Read-only |
| Own Profile | Yes | Limited | Email change needs verification |
| Other Tenants' Data | **NO** | **NO** | **CRITICAL** |
| Staff/Landlord Data | **NO** | **NO** | **CRITICAL** |
| Company Settings | **NO** | **NO** | **CRITICAL** |

---

## 6. Payment Integration (Stripe) <a name="payment-integration"></a>

### PCI Compliance Strategy

**CRITICAL: Never handle card data on our servers.**

```
┌──────────────────────────────────────────────────────────────┐
│                     PCI COMPLIANCE SCOPE                     │
├──────────────────────────────────────────────────────────────┤
│  Our Server (SAQ A eligible - minimal scope):               │
│  - Creates PaymentIntent with amount                        │
│  - Receives webhook confirmations                           │
│  - NEVER sees card numbers, CVV, or full card details       │
│                                                              │
│  Stripe.js (on client):                                     │
│  - Handles all card input                                   │
│  - Tokenizes card data                                      │
│  - Processes payment using client_secret                    │
└──────────────────────────────────────────────────────────────┘
```

### Payment Service Architecture

```python
# website/services/payment_service.py

import stripe
from decimal import Decimal
import os

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

class PaymentService:
    """
    Stripe payment service with security best practices.

    SECURITY NOTES:
    - API key from environment only (never hardcoded)
    - All amounts validated server-side
    - Webhook signature verification required
    - Idempotency keys for duplicate prevention
    """

    @staticmethod
    def create_payment_intent(lease, amount: Decimal, tenant_user: TenantUser):
        """
        Create Stripe PaymentIntent for rent payment.

        SECURITY:
        - Amount validated against lease
        - Metadata includes tenant_id for verification
        - idempotency_key prevents duplicate charges
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > Decimal('99999.99'):
            raise ValueError("Amount exceeds maximum")

        # Ensure tenant owns this lease
        if lease.tenant_id != tenant_user.tenant_id:
            raise PermissionError("Tenant does not own this lease")

        # Get or create Stripe customer
        customer_id = tenant_user.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=tenant_user.email,
                name=f"{tenant_user.tenant.first_name} {tenant_user.tenant.last_name}",
                metadata={
                    'tenant_user_id': tenant_user.id,
                    'tenant_id': tenant_user.tenant_id,
                    'company_id': tenant_user.company_id
                }
            )
            tenant_user.stripe_customer_id = customer.id
            db.session.commit()
            customer_id = customer.id

        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency='usd',
            customer=customer_id,
            description=f"Rent payment for {lease.unit_ref.name}",
            metadata={
                'lease_id': str(lease.id),
                'lease_uuid': str(lease.uuid),
                'tenant_id': str(lease.tenant_id),
                'tenant_user_id': str(tenant_user.id),
                'company_id': str(lease.company_id),
                'property_id': str(lease.property_id)
            },
            # Prevent duplicate charges
            idempotency_key=f"rent-{lease.uuid}-{datetime.utcnow().strftime('%Y%m')}"
        )

        return intent

    @staticmethod
    def verify_webhook_signature(payload, sig_header):
        """
        Verify Stripe webhook signature.

        SECURITY: ALWAYS verify before processing webhooks.
        """
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event
        except stripe.error.SignatureVerificationError:
            return None
```

### Webhook Handler

```python
# website/webhooks/stripe_webhook.py

@webhooks.route('/stripe', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events.

    SECURITY:
    - Signature verification required
    - Idempotent processing (check if already processed)
    - No sensitive data in logs
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    # CRITICAL: Verify signature
    event = PaymentService.verify_webhook_signature(payload, sig_header)
    if not event:
        AuditLogger.log_event(
            event_type='stripe_webhook_invalid_signature',
            category='security',
            severity='warning'
        )
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle events
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']

        # Check idempotency - already processed?
        existing = Payment.query.filter_by(
            stripe_payment_intent_id=payment_intent['id']
        ).first()

        if existing:
            return jsonify({'status': 'already_processed'}), 200

        # Create payment record
        metadata = payment_intent['metadata']

        payment = Payment(
            lease_id=int(metadata['lease_id']),
            property_id=int(metadata['property_id']),
            company_id=int(metadata['company_id']),
            user_id=None,  # Tenant payment, not staff
            amount=Decimal(payment_intent['amount']) / 100,
            payment_method='credit_card',
            payment_date=datetime.utcnow(),
            due_date=datetime.utcnow(),  # Or calculate from lease
            status='completed',
            reference_number=payment_intent['id'],
            notes='Online payment via tenant portal',
            stripe_payment_intent_id=payment_intent['id']
        )

        db.session.add(payment)
        db.session.commit()

        # Send confirmation emails
        NotificationService.send_payment_confirmation(payment)

        # Audit log
        AuditLogger.log_event(
            event_type='tenant_payment_completed',
            category='financial',
            resource_type='payment',
            resource_id=payment.id,
            details={'amount': float(payment.amount)},
            company_id=payment.company_id
        )

    elif event['type'] == 'payment_intent.payment_failed':
        # Log failure, notify tenant
        payment_intent = event['data']['object']

        AuditLogger.log_event(
            event_type='tenant_payment_failed',
            category='financial',
            details={
                'payment_intent_id': payment_intent['id'],
                'error': payment_intent.get('last_payment_error', {}).get('message', 'Unknown')
            },
            severity='warning'
        )

    return jsonify({'status': 'success'}), 200
```

---

## 7. Email Integration (SendGrid) <a name="email-integration"></a>

### Email Service

```python
# website/services/email_service.py

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import os

class EmailService:
    """
    SendGrid email service with security best practices.

    SECURITY:
    - API key from environment
    - No sensitive data in logs
    - Rate limiting on send operations
    - Template IDs prevent injection
    """

    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            api_key = os.environ.get('SENDGRID_API_KEY')
            if not api_key:
                raise RuntimeError("SENDGRID_API_KEY not configured")
            cls._client = SendGridAPIClient(api_key=api_key)
        return cls._client

    @classmethod
    def send_tenant_invitation(cls, tenant, invitation_token, invited_by_user):
        """Send tenant portal invitation email."""
        invitation_url = url_for(
            'tenant_portal.register',
            token=invitation_token,
            _external=True
        )

        message = Mail(
            from_email=Email(os.environ.get('FROM_EMAIL'), 'RentFlow'),
            to_emails=To(tenant.email),
            subject='You\'ve been invited to the RentFlow Tenant Portal'
        )

        message.template_id = os.environ.get('SENDGRID_TENANT_INVITATION_TEMPLATE')
        message.dynamic_template_data = {
            'tenant_name': tenant.first_name,
            'property_name': tenant.get_current_property().name if tenant.get_current_property() else 'your property',
            'company_name': invited_by_user.company_ref.name,
            'invitation_url': invitation_url,
            'expiration_hours': 72  # Token expires in 72 hours
        }

        try:
            response = cls.get_client().send(message)
            return response.status_code == 202
        except Exception as e:
            current_app.logger.error(f"Email send failed: {str(e)}")
            return False

    @classmethod
    def send_payment_confirmation(cls, payment, tenant_user):
        """Send payment confirmation to tenant."""
        message = Mail(
            from_email=Email(os.environ.get('FROM_EMAIL'), 'RentFlow'),
            to_emails=To(tenant_user.email),
            subject=f'Payment Confirmed: ${payment.amount:.2f}'
        )

        message.template_id = os.environ.get('SENDGRID_PAYMENT_CONFIRMATION_TEMPLATE')
        message.dynamic_template_data = {
            'tenant_name': tenant_user.tenant.first_name,
            'amount': f"{payment.amount:.2f}",
            'payment_date': payment.payment_date.strftime('%B %d, %Y'),
            'property_name': payment.property_ref.name,
            'reference_number': payment.reference_number[-12:] if payment.reference_number else 'N/A'
        }

        try:
            response = cls.get_client().send(message)
            return response.status_code == 202
        except Exception as e:
            current_app.logger.error(f"Email send failed: {str(e)}")
            return False
```

---

## 8. User Flows <a name="user-flows"></a>

### Tenant Dashboard Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     TENANT DASHBOARD                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  RENT STATUS     │  │  LEASE INFO      │  │  QUICK       │ │
│  │                  │  │                  │  │  ACTIONS     │ │
│  │  Amount: $1,500  │  │  Unit: #204      │  │              │ │
│  │  Due: Apr 1      │  │  Property: Oak   │  │  [Pay Rent]  │ │
│  │  Status: ✅ Paid │  │  Ends: Dec 31    │  │  [Request]   │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                    PAYMENT HISTORY                         ││
│  ├────────────────────────────────────────────────────────────┤│
│  │  Date       │ Amount  │ Method      │ Status              ││
│  │  Apr 1      │ $1,500  │ Credit Card │ ✅ Completed        ││
│  │  Mar 1      │ $1,500  │ Credit Card │ ✅ Completed        ││
│  │  Feb 1      │ $1,500  │ Credit Card │ ✅ Completed        ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │               MAINTENANCE REQUESTS                         ││
│  ├────────────────────────────────────────────────────────────┤│
│  │  #1042 │ HVAC Issue │ High │ In Progress │ 3 days ago     ││
│  │  #1038 │ Leaky faucet │ Low │ Completed  │ 2 weeks ago    ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Payment Flow

```
Tenant Dashboard → Pay Rent Button
        ↓
    Load payment page
    - Fetch outstanding balance
    - Get/create Stripe customer
    - Create PaymentIntent
        ↓
    Render payment form
    - Display amount
    - Stripe Elements card input
    - Submit button
        ↓
    stripe.confirmCardPayment()
    - Client-side, card never hits our server
        ↓
    Payment succeeds?
    ├── Yes → Redirect to success page
    │         Stripe webhook creates Payment record
    │         Send confirmation email
    │
    └── No → Show error message
             Allow retry
```

---

## 9. API Design <a name="api-design"></a>

### RESTful API Endpoints (Optional for Future Mobile App)

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/v1/tenant/me` | GET | Current tenant profile | Tenant Token |
| `/api/v1/tenant/lease` | GET | Active lease details | Tenant Token |
| `/api/v1/tenant/payments` | GET | Payment history | Tenant Token |
| `/api/v1/tenant/payments/intent` | POST | Create payment intent | Tenant Token |
| `/api/v1/tenant/maintenance` | GET | List maintenance requests | Tenant Token |
| `/api/v1/tenant/maintenance` | POST | Submit new request | Tenant Token |
| `/api/v1/tenant/maintenance/{uuid}` | GET | Request details | Tenant Token |
| `/api/v1/tenant/documents` | GET | List available documents | Tenant Token |

### API Security

```python
# API authentication via JWT tokens (future)
# For now, web portal uses session-based auth

@api_v1.before_request
def verify_api_authentication():
    """Verify API request authentication."""
    if request.endpoint and 'tenant' in request.endpoint:
        # Verify tenant JWT token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401

        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401

        # Load tenant user
        g.current_tenant = TenantUser.query.get(payload['user_id'])
        if not g.current_tenant or not g.current_tenant.is_active:
            return jsonify({'error': 'Account not active'}), 403
```

---

## 10. Security Checklist <a name="security-checklist"></a>

### Pre-Launch Security Review

- [ ] **Authentication**
  - [ ] TenantUser model completely separate from User
  - [ ] Password policy enforced (8+ chars, complexity)
  - [ ] Rate limiting on login (5 per minute)
  - [ ] Account lockout after 5 failed attempts
  - [ ] Timing attack prevention implemented
  - [ ] Session rotation on login
  - [ ] Secure cookie flags (HttpOnly, Secure, SameSite)

- [ ] **Authorization**
  - [ ] `@tenant_required` decorator on all routes
  - [ ] All queries scoped by `tenant_id` AND `company_id`
  - [ ] Resource ownership validated before access
  - [ ] No access to staff/landlord data
  - [ ] No cross-tenant data leakage

- [ ] **Input Validation**
  - [ ] All forms use WTForms with CSRF
  - [ ] Server-side validation for all inputs
  - [ ] File upload validation (type, size, content)
  - [ ] No SQL injection (ORM only, no raw SQL)
  - [ ] XSS prevention (Jinja2 autoescape)

- [ ] **Payment Security**
  - [ ] Stripe.js handles all card input (PCI SAQ A)
  - [ ] No card data stored or logged
  - [ ] Webhook signature verification
  - [ ] Idempotent payment processing
  - [ ] Amount validation server-side

- [ ] **Data Protection**
  - [ ] Audit logging for all sensitive operations
  - [ ] No sensitive data in error messages
  - [ ] No sensitive data in URLs
  - [ ] Secure password reset tokens (time-limited)

- [ ] **Infrastructure**
  - [ ] HTTPS only (TLS 1.2+)
  - [ ] Security headers configured
  - [ ] Rate limiting in place
  - [ ] Redis for session storage (production)
  - [ ] Database backups encrypted

### Test Cases Required

1. **Authentication Tests**
   - Login with valid credentials
   - Login with invalid credentials (timing consistent)
   - Account lockout after failed attempts
   - Password reset flow
   - Session management

2. **Authorization Tests**
   - Tenant cannot access other tenant's data
   - Tenant cannot access staff routes
   - Staff cannot access tenant portal
   - Resource ownership validation

3. **Payment Tests**
   - Successful payment flow
   - Failed payment handling
   - Webhook signature verification
   - Duplicate payment prevention

4. **Input Validation Tests**
   - CSRF protection
   - XSS prevention
   - SQL injection prevention
   - File upload validation

---

## Implementation Priority

### Phase 2A: Core Portal (Week 1-2)
1. TenantUser model + migration
2. Authentication blueprint
3. Tenant dashboard (read-only)

### Phase 2B: Payments (Week 3-4)
1. Stripe integration
2. Payment flow
3. Webhook handler
4. Payment history

### Phase 2C: Maintenance (Week 5-6)
1. MaintenanceRequest model
2. Request submission form
3. Request tracking view
4. Photo upload

### Phase 2D: Email & Polish (Week 7-8)
1. SendGrid integration
2. Email templates
3. Notification system
4. Security review

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04 | RE2 Team | Initial architecture document |
