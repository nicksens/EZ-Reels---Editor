"""
Input validation utilities for Easy Reels application.
"""

import re
from urllib.parse import urlparse


class URLValidator:
    """Validates Instagram URLs and other inputs."""

    def __init__(self):
        # Instagram URL patterns
        self.instagram_patterns = [
            r'https?://(?:www\.)?instagram\.com/reels/([A-Za-z0-9_-]+)',
            r'https?://(?:www\.)?instagram\.com/reel/([A-Za-z0-9_-]+)',
            r'https?://(?:www\.)?instagram\.com/p/([A-Za-z0-9_-]+)',
            r'https?://(?:www\.)?instagram\.com/tv/([A-Za-z0-9_-]+)'
        ]

    def is_valid_instagram_url(self, url: str) -> bool:
        """Check if URL is a valid Instagram reel/post URL."""
        if not url:
            return False

        for pattern in self.instagram_patterns:
            if re.match(pattern, url):
                return True

        return False

    def extract_shortcode(self, url: str) -> str:
        """Extract shortcode from Instagram URL."""
        for pattern in self.instagram_patterns:
            match = re.match(pattern, url)
            if match:
                return match.group(1)

        raise ValueError("Could not extract shortcode from URL")

    def is_valid_image_file(self, file_path: str) -> bool:
        """Check if file is a valid image."""
        valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        return any(file_path.lower().endswith(ext) for ext in valid_extensions)
