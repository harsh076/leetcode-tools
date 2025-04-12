#!/usr/bin/env python3
import json
import os
from typing import Dict, Any, Optional
from rich.console import Console
import appdirs

console = Console()


class ConfigManager:
    """Manages configuration files for the LeetCode CLI."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize with path to config file.

        Args:
            config_path: Optional custom path to config file.
                         If None, use the standard user config location.
        """
        self.app_name = "leetcode-tools"

        if config_path is None:
            # Use standard user config directory
            config_dir = appdirs.user_config_dir(self.app_name)
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "config.json")
        else:
            self.config_path = config_path

        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from the config file or create default."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                # Create a default config if not exists
                default_config = {
                    "session": "",
                    "csrf": "",
                    "db_config": {
                        "host": "localhost",
                        "user": "root",
                        "password": "root",
                        "database": "leetcode"
                    },
                    "data_dir": self._get_default_data_dir()
                }
                self._save_config(default_config)
                console.print(
                    f"Created default config file at {self.config_path}. Please update with your credentials.",
                    style="yellow")
                return default_config

        except Exception as e:
            console.print(f"Error loading config: {e}", style="red")
            # Create a minimal default config as fallback
            return {
                "session": "",
                "csrf": "",
                "db_config": {
                    "host": "localhost",
                    "user": "root",
                    "password": "root",
                    "database": "leetcode"
                },
                "data_dir": self._get_default_data_dir()
            }

    def _get_default_data_dir(self) -> str:
        """Get the default data directory."""
        data_dir = appdirs.user_data_dir(self.app_name)
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            console.print(f"Error saving config: {e}", style="red")
            return False

    def save(self) -> bool:
        """Save the current configuration."""
        return self._save_config(self.config)

    def get_auth_tokens(self) -> Dict[str, str]:
        """Get authentication tokens."""
        return {
            "session": self.config.get("session", ""),
            "csrf": self.config.get("csrf", "")
        }

    def set_auth_tokens(self, session: str, csrf: str) -> bool:
        """Set authentication tokens."""
        self.config["session"] = session
        self.config["csrf"] = csrf
        return self.save()

    def get_db_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.config.get("db_config", {
            "host": "localhost",
            "user": "root",
            "password": "root",
            "database": "leetcode"
        })

    def set_db_config(self, host: str, user: str, password: str, database: str) -> bool:
        """Set database configuration."""
        self.config["db_config"] = {
            "host": host,
            "user": user,
            "password": password,
            "database": database
        }
        return self.save()

    def get_data_dir(self) -> str:
        """Get the data directory."""
        data_dir = self.config.get("data_dir")
        if not data_dir:
            data_dir = self._get_default_data_dir()
            self.config["data_dir"] = data_dir
            self.save()

        # Ensure directory exists
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

    def get_data_file_path(self, filename: str) -> str:
        """
        Get the full path to a data file.

        Args:
            filename: The name of the file

        Returns:
            Full path to the file
        """
        return os.path.join(self.get_data_dir(), filename)

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the configuration."""
        return self.config.get(key, default)

    def set_value(self, key: str, value: Any) -> bool:
        """Set a value in the configuration."""
        self.config[key] = value
        return self.save()