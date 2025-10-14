import instaloader
import requests
import os
import sys
import io
from contextlib import redirect_stderr
from pathlib import Path
from typing import Tuple, Dict
from .ocr_extractor import OCRExtractor
from .config_manager import config


def parse_instagram_url(url: str) -> str:
    """Parse Instagram URL and extract shortcode - handles ALL formats."""
    url = url.strip()

    # All possible Instagram URL patterns
    patterns = ["/reel/", "/reels/", "/p/", "/tv/"]

    for pattern in patterns:
        if pattern in url:
            parts = url.split(pattern)
            if len(parts) > 1:
                shortcode = parts[1].split("/")[0].split("?")[0]
                return shortcode

    # Fallback: try to extract from end of URL
    url_parts = url.rstrip('/').split('/')
    if url_parts:
        potential_shortcode = url_parts[-1].split('?')[0]
        if potential_shortcode and len(potential_shortcode) > 5:
            return potential_shortcode

    raise ValueError(f"Could not extract shortcode from URL: {url}")


def initialize_instaloader():
    """Initializes and logs into Instaloader quietly."""
    print("Initializing Instaloader and logging in...")

    L = instaloader.Instaloader(
        quiet=False,
        download_pictures=False,
        download_video_thumbnails=False,
        save_metadata=False,
        compress_json=False,
        download_geotags=False,
        download_comments=False
    )

    try:
        L.load_session_from_file(config.instagram_username)
        print("Loaded existing session")
    except FileNotFoundError:
        L.login(config.instagram_username, config.instagram_password)
        L.save_session_to_file()
        print("Login successful!")

    return L


def get_post(L, shortcode):
    """Fetches the post data while filtering out unwanted logs."""
    print("PROGRESS:STATUS:--> Fetching video metadata...")

    log_catcher = io.StringIO()
    post = None

    with redirect_stderr(log_catcher):
        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
        except Exception as e:
            print(f"PROGRESS:ERROR:An error occurred while fetching post: {e}")
            raise

    log_output = log_catcher.getvalue()
    for line in log_output.splitlines():
        if not ("JSON Query to" in line and "/info/" in line) and not ("Unable to fetch high-quality" in line):
            print(line)

    return post


def download_video_with_metadata(post, output_path: str) -> Dict[str, str]:
    """
    Downloads video and extracts metadata including OCR text.
    
    Args:
        post: Instaloader Post object
        output_path: Path where video will be saved
    
    Returns:
        dict with:
            - 'video_path': Path to downloaded video
            - 'original_caption': Instagram post caption
            - 'original_title': OCR extracted text from video
            - 'url': Post URL
    """
    print(f"PROGRESS:STATUS:--> Downloading video to {os.path.basename(output_path)}...")
    
    # Download video
    video_url = post.video_url
    with requests.get(video_url, stream=True) as r:
        r.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    
    print(f"PROGRESS:STATUS:--> Video downloaded successfully")
    
    # Extract caption from post
    original_caption = post.caption if post.caption else ""
    
    # Extract text from video using OCR
    print(f"PROGRESS:STATUS:--> Extracting text from video using OCR...")
    try:
        ocr = OCRExtractor()
        ocr_result = ocr.extract_text_from_middle_frame(output_path)
        original_title = ocr_result.get('text', '')
        
        if original_title:
            print(f"PROGRESS:STATUS:--> OCR found text: {original_title[:50]}...")
        else:
            print(f"PROGRESS:STATUS:--> No text detected in video")
            original_title = ""
    except Exception as e:
        print(f"PROGRESS:WARNING:--> OCR failed: {e}")
        original_title = ""
    
    return {
        'video_path': output_path,
        'original_caption': original_caption,
        'original_title': original_title,
        'url': f"https://www.instagram.com/p/{post.shortcode}/"
    }


def download_video(post, output_path: str) -> str:
    """
    Downloads the video file for a given post (legacy function).
    For backward compatibility - use download_video_with_metadata() for new code.
    
    Returns:
        str: Path to downloaded video file
    """
    print(f"PROGRESS:STATUS:--> Downloading video to {os.path.basename(output_path)}...")
    
    video_url = post.video_url
    
    with requests.get(video_url, stream=True) as r:
        r.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    
    return output_path


class InstagramDownloader:
    """Instagram downloader with OCR support and fixed URL parsing."""

    def __init__(self):
        self.loader = None

    def download_reel(self, url: str) -> Dict[str, str]:
        """
        Download Instagram Reel with OCR text extraction.
        
        Args:
            url: Instagram URL (any format)
        
        Returns:
            Dict with:
                - 'video_path': Path to downloaded video
                - 'original_caption': Instagram caption
                - 'original_title': OCR extracted text
                - 'url': Post URL
        """
        try:
            print(f"Starting download from: {url}")

            # Extract shortcode using fixed parser
            shortcode = parse_instagram_url(url)
            print(f"Extracted shortcode: {shortcode}")

            # Initialize instaloader
            L = initialize_instaloader()

            # Get post data
            post = get_post(L, shortcode)

            if not post:
                raise Exception("Failed to retrieve post data")

            if not post.is_video:
                raise Exception("This post does not contain a video")

            # Create output path
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)

            output_filename = f"reel_{shortcode}.mp4"
            output_path = temp_dir / output_filename

            # Download video WITH metadata (including OCR) ← KEY CHANGE!
            metadata = download_video_with_metadata(post, str(output_path))

            print(f"Download completed: {output_path}")
            
            # Log what we extracted
            if metadata['original_title']:
                print(f"✅ OCR extracted: {metadata['original_title'][:50]}...")
            if metadata['original_caption']:
                print(f"📝 Caption length: {len(metadata['original_caption'])} chars")
            
            return metadata  # ← Returns dict, not tuple!

        except Exception as e:
            print(f"Download error: {e}")
            raise

    def download_reel_legacy(self, url: str) -> Tuple[str, str]:
        """
        Legacy function for backward compatibility.
        Returns only (video_path, caption) tuple.
        
        For new code, use download_reel() which returns full metadata dict.
        """
        metadata = self.download_reel(url)
        return metadata['video_path'], metadata['original_caption']


# Function wrappers
def download_instagram_reel(url: str) -> Dict[str, str]:
    """
    Download Instagram reel with full metadata including OCR.
    
    Returns:
        Dict with video_path, original_caption, original_title, url
    """
    downloader = InstagramDownloader()
    return downloader.download_reel(url)


def download_instagram_reel_legacy(url: str) -> Tuple[str, str]:
    """
    Legacy function - returns only (video_path, caption).
    Use download_instagram_reel() for new code.
    """
    downloader = InstagramDownloader()
    return downloader.download_reel_legacy(url)