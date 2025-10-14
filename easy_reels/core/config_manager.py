"""
Configuration management for Easy Reels application.
Loads settings from .env file and provides configuration access.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import json
from typing import Dict, Any, Optional

# Load environment variables from .env file
load_dotenv()

class ConfigManager:
    """Manages application configuration and settings."""

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent.parent / "config"
        self.settings_file = self.config_dir / "user_settings.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        self.config_dir.mkdir(exist_ok=True)

    @property
    def groq_api_key(self) -> Optional[str]:
        """Get Groq API key from environment."""
        return os.getenv("GROQ_API_KEY")

    @property
    def instagram_username(self) -> Optional[str]:
        """Get Instagram username from environment."""
        return os.getenv("INSTAGRAM_USERNAME")

    @property
    def instagram_password(self) -> Optional[str]:
        """Get Instagram password from environment."""
        return os.getenv("INSTAGRAM_PASSWORD")

    def validate_credentials(self) -> Dict[str, bool]:
        """Validate that required credentials are available."""
        return {
            "groq_api_key": bool(self.groq_api_key),
            "instagram_username": bool(self.instagram_username),
            "instagram_password": bool(self.instagram_password)
        }

# Global config instance
config = ConfigManager()
