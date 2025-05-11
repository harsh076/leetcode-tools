#!/usr/bin/env python3
import sys
from rich.console import Console

from .parser import setup_parsers, setup_selector_parser
from .commands import (
    handle_login, handle_fetch, handle_add_to_list,
    handle_update_db, handle_configure_db, handle_select_problems,
    handle_help, handle_config
)
from ..core.config import ConfigManager
from ..core.database import DatabaseManager
from ..api.client import LeetCodeAPIClient

console = Console()


def main(args=None):
    """Main entry point for the CLI application."""
    try:
        cli_main(args)
    except KeyboardInterrupt:
        console.print("\nOperation cancelled by user.", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"An unexpected error occurred: {e}", style="red")
        sys.exit(1)


def cli_main(args=None):
    """
    Run the main CLI application with given arguments.

    Args:
        args: Command-line arguments (if None, use sys.argv)
    """
    # Parse arguments
    parser = setup_parsers()
    args = parser.parse_args(args)

    # Initialize core components
    config_manager = ConfigManager()
    api_client = LeetCodeAPIClient()

    # Set API client auth tokens from config
    auth = config_manager.get_auth_tokens()
    api_client.set_auth_tokens(auth["session"], auth["csrf"])

    # Initialize database manager with config
    db_manager = DatabaseManager(config_manager.get_db_config())

    # Execute the requested command
    if args.command == 'login':
        handle_login(args, config_manager, api_client)
    elif args.command == 'fetch':
        handle_fetch(args, config_manager, api_client)
    elif args.command == 'add-to-list':
        handle_add_to_list(args, config_manager, api_client)
    elif args.command == 'update-db':
        handle_update_db(args, config_manager, db_manager, api_client)
    elif args.command == 'configure-db':
        handle_configure_db(args, config_manager)
    elif args.command == 'select-problems':
        handle_select_problems(args, config_manager, db_manager, api_client)
    elif args.command == 'config':
        handle_config(args, config_manager)
    elif args.command == 'help' or args.command is None:
        handle_help()
    else:
        console.print("Unknown command. Use 'leetcode-cli help' for usage information.", style="red")
        sys.exit(1)


def selector_main(args=None):
    """
    Run the selector CLI application with given arguments.

    Args:
        args: Command-line arguments (if None, use sys.argv)
    """
    try:
        # Parse arguments
        parser = setup_selector_parser()
        args = parser.parse_args(args)

        # Initialize core components
        config_path = args.config if hasattr(args, 'config') and args.config else None
        config_manager = ConfigManager(config_path)

        # Initialize API client if needed
        api_client = LeetCodeAPIClient()
        auth = config_manager.get_auth_tokens()
        api_client.set_auth_tokens(auth["session"], auth["csrf"])

        # Initialize database manager
        db_manager = DatabaseManager(config_manager.get_db_config())
        if not db_manager.connect():
            sys.exit(1)

        try:
            # Handle select problems command
            handle_select_problems(args, config_manager, db_manager, api_client)
        finally:
            # Close database connection
            db_manager.close()

    except KeyboardInterrupt:
        console.print("\nOperation cancelled by user.", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"An unexpected error occurred: {e}", style="red")
        sys.exit(1)