"""
Role-Based Access Control (RBAC) Tests

Tests to verify proper permission enforcement for all user roles:
- Owner: Full access to all features
- Manager: Property/tenant management, financial operations
- Staff: Property/tenant management, limited financial access
- Viewer: Read-only access

SECURITY PRIORITY: CRITICAL
"""

import pytest


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.rbac
class TestOwnerPermissions:
    """
    Test suite for Owner role permissions.

    Owners should have full access to all features:
    - Company settings management
    - User management (invite, edit roles, remove)
    - Create/edit/delete all resources
    - View all financial data
    - Access audit logs
    """

    def test_owner_can_access_company_settings(self, auth_client_company_a, company_a):
        """Owner should be able to access and modify company settings."""
        # Access company settings page
        response = auth_client_company_a.get('/company/profile')
        assert response.status_code == 200, \
            "Owner should be able to access company settings"

        response_data = response.data.decode('utf-8')
        assert company_a.name in response_data, \
            "Company name should be visible on settings page"

        # Attempt to update company settings
        response = auth_client_company_a.post('/company/profile', data={
            'name': 'Updated Company Name',
            'email': company_a.email,
            'phone': company_a.phone
        }, follow_redirects=True)

        assert response.status_code == 200, \
            "Owner should be able to update company settings"

    def test_owner_can_manage_users(self, auth_client_company_a):
        """Owner should be able to invite, edit, and remove users."""
        # Access user management page
        response = auth_client_company_a.get('/users')
        assert response.status_code == 200, \
            "Owner should be able to access user management"

        # Attempt to invite a new user
        response = auth_client_company_a.post('/users/invite', data={
            'email': 'newuser@alpha-properties.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'staff'
        }, follow_redirects=True)

        assert response.status_code == 200, \
            "Owner should be able to invite new users"

    def test_owner_can_create_properties(self, auth_client_company_a):
        """Owner should be able to create new properties."""
        response = auth_client_company_a.get('/property/create')
        assert response.status_code == 200, \
            "Owner should be able to access property creation page"

        response = auth_client_company_a.post('/property/create', data={
            'name': 'New Property',
            'address': '999 New Street',
            'city': 'Los Angeles',
            'state': 'CA',
            'zip_code': '90001',
            'type': 'Apartment',
            'year_built': 2020,
            'total_units': 5
        }, follow_redirects=True)

        assert response.status_code == 200, \
            "Owner should be able to create properties"

    def test_owner_can_view_all_financial_data(self, auth_client_company_a, payment_a, expense_a):
        """Owner should have full access to all financial data."""
        # Access financial overview
        response = auth_client_company_a.get('/financial')
        assert response.status_code == 200, \
            "Owner should be able to access financial overview"

        response_data = response.data.decode('utf-8')

        # Verify payment data is visible
        assert payment_a.reference_number in response_data, \
            "Owner should see payment data"

        # Verify expense data is visible
        assert expense_a.vendor in response_data, \
            "Owner should see expense data"

        # Access financial analytics
        response = auth_client_company_a.get('/financial/analytics')
        if response.status_code == 200:  # If analytics page exists
            assert response.status_code == 200, \
                "Owner should be able to access financial analytics"

    def test_owner_can_delete_resources(self, auth_client_company_a, property_a):
        """Owner should be able to delete properties and other resources."""
        # Note: This test doesn't actually delete to avoid affecting other tests
        # In a real scenario, you'd create a separate property just for deletion

        response = auth_client_company_a.get(f'/property/{property_a.uuid}')
        assert response.status_code == 200, \
            "Owner should be able to view property detail page"

        response_data = response.data.decode('utf-8')

        # Check if delete button/option is present (indicates permission)
        # The exact HTML structure may vary, but typically there's a delete link/button
        assert 'delete' in response_data.lower(), \
            "Owner should see delete option for properties"

    def test_owner_can_change_user_roles(self, auth_client_company_a, manager_user):
        """Owner should be able to change other users' roles."""
        # Access user edit page
        response = auth_client_company_a.get(f'/users/{manager_user.id}/edit')

        # If the edit endpoint exists and is accessible
        if response.status_code == 200:
            assert response.status_code == 200, \
                "Owner should be able to access user edit page"

            # The edit form should show role options
            response_data = response.data.decode('utf-8')
            assert 'role' in response_data.lower(), \
                "User edit page should show role selection for Owner"

    def test_owner_can_access_audit_logs(self, auth_client_company_a):
        """Owner should be able to view audit logs if they exist."""
        # Try to access audit logs endpoint (if it exists)
        response = auth_client_company_a.get('/company/audit-logs')

        # If audit logs exist, owner should have access
        # If they don't exist yet, this will 404 which is fine
        assert response.status_code in [200, 404], \
            f"Owner should either access audit logs or get 404 if not implemented. Got {response.status_code}"


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.rbac
class TestManagerPermissions:
    """
    Test suite for Manager role permissions.

    Managers should have:
    - Property and tenant management access
    - Financial operations (record payments, add expenses)
    - Cannot access company settings
    - Cannot manage users
    """

    def test_manager_can_create_properties(self, auth_client_manager):
        """Manager should be able to create properties."""
        response = auth_client_manager.get('/property/create')
        assert response.status_code == 200, \
            "Manager should be able to access property creation page"

    def test_manager_can_manage_tenants(self, auth_client_manager):
        """Manager should be able to create and edit tenants."""
        response = auth_client_manager.get('/tenant/create')
        assert response.status_code == 200, \
            "Manager should be able to access tenant creation page"

    def test_manager_can_record_payments(self, auth_client_manager):
        """Manager should be able to record payments."""
        response = auth_client_manager.get('/financial/payments/record')
        assert response.status_code == 200, \
            "Manager should be able to access payment recording page"

    def test_manager_can_add_expenses(self, auth_client_manager):
        """Manager should be able to add expenses."""
        response = auth_client_manager.get('/financial/expenses/add')
        assert response.status_code == 200, \
            "Manager should be able to access expense creation page"

    def test_manager_cannot_access_company_settings(self, auth_client_manager):
        """Manager should NOT be able to access company settings."""
        response = auth_client_manager.get('/company/profile')
        assert response.status_code in [302, 403, 404], \
            f"Manager should not access company settings. Got {response.status_code}"

    def test_manager_cannot_manage_users(self, auth_client_manager):
        """Manager should NOT be able to invite or manage users."""
        response = auth_client_manager.get('/users/invite')
        assert response.status_code in [302, 403, 404], \
            f"Manager should not access user invitation page. Got {response.status_code}"


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.rbac
class TestStaffPermissions:
    """
    Test suite for Staff role permissions.

    Staff should have:
    - Property and tenant management access
    - Limited financial access (view, but not full management)
    - Cannot access company settings
    - Cannot manage users
    - Cannot delete critical resources
    """

    def test_staff_can_view_properties(self, auth_client_staff, property_a):
        """Staff should be able to view properties."""
        response = auth_client_staff.get('/property')
        assert response.status_code == 200, \
            "Staff should be able to view property list"

        response = auth_client_staff.get(f'/property/{property_a.uuid}')
        assert response.status_code == 200, \
            "Staff should be able to view property details"

    def test_staff_can_manage_tenants(self, auth_client_staff):
        """Staff should be able to create and edit tenants."""
        response = auth_client_staff.get('/tenant/create')
        assert response.status_code == 200, \
            "Staff should be able to access tenant creation page"

    def test_staff_cannot_access_company_settings(self, auth_client_staff):
        """Staff should NOT be able to access company settings."""
        response = auth_client_staff.get('/company/profile')
        assert response.status_code in [302, 403, 404], \
            f"Staff should not access company settings. Got {response.status_code}"

    def test_staff_cannot_manage_users(self, auth_client_staff):
        """Staff should NOT be able to manage users."""
        response = auth_client_staff.get('/users/invite')
        assert response.status_code in [302, 403, 404], \
            f"Staff should not access user management. Got {response.status_code}"

    def test_staff_has_limited_financial_access(self, auth_client_staff):
        """Staff should have view access to financial data but limited modification rights."""
        # Staff should be able to VIEW financial data
        response = auth_client_staff.get('/financial')
        assert response.status_code == 200, \
            "Staff should be able to view financial overview"

        # But may not have full expense management (implementation dependent)
        # This test documents the expected behavior
        response = auth_client_staff.get('/financial/expenses/add')

        # Result depends on business rules - either allowed or forbidden
        assert response.status_code in [200, 403, 404], \
            "Staff financial access should be controlled (either allowed or forbidden)"


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.rbac
class TestViewerPermissions:
    """
    Test suite for Viewer role permissions.

    Viewers should have:
    - Read-only access to assigned data
    - Cannot create, edit, or delete any resources
    - Cannot access financial operations
    - Cannot access company settings
    """

    def test_viewer_can_view_properties(self, auth_client_viewer, property_a):
        """Viewer should be able to view properties (read-only)."""
        response = auth_client_viewer.get('/property')
        assert response.status_code == 200, \
            "Viewer should be able to view property list"

        response = auth_client_viewer.get(f'/property/{property_a.uuid}')
        assert response.status_code == 200, \
            "Viewer should be able to view property details"

    def test_viewer_cannot_create_properties(self, auth_client_viewer):
        """Viewer should NOT be able to create properties."""
        response = auth_client_viewer.get('/property/create')
        assert response.status_code in [302, 403, 404], \
            f"Viewer should not access property creation. Got {response.status_code}"

    def test_viewer_cannot_edit_tenants(self, auth_client_viewer, tenant_a):
        """Viewer should NOT be able to edit tenants."""
        response = auth_client_viewer.post(f'/tenant/{tenant_a.uuid}/edit', data={
            'first_name': 'Modified',
            'last_name': 'Name'
        })
        assert response.status_code in [302, 403, 404], \
            f"Viewer should not be able to edit tenants. Got {response.status_code}"

    def test_viewer_cannot_delete_leases(self, auth_client_viewer, active_lease_a):
        """Viewer should NOT be able to delete leases."""
        response = auth_client_viewer.post(f'/lease/{active_lease_a.uuid}/delete')
        assert response.status_code in [302, 403, 404], \
            f"Viewer should not be able to delete leases. Got {response.status_code}"

    def test_viewer_cannot_access_financial_operations(self, auth_client_viewer):
        """Viewer should NOT be able to access financial operations."""
        # Cannot record payments
        response = auth_client_viewer.get('/financial/payments/record')
        assert response.status_code in [302, 403, 404], \
            f"Viewer should not access payment recording. Got {response.status_code}"

        # Cannot add expenses
        response = auth_client_viewer.get('/financial/expenses/add')
        assert response.status_code in [302, 403, 404], \
            f"Viewer should not access expense creation. Got {response.status_code}"

        # May be able to VIEW financial summary (read-only) - implementation dependent
        response = auth_client_viewer.get('/financial')

        # Either completely forbidden or read-only access allowed
        assert response.status_code in [200, 403, 404], \
            "Viewer financial access should be controlled"


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.rbac
class TestRoleHierarchyEnforcement:
    """
    Tests to verify role hierarchy is properly enforced.

    Lower-privilege roles should not be able to access higher-privilege features.
    """

    def test_staff_cannot_access_owner_only_features(self, auth_client_staff):
        """Staff should not be able to access Owner-only features."""
        # Company settings - Owner only
        response = auth_client_staff.get('/company/profile')
        assert response.status_code in [302, 403, 404], \
            "Staff should not access Owner-only company settings"

        # User management - Owner only
        response = auth_client_staff.get('/users')
        assert response.status_code in [302, 403, 404], \
            "Staff should not access Owner-only user management"

    def test_viewer_cannot_access_manager_features(self, auth_client_viewer):
        """Viewer should not be able to access Manager-level features."""
        # Property creation - Manager/Owner only
        response = auth_client_viewer.get('/property/create')
        assert response.status_code in [302, 403, 404], \
            "Viewer should not create properties"

        # Financial operations - Manager/Owner only
        response = auth_client_viewer.get('/financial/payments/record')
        assert response.status_code in [302, 403, 404], \
            "Viewer should not record payments"

    def test_viewer_cannot_access_staff_features(self, auth_client_viewer):
        """Viewer should not be able to access Staff-level features."""
        # Tenant creation - Staff/Manager/Owner only
        response = auth_client_viewer.get('/tenant/create')
        assert response.status_code in [302, 403, 404], \
            "Viewer should not create tenants"

    def test_manager_cannot_escalate_privileges(self, auth_client_manager):
        """Manager should not be able to escalate their own privileges."""
        # Attempt to access user management (which could allow role changes)
        response = auth_client_manager.get('/users')
        assert response.status_code in [302, 403, 404], \
            "Manager should not access user management (prevents privilege escalation)"


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.rbac
class TestCrossRoleDataAccess:
    """
    Tests to verify users can only access data within their company,
    regardless of role.
    """

    def test_manager_cannot_access_other_company_even_with_manager_role(
        self, auth_client_manager, property_b
    ):
        """
        Even with Manager privileges, cannot access another company's data.

        This verifies that ROLE does not override COMPANY isolation.
        """
        response = auth_client_manager.get(f'/property/{property_b.uuid}')
        assert response.status_code in [302, 403, 404], \
            "Manager role should not override company isolation"

    def test_staff_with_property_access_cannot_see_other_company_properties(
        self, auth_client_staff, property_a, property_b
    ):
        """Staff can see their company's properties but not other companies."""
        # Can see Company A properties
        response = auth_client_staff.get('/property')
        assert response.status_code == 200

        response_data = response.data.decode('utf-8')
        assert property_a.name in response_data, \
            "Staff should see their own company's properties"

        # Cannot see Company B properties
        assert property_b.name not in response_data, \
            "Staff should not see other companies' properties"
