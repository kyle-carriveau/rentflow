"""
View tests for report endpoints.

This module demonstrates testing patterns for:
- Authentication and authorization
- Role-based access control
- Multi-tenant data isolation in views
- HTTP response validation
- Template rendering
"""

import pytest
from flask import url_for
from decimal import Decimal
from datetime import datetime, timedelta

from website.models import User, Property, Unit, Tenant, Lease, Payment, Expense


@pytest.mark.views
@pytest.mark.auth
class TestReportViewsAuthentication:
    """Test authentication requirements for report views."""

    def test_dashboard_requires_authentication(self, client):
        """Test that report dashboard requires authentication."""
        response = client.get('/reports/')
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location

    def test_financial_trends_requires_authentication(self, client):
        """Test that financial trends requires authentication."""
        response = client.get('/reports/financial-trends')
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location

    def test_portfolio_performance_requires_authentication(self, client):
        """Test that portfolio performance requires authentication."""
        response = client.get('/reports/portfolio-performance')
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location


@pytest.mark.views
@pytest.mark.security
class TestReportViewsAuthorization:
    """Test role-based authorization for report views."""

    def test_owner_can_access_all_reports(self, app, authenticated_client, owner_user):
        """Test that owner role can access all report views."""
        with app.test_request_context():
            # Test dashboard access
            response = authenticated_client.get(url_for('report.dashboard'))
            assert response.status_code == 200

            # Test financial trends access
            response = authenticated_client.get(url_for('report.financial_trends'))
            assert response.status_code == 200

            # Test portfolio performance access
            response = authenticated_client.get(url_for('report.portfolio_performance'))
            assert response.status_code == 200

    def test_viewer_has_limited_access(self, app, client, viewer_user):
        """Test that viewer role has appropriate access restrictions."""
        with app.test_request_context():
            # Login as viewer
            with client.session_transaction() as sess:
                sess['_user_id'] = str(viewer_user.id)
                sess['_fresh'] = True

            # Viewers should be able to view reports but not modify
            response = client.get(url_for('report.dashboard'))
            assert response.status_code == 200

            # Verify no edit/delete buttons in response for viewer
            assert b'Edit' not in response.data
            assert b'Delete' not in response.data


@pytest.mark.views
@pytest.mark.security
class TestReportViewsDataIsolation:
    """Test multi-tenant data isolation in report views."""

    def test_dashboard_shows_only_company_data(self, app, client, owner_user, company_a,
                                             property_a, property_b, unit, tenant,
                                             active_lease, payment):
        """Test that dashboard only shows data for user's company."""
        with app.test_request_context():
            # Login as company A owner
            with client.session_transaction() as sess:
                sess['_user_id'] = str(owner_user.id)
                sess['_fresh'] = True

            response = client.get(url_for('report.dashboard'))
            assert response.status_code == 200

            # Should see company A data
            assert property_a.name.encode() in response.data

            # Should NOT see company B data
            assert property_b.name.encode() not in response.data

    def test_financial_trends_isolated_by_company(self, app, client, owner_user,
                                                 user_company_b, company_a, company_b,
                                                 property_a, expense):
        """Test that financial trends are isolated by company."""
        with app.app_context():
            from website import db

            # Create expense for company B
            expense_b = Expense(
                amount=Decimal('500.00'),
                description='Company B Expense',
                category='maintenance',
                expense_date=datetime.now().date(),
                company_id=company_b.id,
                property_id=property_a.id  # This should be filtered out
            )
            db.session.add(expense_b)
            db.session.commit()

        with app.test_request_context():
            # Login as company A owner
            with client.session_transaction() as sess:
                sess['_user_id'] = str(owner_user.id)
                sess['_fresh'] = True

            response = client.get(url_for('report.financial_trends'))
            assert response.status_code == 200

            # Should see company A expense
            assert expense.description.encode() in response.data

            # Should NOT see company B expense
            assert b'Company B Expense' not in response.data


@pytest.mark.views
@pytest.mark.integration
class TestReportViewsDataAccuracy:
    """Test that report views display accurate data."""

    def test_dashboard_kpi_calculations(self, app, authenticated_client, company_a,
                                       property_a, unit, tenant, active_lease,
                                       payment, expense):
        """Test that dashboard KPI calculations are correct."""
        with app.test_request_context():
            response = authenticated_client.get(url_for('report.dashboard'))
            assert response.status_code == 200

            # Parse response and verify KPI values
            response_text = response.data.decode('utf-8')

            # Should show correct property count
            assert '1' in response_text  # 1 property

            # Should show payment amount
            assert str(payment.amount) in response_text

            # Should show expense amount
            assert str(expense.amount) in response_text

    def test_financial_trends_date_filtering(self, app, authenticated_client,
                                           company_a, property_a):
        """Test that financial trends respect date filters."""
        with app.app_context():
            from website import db

            # Create expenses in different months
            current_date = datetime.now().date()
            old_date = current_date - timedelta(days=90)

            current_expense = Expense(
                amount=Decimal('300.00'),
                description='Current expense',
                category='maintenance',
                expense_date=current_date,
                company_id=company_a.id,
                property_id=property_a.id
            )

            old_expense = Expense(
                amount=Decimal('500.00'),
                description='Old expense',
                category='maintenance',
                expense_date=old_date,
                company_id=company_a.id,
                property_id=property_a.id
            )

            db.session.add_all([current_expense, old_expense])
            db.session.commit()

        with app.test_request_context():
            # Test with date filter for last 30 days
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')

            response = authenticated_client.get(
                url_for('report.financial_trends'),
                query_string={
                    'start_date': start_date,
                    'end_date': end_date
                }
            )

            assert response.status_code == 200
            response_text = response.data.decode('utf-8')

            # Should show current expense
            assert 'Current expense' in response_text

            # Should NOT show old expense (outside date range)
            assert 'Old expense' not in response_text


@pytest.mark.views
class TestReportViewsResponseFormat:
    """Test response format and template rendering."""

    def test_dashboard_renders_correct_template(self, app, authenticated_client):
        """Test that dashboard renders with correct template structure."""
        with app.test_request_context():
            response = authenticated_client.get(url_for('report.dashboard'))
            assert response.status_code == 200

            # Check for expected template elements
            response_text = response.data.decode('utf-8')
            assert 'Reports Dashboard' in response_text
            assert 'Chart.js' in response_text or 'chart' in response_text.lower()
            assert 'KPI' in response_text or 'metric' in response_text.lower()

    def test_json_endpoints_return_valid_json(self, app, authenticated_client):
        """Test that JSON endpoints return valid JSON data."""
        # If your reports have JSON endpoints for chart data
        with app.test_request_context():
            # Example: Test chart data endpoint if it exists
            # response = authenticated_client.get(url_for('report.chart_data'))
            # assert response.status_code == 200
            # assert response.content_type == 'application/json'
            #
            # data = response.get_json()
            # assert data is not None
            # assert 'labels' in data
            # assert 'datasets' in data
            pass  # Replace with actual JSON endpoint tests

    def test_error_handling(self, app, authenticated_client):
        """Test error handling in report views."""
        with app.test_request_context():
            # Test invalid date parameters
            response = authenticated_client.get(
                url_for('report.financial_trends'),
                query_string={
                    'start_date': 'invalid-date',
                    'end_date': 'also-invalid'
                }
            )

            # Should handle gracefully (either 400 error or default to valid dates)
            assert response.status_code in [200, 400]

            if response.status_code == 200:
                # If it defaults to valid dates, should still render
                assert b'Financial Trends' in response.data


@pytest.mark.views
@pytest.mark.performance
class TestReportViewsPerformance:
    """Test performance characteristics of report views."""

    def test_dashboard_loads_within_time_limit(self, app, authenticated_client):
        """Test that dashboard loads within reasonable time."""
        import time

        with app.test_request_context():
            start_time = time.time()
            response = authenticated_client.get(url_for('report.dashboard'))
            end_time = time.time()

            assert response.status_code == 200

            # Dashboard should load within 2 seconds (adjust as needed)
            load_time = end_time - start_time
            assert load_time < 2.0, f"Dashboard took {load_time:.2f}s to load"

    def test_large_dataset_handling(self, app, authenticated_client, company_a,
                                   property_a, test_factory):
        """Test report performance with larger datasets."""
        with app.app_context():
            from website import db

            # Create multiple properties and expenses
            properties = []
            expenses = []

            for i in range(10):  # Create 10 properties
                prop = test_factory.create_property(
                    app, company_a,
                    name=f'Test Property {i}',
                    address=f'{i} Test St'
                )
                properties.append(prop)

                # Create multiple expenses per property
                for j in range(5):  # 5 expenses per property = 50 total
                    expense = Expense(
                        amount=Decimal(f'{100 + j * 10}.00'),
                        description=f'Expense {j} for property {i}',
                        category='maintenance',
                        expense_date=datetime.now().date(),
                        company_id=company_a.id,
                        property_id=prop.id
                    )
                    expenses.append(expense)

            db.session.add_all(expenses)
            db.session.commit()

        with app.test_request_context():
            # Test dashboard with larger dataset
            response = authenticated_client.get(url_for('report.dashboard'))
            assert response.status_code == 200

            # Should handle the data without errors
            response_text = response.data.decode('utf-8')
            assert 'Test Property' in response_text  # Should show some properties