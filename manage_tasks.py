#!/usr/bin/env python3
"""
Management script for running RE2 scheduled tasks.

Usage:
    python manage_tasks.py update_leases              # Update all lease statuses
    python manage_tasks.py update_leases --company=5  # Update specific company
    python manage_tasks.py check_expirations          # Check for expiring leases
    python manage_tasks.py cleanup_old_leases         # Clean up old expired leases
    python manage_tasks.py run_all                    # Run all tasks
"""

import sys
import argparse
from website import create_app
from website.tasks.lease_tasks import (
    update_all_lease_statuses,
    update_lease_statuses_all_companies,
    send_lease_expiration_notifications,
    cleanup_expired_leases
)


def update_leases_command(args):
    """Update lease statuses."""
    app = create_app()

    with app.app_context():
        if args.company:
            print(f"Updating lease statuses for company ID: {args.company}")
            result = update_all_lease_statuses(company_id=args.company)
        else:
            print("Updating lease statuses for all companies")
            result = update_lease_statuses_all_companies()

        print("\nUpdate complete!")
        return result


def check_expirations_command(args):
    """Check for expiring leases and send notifications."""
    app = create_app()

    with app.app_context():
        print("Checking for lease expirations...")
        result = send_lease_expiration_notifications()
        print("\nExpiration check complete!")
        return result


def cleanup_old_leases_command(args):
    """Clean up old expired leases."""
    app = create_app()

    with app.app_context():
        days = args.days if hasattr(args, 'days') else 365
        print(f"Checking for leases expired more than {days} days ago...")
        result = cleanup_expired_leases(days_after_expiration=days)
        print("\nCleanup check complete!")
        return result


def run_all_command(args):
    """Run all tasks in sequence."""
    print("=" * 70)
    print("Running all scheduled tasks")
    print("=" * 70)
    print()

    # Update lease statuses
    print("1. Updating lease statuses...")
    update_leases_command(args)
    print()

    # Check expirations
    print("2. Checking for expiring leases...")
    check_expirations_command(args)
    print()

    # Cleanup old leases
    print("3. Checking for old leases...")
    cleanup_old_leases_command(args)
    print()

    print("=" * 70)
    print("All tasks complete!")
    print("=" * 70)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='RE2 Task Management')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Update leases command
    update_parser = subparsers.add_parser('update_leases', help='Update lease statuses')
    update_parser.add_argument('--company', type=int, help='Limit to specific company ID')
    update_parser.set_defaults(func=update_leases_command)

    # Check expirations command
    expiration_parser = subparsers.add_parser('check_expirations', help='Check for expiring leases')
    expiration_parser.set_defaults(func=check_expirations_command)

    # Cleanup old leases command
    cleanup_parser = subparsers.add_parser('cleanup_old_leases', help='Clean up old expired leases')
    cleanup_parser.add_argument('--days', type=int, default=365,
                               help='Days after expiration to consider for cleanup (default: 365)')
    cleanup_parser.set_defaults(func=cleanup_old_leases_command)

    # Run all command
    runall_parser = subparsers.add_parser('run_all', help='Run all tasks')
    runall_parser.set_defaults(func=run_all_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute the command
    args.func(args)


if __name__ == '__main__':
    main()
