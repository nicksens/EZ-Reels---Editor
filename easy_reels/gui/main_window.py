import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import datetime
import subprocess
import platform
from pathlib import Path
from PIL import Image, ImageTk
import sys
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import our modules
try:
    from easy_reels.core.config_manager import config
    from easy_reels.core.instagram_downloader import InstagramDownloader
    from easy_reels.core.ai_content_generator import AIContentGenerator
    from easy_reels.core.video_processor import VideoProcessor
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all core modules are in place")

def generate_day_number_filename(output_dir, prefix, daily_limit, extension="mp4"):
    """
    Generate a new filename in the format prefix-number within output_dir.
    Enforce daily_limit (max number files per prefix).
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # List all files in the output directory
    existing_files = os.listdir(output_dir)

    # Pattern to match files like "24-1.mp4"
    pattern = re.compile(rf'^{re.escape(prefix)}-(\d+)\.{re.escape(extension)}$')
    
    # Extract all numbers already used with the prefix
    existing_numbers = []
    for filename in existing_files:
        match = pattern.match(filename)
        if match:
            existing_numbers.append(int(match.group(1)))
    
    # Determine the next available number
    next_number = 1
    if existing_numbers:
        next_number = max(existing_numbers) + 1
    
    # Check if daily limit exceeded
    if next_number > daily_limit:
        raise ValueError(f"Daily limit reached for prefix '{prefix}': {daily_limit}")
    
    # Construct and return the new filename
    new_filename = f"{prefix}-{next_number}.{extension}"
    
    return new_filename

class EasyReelsApp(ctk.CTk):
    """Compact main application window for single video processing."""
    
    def __init__(self):
        super().__init__()
        
        # Configure window - Compact size
        self.title("Easy Reels - AI Video Creator (Single Mode)")
        self.geometry("1200x750")  # Smaller size
        self.minsize(1000, 650)    # Smaller minimum
        
        # Center window on screen
        self.center_window()
        
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize variables
        self.current_project = {}
        self.processing_thread = None
        self.logo_path = None
        self.profile_pic_path = None
        
        # Create UI
        self.create_ui()
        
        # Validate credentials on startup
        self.validate_setup()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def center_window(self):
        """Center the window on screen."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.winfo_screenheight() // 2) - (750 // 2)
        self.geometry(f"1200x750+{x}+{y}")
        
    def on_closing(self):
        """Handle window closing event."""
        if self.processing_thread and self.processing_thread.is_alive():
            if messagebox.askyesno("Confirm Exit", "Video processing is in progress. Are you sure you want to exit?"):
                self.destroy()
        else:
            self.destroy()
        
    def create_ui(self):
        """Create the compact user interface."""
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left sidebar - Narrower
        self.create_sidebar()
        
        # Main content area
        self.create_main_content()
        
    def create_sidebar(self):
        """Create compact left sidebar with controls."""
        
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0)  # Narrower
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(12, weight=1)
        
        # Logo/Title - Smaller
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="Easy Reels",
            font=ctk.CTkFont(size=24, weight="bold")  # Smaller font
        )
        self.logo_label.grid(row=0, column=0, padx=15, pady=(20, 5))
        
        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="AI Video Creator - Single Mode",
            font=ctk.CTkFont(size=12)  # Smaller font
        )
        self.subtitle_label.grid(row=1, column=0, padx=15, pady=(0, 15))
        
        # Mode switch button - Smaller
        self.switch_mode_btn = ctk.CTkButton(
            self.sidebar,
            text="🚀 Switch to Batch Mode",
            command=self.switch_to_batch_mode,
            height=32,  # Smaller height
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            font=ctk.CTkFont(size=11)
        )
        self.switch_mode_btn.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # URL Input Section - Compact
        self.url_frame = ctk.CTkFrame(self.sidebar)
        self.url_frame.grid(row=3, column=0, padx=15, pady=8, sticky="ew")
        
        ctk.CTkLabel(self.url_frame, text="Instagram Reel URL", 
                    font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(15, 5))
        
        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            placeholder_text="https://www.instagram.com/reel/...",
            height=35,  # Smaller height
            font=ctk.CTkFont(size=11)
        )
        self.url_entry.pack(padx=15, pady=5, fill="x")
        
        # Paste button - Smaller
        self.paste_btn = ctk.CTkButton(
            self.url_frame,
            text="📋 Paste URL",
            command=self.paste_url,
            height=28,
            fg_color=("gray60", "gray40"),
            font=ctk.CTkFont(size=10)
        )
        self.paste_btn.pack(padx=15, pady=(0, 5))
        
        self.download_btn = ctk.CTkButton(
            self.url_frame,
            text="🎬 Download & Process",
            command=self.start_processing,
            height=40,  # Smaller height
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.download_btn.pack(padx=15, pady=(5, 15), fill="x")
        
        # Asset Upload Section - Compact
        self.assets_frame = ctk.CTkFrame(self.sidebar)
        self.assets_frame.grid(row=4, column=0, padx=15, pady=8, sticky="ew")
        
        ctk.CTkLabel(self.assets_frame, text="Branding Assets", 
                    font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(15, 8))
        
        # Logo upload - Smaller
        self.logo_btn = ctk.CTkButton(
            self.assets_frame,
            text="📎 Upload Logo",
            command=self.upload_logo,
            height=32
        )
        self.logo_btn.pack(padx=15, pady=5, fill="x")
        
        self.logo_status = ctk.CTkLabel(
            self.assets_frame,
            text="No logo selected",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.logo_status.pack(pady=3)
        
        # Profile pic upload - Smaller
        self.profile_btn = ctk.CTkButton(
            self.assets_frame,
            text="👤 Upload Profile Picture",
            command=self.upload_profile_pic,
            height=32
        )
        self.profile_btn.pack(padx=15, pady=5, fill="x")
        
        self.profile_status = ctk.CTkLabel(
            self.assets_frame,
            text="No profile picture selected",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.profile_status.pack(pady=(3, 15))
        
        # Progress Section - Compact
        self.progress_frame = ctk.CTkFrame(self.sidebar)
        self.progress_frame.grid(row=5, column=0, padx=15, pady=8, sticky="ew")
        
        ctk.CTkLabel(self.progress_frame, text="Processing Progress", 
                    font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(15, 8))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=16)  # Thinner
        self.progress_bar.pack(padx=15, pady=5, fill="x")
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="Ready to process video",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(pady=(5, 15))
        
        # Settings Section - Compact
        self.settings_frame = ctk.CTkFrame(self.sidebar)
        self.settings_frame.grid(row=6, column=0, padx=15, pady=8, sticky="ew")
        
        ctk.CTkLabel(self.settings_frame, text="Processing Options", 
                    font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(15, 8))
        
        self.auto_crop_var = ctk.BooleanVar(value=True)
        self.auto_crop_check = ctk.CTkCheckBox(
            self.settings_frame,
            text="Auto-crop to vertical format",
            variable=self.auto_crop_var,
            font=ctk.CTkFont(size=11)
        )
        self.auto_crop_check.pack(padx=15, pady=3, anchor="w")
        
        self.add_branding_var = ctk.BooleanVar(value=True)
        self.add_branding_check = ctk.CTkCheckBox(
            self.settings_frame,
            text="Add branding overlay",
            variable=self.add_branding_var,
            font=ctk.CTkFont(size=11)
        )
        self.add_branding_check.pack(padx=15, pady=3, anchor="w")
        
        self.add_title_var = ctk.BooleanVar(value=True)
        self.add_title_check = ctk.CTkCheckBox(
            self.settings_frame,
            text="Add AI title overlay",
            variable=self.add_title_var,
            font=ctk.CTkFont(size=11)
        )
        self.add_title_check.pack(padx=15, pady=(3, 15), anchor="w")
        
    def create_main_content(self):
        """Create compact main content area."""
        
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Header - Smaller
        self.content_header = ctk.CTkLabel(
            self.main_frame,
            text="Single Video Processing",
            font=ctk.CTkFont(size=18, weight="bold")  # Smaller font
        )
        self.content_header.grid(row=0, column=0, pady=(20, 10))
        
        # Content area with tabs - Smaller padding
        self.content_tabs = ctk.CTkTabview(self.main_frame)
        self.content_tabs.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Preview tab
        self.content_tabs.add("Video Preview")
        preview_tab = self.content_tabs.tab("Video Preview")
        
        # Video preview placeholder - Smaller padding
        self.video_preview_frame = ctk.CTkFrame(preview_tab)
        self.video_preview_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.video_placeholder = ctk.CTkLabel(
            self.video_preview_frame,
            text="🎬\\n\\nVideo preview will appear here\\nafter processing\\n\\nUpload your logo and profile picture,\\nthen paste an Instagram Reel URL to get started!",
            font=ctk.CTkFont(size=14),  # Smaller font
            text_color="gray"
        )
        self.video_placeholder.pack(expand=True)
        
        # AI Content tab
        self.content_tabs.add("AI Generated Content")
        ai_tab = self.content_tabs.tab("AI Generated Content")
        
        self.ai_content_frame = ctk.CTkScrollableFrame(ai_tab)
        self.ai_content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title section - Smaller
        ctk.CTkLabel(self.ai_content_frame, text="Generated Title", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        
        self.title_text = ctk.CTkTextbox(self.ai_content_frame, height=60)  # Smaller
        self.title_text.pack(fill="x", pady=5)
        
        # Caption section - Smaller
        ctk.CTkLabel(self.ai_content_frame, text="Generated Caption", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))
        
        self.caption_text = ctk.CTkTextbox(self.ai_content_frame, height=180)  # Smaller
        self.caption_text.pack(fill="x", pady=5)
        
        # Action buttons - Smaller
        self.action_frame = ctk.CTkFrame(self.ai_content_frame)
        self.action_frame.pack(fill="x", pady=20)
        
        self.regenerate_btn = ctk.CTkButton(
            self.action_frame,
            text="🔄 Regenerate Content",
            command=self.regenerate_ai_content,
            state="disabled",
            height=35,  # Smaller
            font=ctk.CTkFont(size=12)
        )
        self.regenerate_btn.pack(side="left", padx=10, pady=10)
        
        self.export_btn = ctk.CTkButton(
            self.action_frame,
            text="💾 Export Video",
            command=self.export_video,
            state="disabled",
            height=35,  # Smaller
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.export_btn.pack(side="right", padx=10, pady=10)
        
        # Logs tab
        self.content_tabs.add("Processing Logs")
        logs_tab = self.content_tabs.tab("Processing Logs")
        
        self.logs_text = ctk.CTkTextbox(
            logs_tab, 
            font=ctk.CTkFont(family="Consolas", size=10)  # Smaller font
        )
        self.logs_text.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add some initial log entries
        self.log_message("Easy Reels Single Mode initialized")
        self.log_message("Ready for video processing")
        
    def paste_url(self):
        """Paste URL from clipboard."""
        try:
            clipboard_content = self.clipboard_get()
            if clipboard_content:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, clipboard_content.strip())
                self.log_message("URL pasted from clipboard")
        except Exception as e:
            self.log_message(f"Could not paste from clipboard: {e}")
        
    def switch_to_batch_mode(self):
        """Switch to batch processing mode."""
        if self.processing_thread and self.processing_thread.is_alive():
            messagebox.showwarning("Processing in Progress", "Cannot switch modes while processing. Please wait for completion.")
            return
            
        if messagebox.askyesno("Switch Mode", "Switch to Batch Processing mode?\\n\\nThis will close the current window and open batch mode for processing multiple videos."):
            self.destroy()
            try:
                from easy_reels.gui.batch_main_window import BatchEasyReelsApp
                app = BatchEasyReelsApp()
                app.mainloop()
            except ImportError as e:
                messagebox.showerror("Error", f"Could not load batch mode: {e}\\n\\nPlease ensure batch_main_window.py is installed.")
                
    def upload_logo(self):
        """Handle logo upload without resizing or altering transparency."""
        file_path = filedialog.askopenfilename(
            title="Select Logo",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Set up destination path
                assets_dir = Path("assets")
                assets_dir.mkdir(exist_ok=True)
                logo_dest = assets_dir / "logo.png"
                
                # Open the image and save it directly to the destination as a PNG
                # This preserves the original content, including transparency for PNGs.
                with Image.open(file_path) as img:
                    # --- REMOVED ---
                    # The block that converted RGBA to RGB by adding a white background
                    # has been removed to preserve transparency.

                    # --- REMOVED ---
                    # The resizing logic (img.thumbnail) has been removed.
                    
                    img.save(logo_dest, "PNG", optimize=True)
                
                self.logo_path = str(logo_dest)
                self.logo_status.configure(text="✅ Logo uploaded", text_color="green")
                self.log_message(f"Logo uploaded: {logo_dest}")
                
            except Exception as e:
                messagebox.showerror("Upload Error", f"Failed to upload logo:\n{e}")
                self.log_message(f"Logo upload failed: {e}")
                
    def upload_profile_pic(self):
        """Handle profile picture upload without resizing."""
        file_path = filedialog.askopenfilename(
            title="Select Profile Picture",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Set up destination path
                assets_dir = Path("assets")
                assets_dir.mkdir(exist_ok=True)
                profile_dest = assets_dir / "profpic.jpg"
                
                # Open the image, convert to RGB (necessary for JPEG), and save
                with Image.open(file_path) as img:
                    # Convert to RGB if necessary, as JPEG format does not support transparency
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    
                    # --- REMOVED ---
                    # The cropping and resizing logic has been completely removed.
                    
                    img.save(profile_dest, "JPEG", quality=90, optimize=True)
                
                self.profile_pic_path = str(profile_dest)
                self.profile_status.configure(text="✅ Profile pic uploaded", text_color="green")
                self.log_message(f"Profile picture uploaded: {profile_dest}")
                
            except Exception as e:
                messagebox.showerror("Upload Error", f"Failed to upload profile picture:\n{e}")
                self.log_message(f"Profile pic upload failed: {e}")
                
    def validate_setup(self):
        """Validate application setup and credentials."""
        try:
            credentials = config.validate_credentials()
            missing = [k for k, v in credentials.items() if not v]
            
            if missing:
                self.log_message(f"⚠️ Missing credentials: {', '.join(missing)}")
                self.status_label.configure(text="Setup incomplete", text_color="orange")
            else:
                self.log_message("✅ All credentials configured correctly")
                self.status_label.configure(text="Ready to process video", text_color="green")
                
        except Exception as e:
            self.log_message(f"❌ Setup validation failed: {e}")
            self.status_label.configure(text="Setup error", text_color="red")
            
    def log_message(self, message):
        """Add message to logs."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\\n"
        self.logs_text.insert("end", log_entry)
        self.logs_text.see("end")
        
    def start_processing(self):
        """Start the video processing workflow."""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showwarning("Missing URL", "Please enter an Instagram Reel URL")
            return
            
        # Basic URL validation
        if 'instagram.com' not in url and 'instagr.am' not in url:
            messagebox.showwarning("Invalid URL", "Please enter a valid Instagram URL")
            return
            
        if self.processing_thread and self.processing_thread.is_alive():
            messagebox.showwarning("Processing in Progress", "Video processing is already in progress. Please wait for completion.")
            return
            
        # Check if assets are uploaded
        if not self.logo_path or not os.path.exists(self.logo_path):
            if not messagebox.askyesno("Missing Logo", "No logo uploaded. Continue without logo?"):
                return
                
        if not self.profile_pic_path or not os.path.exists(self.profile_pic_path):
            if not messagebox.askyesno("Missing Profile Picture", "No profile picture uploaded. Continue without profile picture?"):
                return
        
        # Disable button and start processing
        self.download_btn.configure(state="disabled", text="Processing...")
        self.processing_thread = threading.Thread(target=self.process_video, args=(url,))
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
    def process_video(self, url):
        try:
            self.update_progress(0.1, "Validating URL...")
            
            # Step 1: Download the video from Instagram
            self.update_progress(0.2, "Downloading video from Instagram...")
            downloader = InstagramDownloader()
            video_path, caption = downloader.download_reel(url)
            
            self.current_project = {
                'url': url,
                'video_path': video_path,
                'original_caption': caption
            }
            
            self.log_message(f"Video downloaded: {video_path}")
            self.log_message(f"Original caption: {caption[:100]}...")
            
            # Step 2: Generate AI content from caption
            self.update_progress(0.5, "Generating AI content...")
            ai_generator = AIContentGenerator()
            ai_content = ai_generator.generate_complete_content(caption)
            
            self.current_project['ai_content'] = ai_content
            
            self.log_message(f"AI title generated: {ai_content.get('title', '')}")
            self.log_message("AI caption generated successfully")
            
            # Update UI with AI content asynchronously
            self.after(0, lambda: self.display_ai_content(ai_content))
            
            # Step 3: Set output directory and get prefix and daily limit from UI
            output_dir = os.path.dirname(video_path)
            prefix = self.prefixentry.get().strip()
            daily_limit_str = self.dailylimitentry.get().strip()
            daily_limit = int(daily_limit_str) if daily_limit_str.isdigit() else 50
            
            # Generate new filename in prefix-number format with limit check
            new_filename = generate_day_number_filename(output_dir, prefix, daily_limit, extension="mp4")
            final_video_path = os.path.join(output_dir, new_filename)
            
            # Step 4: Process video with processor, passing target output path
            self.update_progress(0.7, "Processing video with AI content...")
            processor = VideoProcessor()
            
            branding_assets = {}
            if self.logo_path and os.path.exists(self.logo_path):
                branding_assets['logo_path'] = self.logo_path
            if self.profile_pic_path and os.path.exists(self.profile_pic_path):
                branding_assets['profile_pic_path'] = self.profile_pic_path
            
            options = {
                'auto_crop': self.auto_crop_var.get(),
                'add_branding': self.add_branding_var.get(),
                'add_title_overlay': self.add_title_var.get(),
                'use_original_layout': True,
                'output_quality': 'high'
            }
            
            # Assuming process_video can accept an output_path to save output there
            final_video = processor.process_video(
                video_path,
                ai_content,
                branding_assets,
                options,
                output_path=final_video_path
            )
            
            # Store final video path in current project
            self.current_project['final_video'] = final_video_path
            
            # Step 5: Clean up temp files
            if os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    self.log_message("Temporary files cleaned up")
                except Exception as cleanup_error:
                    self.log_message(f"Cleanup error: {cleanup_error}")
            
            self.update_progress(1.0, "Processing complete!")
            self.after(0, lambda: self.processing_complete(final_video_path))
            
        except ValueError as ve:
            # Handle daily limit exceeded error
            self.log_message(str(ve))
            messagebox.showerror("Daily Limit Reached", str(ve))
            return
        except Exception as e:
            error_msg = str(e)
            self.log_message(f"Processing error: {error_msg}")
            self.after(0, lambda msg=error_msg: self.processing_error(msg))
            
    def update_progress(self, value, status):
        """Update progress bar and status."""
        def update():
            self.progress_bar.set(value)
            self.status_label.configure(text=status)
            self.log_message(status)
            
        self.after(0, update)
        
    def display_ai_content(self, ai_content):
        """Display generated AI content."""
        self.title_text.delete("1.0", "end")
        self.title_text.insert("1.0", ai_content.get('title', ''))
        
        self.caption_text.delete("1.0", "end")
        self.caption_text.insert("1.0", ai_content.get('caption', ''))
        
        self.regenerate_btn.configure(state="normal")
        
    def processing_complete(self, final_video):
        """Handle processing completion."""
        self.download_btn.configure(state="normal", text="🎬 Download & Process")
        self.export_btn.configure(state="normal")
        
        # Switch to AI content tab to show results
        self.content_tabs.set("AI Generated Content")
        
        self.video_placeholder.configure(
            text=f"✅ Video Processing Complete!\\n\\nFinal video saved to:\\n{final_video}\\n\\nCheck the 'AI Generated Content' tab to see the title and caption.\\nClick 'Export Video' to open the output folder."
        )
        
        self.log_message(f"Processing completed successfully!")
        self.log_message(f"Final video: {final_video}")
        
        messagebox.showinfo(
            "Success", 
            f"Video processing complete!\\n\\nFinal video saved to:\\n{Path(final_video).name}\\n\\nClick 'Export Video' to open the output folder."
        )
        
    def processing_error(self, error):
        """Handle processing error."""
        self.download_btn.configure(state="normal", text="🎬 Download & Process")
        self.update_progress(0, f"Error: {error}")
        
        self.log_message(f"Processing failed: {error}")
        
        messagebox.showerror("Processing Failed", f"Video processing failed:\\n\\n{error}\\n\\nCheck the logs for more details.")
        
    def regenerate_ai_content(self):
        """Regenerate AI content."""
        if not self.current_project.get('original_caption'):
            messagebox.showwarning("No Content", "No original caption available for regeneration")
            return
            
        try:
            self.log_message("Regenerating AI content...")
            ai_generator = AIContentGenerator()
            ai_content = ai_generator.generate_complete_content(
                self.current_project['original_caption']
            )
            self.current_project['ai_content'] = ai_content
            self.display_ai_content(ai_content)
            self.log_message("AI content regenerated successfully")
            
        except Exception as e:
            error_msg = f"Failed to regenerate content: {e}"
            messagebox.showerror("Regeneration Failed", error_msg)
            self.log_message(error_msg)
            
    def export_video(self):
        """Export/open final video location."""
        if 'final_video' not in self.current_project:
            messagebox.showwarning("No Video", "No processed video available for export")
            return
            
        video_path = Path(self.current_project['final_video'])
        
        if not video_path.exists():
            messagebox.showerror("File Not Found", f"Video file not found:\\n{video_path}")
            return
            
        try:
            # Open file location
            if platform.system() == "Windows":
                subprocess.run(['explorer', '/select,', str(video_path)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(['open', '-R', str(video_path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(video_path.parent)])
                
            self.log_message(f"Opened output folder: {video_path.parent}")
            
        except Exception as e:
            messagebox.showerror("Open Failed", f"Could not open file location:\\n{e}")
            self.log_message(f"Failed to open output folder: {e}")


def main():
    """Main entry point for single GUI application."""
    app = EasyReelsApp()
    app.mainloop()


if __name__ == "__main__":
    main()