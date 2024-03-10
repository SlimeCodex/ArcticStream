# Desc: AppConfig class for managing application configuration
# This file is part of ArcticStream Library.

import json


class AppConfig:
    def __init__(self, config_file_path):
        try:
            with open(config_file_path, "r") as f:
                self.config_data = json.load(f)
        except FileNotFoundError:
            print("Error: Config file not found. Using default values.")
            self.config_data = {}

    def get(self, section, key, default_value=None):
        """Retrieves a value from the config, returning a default if not found."""
        try:
            return self.config_data[section][key]
        except KeyError:
            return default_value


# Create a global AppConfig instance
app_config = AppConfig("config.json")
