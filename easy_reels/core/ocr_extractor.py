"""
OCR Text Extractor Module
Extracts text from video frames using Tesseract OCR
"""

import cv2
import pytesseract
from PIL import Image
import os
from pathlib import Path
from typing import Optional, Dict
import tempfile


class OCRExtractor:
    """Extract text from video frames using OCR."""
    
    def __init__(self, tesseract_path: str = None):
        """
        Initialize OCR Extractor.
        
        Args:
            tesseract_path: Path to tesseract.exe (Windows only)
                           If None, will try to auto-detect
        """
        # Set Tesseract path (Windows)
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # Try to auto-detect on Windows
            default_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
    
    def extract_text_from_middle_frame(self, video_path: str) -> Dict[str, str]:
        """
        Extract text from the middle frame of a video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with:
                - 'text': Extracted text (or empty string)
                - 'status': 'success' or 'error'
                - 'message': Status message
                - 'frame_path': Path to saved frame (for debugging)
        """
        result = {
            'text': '',
            'status': 'error',
            'message': '',
            'frame_path': None
        }
        
        # 1. Check if video file exists
        if not os.path.exists(video_path):
            result['message'] = f"Video file not found: {video_path}"
            return result
        
        cap = None
        try:
            # 2. Open the video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                result['message'] = "Could not open video file"
                return result
            
            # 3. Get frame information
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames == 0:
                result['message'] = "Video has no frames"
                return result
            
            # 4. Seek to the middle frame
            mid_frame_index = total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame_index)
            
            # 5. Read the frame
            ret, frame = cap.read()
            if not ret:
                result['message'] = "Failed to read middle frame"
                return result
            
            # Release video early
            cap.release()
            cap = None
            
            # 6. Save frame for debugging (optional)
            try:
                temp_frame_path = os.path.join(tempfile.gettempdir(), "ocr_frame.jpg")
                cv2.imwrite(temp_frame_path, frame)
                result['frame_path'] = temp_frame_path
            except Exception as e:
                print(f"--> Warning: Could not save debug frame: {e}")
            
            # 7. Perform OCR
            # Convert BGR (OpenCV) to RGB (PIL)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            # Extract text
            extracted_text = pytesseract.image_to_string(pil_image)
            
            # Clean up text
            cleaned_text = extracted_text.strip()
            
            result['text'] = cleaned_text
            result['status'] = 'success'
            result['message'] = f"Extracted {len(cleaned_text)} characters"
            
            return result
            
        except Exception as e:
            result['message'] = f"OCR error: {str(e)}"
            return result
            
        finally:
            if cap is not None:
                cap.release()


# Convenience function for backward compatibility
def extract_text_from_video(video_path: str) -> str:
    """
    Simple function to extract text from video.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Extracted text (or empty string on error)
    """
    extractor = OCRExtractor()
    result = extractor.extract_text_from_middle_frame(video_path)
    return result.get('text', '')
