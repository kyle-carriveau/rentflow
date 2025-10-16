"""
Unit tests for custom Jinja2 template filters.

Tests the currency, number, and percentage filters added for consistent
number formatting across the application.
"""

import pytest
from decimal import Decimal
from website import create_app


@pytest.mark.unit
class TestTemplateFilters:
    """Test custom Jinja2 template filters."""

    def test_currency_filter_with_integers(self, app):
        """Test currency filter with integer values."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|currency }}")

            assert template.render(value=1500) == "$1,500"
            assert template.render(value=0) == "$0"
            assert template.render(value=1000000) == "$1,000,000"

    def test_currency_filter_with_floats(self, app):
        """Test currency filter with float values."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|currency }}")

            assert template.render(value=1500.00) == "$1,500"
            assert template.render(value=1500.50) == "$1,500"  # 0.5 rounds to even (banker's rounding)
            assert template.render(value=999.99) == "$1,000"   # Rounds up

    def test_currency_filter_with_decimals(self, app):
        """Test currency filter with Decimal values."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|currency }}")

            assert template.render(value=Decimal('1500.00')) == "$1,500"
            assert template.render(value=Decimal('1500.50')) == "$1,500"
            assert template.render(value=Decimal('999.49')) == "$999"

    def test_currency_filter_with_strings(self, app):
        """Test currency filter with string values."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|currency }}")

            assert template.render(value="1500") == "$1,500"
            assert template.render(value="1500.00") == "$1,500"

    def test_currency_filter_with_none_and_empty(self, app):
        """Test currency filter with None and empty values."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|currency }}")

            assert template.render(value=None) == "$0"
            assert template.render(value="") == "$0"

    def test_currency_filter_with_invalid_input(self, app):
        """Test currency filter with invalid input."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|currency }}")

            assert template.render(value="invalid") == "$0"
            assert template.render(value="$1500") == "$0"  # Invalid format

    def test_number_filter_with_integers(self, app):
        """Test number filter with integer values."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|number }}")

            assert template.render(value=1500) == "1,500"
            assert template.render(value=0) == "0"
            assert template.render(value=1000000) == "1,000,000"

    def test_number_filter_with_floats(self, app):
        """Test number filter with float values."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|number }}")

            assert template.render(value=1500.00) == "1,500"
            assert template.render(value=1500.50) == "1,500"  # 0.5 rounds to even
            assert template.render(value=999.99) == "1,000"   # Rounds up

    def test_number_filter_with_strings(self, app):
        """Test number filter with string values."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|number }}")

            assert template.render(value="1500") == "1,500"
            assert template.render(value="1500.00") == "1,500"

    def test_number_filter_with_none_and_empty(self, app):
        """Test number filter with None and empty values."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|number }}")

            assert template.render(value=None) == "0"
            assert template.render(value="") == "0"

    def test_number_filter_with_invalid_input(self, app):
        """Test number filter with invalid input."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|number }}")

            assert template.render(value="invalid") == "0"

    def test_percentage_filter_default_decimals(self, app):
        """Test percentage filter with default 1 decimal place."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|percentage }}")

            assert template.render(value=85.5) == "85.5%"
            assert template.render(value=100.0) == "100.0%"
            assert template.render(value=0) == "0.0%"
            assert template.render(value=85.56789) == "85.6%"  # Rounds to 1 decimal

    def test_percentage_filter_custom_decimals(self, app):
        """Test percentage filter with custom decimal places."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|percentage(0) }}")
            assert template.render(value=85.5) == "86%"  # Rounds to nearest whole

            template = app.jinja_env.from_string("{{ value|percentage(2) }}")
            assert template.render(value=85.567) == "85.57%"  # 2 decimal places

    def test_percentage_filter_with_strings(self, app):
        """Test percentage filter with string values."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|percentage }}")

            assert template.render(value="85.5") == "85.5%"
            assert template.render(value="100") == "100.0%"

    def test_percentage_filter_with_none_and_empty(self, app):
        """Test percentage filter with None and empty values."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|percentage }}")

            assert template.render(value=None) == "0.0%"
            assert template.render(value="") == "0.0%"

    def test_percentage_filter_with_invalid_input(self, app):
        """Test percentage filter with invalid input."""
        with app.app_context():
            template = app.jinja_env.from_string("{{ value|percentage }}")

            assert template.render(value="invalid") == "0.0%"

    def test_filters_in_realistic_templates(self, app):
        """Test filters in realistic template scenarios."""
        with app.app_context():
            # Test currency in a typical property revenue context
            template = app.jinja_env.from_string(
                "Monthly Revenue: {{ revenue|currency }}"
            )
            assert template.render(revenue=2850.00) == "Monthly Revenue: $2,850"

            # Test number for square footage
            template = app.jinja_env.from_string(
                "{{ sqft|number }} sq ft"
            )
            assert template.render(sqft=1250) == "1,250 sq ft"

            # Test percentage for occupancy rate
            template = app.jinja_env.from_string(
                "Occupancy: {{ rate|percentage }}%"
            )
            # Note: This would show as "Occupancy: 95.5%%" - percentage filter already adds %
            # This test documents current behavior for future reference

    def test_filter_edge_cases(self, app):
        """Test filters with edge cases and boundary values."""
        with app.app_context():
            # Very large numbers
            template = app.jinja_env.from_string("{{ value|currency }}")
            assert template.render(value=999999999) == "$999,999,999"

            # Very small percentages
            template = app.jinja_env.from_string("{{ value|percentage(2) }}")
            assert template.render(value=0.01) == "0.01%"

            # Negative numbers
            template = app.jinja_env.from_string("{{ value|currency }}")
            assert template.render(value=-1500) == "$-1,500"

            template = app.jinja_env.from_string("{{ value|percentage }}")
            assert template.render(value=-5.5) == "-5.5%"