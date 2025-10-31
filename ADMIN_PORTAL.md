# Super Admin Portal - God View Dashboard

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
- [Managing Admin Accounts](#managing-admin-accounts)
- [Dashboard Features](#dashboard-features)
- [Security & Compliance](#security--compliance)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Overview

### What is the Super Admin Portal?

The Super Admin Portal is a **read-only system administration interface** that provides complete visibility into all companies, users, properties, and assets across the entire RentFlow multi-tenant application.

### Key Characteristics

- **🔒 Separate Authentication**: Completely isolated from regular user login system
- **👁️ Read-Only Access**: Admins can view all data but cannot modify anything
- **📊 System-Wide Visibility**: See data across all companies (bypasses company_id filtering)
- **📝 Complete Audit Trail**: Every admin action is logged for security and compliance
- **🎨 Visual Distinction**: Dark theme separates admin portal from user interface
- **🚫 No Multi-Tenant Restrictions**: Super admins exist outside the company system

### Use Cases

- Monitor overall system health and usage
- Track company signups and growth
- Analyze user distribution across companies
- Monitor property portfolio across all companies
- Investigate support requests with full data visibility
- Generate system-wide analytics and reports
- Compliance and security auditing

---

## Getting Started

### Prerequisites

- Deployment must be completed (Docker containers running)
- Database migrations must be applied
- CLI access to the production/staging server

### Initial Setup

#### Step 1: Create Your First Admin Account

**On Local Development:**
```bash
# Activate virtual environment
source reenv312/bin/activate

# Create admin account
flask admin-cli create-admin
```

**On Production/Staging (Docker):**
```bash
# Navigate to project directory
cd /path/to/re2

# Create admin account via Docker
docker compose -f deployment/docker/docker-compose.yml exec web flask admin-cli create-admin
```

**Interactive Prompts:**
```
Username: admin
Password: [hidden input]
Repeat for confirmation: [hidden input]
First name (optional): John
Last name (optional): Doe
Email (optional): admin@yourcompany.com

✓ Super Admin created successfully!
  Username: admin
  Name: John Doe
  Email: admin@yourcompany.com
  Status: Active

You can now log in at /admin/login
```

#### Step 2: Access the Admin Portal

Navigate to the admin login page:
- **Local**: `http://localhost:5000/admin/login`
- **Staging**: `https://staging.yourdomain.com/admin/login`
- **Production**: `https://yourdomain.com/admin/login`

#### Step 3: Log In

1. Enter your admin username (not email)
2. Enter your admin password
3. Click "Login as Admin"

**Note:** Admin login is completely separate from regular user login. You cannot use regular user credentials to access the admin portal.

### User Interface Overview

After logging in, you'll see:
- **Dark theme** - Visual distinction from regular user portal
- **Red accent colors** - Admin branding
- **ADMIN badge** - Clear identification of admin context
- **Minimal navigation** - Dashboard-focused interface

---

## Managing Admin Accounts

### CLI Commands Reference

All admin management is done via Flask CLI commands. These commands must be run on the server (via SSH or Docker exec).

#### Create Admin Account

```bash
flask admin-cli create-admin
```

**What it does:**
- Prompts for username (3-50 characters)
- Prompts for password (min 8 characters, hidden input with confirmation)
- Prompts for optional name and email
- Creates active admin account
- Validates uniqueness of username

**Example:**
```bash
$ flask admin-cli create-admin
Username: jsmith
Password:
Repeat for confirmation:
First name (optional): Jane
Last name (optional): Smith
Email (optional): jane.smith@company.com

✓ Super Admin created successfully!
  Username: jsmith
  Name: Jane Smith
  Email: jane.smith@company.com
  Status: Active

You can now log in at /admin/login
```

#### List All Admins

```bash
flask admin-cli list-admins
```

**What it does:**
- Lists all super admin accounts
- Shows ID, username, name, email, status
- Shows created date and last login timestamp
- Color-coded status (green = active, red = inactive)

**Example Output:**
```
Super Administrators (2 total):
────────────────────────────────────────────────────────────────────────────────

  ID: 1
  Username: admin
  Name: John Doe
  Email: admin@yourcompany.com
  Status: Active
  Created: 2025-01-29 16:30:00
  Last Login: 2025-01-29 18:45:23

  ID: 2
  Username: jsmith
  Name: Jane Smith
  Email: jane.smith@company.com
  Status: Active
  Created: 2025-01-29 17:00:00
  Last Login: Never

────────────────────────────────────────────────────────────────────────────────
```

#### Deactivate Admin Account

```bash
flask admin-cli deactivate-admin USERNAME
```

**What it does:**
- Prevents admin from logging in
- Preserves account and all audit logs
- Does NOT delete the admin account
- Can be reactivated later

**Example:**
```bash
$ flask admin-cli deactivate-admin jsmith
✓ Admin "jsmith" has been deactivated
```

**Use cases:**
- Temporary suspension
- Employee leaves company
- Security concerns
- Account compromise

#### Activate Admin Account

```bash
flask admin-cli activate-admin USERNAME
```

**What it does:**
- Reactivates a previously deactivated admin
- Allows admin to log in again
- All previous audit logs remain intact

**Example:**
```bash
$ flask admin-cli activate-admin jsmith
✓ Admin "jsmith" has been activated
```

#### Reset Admin Password

```bash
flask admin-cli reset-password USERNAME
```

**What it does:**
- Changes admin password
- Prompts for new password with confirmation
- Validates minimum password length (8 characters)
- Admin can log in immediately with new password

**Example:**
```bash
$ flask admin-cli reset-password jsmith
Password:
Repeat for confirmation:
✓ Password reset successfully for "jsmith"
```

**Use cases:**
- Admin forgot password
- Security policy requires password rotation
- Suspected password compromise

### Best Practices for Admin Management

#### Password Security
- ✅ Use strong passwords (min 8 chars, recommend 12+ chars)
- ✅ Use mix of uppercase, lowercase, numbers, symbols
- ✅ Never share admin passwords
- ✅ Rotate passwords regularly (every 90 days recommended)
- ✅ Use password manager for storage

#### Account Management
- ✅ Create individual accounts for each admin (no sharing)
- ✅ Use descriptive first/last names for audit clarity
- ✅ Provide valid email addresses for contact
- ✅ Deactivate accounts when admins leave
- ✅ Regularly review active admins (`list-admins`)

#### Access Control
- ✅ Limit number of super admins (principle of least privilege)
- ✅ Document why each admin needs access
- ✅ Review audit logs regularly
- ✅ Deactivate unused accounts promptly

---

## Dashboard Features

### Main Dashboard (`/admin/dashboard`)

The God View Dashboard provides comprehensive system-wide analytics across all companies.

#### Section 1: Company Overview

**Total Companies**
- Total number of registered companies
- Includes both active and inactive companies

**New This Month**
- Companies that signed up in the current calendar month
- Useful for tracking growth trends

**Active Companies (30 days)**
- Companies with user activity in the last 30 days
- Based on recent user logins/activity

**Inactive Companies (90+ days)**
- Companies with no activity for 90+ days
- Potential churn candidates

#### Section 2: User Metrics

**Total Users**
- All users across all companies
- Includes all role types

**Users by Role**
- Breakdown by role type:
  - **Owners**: Company administrators
  - **Managers**: Property managers
  - **Staff**: Day-to-day operations
  - **Viewers**: Read-only access

**Recent Signups**
- New user registrations in last 30 days

**Top Companies by Users**
- Top 10 companies ranked by user count
- Includes drill-down links

#### Section 3: Property & Asset Metrics

**Total Properties**
- All properties across all companies

**Total Units**
- All rentable units across all properties
- Shows occupied count

**Occupancy Rate**
- System-wide occupancy percentage
- Formula: (Occupied Units / Total Units) × 100

**Total Tenants**
- All tenant records across all companies

**Units by Status**
- Available
- Occupied
- Reserved
- Maintenance

#### Section 4: Top Companies

**Top Companies by Users**
- Ranked list of top 10 companies by user count
- Shows company name, user count, and drill-down link

**Top Companies by Properties**
- Ranked list of top 10 companies by property count
- Shows company name, property count, and drill-down link

#### Section 5: Company Directory

**All Companies List**
- Complete directory of all registered companies
- Sortable table with:
  - Company ID
  - Company Name
  - Contact Email (clickable mailto link)
  - Phone
  - Created Date
  - View Details button

**Recent Company Signups**
- Last 10 company registrations
- Shows company name, contact, created timestamp
- Most recent first

### Company Detail View (`/admin/company/<id>`)

Drill-down view for a specific company showing all associated data.

#### Company Information Card
- Company ID
- Company Name
- Email (clickable)
- Phone
- Full Address (street, city, state)
- Created Date

#### Company Metrics Dashboard
- **Users**: Total users in this company
- **Properties**: Total properties owned
- **Units**: Total units (with occupied count)
- **Occupancy Rate**: Company-specific occupancy %
- **Tenants**: Total tenant count
- **Leases**: Total lease count
- **Users by Role**: Breakdown of owner/manager/staff/viewer

#### Data Tables

**Users Table**
- Name, Email (clickable), Role (color-coded badge), Date Joined

**Properties Table**
- Property Name, Address, City, State, Unit Count

**Units Table**
- Unit Number, Property Name, Bedrooms, Bathrooms, Rent, Status (color-coded)

**Tenants Table**
- Name, Email (clickable), Phone, Date Added

**Leases Table**
- Tenant Name, Unit Number, Start Date, End Date, Rent, Status (color-coded)

#### Navigation
- Breadcrumb navigation (Dashboard → Company Details)
- Back to dashboard link

---

## Security & Compliance

### Authentication & Authorization

#### Separate Authentication System
- **Not Flask-Login based**: Admin auth is completely separate
- **Session key**: Uses `session['admin_id']` instead of `session['user_id']`
- **No interference**: Can be logged in as both admin AND regular user simultaneously
- **Username-based**: Admins log in with username, not email

#### Authorization Enforcement
- **@super_admin_required decorator**: All admin routes protected
- **Session validation**: Every request verifies admin session exists
- **Active check**: Deactivated admins cannot access even with valid session
- **Automatic logout**: Invalid/inactive admins redirected to login

### Read-Only Access

#### What Admins CAN Do
✅ View all companies and their data
✅ View all users across all companies
✅ View all properties, units, tenants, leases
✅ View financial data (payments, expenses)
✅ View system-wide analytics and metrics
✅ Navigate between companies
✅ Log in and log out

#### What Admins CANNOT Do
❌ Create, edit, or delete companies
❌ Create, edit, or delete users
❌ Create, edit, or delete properties/units
❌ Create, edit, or delete tenants/leases
❌ Process payments or record expenses
❌ Modify any data
❌ Export data (not implemented in Phase 1-3)
❌ Impersonate regular users

**Enforcement**: All admin routes use GET requests only. There are no POST/PUT/DELETE handlers in the admin blueprint.

### Audit Logging

#### What Gets Logged
Every admin action is automatically logged to the `super_admin_audit_log` table:

- **Admin ID**: Which admin performed the action
- **Action**: Function name (e.g., `dashboard`, `company_detail`, `login`)
- **Target Company ID**: If viewing a specific company
- **IP Address**: Where the request came from
- **User Agent**: Browser/client information
- **Timestamp**: When the action occurred (indexed for fast queries)
- **Details**: JSON with path, HTTP method, endpoint

#### Audit Trail Uses
- **Security monitoring**: Detect unusual access patterns
- **Compliance**: SOC2, GDPR, HIPAA audit requirements
- **Forensics**: Investigate security incidents
- **Usage analytics**: Understand admin behavior

#### Querying Audit Logs

**Via Database:**
```sql
-- Recent admin actions
SELECT
    sa.username,
    sal.action,
    sal.ip_address,
    sal.timestamp
FROM super_admin_audit_log sal
JOIN super_admin sa ON sal.admin_id = sa.id
ORDER BY sal.timestamp DESC
LIMIT 100;

-- Actions on specific company
SELECT
    sa.username,
    sal.action,
    sal.timestamp
FROM super_admin_audit_log sal
JOIN super_admin sa ON sal.admin_id = sa.id
WHERE sal.target_company_id = 5
ORDER BY sal.timestamp DESC;

-- Admin login history
SELECT
    sa.username,
    sal.timestamp,
    sal.ip_address
FROM super_admin_audit_log sal
JOIN super_admin sa ON sal.admin_id = sa.id
WHERE sal.action = 'admin_login'
ORDER BY sal.timestamp DESC;
```

### Data Isolation

#### Multi-Tenant Bypass
- Regular users: Queries filtered by `company_id` (e.g., `User.query.filter_by(company_id=current_user.company_id)`)
- Super admins: Queries **without** `company_id` filter (e.g., `User.query.all()`)
- SuperAdmin model: **No** `company_id` field (exists outside tenant system)

#### No Cross-Contamination
- Admin sessions don't affect user sessions
- Admin actions don't trigger user notifications
- Admin views don't modify user data
- Complete separation of concerns

### Password Security

#### Hashing
- **Algorithm**: Werkzeug's `generate_password_hash()` (PBKDF2-SHA256)
- **Storage**: Never stored in plaintext
- **Verification**: `check_password_hash()` for login

#### Password Requirements
- Minimum 8 characters (enforced by CLI)
- No maximum length
- Recommend: 12+ characters with mixed case, numbers, symbols

#### Password Reset
- Only via CLI command (no email reset link)
- Requires server access
- New password required immediately

---

## Troubleshooting

### Cannot Access Admin Portal

**Problem**: Going to `/admin/login` shows 404 error

**Solutions:**
1. Verify admin blueprint is registered:
   ```python
   # In website/__init__.py
   from website.admin import admin
   app.register_blueprint(admin)
   ```

2. Restart Flask application
   ```bash
   # Local
   python main.py

   # Docker
   docker compose restart web
   ```

3. Check routes are registered:
   ```bash
   flask routes | grep admin
   ```

---

**Problem**: "Invalid username or password" error

**Solutions:**
1. Verify admin account exists:
   ```bash
   flask admin-cli list-admins
   ```

2. Ensure you're using **username**, not email

3. Check account is active (not deactivated)

4. Reset password if needed:
   ```bash
   flask admin-cli reset-password USERNAME
   ```

---

**Problem**: "Admin authentication required" after logging in

**Solutions:**
1. Check session configuration:
   - `SECRET_KEY` must be set in environment
   - `SESSION_COOKIE_SECURE` should be True in production

2. Verify admin account is active:
   ```bash
   flask admin-cli list-admins
   ```

3. Clear browser cookies and try again

4. Check application logs for errors

---

### CLI Commands Not Found

**Problem**: `flask admin-cli: command not found`

**Solutions:**
1. Verify CLI blueprint is registered:
   ```python
   # In website/__init__.py
   from website.admin.cli import admin_cli
   app.register_blueprint(admin_cli)
   ```

2. Set FLASK_APP environment variable:
   ```bash
   export FLASK_APP=main.py
   ```

3. Activate virtual environment:
   ```bash
   source reenv312/bin/activate
   ```

4. List available commands:
   ```bash
   flask --help
   ```

---

### Database Migration Issues

**Problem**: SuperAdmin tables don't exist

**Solutions:**
1. Check migration file exists:
   ```bash
   ls migrations/versions/ | grep superadmin
   ```

2. Run migrations:
   ```bash
   # Local
   flask db upgrade

   # Docker
   docker compose exec web flask db upgrade
   ```

3. Verify tables were created:
   ```sql
   SELECT table_name
   FROM information_schema.tables
   WHERE table_name IN ('super_admin', 'super_admin_audit_log');
   ```

---

**Problem**: Migration fails with "table already exists"

**Solutions:**
1. Check current migration version:
   ```bash
   flask db current
   ```

2. Mark migration as completed without running:
   ```bash
   flask db stamp head
   ```

3. Or downgrade and re-upgrade:
   ```bash
   flask db downgrade
   flask db upgrade
   ```

---

### Dashboard Shows No Data

**Problem**: Dashboard shows 0 companies/users/properties

**Solutions:**
1. Verify database has data:
   ```sql
   SELECT COUNT(*) FROM company;
   SELECT COUNT(*) FROM "user";
   SELECT COUNT(*) FROM property;
   ```

2. Check database connection:
   - Review `DATABASE_URL` in environment
   - Verify connection string is correct
   - Check database server is running

3. Review application logs for errors

4. Verify admin queries are not filtered by company_id

---

### Template Rendering Errors

**Problem**: `TemplateNotFound: admin_dashboard.html`

**Solutions:**
1. Verify templates exist:
   ```bash
   ls website/admin/templates/
   ```

2. Check template path in views:
   ```python
   # Should be:
   return render_template('admin_dashboard.html', ...)
   # NOT:
   return render_template('admin/admin_dashboard.html', ...)
   ```

3. Verify blueprint template_folder:
   ```python
   # In website/admin/__init__.py
   admin = Blueprint('admin', __name__,
                     url_prefix='/admin',
                     template_folder='templates')
   ```

---

## FAQ

### General Questions

**Q: Can super admins modify data?**
A: No. Super admins have **read-only** access. They can view all data but cannot create, edit, or delete anything.

**Q: Can I use my regular user account to access the admin portal?**
A: No. The admin portal uses a completely separate authentication system. You must create a dedicated super admin account.

**Q: Can I be logged in as both a regular user and super admin at the same time?**
A: Yes. The sessions are completely separate (`session['user_id']` vs `session['admin_id']`), so you can be authenticated as both simultaneously.

**Q: How many super admin accounts should I create?**
A: Follow the principle of least privilege. Create one account per administrator who needs system-wide visibility. Typically 1-3 accounts for a small team.

**Q: Can I create admin accounts through the web interface?**
A: No. Admin accounts can only be created via CLI commands (`flask admin-cli create-admin`). This is a security feature requiring server access.

---

### Security Questions

**Q: Are admin actions logged?**
A: Yes. Every admin action is logged to the `super_admin_audit_log` table, including: admin ID, action, timestamp, IP address, user agent, and target company (if applicable).

**Q: Can I see who accessed what data?**
A: Yes. Query the `super_admin_audit_log` table to see all admin activity, including what companies they viewed and when.

**Q: What happens if an admin account is compromised?**
A: Immediately deactivate the account (`flask admin-cli deactivate-admin USERNAME`), reset the password, review audit logs for suspicious activity, and reactivate only after investigation.

**Q: Can super admins see deleted data?**
A: Only if your database retains deleted records (soft deletes). If data is hard-deleted from the database, super admins cannot see it.

**Q: Is the admin portal GDPR compliant?**
A: The audit logging supports GDPR compliance by tracking who accessed what data and when. However, full GDPR compliance depends on your data retention policies and privacy controls.

---

### Technical Questions

**Q: Can I customize the admin dashboard?**
A: Yes. Edit the templates in `website/admin/templates/` to add custom metrics, charts, or filters.

**Q: Can I export data from the admin portal?**
A: Not in the current implementation (Phase 1-3). This feature could be added in a future phase.

**Q: Can I add charts/visualizations to the dashboard?**
A: Yes. You can integrate charting libraries (Chart.js, Plotly, etc.) by editing `admin_dashboard.html`.

**Q: Can I create multiple admin roles (e.g., view-only, full-access)?**
A: Not currently. All super admins have the same read-only access. You could extend the SuperAdmin model with a `role` field to implement this.

**Q: Does the admin portal work on mobile devices?**
A: Yes. The templates use Bootstrap responsive design and work on all device sizes.

**Q: Can I change the dark theme to light theme?**
A: Yes. Edit `admin_base.html` and remove `data-bs-theme="dark"` from the `<html>` tag, then adjust the custom CSS accordingly.

---

### Operational Questions

**Q: How do I back up admin accounts?**
A: Admin accounts are stored in the `super_admin` table. Back them up as part of your regular database backups.

**Q: What happens if I forget my admin password?**
A: Use the CLI command to reset it: `flask admin-cli reset-password USERNAME`

**Q: Can I delete an admin account?**
A: The CLI doesn't provide a delete command (by design). Use `deactivate-admin` instead. If you must delete, use SQL:
```sql
DELETE FROM super_admin WHERE username = 'username';
```
**Warning**: This also deletes all audit logs for that admin due to foreign key constraints.

**Q: How do I recover if all admin accounts are deactivated?**
A: Use the CLI to activate an account:
```bash
flask admin-cli activate-admin USERNAME
```
Or create a new admin:
```bash
flask admin-cli create-admin
```

**Q: Can I automate admin account creation?**
A: Yes. You can pass parameters to the CLI command in a script:
```bash
flask admin-cli create-admin \
  --username admin \
  --password "SecurePassword123" \
  --first-name "Admin" \
  --last-name "User" \
  --email "admin@company.com"
```
However, this stores the password in command history, so use with caution.

---

## Additional Resources

### Related Documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [README.md](README.md) - General application documentation
- [CLAUDE.md](CLAUDE.md) - Complete development documentation

### Code Locations
- **Models**: `website/models.py` (SuperAdmin, SuperAdminAuditLog)
- **Views**: `website/admin/views.py`
- **Forms**: `website/admin/forms.py`
- **Templates**: `website/admin/templates/`
- **CLI**: `website/admin/cli.py`
- **Auth Utils**: `website/auth_utils.py` (@super_admin_required)
- **Migration**: `migrations/versions/f9a1b3c4d5e6_*.py`

### Support
For issues or questions:
1. Review troubleshooting section above
2. Check application logs
3. Review audit logs for security issues
4. Contact system administrator

---

**Version**: 1.0
**Last Updated**: January 29, 2025
**Status**: Production Ready ✅

---

*Generated with Claude Code - https://claude.com/claude-code*
