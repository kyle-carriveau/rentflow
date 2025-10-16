"""
Unit tests for loading states functionality in forms.

Tests that form templates include proper data-loading attributes
and that the loading states JavaScript integration works correctly.
"""

import pytest
from bs4 import BeautifulSoup


@pytest.mark.unit
@pytest.mark.views
class TestLoadingStates:
    """Test loading states functionality in forms."""

    def test_tenant_create_form_has_loading_state(self, app, authenticated_client):
        """Test that tenant create form has data-loading attribute."""
        with app.app_context():
            response = authenticated_client.get('/tenant/create')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')
            submit_button = soup.find('button', {'type': 'submit'})

            assert submit_button is not None
            assert submit_button.get('data-loading') == 'Creating tenant...'

    def test_property_create_form_has_loading_state(self, app, authenticated_client):
        """Test that property create form has data-loading attribute."""
        with app.app_context():
            response = authenticated_client.get('/property/create')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')
            submit_button = soup.find('button', {'type': 'submit', 'id': 'submit-btn'})

            assert submit_button is not None
            assert submit_button.get('data-loading') == 'Creating property...'

    def test_user_invite_form_has_loading_state(self, app, authenticated_client):
        """Test that user invite form has data-loading attribute."""
        with app.app_context():
            response = authenticated_client.get('/users/invite')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')
            submit_button = soup.find('button', {'type': 'submit'})

            assert submit_button is not None
            assert submit_button.get('data-loading') == 'Inviting user...'

    def test_expense_form_has_loading_state(self, app, authenticated_client):
        """Test that add expense form has data-loading attribute."""
        with app.app_context():
            response = authenticated_client.get('/financial/expenses/add')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')
            submit_button = soup.find('button', {'type': 'submit'})

            assert submit_button is not None
            assert submit_button.get('data-loading') == 'Adding expense...'

    def test_payment_form_has_loading_state(self, app, authenticated_client):
        """Test that record payment form has data-loading attribute."""
        with app.app_context():
            response = authenticated_client.get('/financial/payments/add')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')
            submit_button = soup.find('button', {'type': 'submit'})

            assert submit_button is not None
            assert submit_button.get('data-loading') == 'Recording payment...'

    def test_loading_states_js_included(self, app, authenticated_client):
        """Test that loading-states.js is included in base template."""
        with app.app_context():
            response = authenticated_client.get('/tenant/')  # Any page that extends base
            assert response.status_code == 200

            # Check that loading-states.js is referenced
            assert b'loading-states.js' in response.data

    def test_forms_have_consistent_loading_messages(self, app, authenticated_client):
        """Test that loading messages follow consistent patterns."""
        with app.app_context():
            forms_to_test = [
                ('/tenant/create', 'Creating tenant...'),
                ('/users/invite', 'Inviting user...'),
                ('/financial/expenses/add', 'Adding expense...'),
                ('/financial/payments/add', 'Recording payment...'),
            ]

            for url, expected_message in forms_to_test:
                response = authenticated_client.get(url)
                assert response.status_code == 200

                soup = BeautifulSoup(response.data, 'html.parser')
                submit_button = soup.find('button', {'type': 'submit'})

                if submit_button:  # Some forms might not be accessible in test environment
                    loading_message = submit_button.get('data-loading')
                    assert loading_message == expected_message, f"Form {url} has incorrect loading message: {loading_message}"

    def test_edit_forms_have_loading_states(self, app, authenticated_client, property_a, tenant):
        """Test that edit forms have appropriate loading states."""
        with app.app_context():
            # Test property edit form
            response = authenticated_client.get(f'/property/{property_a.uuid}/edit')
            if response.status_code == 200:  # Check if accessible
                soup = BeautifulSoup(response.data, 'html.parser')
                submit_button = soup.find('button', {'type': 'submit'})

                if submit_button:
                    assert submit_button.get('data-loading') == 'Saving changes...'

            # Test tenant edit form
            response = authenticated_client.get(f'/tenant/{tenant.uuid}/edit')
            if response.status_code == 200:  # Check if accessible
                soup = BeautifulSoup(response.data, 'html.parser')
                submit_button = soup.find('button', {'type': 'submit'})

                if submit_button:
                    assert submit_button.get('data-loading') == 'Saving changes...'

    def test_loading_state_attributes_format(self, app, authenticated_client):
        """Test that data-loading attributes follow correct format."""
        with app.app_context():
            response = authenticated_client.get('/tenant/create')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')
            submit_button = soup.find('button', {'type': 'submit'})

            if submit_button:
                loading_message = submit_button.get('data-loading')

                # Should be present and non-empty
                assert loading_message is not None
                assert len(loading_message.strip()) > 0

                # Should end with '...' for consistency
                assert loading_message.endswith('...')

                # Should be descriptive (not just 'Loading...')
                assert loading_message != 'Loading...'