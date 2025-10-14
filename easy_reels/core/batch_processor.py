"""
Batch processor for handling multiple Instagram Reels.
Main processing logic for batch operations.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
import threading

from .config_manager import config
from .instagram_downloader import InstagramDownloader
from .ai_content_generator import AIContentGenerator
from .video_processor import VideoProcessor
from .batch_settings_manager import batch_settings
from .file_naming_manager import FileNamingManager, BatchProgressTracker
from typing import Dict, List, Any, Optional

class BatchProcessor:
    """Handles batch processing of multiple Instagram Reels."""

    def __init__(self, progress_callback: Callable[[float, str], None] = None):
        self.progress_callback = progress_callback
        self.is_processing = False
        self.should_stop = False

        # Initialize components
        self.downloader = InstagramDownloader()
        self.ai_generator = AIContentGenerator()
        self.video_processor = VideoProcessor()
        self.file_manager = FileNamingManager()

    def log_progress(self, progress: float, message: str):
        """Send progress update to callback."""
        if self.progress_callback:
            self.progress_callback(progress, message)
        print(f"[{progress*100:.1f}%] {message}")

    def parse_urls(self, urls_text: str) -> List[str]:
        """Parse URLs from multi-line text input."""
        if not urls_text.strip():
            return []

        urls = []
        lines = urls_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line and ('instagram.com' in line or 'instagr.am' in line):
                urls.append(line)

        return urls

    def validate_batch_settings(self) -> tuple[bool, str]:
        """Validate current batch settings."""
        if batch_settings.get_custom_naming_enabled():
            prefix = batch_settings.get_file_prefix()
            if not prefix or not prefix.strip():
                return False, "Custom file prefix cannot be empty"

            # Check for invalid characters
            invalid_chars = '<>:"/\\|?*'
            if any(char in prefix for char in invalid_chars):
                return False, f"File prefix contains invalid characters: {invalid_chars}"

            daily_limit = batch_settings.get_daily_limit()
            if daily_limit <= 0:
                return False, "Daily limit must be greater than 0"

        return True, "Settings are valid"

    def check_daily_limit(self, prefix: str) -> tuple[bool, int, int]:
        """Check if daily limit allows processing. Returns (can_process, current, limit)."""
        limit = batch_settings.get_daily_limit()
        can_process, current_count = self.file_manager.check_daily_limit(prefix, limit)
        return can_process, current_count, limit

    def process_single_url(self, url: str, custom_filename: str = None) -> tuple[bool, str, Dict[str, Any]]:
        """
        Process a single Instagram Reel URL.

        Returns:
            (success: bool, output_path: str, metadata: dict)
        """
        metadata = {
            'url': url,
            'download_time': 0,
            'ai_generation_time': 0,
            'processing_time': 0,
            'total_time': 0
        }

        start_time = time.time()

        try:
            # Step 1: Download
            self.log_progress(0.2, "Downloading video...")
            download_start = time.time()

            video_path, caption = self.downloader.download_reel(url)

            metadata['download_time'] = time.time() - download_start
            metadata['original_caption'] = caption

            # Step 2: Generate AI content
            self.log_progress(0.4, "Generating AI content...")
            ai_start = time.time()

            ai_content = self.ai_generator.generate_complete_content(caption)

            metadata['ai_generation_time'] = time.time() - ai_start
            metadata['ai_content'] = ai_content

            # Step 3: Process video
            self.log_progress(0.6, "Processing video...")
            processing_start = time.time()

            # Use custom filename if provided
            if custom_filename:
                # Temporarily modify the processor to use custom filename
                original_process = self.video_processor.process_video

                def custom_process_video(input_path, ai_content, branding_assets=None, options=None):
                    # Process normally but save with custom name
                    result = original_process(input_path, ai_content, branding_assets, options)

                    # Move to custom filename if different
                    result_path = Path(result)
                    custom_path = Path("output") / custom_filename

                    if result_path != custom_path:
                        result_path.rename(custom_path)

                        # Also rename caption file
                        caption_file = result_path.with_name(result_path.stem + "_caption.txt")
                        if caption_file.exists():
                            custom_caption = custom_path.with_name(custom_path.stem + "_caption.txt")
                            caption_file.rename(custom_caption)

                    return str(custom_path)

                final_video = custom_process_video(video_path, ai_content)
            else:
                final_video = self.video_processor.process_video(video_path, ai_content)

            metadata['processing_time'] = time.time() - processing_start

            # Save caption with custom naming if applicable
            if custom_filename and batch_settings.get_custom_naming_enabled():
                caption_path = self.file_manager.get_caption_filename(custom_filename)
                with open(caption_path, 'w', encoding='utf-8') as f:
                    f.write(ai_content.get('caption', ''))

            # Cleanup temp file
            if os.path.exists(video_path):
                os.remove(video_path)

            metadata['total_time'] = time.time() - start_time
            metadata['output_path'] = final_video

            self.log_progress(1.0, "Video completed successfully!")

            return True, final_video, metadata

        except Exception as e:
            error_msg = str(e)
            metadata['error'] = error_msg
            metadata['total_time'] = time.time() - start_time

            self.log_progress(0.0, f"Error: {error_msg}")

            # Cleanup on error
            try:
                if 'video_path' in locals() and os.path.exists(video_path):
                    os.remove(video_path)
            except:
                pass

            return False, error_msg, metadata

    def process_batch(self, 
                     urls: List[str], 
                     branding_assets: Dict[str, str] = None,
                     progress_callback: Callable[[float, str, Dict], None] = None) -> Dict[str, Any]:
        """
        Process multiple URLs in batch.

        Args:
            urls: List of Instagram Reel URLs
            branding_assets: Dictionary of branding asset paths
            progress_callback: Callback for progress updates (progress, message, batch_info)

        Returns:
            Dictionary with batch processing results
        """
        if self.is_processing:
            raise Exception("Batch processing already in progress")

        self.is_processing = True
        self.should_stop = False

        try:
            # Validate settings
            settings_valid, settings_error = self.validate_batch_settings()
            if not settings_valid:
                raise Exception(f"Invalid settings: {settings_error}")

            # Initialize progress tracker
            progress_tracker = BatchProgressTracker(len(urls))

            # Check daily limit if using custom naming
            if batch_settings.get_custom_naming_enabled():
                prefix = batch_settings.get_file_prefix()
                can_process, current_count, limit = self.check_daily_limit(prefix)

                remaining_slots = limit - current_count
                if remaining_slots <= 0:
                    raise Exception(f"Daily limit reached ({current_count}/{limit}). No more videos can be processed today.")

                if len(urls) > remaining_slots:
                    self.log_progress(0.0, f"Warning: Only {remaining_slots} videos can be processed due to daily limit.")
                    urls = urls[:remaining_slots]  # Trim to remaining slots
                    progress_tracker.total_urls = len(urls)

            # Process each URL
            for i, url in enumerate(urls):
                if self.should_stop:
                    self.log_progress(0.0, "Batch processing stopped by user")
                    break

                progress_tracker.start_next_video(url)

                # Update overall progress
                overall_progress = i / len(urls)
                status_text = progress_tracker.get_progress_text()

                if progress_callback:
                    batch_info = {
                        'current_index': i + 1,
                        'total_urls': len(urls),
                        'successful_count': progress_tracker.successful_count,
                        'failed_count': progress_tracker.failed_count
                    }
                    progress_callback(overall_progress, status_text, batch_info)

                # Generate custom filename if enabled
                custom_filename = None
                if batch_settings.get_custom_naming_enabled():
                    prefix = batch_settings.get_file_prefix()
                    custom_filename = self.file_manager.generate_filename(prefix)

                # Process single URL
                success, result, metadata = self.process_single_url(url, custom_filename)

                if success:
                    progress_tracker.mark_success(result)
                    self.log_progress(overall_progress, f"✅ Video {i+1} completed: {result}")
                else:
                    progress_tracker.mark_failure(url, result)
                    self.log_progress(overall_progress, f"❌ Video {i+1} failed: {result}")

                    # Stop on error if not set to continue
                    if not batch_settings.should_auto_continue_on_error():
                        break

            # Generate final summary
            final_summary = progress_tracker.get_final_summary()

            # Save failed URLs report if any failures
            if progress_tracker.failed_urls and batch_settings.get("SAVE_FAILED_URLS", True):
                progress_tracker.save_failed_urls_report("output")

            self.log_progress(1.0, f"Batch completed: {final_summary['successful']} successful, {final_summary['failed']} failed")

            return final_summary

        finally:
            self.is_processing = False

    def stop_processing(self):
        """Stop current batch processing."""
        self.should_stop = True

    def is_busy(self) -> bool:
        """Check if processor is currently busy."""
        return self.is_processing
