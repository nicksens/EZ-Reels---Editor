"""
File naming utility for batch processing.
Handles sequential file naming with custom prefixes.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


class FileNamingManager:
    """Manages sequential file naming for batch processing."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def get_existing_files(self, prefix: str) -> List[Path]:
        """Get all existing files with the given prefix pattern."""
        pattern = f"{prefix}-*.mp4"
        return list(self.output_dir.glob(pattern))

    def extract_counter_from_filename(self, filename: str, prefix: str) -> Optional[int]:
        """Extract counter number from filename."""
        # Pattern: prefix-number.mp4
        pattern = rf"{re.escape(prefix)}-(\d+)\.mp4$"
        match = re.match(pattern, filename)
        if match:
            return int(match.group(1))
        return None

    def get_next_counter(self, prefix: str) -> int:
        """Get the next available counter for the given prefix."""
        existing_files = self.get_existing_files(prefix)

        if not existing_files:
            return 1

        # Extract all counter numbers
        counters = []
        for file_path in existing_files:
            counter = self.extract_counter_from_filename(file_path.name, prefix)
            if counter is not None:
                counters.append(counter)

        if not counters:
            return 1

        # Return the next sequential number
        return max(counters) + 1

    def generate_filename(self, prefix: str, extension: str = ".mp4") -> str:
        """Generate next sequential filename with prefix."""
        counter = self.get_next_counter(prefix)
        return f"{prefix}-{counter}{extension}"

    def generate_output_path(self, prefix: str, extension: str = ".mp4") -> str:
        """Generate full output path for next sequential file."""
        filename = self.generate_filename(prefix, extension)
        return str(self.output_dir / filename)

    def check_daily_limit(self, prefix: str, limit: int) -> tuple[bool, int]:
        """Check if daily limit is reached. Returns (within_limit, current_count)."""
        existing_files = self.get_existing_files(prefix)
        current_count = len(existing_files)
        return current_count < limit, current_count

    def get_caption_filename(self, video_filename: str) -> str:
        """Get corresponding caption filename for a video."""
        video_path = Path(video_filename)
        caption_name = video_path.stem + "_caption.txt"
        return str(self.output_dir / caption_name)


class BatchProgressTracker:
    """Tracks progress across batch processing operations."""

    def __init__(self, total_urls: int):
        self.total_urls = total_urls
        self.current_index = 0
        self.successful_count = 0
        self.failed_count = 0
        self.failed_urls = []

    def start_next_video(self, url: str):
        """Start processing next video."""
        self.current_index += 1
        self.current_url = url

    def mark_success(self, output_path: str):
        """Mark current video as successful."""
        self.successful_count += 1

    def mark_failure(self, url: str, error: str):
        """Mark current video as failed."""
        self.failed_count += 1
        self.failed_urls.append({
            'url': url,
            'error': error,
            'index': self.current_index
        })

    def get_progress_text(self, current_step: str = "") -> str:
        """Get formatted progress text."""
        base_text = f"Processing Video {self.current_index} of {self.total_urls}"
        if current_step:
            return f"{base_text}: {current_step}"
        return base_text

    def get_progress_percentage(self) -> float:
        """Get overall progress percentage (0.0 to 1.0)."""
        if self.total_urls == 0:
            return 0.0
        return (self.current_index - 1) / self.total_urls

    def get_final_summary(self) -> Dict[str, Any]:
        """Get final batch processing summary."""
        return {
            'total_urls': self.total_urls,
            'successful': self.successful_count,
            'failed': self.failed_count,
            'failed_urls': self.failed_urls,
            'completion_rate': self.successful_count / self.total_urls if self.total_urls > 0 else 0
        }

    def save_failed_urls_report(self, output_dir: str):
        """Save failed URLs report to file."""
        if not self.failed_urls:
            return

        report_path = Path(output_dir) / f"failed_urls_report_{int(time.time())}.txt"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("BATCH PROCESSING FAILED URLS REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total URLs processed: {self.total_urls}\n")
            f.write(f"Successful: {self.successful_count}\n")
            f.write(f"Failed: {self.failed_count}\n\n")

            for failed in self.failed_urls:
                f.write(f"Video {failed['index']}: {failed['url']}\n")
                f.write(f"Error: {failed['error']}\n\n")

        print(f"Failed URLs report saved: {report_path}")


import time
from typing import Dict, Any
