"""
Command-line interface module for LeetCode tools.
"""

from .main import main, cli_main, selector_main
from .commands import (
    handle_login, handle_fetch, handle_add_to_list,
    handle_update_db, handle_configure_db, handle_select_problems,
    handle_help, handle_config
)
from .parser import setup_parsers, setup_selector_parser

__all__ = [
    'main', 'cli_main', 'selector_main',
    'handle_login', 'handle_fetch', 'handle_add_to_list',
    'handle_update_db', 'handle_configure_db', 'handle_select_problems',
    'handle_help', 'handle_config',
    'setup_parsers', 'setup_selector_parser'
]