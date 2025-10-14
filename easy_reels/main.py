#!/usr/bin/env python3
"""
Easy Reels - Main Application Entry Point
Coordinates all modules and provides simple CLI interface for testing
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import our modules
from easy_reels.core.config_manager import config
from easy_reels.core.instagram_downloader import InstagramDownloader
from easy_reels.core.ai_content_generator import AIContentGenerator  
from easy_reels.core.video_processor import VideoProcessor


def test_complete_workflow():
    """Test the complete workflow with all modules."""
    print("🚀 EASY REELS - COMPLETE WORKFLOW TEST")
    print("=" * 50)
    print()

    # Validate credentials
    credentials = config.validate_credentials()
    print("📋 Credential Check:")
    for cred, status in credentials.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {cred}: {'OK' if status else 'MISSING'}")

    if not all(credentials.values()):
        print()
        print("⚠️  Please configure your .env file with all required credentials:")
        print("   - INSTAGRAM_USERNAME")
        print("   - INSTAGRAM_PASSWORD")
        print("   - GROQ_API_KEY")
        return False

    print()
    print("🎯 All modules loaded successfully!")
    print("Ready to process Instagram Reels!")

    return True


def process_single_reel(url: str):
    """Process a single Instagram Reel through the complete pipeline."""
    try:
        print(f"\n🎬 PROCESSING REEL: {url}")
        print("-" * 50)

        # Step 1: Download
        print("\n1️⃣ DOWNLOADING...")
        downloader = InstagramDownloader()
        video_path, original_caption = downloader.download_reel(url)
        print(f"   ✅ Downloaded: {video_path}")
        print(f"   📝 Caption: {original_caption[:100]}...")

        # Step 2: Generate AI Content  
        print("\n2️⃣ GENERATING AI CONTENT...")
        ai_generator = AIContentGenerator()
        ai_content = ai_generator.generate_complete_content(original_caption)
        print(f"   ✅ Title: {ai_content['title']}")
        print(f"   📝 Caption: {ai_content['caption'][:100]}...")

        # Step 3: Process Video
        print("\n3️⃣ PROCESSING VIDEO...")
        processor = VideoProcessor()

        # Default branding assets (create these folders/files)
        branding_assets = {
            'logo_path': 'assets/branding/logo.png',
            'profile_pic_path': 'assets/branding/profpic.jpg'
        }

        processing_options = {
            'auto_crop': True,
            'add_branding': True, 
            'add_title_overlay': True,
            'add_subtitles': False,
            'output_quality': 'high'
        }

        final_video = processor.process_video(
            video_path,
            ai_content, 
            branding_assets,
            processing_options
        )

        print(f"   ✅ Final video: {final_video}")

        # Cleanup temp file
        if os.path.exists(video_path):
            os.remove(video_path)

        print("\n🎉 PROCESSING COMPLETE!")
        print(f"Final video saved to: {final_video}")

        return final_video

    except Exception as e:
        print(f"\n❌ Error processing reel: {e}")
        return None


def main():
    """Main entry point."""
    print("🎯 Easy Reels - Automated Video Creator")
    print("=" * 40)

    # Test all modules
    if not test_complete_workflow():
        return

    print("\n" + "="*50)
    print("READY FOR TESTING!")
    print("="*50)
    print()
    print("To test the complete pipeline:")
    print("1. Make sure you have branding assets in assets/branding/")
    print("2. Run: process_single_reel('INSTAGRAM_REEL_URL')")
    print("3. Or wait for the GUI in the next step!")

    # Uncomment to test with a real URL:
    # test_url = input("\nEnter Instagram Reel URL to test (or press Enter to skip): ").strip()
    # if test_url:
    #     process_single_reel(test_url)


if __name__ == "__main__":
    main()
