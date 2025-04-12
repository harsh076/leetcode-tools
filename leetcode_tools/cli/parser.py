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
  leetcode-cli fetch
  leetcode-cli add-to-list LIST_ID --problems-file=problems.txt
  leetcode-cli update-db
  leetcode-cli configure-db --host=localhost --user=root --password=root --database=leetcode
  leetcode-cli help
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Login command
    login_parser = subparsers.add_parser('login', help='Update LeetCode session and CSRF tokens')
    login_parser.add_argument('--session', required=True, help='Your LeetCode session token')
    login_parser.add_argument('--csrf', required=True, help='Your LeetCode CSRF token')

    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch all LeetCode problems and save to JSON/CSV')
    fetch_parser.add_argument('--json-file', help='Output JSON file path')
    fetch_parser.add_argument('--csv-file', help='Output CSV file path')
    fetch_parser.add_argument('--no-csv', action='store_true', help='Skip CSV generation')

    # Add to list command
    add_list_parser = subparsers.add_parser('add-to-list', help='Add problems from a file to a LeetCode list')
    add_list_parser.add_argument('list_id', help='Your LeetCode list ID')
    add_list_parser.add_argument('--problems-file', default='problems.txt', help='File containing problem slugs or IDs')
    add_list_parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests in seconds')

    # Update database command
    update_db_parser = subparsers.add_parser('update-db', help='Update database with problem information')
    update_db_parser.add_argument('--json-file', help='JSON file with problem data')

    # Configure database command
    config_db_parser = subparsers.add_parser('configure-db', help='Configure database connection settings')
    config_db_parser.add_argument('--host', default='localhost', help='Database host')
    config_db_parser.add_argument('--user', default='root', help='Database user')
    config_db_parser.add_argument('--password', default='root', help='Database password')
    config_db_parser.add_argument('--database', default='leetcode', help='Database name')

    # Select problems command
    select_problems_parser = subparsers.add_parser('select-problems', help='Select high-quality LeetCode problems')
    select_problems_parser.add_argument('rating_bracket', help='Rating bracket to generate problems for')
    select_problems_parser.add_argument('problem_count', type=int, help='Total number of problems to generate')
    select_problems_parser.add_argument('--output', '-o', required=True, help='Output file for problem list')
    select_problems_parser.add_argument('--display', '-d', action='store_true', help='Display the problem list')
    select_problems_parser.add_argument('--rating-brackets', help='Path to custom rating brackets config file')
    select_problems_parser.add_argument('--topic-weights', help='Path to custom topic weights config file')

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
  leetcode-selector 1700-1800 100 --output=problems_1700_1800.txt
  leetcode-selector 2000-2100 50 --output=problems_2000_2100.txt --display
        """
    )

    parser.add_argument('rating_bracket', help='Rating bracket to generate problems for')
    parser.add_argument('problem_count', type=int, help='Total number of problems to generate')
    parser.add_argument('--output', '-o', required=True, help='Output file for problem list')
    parser.add_argument('--display', '-d', action='store_true', help='Display the problem list')
    parser.add_argument('--rating-brackets', help='Path to custom rating brackets JSON file')
    parser.add_argument('--topic-weights', help='Path to custom topic weights JSON file')
    parser.add_argument('--config', help='Path to config file')

    return parser