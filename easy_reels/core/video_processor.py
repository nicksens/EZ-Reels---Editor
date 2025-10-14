"""
Video processing module - NO IMAGEMAGICK REQUIRED
Fixed to work without ImageMagick by using PIL for text rendering
"""

import cv2
import numpy as np
import os
import time
import gc
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont
import tempfile
import re
import datetime

# Import MoviePy - handle both versions
try:
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, ColorClip
except ImportError:
    from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, ColorClip

from .config_manager import config


def detect_crop_dimensions(video_path: str, num_frames_to_sample=15) -> dict | None:
    """Detect crop dimensions using background subtraction."""
    cap = None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_indices = np.linspace(0, frame_count - 1, num_frames_to_sample, dtype=int)
        
        frames = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (21, 21), 0)
                frames.append(blurred)
        
        if len(frames) < 3:
            return None
        
        median_frame = np.median(frames, axis=0).astype(np.uint8)
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_count / 2))
        ret, middle_frame = cap.read()
        if not ret:
            return None
        
        middle_gray = cv2.cvtColor(middle_frame, cv2.COLOR_BGR2GRAY)
        middle_blurred = cv2.GaussianBlur(middle_gray, (21, 21), 0)
        foreground_mask = cv2.absdiff(middle_blurred, median_frame)
        _, foreground_mask = cv2.threshold(foreground_mask, 10, 255, cv2.THRESH_BINARY)
        moving_pixels = np.where(foreground_mask > 0)
        
        if moving_pixels[0].size < (width * height * 0.01):
            return None
        
        y_min, y_max = np.min(moving_pixels[0]), np.max(moving_pixels[0])
        x_min, x_max = np.min(moving_pixels[1]), np.max(moving_pixels[1])
        
        padding = 5
        y_min = max(0, y_min - padding)
        y_max = min(height, y_max + padding)
        x_min = max(0, x_min - padding)
        x_max = min(width, x_max + padding)
        
        w = (x_max - x_min)
        h = (y_max - y_min)
        
        if w < width * 0.25 or h < height * 0.25:
            return None
        
        w -= (w % 2)
        h -= (h % 2)
        x = x_min - (x_min % 2)
        y = y_min - (y_min % 2)
        
        return {'w': w, 'h': h, 'x': x, 'y': y}
    
    except Exception as e:
        print(f"--> Background subtraction analysis failed: {e}")
        return None
    finally:
        if cap is not None:
            cap.release()


def create_text_image_with_pil(text: str, width: int, font_size: int = 60, font_path: str = None, style: str = 'transparent') -> str:
    """
    Create text image using PIL.
    Supports two styles:
    - 'transparent': White text with black outline on a transparent BG.
    - 'white_bg': Black text on a dynamically sized, rounded white background.
    """
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        temp_path = temp_file.name
        temp_file.close()

        # --- Word wrap logic (unchanged) ---
        lines = text.split('\n')
        if not lines: lines = [text]
        max_chars_per_line = max(1, width // (font_size // 2))
        wrapped_lines = []
        for line in lines:
            if len(line) <= max_chars_per_line:
                wrapped_lines.append(line)
            else:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + " " + word) <= max_chars_per_line:
                        current_line += (" " + word) if current_line else word
                    else:
                        if current_line: wrapped_lines.append(current_line)
                        current_line = word
                if current_line: wrapped_lines.append(current_line)

        # --- Font loading (unchanged) ---
        try:
            if font_path and os.path.exists(font_path): font = ImageFont.truetype(font_path, font_size)
            else:
                try: font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    try: font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
                    except: font = ImageFont.load_default()
        except: font = ImageFont.load_default()

        v_padding = 20
        line_height = font_size + 10

        if style == 'white_bg':
            # --- 1. Measure text to find the required width (unchanged) ---
            dummy_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            max_text_width = 0
            for line in wrapped_lines:
                try:
                    bbox = dummy_draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                except AttributeError:
                    line_width, _ = dummy_draw.textsize(line, font=font)
                if line_width > max_text_width:
                    max_text_width = line_width

            # --- 2. Calculate dynamic canvas size (unchanged) ---
            h_padding = 40
            canvas_width = int(max_text_width + (2 * h_padding))
            canvas_height = len(wrapped_lines) * line_height + (2 * v_padding)

            # <--- MODIFICATION START --->
            # --- 3. Create a transparent canvas, then draw the shape and text ---
            img = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)

            # Draw the rounded rectangle background
            corner_radius = 30
            draw.rounded_rectangle(
                (0, 0, canvas_width, canvas_height), 
                radius=corner_radius, 
                fill='white'
            )
            # <--- MODIFICATION END --->
            
            y_position = v_padding
            for line in wrapped_lines:
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_w = bbox[2] - bbox[0]
                except AttributeError:
                    text_w, _ = draw.textsize(line, font=font)
                
                x_position = (canvas_width - text_w) // 2
                draw.text((x_position, y_position), line, font=font, fill='black')
                y_position += line_height

        else: # 'transparent' style (original logic is unchanged)
            canvas_height = len(wrapped_lines) * line_height + (2 * v_padding)
            img = Image.new('RGBA', (width, canvas_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            y_position = v_padding
            for line in wrapped_lines:
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_w = bbox[2] - bbox[0]
                except AttributeError:
                    text_w, _ = draw.textsize(line, font=font)
                
                x_position = (width - text_w) // 2
                
                stroke_width = 2
                for adj in range(-stroke_width, stroke_width + 1):
                    for adj2 in range(-stroke_width, stroke_width + 1):
                        draw.text((x_position + adj, y_position + adj2), line, font=font, fill='black')
                draw.text((x_position, y_position), line, font=font, fill='white')
                y_position += line_height

        img.save(temp_path, 'PNG')
        print(f"--> Created text image with style '{style}': {temp_path}")
        return temp_path

    except Exception as e:
        print(f"--> Error creating text image: {e}")
        return None

def create_final_video(cropped_video_path, title_text, output_path, options: dict = None):
    """
    Assembles the final video. For taller videos that exceed a height threshold,
    the AI-generated title is omitted to maximize content visibility.
    """
    print("--> Assembling final video...")
    if options is None:
        options = {}

    video_clip, header, logo, title_image_clip, top_element, video_content, final_video = (None,) * 7
    temp_text_image = None

    try:
        screen_w, screen_h = 1080, 1920
        video_clip = VideoFileClip(cropped_video_path)
        clip_duration = video_clip.duration

        add_branding = options.get('add_branding', True)
        add_logo = options.get('add_logo', True)
        font_path = "assets/fonts/font.ttf"
        
        # --- 🎬 1. Prepare Media Clips ---
        video_content = video_clip.resize(width=screen_w)
        
        # <--- MODIFICATION START --->
        # For tall videos, don't use a title at all.
        height_threshold = screen_h * 0.70
        if video_content.h > height_threshold:
            print(f"--> Tall video detected ({video_content.h}px). Skipping AI title to maximize visibility.")
            title_text = "" # Clear the title text
        # <--- MODIFICATION END --->

        if title_text and title_text.strip():
            text_width = int(screen_w * 0.9)
            
            # The style will always be 'transparent' now, as the other case is handled by removing the title.
            temp_text_image = create_text_image_with_pil(
                title_text, text_width, 60, 
                font_path if os.path.exists(font_path) else None,
                style='transparent'
            )

            if not temp_text_image:
                raise Exception("Failed to create text image")
            
            title_image_clip = ImageClip(temp_text_image, transparent=True).set_duration(clip_duration)
            if add_branding:
                profpic_path = "assets/profpic.jpg"
                if not os.path.exists(profpic_path):
                    raise Exception(f"Profile pic not found: {profpic_path}.")
                header = ImageClip(profpic_path).set_duration(clip_duration).resize(width=screen_w)
                top_element = CompositeVideoClip(
                    [
                        header.set_position(('center', 0)),
                        title_image_clip.set_position(('center', header.h + 10))
                    ], 
                    size=(screen_w, header.h + 10 + title_image_clip.h)
                ).set_duration(clip_duration)
            else:
                top_element = title_image_clip
        
        if add_logo:
            logo_path = "assets/logo.png"
            if os.path.exists(logo_path):
                logo = ImageClip(logo_path, transparent=True).set_duration(clip_duration).resize(width=225)
            else:
                print("--> WARNING: 'Add Logo' is ON, but logo.png was not found in assets folder.")

        # --- 🎬 2. Calculate Positions ---
        # The layout logic simplifies, as the 'OVERLAP' case is no longer needed
        # because tall videos will have no 'top_element'.
        print(f"--> Using STACKED layout.")
        spacing_top = 50
        total_content_h = video_content.h
        pos_top_element = None
        
        if top_element:
            total_content_h += top_element.h + spacing_top
        
        start_y = max(80, (screen_h - total_content_h) / 2)
        current_y = start_y
        
        if top_element:
            pos_top_element = current_y
            current_y += top_element.h + spacing_top
        
        pos_video_y = current_y
        pos_logo_y = int(screen_h * 0.8) if logo else None
        
        # --- 🎬 3. Build and Render ---
        clips_for_final = [
            ColorClip(size=(screen_w, screen_h), color=(0, 0, 0), duration=clip_duration),
            video_content.set_position(('center', pos_video_y))
        ]
        if top_element:
            clips_for_final.append(top_element.set_position(('center', pos_top_element)))
        if logo:
            clips_for_final.append(logo.set_position(('center', pos_logo_y)))

        final_video = CompositeVideoClip(clips_for_final, size=(screen_w, screen_h)).set_audio(video_content.audio)

        print(f"--> Writing final video to: {output_path}")
        final_video.write_videofile(
            output_path, fps=video_clip.fps, codec="libx264", 
            audio_codec="aac", logger=None, threads=4
        )
        print("--> Final video created successfully!")

    except Exception as e:
        print(f"--> Failed to create final video. Error: {e}")
        raise
    finally:
        # Cleanup
        clips_to_close = [video_clip, header, logo, title_image_clip, top_element, video_content, final_video]
        for clip in clips_to_close:
            if clip is not None:
                try: clip.close()
                except Exception: pass
        if temp_text_image and os.path.exists(temp_text_image):
            try: os.remove(temp_text_image)
            except Exception: pass
        gc.collect()



def generate_day_number_filename(output_dir: str, daily_limit: int, extension="mp4") -> str:
    """
    Generate a filename with prefix as the current day number (e.g., '3')
    plus incremental number. If the max daily limit is reached, roll over
    to the next day until an available slot is found.
    """
    # Make sure output dir exists
    os.makedirs(output_dir, exist_ok=True)

    # Start prefix as today's day number string
    current_date = datetime.date.today()
    prefix = str(current_date.day)  # e.g. "3"

    while True:
        existing_files = os.listdir(output_dir)
        pattern = re.compile(rf'^{re.escape(prefix)}-(\d+)\.{re.escape(extension)}$')
        
        existing_numbers = [int(m.group(1)) for f in existing_files if (m := pattern.match(f))]
        
        # Find the next available number
        next_number = 1 if not existing_numbers else max(existing_numbers) + 1
        
        # Check if the file with this exact filename already exists (safety check)
        candidate_filename = f"{prefix}-{next_number}.{extension}"
        candidate_path = os.path.join(output_dir, candidate_filename)
        
        if os.path.exists(candidate_path):
            # If max limit reached, roll forward to next day
            if next_number > daily_limit:
                current_date += datetime.timedelta(days=1)
                prefix = str(current_date.day)
                continue
            else:
                # Conflict but still under limit, increment number and try again
                next_number += 1
                continue
        else:
            # Check daily limit not breached
            if next_number > daily_limit:
                current_date += datetime.timedelta(days=1)
                prefix = str(current_date.day)
                continue
            else:
                # Found a valid filename
                return candidate_filename


class VideoProcessor:
    """Video processor - NO IMAGEMAGICK REQUIRED."""

    def __init__(self):
        self.temp_dir = Path("temp")
        # --- 👇 MODIFICATION 2 ---
        # Default output_dir is still here, but it can be overridden.
        self.output_dir = Path("output") 
        self.assets_dir = Path("assets")

        # Ensure directories exist
        self.temp_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)

    def safe_file_remove(self, file_path: str, max_retries: int = 5) -> bool:
        """Safely remove file with retries."""
        for attempt in range(max_retries):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"--> Cleaned up: {file_path}")
                return True
            except PermissionError:
                print(f"--> File in use, waiting... (attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
                gc.collect()
            except Exception as e:
                print(f"--> Error removing file: {e}")
                break

        print(f"--> Warning: Could not remove {file_path}")
        return False

    # --- 👇 MODIFICATION 3 ---
    # The output_dir is now passed in to save the caption to the right place.
    def save_caption_to_file(self, caption: str, video_name: str, output_dir: Path) -> str:
        """Save AI generated caption to .txt file."""
        try:
            caption_filename = f"{Path(video_name).stem}_caption.txt"
            caption_path = output_dir / caption_filename

            with open(caption_path, 'w', encoding='utf-8') as f:
                f.write(caption)

            print(f"--> Caption saved to: {caption_path}")
            return str(caption_path)

        except Exception as e:
            print(f"--> Failed to save caption: {e}")
            return ""

    def process_video(self, 
                      input_path: str, 
                      ai_content: dict,
                      original_metadata: dict = None,
                      branding_assets: dict = None,
                      options: dict = None) -> str:
        """Process video with cropping, branding, and AI content."""
        cropped_video_path = None
        original_clip = None
        cropped_clip = None

        try:
            print(f"--> Starting video processing: {input_path}")

            # ===== 🔥 KEY CHANGE HERE =====
            # Prioritize OCR extracted text if available
           
            title_text = ai_content.get('title', 'Generated Title')
            print(f"--> Using AI generated title: {title_text[:50]}...")
            # ==============================
            
            caption_text = ai_content.get('caption', 'Generated caption')

            # --- 👇 MODIFICATION 4 ---
            # Get the custom output directory from options, or use the default.
            custom_output_dir = options.get('output_directory') if options else None
            effective_output_dir = Path(custom_output_dir) if custom_output_dir else self.output_dir
            print(f"--> Using output directory: {effective_output_dir}")

            # Step 1: Detect crop dimensions
            print("--> Detecting crop dimensions...")
            crop_info = detect_crop_dimensions(input_path)

            cropped_video_path = input_path

            if crop_info:
                print(f"--> Cropping detected: {crop_info}")

                timestamp = int(time.time())
                temp_filename = f"cropped_{timestamp}_{os.getpid()}.mp4"
                cropped_video_path = str(self.temp_dir / temp_filename)

                original_clip = VideoFileClip(input_path)
                cropped_clip = original_clip.crop(
                    x1=crop_info['x'],
                    y1=crop_info['y'],
                    x2=crop_info['x'] + crop_info['w'],
                    y2=crop_info['y'] + crop_info['h']
                )

                print(f"--> Writing cropped video to: {cropped_video_path}")
                cropped_clip.write_videofile(
                    cropped_video_path,
                    codec='libx264',
                    audio_codec='aac',
                    logger=None
                )

                cropped_clip.close()
                original_clip.close()
                cropped_clip = None
                original_clip = None
                gc.collect()

                print(f"--> Video cropped and saved: {cropped_video_path}")
            else:
                print("--> No cropping needed, using original video")

            # Step 2: Generate output filename with day-number and daily limit
            daily_limit = options.get('daily_limit', 10) if options else 10

            # --- 👇 MODIFICATION 5 ---
            # Pass the correct output directory to the filename generator.
            output_filename = generate_day_number_filename(str(effective_output_dir), daily_limit, extension="mp4")
            output_path = effective_output_dir / output_filename

            print(f"--> Creating final video: {output_path}")

            # Use modified create_final_video function (no ImageMagick)
            create_final_video(cropped_video_path, title_text, str(output_path), options)

            # Step 3: Save caption
            # --- 👇 MODIFICATION 6 ---
            # Pass the correct output directory to the caption saver.
            caption_path = self.save_caption_to_file(caption_text, str(output_path), effective_output_dir)

            # Step 4: Cleanup
            if cropped_video_path != input_path:
                time.sleep(1)
                self.safe_file_remove(cropped_video_path)

            print(f"--> Video processing completed!")
            print(f"--> Final video: {output_path}")
            print(f"--> Caption file: {caption_path}")

            return str(output_path)

        except Exception as e:
            print(f"--> Error processing video: {e}")

            if original_clip:
                original_clip.close()
            if cropped_clip:
                cropped_clip.close()
            if cropped_video_path and cropped_video_path != input_path:
                self.safe_file_remove(cropped_video_path)

            raise


# Backward compatibility
def process_video(input_path: str, branding_assets: Dict[str, str]) -> str:
    """Backward compatibility function."""
    processor = VideoProcessor()

    ai_content = {
        'title': 'Processed Video Content',
        'caption': 'Automatically processed video content'
    }

    return processor.process_video(input_path, ai_content, branding_assets)
