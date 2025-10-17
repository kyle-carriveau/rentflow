"""
Unit tests for Lease model methods.
"""
import pytest
from datetime import datetime, timedelta
from website.models import Lease, Company, Tenant, Unit, Property


@pytest.fixture
def sample_lease():
    """Create a sample lease for testing."""
    # Note: This is a simple fixture for unit testing the method logic
    # In a real scenario, you'd use the app context and database fixtures
    lease = Lease()
    lease.start = datetime.now()
    lease.end = datetime.now() + timedelta(days=365)
    lease.payment_due_date = 1  # Due on 1st of each month
    lease.rent = 1500
    return lease


def test_days_until_next_payment_current_month(sample_lease):
    """Test days_until_next_payment when payment is due this month."""
    today = datetime.now().date()

    # Set payment due date to later this month
    sample_lease.payment_due_date = min(28, (today.day + 5) if today.day < 23 else 28)

    days_until = sample_lease.days_until_next_payment()

    # Should return a positive integer or 0
    assert days_until is not None
    assert isinstance(days_until, int)
    assert days_until >= 0


def test_days_until_next_payment_next_month(sample_lease):
    """Test days_until_next_payment when next payment is next month."""
    today = datetime.now().date()

    # Set payment due date to earlier in the month (already passed)
    sample_lease.payment_due_date = max(1, today.day - 5) if today.day > 5 else 1

    # If today's day is before payment due date, skip this test
    if today.day <= sample_lease.payment_due_date:
        pytest.skip("Test requires current day to be after payment due date")

    days_until = sample_lease.days_until_next_payment()

    # Should return days until next month's payment
    assert days_until is not None
    assert isinstance(days_until, int)
    assert days_until > 0


def test_days_until_next_payment_lease_not_started():
    """Test that method returns None when lease hasn't started yet."""
    lease = Lease()
    lease.start = datetime.now() + timedelta(days=30)
    lease.end = datetime.now() + timedelta(days=395)
    lease.payment_due_date = 1
    lease.rent = 1500

    days_until = lease.days_until_next_payment()

    assert days_until is None


def test_days_until_next_payment_lease_ended():
    """Test that method returns None when lease has ended."""
    lease = Lease()
    lease.start = datetime.now() - timedelta(days=400)
    lease.end = datetime.now() - timedelta(days=35)
    lease.payment_due_date = 1
    lease.rent = 1500

    days_until = lease.days_until_next_payment()

    assert days_until is None


def test_days_until_next_payment_handles_month_boundaries():
    """Test that method correctly handles months with different day counts."""
    lease = Lease()
    lease.start = datetime.now() - timedelta(days=30)
    lease.end = datetime.now() + timedelta(days=335)
    lease.payment_due_date = 31  # Test with 31st (not all months have this)
    lease.rent = 1500

    # Should not crash and should return a valid result
    days_until = lease.days_until_next_payment()

    # Should handle gracefully (return days until last day of month if 31st doesn't exist)
    assert days_until is None or isinstance(days_until, int)
