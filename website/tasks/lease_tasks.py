"""
Lease-related scheduled tasks.

These tasks should be run daily to keep lease statuses up-to-date.
"""

from datetime import datetime
from website import db
from website.models import Lease, Company


def update_all_lease_statuses(company_id=None):
    """
    Update all lease statuses based on current date.

    This should be run daily to ensure:
    - Pending leases become active when start date arrives
    - Active leases become expiring when within 30 days of end
    - Expiring/active leases become expired when end date passes

    Args:
        company_id: Optional company_id to limit updates to specific company

    Returns:
        dict: Summary of updates performed
    """
    print(f"[{datetime.now()}] Starting lease status updates...")

    summary = Lease.update_all_statuses(company_id=company_id)

    print(f"[{datetime.now()}] Lease status update complete:")
    print(f"  Total leases processed: {summary['total_processed']}")
    print(f"  Statuses changed: {summary['status_changed']}")
    if summary['by_status']:
        print(f"  Status breakdown:")
        for status, count in summary['by_status'].items():
            print(f"    - {status}: {count}")

    return summary


def update_lease_statuses_all_companies():
    """
    Update lease statuses for all companies in the system.

    Returns:
        dict: Summary with company-level breakdown
    """
    from website.models import Company

    print(f"[{datetime.now()}] Starting company-wide lease status updates...")

    companies = Company.query.all()
    company_summaries = {}
    total_summary = {
        'companies_processed': 0,
        'total_leases': 0,
        'total_changed': 0
    }

    for company in companies:
        print(f"[{datetime.now()}] Processing company: {company.name} (ID: {company.id})")
        summary = update_all_lease_statuses(company_id=company.id)

        company_summaries[company.id] = {
            'company_name': company.name,
            'summary': summary
        }

        total_summary['companies_processed'] += 1
        total_summary['total_leases'] += summary['total_processed']
        total_summary['total_changed'] += summary['status_changed']

    print(f"[{datetime.now()}] All companies processed:")
    print(f"  Total companies: {total_summary['companies_processed']}")
    print(f"  Total leases: {total_summary['total_leases']}")
    print(f"  Total changed: {total_summary['total_changed']}")

    return {
        'summary': total_summary,
        'companies': company_summaries
    }


def send_lease_expiration_notifications():
    """
    Send notifications for leases expiring soon.

    Notifications sent for leases expiring in:
    - 90 days
    - 60 days
    - 30 days
    - 14 days
    - 7 days

    TODO: Implement email notification system
    """
    from datetime import timedelta

    print(f"[{datetime.now()}] Checking for lease expiration notifications...")

    today = datetime.now().date()
    notification_periods = [90, 60, 30, 14, 7]

    notifications_sent = 0

    for days in notification_periods:
        target_date = today + timedelta(days=days)

        # Find leases expiring on target date
        expiring_leases = Lease.query.filter(
            db.func.date(Lease.end) == target_date,
            Lease.lease_status.in_(['active', 'expiring'])
        ).all()

        for lease in expiring_leases:
            # TODO: Send email notification to tenant and property manager
            print(f"  Lease {lease.uuid} expiring in {days} days")
            print(f"    Tenant: {lease.tenant_ref.first_name} {lease.tenant_ref.last_name}")
            print(f"    Unit: {lease.unit_ref.name}")
            print(f"    Property: {lease.property_ref.name}")

            # For now, just count
            notifications_sent += 1

    print(f"[{datetime.now()}] Notifications checked: {notifications_sent} leases expiring soon")

    return {
        'notifications_sent': notifications_sent
    }


def cleanup_expired_leases(days_after_expiration=365):
    """
    Archive or clean up very old expired leases.

    Args:
        days_after_expiration: Number of days after expiration to consider for cleanup

    Returns:
        dict: Summary of cleanup operations
    """
    from datetime import timedelta

    print(f"[{datetime.now()}] Checking for old expired leases to archive...")

    cutoff_date = datetime.now().date() - timedelta(days=days_after_expiration)

    old_expired_leases = Lease.query.filter(
        db.func.date(Lease.end) < cutoff_date,
        Lease.lease_status == 'expired'
    ).all()

    print(f"  Found {len(old_expired_leases)} old expired leases (ended before {cutoff_date})")

    # For now, just report - don't actually delete
    # In the future, could:
    # - Archive to separate table
    # - Export to long-term storage
    # - Delete if no associated payments/documents

    return {
        'old_leases_found': len(old_expired_leases),
        'cutoff_date': cutoff_date
    }


if __name__ == '__main__':
    """
    Allow running tasks directly for testing/manual execution.

    Usage:
        python -m website.tasks.lease_tasks
    """
    from website import create_app

    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("RE2 Lease Status Update Task")
        print("=" * 70)

        # Update all lease statuses
        result = update_lease_statuses_all_companies()

        print("\n" + "=" * 70)
        print("Lease Expiration Notification Check")
        print("=" * 70)

        # Check for expiring leases
        expiration_result = send_lease_expiration_notifications()

        print("\n" + "=" * 70)
        print("Old Lease Cleanup Check")
        print("=" * 70)

        # Check for old leases
        cleanup_result = cleanup_expired_leases()

        print("\n" + "=" * 70)
        print("Task Complete")
        print("=" * 70)
