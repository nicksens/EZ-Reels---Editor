"""
File management utilities for Easy Reels application.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List


class FileManager:
    """Handles file operations and asset management."""

    def __init__(self):
        self.assets_dir = Path("assets")
        self.temp_dir = Path("temp")
        self.output_dir = Path("output")

        # Ensure directories exist
        self.assets_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def copy_asset(self, source_path: str, asset_type: str) -> Optional[str]:
        """Copy asset file to assets directory."""
        try:
            source = Path(source_path)
            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            # Determine destination based on asset type
            if asset_type == "logo":
                dest = self.assets_dir / "logo.png"
            elif asset_type == "profile_pic":
                dest = self.assets_dir / "profpic.jpg"
            else:
                dest = self.assets_dir / source.name

            # Copy file
            shutil.copy2(source, dest)
            return str(dest)

        except Exception as e:
            print(f"Error copying asset: {e}")
            return None

    def cleanup_temp_files(self, keep_recent: bool = True) -> int:
        """Clean up temporary files."""
        cleaned = 0
        try:
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    # Keep recent files if requested
                    if keep_recent:
                        age_hours = (time.time() - file_path.stat().st_mtime) / 3600
                        if age_hours < 1:  # Keep files newer than 1 hour
                            continue

                    file_path.unlink()
                    cleaned += 1

        except Exception as e:
            print(f"Error cleaning temp files: {e}")

        return cleaned

    def get_output_files(self) -> List[Path]:
        """Get list of output video files."""
        try:
            return [f for f in self.output_dir.glob("*.mp4") if f.is_file()]
        except Exception:
            return []

    def ensure_assets_directory_structure(self):
        """Ensure proper assets directory structure."""
        (self.assets_dir / "branding").mkdir(exist_ok=True)
        (self.assets_dir / "fonts").mkdir(exist_ok=True)


import time  # Add missing import
