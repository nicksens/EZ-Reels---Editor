"""
Settings manager for batch processing and custom file naming.
Handles user preferences for batch operations.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class BatchSettingsManager:
    """Manages batch processing settings and file naming conventions."""

    def __init__(self):
        self.settings_file = Path("config") / "batch_settings.json"
        self.settings_file.parent.mkdir(exist_ok=True)
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        """Load batch settings from file."""
        default_settings = {
            "USE_CUSTOM_DATE": True,
            "CUSTOM_DATE_STR": "24",
            "DAY_LIMIT": 50,
            "AUTO_CONTINUE_ON_ERROR": True,
            "SHOW_DETAILED_PROGRESS": True,
            "SAVE_FAILED_URLS": True
        }

        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, default_value in default_settings.items():
                    if key not in settings:
                        settings[key] = default_value
                return settings
        except Exception as e:
            print(f"Error loading batch settings: {e}")

        return default_settings

    def save_settings(self) -> bool:
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving batch settings: {e}")
            return False

    def get(self, key: str, default=None):
        """Get setting value."""
        return self.settings.get(key, default)

    def set(self, key: str, value):
        """Set setting value."""
        self.settings[key] = value

    def get_custom_naming_enabled(self) -> bool:
        """Check if custom file naming is enabled."""
        return self.get("USE_CUSTOM_DATE", False)

    def get_file_prefix(self) -> str:
        """Get custom file prefix."""
        return self.get("CUSTOM_DATE_STR", "24")

    def get_daily_limit(self) -> int:
        """Get daily video limit."""
        return self.get("DAY_LIMIT", 50)

    def should_auto_continue_on_error(self) -> bool:
        """Check if should continue processing on error."""
        return self.get("AUTO_CONTINUE_ON_ERROR", True)


# Global settings instance
batch_settings = BatchSettingsManager()
