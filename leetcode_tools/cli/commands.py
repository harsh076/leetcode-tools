#!/usr/bin/env python3
import os
import sys
import time
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.box import ROUNDED
from rich.progress import Progress, TaskProgressColumn, TextColumn, BarColumn, TimeRemainingColumn

from ..core.config import ConfigManager
from ..core.database import DatabaseManager
from ..core.file import FileManager
from ..api.client import LeetCodeAPIClient
from ..selector.engine import ProblemSelector

console = Console()


def handle_login(args, config_manager: ConfigManager, api_client: LeetCodeAPIClient) -> None:
    """Handle login command."""
    config_manager.set_auth_tokens(args.session, args.csrf)

    # Update API client
    api_client.set_auth_tokens(args.session, args.csrf)

    # Verify authentication
    auth_result = api_client.verify_auth()
    if auth_result["success"]:
        console.print(f"Login successful. Authenticated as: {auth_result['username']}", style="green")
    else:
        console.print(f"Login failed: {auth_result['message']}", style="red")


def handle_fetch(args, config_manager: ConfigManager, api_client: LeetCodeAPIClient) -> None:
    """Handle fetch command."""
    # Verify authentication first
    auth_result = api_client.verify_auth()
    if not auth_result["success"]:
        console.print(f"Authentication failed: {auth_result['message']}", style="red")
        return

    # Determine output file paths
    data_dir = config_manager.get_data_dir()

    json_file = args.json_file
    if not json_file:
        json_file = os.path.join(data_dir, "leetcode_problems.json")

    csv_file = args.csv_file
    if not csv_file and not args.no_csv:
        csv_file = os.path.join(data_dir, "leetcode_problems.csv")

    # Fetch problems
    problems = api_client.fetch_problems()

    if not problems:
        console.print("No problems fetched, exiting.", style="red")
        return

    # Save to JSON
    FileManager.save_to_json(problems, json_file)

    # Convert to CSV if needed
    if not args.no_csv:
        FileManager.convert_problems_to_csv(problems, csv_file)


def handle_add_to_list(args, config_manager: ConfigManager, api_client: LeetCodeAPIClient) -> None:
    """Handle add-to-list command."""
    # Verify authentication first
    auth_result = api_client.verify_auth()
    if not auth_result["success"]:
        console.print(f"Authentication failed: {auth_result['message']}", style="red")
        return

    # Load problems from file
    problems = FileManager.load_problem_slugs(args.problems_file)

    if not problems:
        console.print(f"No problems loaded from {args.problems_file}", style="red")
        return

    console.print(f"Loaded {len(problems)} problems from {args.problems_file}")
    console.print(f"Target list ID: {args.list_id}")
    console.print(f"Using {args.delay} second delay between requests")
    console.print("─" * 50)

    success_count = 0
    fail_count = 0

    with Progress(
            TextColumn("[bold blue]Processing problems..."),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            transient=False  # This prevents flickering
    ) as progress:
        task = progress.add_task("[cyan]Adding to list...", total=len(problems))

        for i, problem_input in enumerate(problems, 1):
            progress.print(f"[{i}/{len(problems)}] Processing: {problem_input}")

            # Get the problem ID
            problem_id, error = api_client.get_problem_id(problem_input)
            if error:
                progress.print(f"  ❌ Error: {error}", style="red")
                fail_count += 1
                progress.update(task, advance=1)
                continue

            progress.print(f"  📝 Found problem ID: {problem_id}")

            # Add the problem to the list
            success, message = api_client.add_problem_to_list(args.list_id, problem_id)
            if success:
                progress.print(f"  ✅ {message}", style="green")
                success_count += 1
            else:
                progress.print(f"  ❌ {message}", style="red")
                fail_count += 1

            # Sleep to be nice to the server, but not after the last item
            if i < len(problems):
                time.sleep(args.delay)

            progress.update(task, advance=1)

    console.print("─" * 50)
    console.print(f"Summary: {success_count} added successfully, {fail_count} failed")


def handle_update_db(args, config_manager: ConfigManager, db_manager: DatabaseManager,
                     api_client: LeetCodeAPIClient) -> None:
    """Handle update-db command."""
    # Determine JSON file path
    data_dir = config_manager.get_data_dir()

    json_file = args.json_file
    if not json_file:
        json_file = os.path.join(data_dir, "leetcode_problems.json")

    # Load problems from JSON file
    problems = FileManager.load_from_json(json_file)

    if not problems:
        console.print(f"No problems loaded from {json_file}", style="red")
        return

    # Verify database connection
    if not db_manager.connect():
        return

    # Create tables if they don't exist
    db_manager.create_tables()

    # Get rating dictionary
    rating_dict = api_client.get_rating_dict()

    # Update problems in database
    with Progress(
            TextColumn("[bold blue]Updating database..."),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            transient=False  # This prevents flickering
    ) as progress:
        task = progress.add_task("[cyan]Updating problems...", total=len(problems))

        success_count = 0
        fail_count = 0

        for problem in problems:
            # Add rating to problem
            slug = problem.get('titleSlug', '')
            acceptance_rate = problem.get('acRate', 0)

            # Calculate rating
            if slug in rating_dict:
                problem['rating'] = rating_dict[slug]
            elif acceptance_rate:
                if acceptance_rate <= 10:
                    point_value = 6
                elif acceptance_rate >= 50:
                    point_value = 3
                else:
                    point_value = 6 - ((acceptance_rate - 10) / 40) * 3
                problem['rating'] = 1600 + (point_value - 3) * 200

            # Update problem in database
            if db_manager.update_problem(problem):
                success_count += 1
            else:
                fail_count += 1

            # Update progress
            progress.update(task, advance=1)

    # Commit and close
    db_manager.close()

    console.print(f"Database update completed: {success_count} successful, {fail_count} failed", style="green")


def handle_configure_db(args, config_manager: ConfigManager) -> None:
    """Handle configure-db command."""
    config_manager.set_db_config(args.host, args.user, args.password, args.database)
    console.print("Database configuration updated.", style="green")


def handle_select_problems(args, config_manager: ConfigManager, db_manager: DatabaseManager) -> None:
    """Handle select-problems command."""
    # Update config paths if provided
    if args.rating_brackets:
        config_manager.set_value("rating_brackets_path", args.rating_brackets)

    if args.topic_weights:
        config_manager.set_value("topic_weights_path", args.topic_weights)

    # Connect to database
    if not db_manager.connect():
        return

    try:
        # Initialize problem selector
        selector = ProblemSelector(
            db_manager,
            rating_brackets_path=config_manager.get_value("rating_brackets_path"),
            topic_weights_path=config_manager.get_value("topic_weights_path")
        )

        # Generate problem list
        problems = selector.generate_problem_list(args.rating_bracket, args.problem_count)

        # Display if requested
        if args.display:
            selector.display_problem_list(problems)

        # Save to file
        selector.save_to_file(problems, args.output)

    finally:
        # Close database connection
        db_manager.close()


def handle_help() -> None:
    """Display help information."""
    table = Table(title="LeetCode CLI Commands", box=ROUNDED)

    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    table.add_column("Example", style="yellow")

    table.add_row(
        "login",
        "Update LeetCode session and CSRF tokens",
        "leetcode-cli login --session=YOUR_SESSION --csrf=YOUR_CSRF"
    )
    table.add_row(
        "fetch",
        "Fetch all LeetCode problems and save to JSON/CSV",
        "leetcode-cli fetch"
    )
    table.add_row(
        "add-to-list",
        "Add problems from a file to a LeetCode list",
        "leetcode-cli add-to-list LIST_ID --problems-file=problems.txt"
    )
    table.add_row(
        "update-db",
        "Update database with problem information",
        "leetcode-cli update-db"
    )
    table.add_row(
        "configure-db",
        "Configure database connection settings",
        "leetcode-cli configure-db --host=localhost --user=root --password=root --database=leetcode"
    )
    table.add_row(
        "select-problems",
        "Select high-quality LeetCode problems",
        "leetcode-cli select-problems 1900-2000 100 --output=problems.txt"
    )
    table.add_row(
        "config",
        "Show or update configuration",
        "leetcode-cli config --show"
    )

    console.print(Panel.fit(table))

    console.print("\n[bold]Getting Your Session and CSRF Tokens:[/bold]")
    console.print("1. Log in to LeetCode in your browser")
    console.print("2. Open your browser's developer tools (F12 or right-click > Inspect)")
    console.print("3. Go to the 'Application' or 'Storage' tab")
    console.print("4. Look for Cookies under Storage")
    console.print("5. Find the 'LEETCODE_SESSION' and 'csrftoken' values")


def handle_config(args, config_manager: ConfigManager) -> None:
    """Handle config command."""
    if args.show:
        # Show current configuration
        table = Table(title="LeetCode Tools Configuration", box=ROUNDED)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")

        # Get DB config
        db_config = config_manager.get_db_config()
        for key, value in config_manager.config.items():
            if key == "session" or key == "csrf":
                # Mask authentication tokens
                masked_value = "***" + value[-4:] if value else "Not set"
                table.add_row(key, masked_value)
            elif key == "db_config":
                # Show db config as host, user, database
                table.add_row("db_host", db_config.get("host", "localhost"))
                table.add_row("db_user", db_config.get("user", "root"))
                table.add_row("db_database", db_config.get("database", "leetcode"))
                # Don't show password
            elif key == "data_dir":
                table.add_row(key, value)
            elif key == "rating_brackets_path":
                table.add_row(key, value if value else "Default")
            elif key == "topic_weights_path":
                table.add_row(key, value if value else "Default")

        console.print(table)

    # Set configuration values
    if args.set:
        for key, value in args.set:
            config_manager.set_value(key, value)
            console.print(f"Set {key} = {value}", style="green")