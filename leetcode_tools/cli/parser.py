#!/usr/bin/env python3
import argparse
from typing import Optional


def setup_parsers() -> argparse.ArgumentParser:
    """Set up command-line argument parsers for the main CLI tool."""
    parser = argparse.ArgumentParser(
        description="LeetCode CLI - A command-line tool for managing your LeetCode problems and lists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
          leetcode-cli login --session=YOUR_SESSION --csrf=YOUR_CSRF
          leetcode-cli sync [--json-file=problems.json] [--csv-file=problems.csv] [--no-csv]
          leetcode-cli add-to-list LIST_ID --problems-file=problems.txt
          leetcode-cli configure-db --host=localhost --user=root --password=root --database=leetcode
          leetcode-cli select-problems [--sql-script=custom.sql] [--count=20] [--output-file=problems.txt]
          leetcode-cli help
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Login command
    login_parser = subparsers.add_parser('login', help='Update LeetCode session and CSRF tokens')
    login_parser.add_argument('--session', required=True, help='Your LeetCode session token')
    login_parser.add_argument('--csrf', required=True, help='Your LeetCode CSRF token')

    # Sync command (combines fetch and update-db)
    sync_parser = subparsers.add_parser('sync', help='Fetch LeetCode problems and update the database in one step')
    sync_parser.add_argument('--json-file', help='Output JSON file path')
    sync_parser.add_argument('--csv-file', help='Output CSV file path')
    sync_parser.add_argument('--no-csv', action='store_true', help='Skip CSV generation')

    # Add to list command
    add_list_parser = subparsers.add_parser('add-to-list', help='Add problems from a file to a LeetCode list')
    add_list_parser.add_argument('list_id', help='Your LeetCode list ID')
    add_list_parser.add_argument('--problems-file', default='problems.txt', help='File containing problem slugs or IDs')
    add_list_parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests in seconds')

    # Configure database command
    config_db_parser = subparsers.add_parser('configure-db', help='Configure database connection settings')
    config_db_parser.add_argument('--host', default='localhost', help='Database host')
    config_db_parser.add_argument('--user', default='root', help='Database user')
    config_db_parser.add_argument('--password', default='root', help='Database password')
    config_db_parser.add_argument('--database', default='leetcode', help='Database name')

    # Select problems command
    select_problems_parser = subparsers.add_parser('select-problems',
                                                   help='Select high-quality problems using custom SQL')
    select_problems_parser.add_argument('--sql-script',
                                        help='Path to custom SQL script (default: Stats.sql in data directory)')
    select_problems_parser.add_argument('--count', '-n', type=int, help='Maximum number of problems to display/output')
    # Mutually exclusive group for output options
    output_group = select_problems_parser.add_mutually_exclusive_group()
    output_group.add_argument('--output-file', '-o', help='Save problem slugs to a file')
    output_group.add_argument('--list-id', '-l', help='Add problems to a LeetCode list')

    # Help command
    subparsers.add_parser('help', help='Display help information')

    # Config command
    config_parser = subparsers.add_parser('config', help='Show or update configuration')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    config_parser.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'), action='append',
                               help='Set a configuration value (can be used multiple times)')

    return parser


def setup_selector_parser() -> argparse.ArgumentParser:
    """Set up command-line argument parsers for the selector tool."""
    parser = argparse.ArgumentParser(
        description="LeetCode Quality Problem Selector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
          leetcode-selector --sql-script=custom.sql --count=20 --output-file=problems.txt
          leetcode-selector --list-id=YOUR_LIST_ID
        """
    )

    parser.add_argument('--sql-script', help='Path to custom SQL script (default: Stats.sql in data directory)')

    # Mutually exclusive group for output options
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument('--output-file', '-o', help='Save problem slugs to a file')
    output_group.add_argument('--list-id', '-l', help='Add problems to a LeetCode list')
    parser.add_argument('--config', help='Path to config file')

    return parser