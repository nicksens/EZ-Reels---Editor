import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import threading
import os
import datetime
import subprocess
import platform
from pathlib import Path
from PIL import Image, ImageTk
import sys
from typing import Dict, List, Any, Optional
import json
import shutil
import time
# ADD THESE IMPORTS (SAME AS MAIN_WINDOW)
from easy_reels.core.instagram_downloader import InstagramDownloader
from easy_reels.core.ai_content_generator import AIContentGenerator, ApiKeyManager
from easy_reels.core.video_processor import VideoProcessor
from easy_reels.gui.reels_scraper import ReelScraperApp 

api_key_manager = ApiKeyManager()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ═══════════════════════════════════════════════════════════════════════════════
# EMBEDDED COMPLETE TEMPLATE MANAGER CLASS - FULL VERSION FROM template_manager.py
# ═══════════════════════════════════════════════════════════════════════════════

class TemplateManager:
    """COMPLETE TemplateManager - All methods from original template_manager.py"""
    
    def __init__(self):
        self.templates_dir = Path("config/templates")
        self.templates_file = self.templates_dir / "templates.json"
        self.settings_file = self.templates_dir / "template_settings.json"
        
        # Ensure directories exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing templates or create default
        self.templates = self.load_templates()
        self.settings = self.load_settings()
        
    def load_templates(self) -> Dict:
        """Load templates from file or create defaults."""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading templates: {e}")
                
        # Create default templates
        return self.create_default_templates()
        
    def create_default_templates(self) -> Dict:
        """Create default template structure - FULL VERSION with your prompts."""
        default_templates = {
            "theanomalists": {
                "name": "@theanomalists",
                "description": "The Anomalists - History and mystery investigations",
                "account_handle": "@theanomalists",
                "created_date": datetime.datetime.now().isoformat(),
                "title_prompt": '''You are a young and wild headline editor for a viral news publication, specializing in crafting short, relateable, and irresistible titles. Your task is to create a single headline for a video.

# Video's Original Caption:
{original_caption}

# Write a single, clickbait video title based on the provided context.
# 1. Analyze the Core Conflict: Identify the most dramatic contrast in the story (e.g., power vs. fragility, tradition vs. rebellion, public image vs. private reality).
# 2. Create a Bold Statement: Write a headline that sounds like a definitive, relateable, and slightly funny declaration.
# 3. Deliver the Headline: Provide only the single line of text for the title.

# - Word Count: Maximum 12 words.
# - Never hallucinate, if the context is not clear enough, don't make up random facts.
# - Punctuation: Absolutely no colons (:), dashes (–), periods (.), or commas (,).
# - Absolutely no emojis.
# - Tone: Light, funny, and relateable. Must feel like a major revelation.
# - Format: Plain text only. No bolding, no quotation marks.
# - The Queen secretly feared Diana's growing power
# - Putin bowed lower than any royal tradition allowed
# - Diana's Versace dress ended royal fashion forever''',

                "caption_prompt": '''You are a captivating storyteller who makes history feel like trending gossip. Your task is to write a short, powerful Instagram caption based on the provided context.

# Video's Original Caption:
{original_caption}

# Write a complete Instagram caption by creating these four parts in order:
# 1. The Hook: Start with a single, dramatic sentence that drops the audience right into the middle of the story. Make it feel personal and intriguing.
# - Example: "It was the one night Princess Diana decided to break all the rules."
# 2. The Story: In one single paragraph, tell the story behind the video. Write in a simple, conversational tone, as if you're explaining it to a friend. Use short, punchy sentences.
# 3. Call to Action: Write a single, relatable question that starts with an emoji, encouraging people to share their own take.
# - Example: "🤔 What do you think was really going on here? Let me know below!"
# 4. Call to Action: Ask the viewer to follow @theanomalists (my instagram account).
# - Example: "🕵️♂️ Did you enjoy this kind of content? Follow @theanomalists for more investigations into the world's greatest anomalies."
# 5. Hashtags: Provide exactly 10 relevant, viral-ready hashtags.

# - Keep the tone engaging and relatable, not overly serious.
# - Never hallucinate, if the context is not clear enough, don't make up random facts.
# - Use plain text only.
# - Add line spacing so the reader dont read just one line of text.
# - The final output should be a block of text.'''
            }
        }
        
        self.save_templates(default_templates)
        return default_templates
        
    def load_settings(self) -> Dict:
        """Load template settings."""
        default_settings = {
            "last_used_template": "theanomalists",
            "auto_save": True,
            "template_backup": True
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Ensure all default keys exist
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
            except Exception as e:
                print(f"Error loading settings: {e}")
                
        return default_settings
        
    def save_templates(self, templates: Dict = None) -> bool:
        """Save templates to file."""
        try:
            if templates is None:
                templates = self.templates
                
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving templates: {e}")
            return False
            
    def save_settings(self, settings: Dict = None) -> bool:
        """Save settings to file."""
        try:
            if settings is None:
                settings = self.settings
                
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
            
    def get_template_names(self) -> List[str]:
        """Get list of all template names."""
        return list(self.templates.keys())
        
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a specific template."""
        return self.templates.get(template_id)
        
    def get_current_template(self) -> Dict:
        """Get the currently selected template."""
        current_id = self.settings.get("last_used_template", "theanomalists")
        template = self.get_template(current_id)
        
        if template is None:
            # Fallback to first available template
            if self.templates:
                current_id = list(self.templates.keys())[0]
                template = self.templates[current_id]
                self.set_current_template(current_id)
                
        return template or {}
        
    def set_current_template(self, template_id: str) -> bool:
        """Set the current template."""
        if template_id in self.templates:
            self.settings["last_used_template"] = template_id
            return self.save_settings()
        return False
        
    def create_template(self, template_id: str, template_data: Dict) -> bool:
        """Create a new template."""
        if template_id in self.templates:
            return False  # Template already exists
            
        # Add metadata
        template_data["created_date"] = datetime.datetime.now().isoformat()
        template_data["modified_date"] = datetime.datetime.now().isoformat()
        
        self.templates[template_id] = template_data
        return self.save_templates()
        
    def update_template(self, template_id: str, template_data: Dict) -> bool:
        """Update an existing template."""
        if template_id not in self.templates:
            return False
            
        # Preserve created date, update modified date
        if "created_date" in self.templates[template_id]:
            template_data["created_date"] = self.templates[template_id]["created_date"]
        template_data["modified_date"] = datetime.datetime.now().isoformat()
        
        self.templates[template_id] = template_data
        return self.save_templates()
        
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        if template_id not in self.templates or len(self.templates) <= 1:
            return False  # Cannot delete last template
            
        # If deleting current template, switch to another
        if self.settings.get("last_used_template") == template_id:
            remaining_templates = [t for t in self.templates.keys() if t != template_id]
            if remaining_templates:
                self.set_current_template(remaining_templates[0])
                
        del self.templates[template_id]
        return self.save_templates()
        
    def duplicate_template(self, source_id: str, new_id: str, new_name: str) -> bool:
        """Duplicate an existing template."""
        if source_id not in self.templates or new_id in self.templates:
            return False
            
        # Copy template data
        source_template = self.templates[source_id].copy()
        source_template["name"] = new_name
        source_template["created_date"] = datetime.datetime.now().isoformat()
        source_template["modified_date"] = datetime.datetime.now().isoformat()
        
        self.templates[new_id] = source_template
        return self.save_templates()
        
    def export_template(self, template_id: str, file_path: str) -> bool:
        """Export a template to file."""
        if template_id not in self.templates:
            return False
            
        try:
            export_data = {
                "template": self.templates[template_id],
                "exported_date": datetime.datetime.now().isoformat(),
                "exported_by": "Easy Reels Template Manager"
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting template: {e}")
            return False
            
    def import_template(self, file_path: str, template_id: str = None) -> bool:
        """Import a template from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
                
            if "template" not in import_data:
                return False
                
            template_data = import_data["template"]
            
            if template_id is None:
                # Generate unique ID
                base_id = template_data.get("name", "imported_template").lower().replace(" ", "_").replace("@", "")
                template_id = base_id
                counter = 1
                while template_id in self.templates:
                    template_id = f"{base_id}_{counter}"
                    counter += 1
                    
            return self.create_template(template_id, template_data)
        except Exception as e:
            print(f"Error importing template: {e}")
            return False
            
    def get_template_stats(self) -> Dict:
        """Get template usage statistics."""
        return {
            "total_templates": len(self.templates),
            "current_template": self.settings.get("last_used_template"),
            "template_names": [t.get("name", k) for k, t in self.templates.items()],
            "last_modified": max([t.get("modified_date", t.get("created_date", "")) 
                                for t in self.templates.values()] or [""])
        }

# ═══════════════════════════════════════════════════════════════════════════════
# EMBEDDED COMPLETE TEMPLATE EDITOR - FULL VERSION
# ═══════════════════════════════════════════════════════════════════════════════

class EmbeddedTemplateEditor(ctk.CTkToplevel):
    """COMPLETE Template Editor with ALL functionality embedded."""
    
    def __init__(self, parent, template_manager, callback=None):
        super().__init__(parent)
        
        self.template_manager = template_manager
        self.callback = callback
        self.current_template_id = None
        self.is_editing = False
        
        # Configure window
        self.title("Template Editor - AI Prompt Templates")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        # Create UI
        self.create_ui()
        self.load_templates()
        
    def create_ui(self):
        """--- 👇 CRITICAL FIX ---
        This method now calls the correct functions to build the editor UI.
        """
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.create_template_list()
        self.create_template_editor()

    def create_template_list(self):
        """Create template list panel."""
        
        self.list_frame = ctk.CTkFrame(self, width=250)
        self.list_frame.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        self.list_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        ctk.CTkLabel(self.list_frame, text="Templates", 
                     font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=(20, 10))
        
        # Template listbox with FIXED event binding
        self.template_listbox = tk.Listbox(
            self.list_frame,
            bg="#2b2b2b",
            fg="white",
            selectbackground="#1f538d",
            font=("Arial", 11),
            height=15
        )
        self.template_listbox.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        
        # CRITICAL FIX: Correct event binding (no more tkinter errors)
        self.template_listbox.bind('<<ListboxSelect>>', self.on_template_select)
        
        # Buttons
        self.btn_frame = ctk.CTkFrame(self.list_frame)
        self.btn_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.new_btn = ctk.CTkButton(
            self.btn_frame,
            text="➕ New",
            command=self.create_new_template,
            height=32,
            font=ctk.CTkFont(size=11)
        )
        self.new_btn.pack(pady=5, fill="x")
        
        self.duplicate_btn = ctk.CTkButton(
            self.btn_frame,
            text="📋 Duplicate",
            command=self.duplicate_template,
            height=32,
            font=ctk.CTkFont(size=11)
        )
        self.duplicate_btn.pack(pady=5, fill="x")
        
        self.export_btn = ctk.CTkButton(
            self.btn_frame,
            text="📤 Export",
            command=self.export_template,
            height=32,
            font=ctk.CTkFont(size=11)
        )
        self.export_btn.pack(pady=5, fill="x")
        
        self.import_btn = ctk.CTkButton(
            self.btn_frame,
            text="📥 Import",
            command=self.import_template,
            height=32,
            font=ctk.CTkFont(size=11)
        )
        self.import_btn.pack(pady=5, fill="x")
        
        self.delete_btn = ctk.CTkButton(
            self.btn_frame,
            text="🗑 Delete",
            command=self.delete_template,
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_btn.pack(pady=5, fill="x")
        
    def create_template_editor(self):
        """Create template editor panel."""
        
        self.editor_frame = ctk.CTkFrame(self)
        self.editor_frame.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self.editor_frame.grid_columnconfigure(0, weight=1)
        self.editor_frame.grid_rowconfigure(2, weight=1)
        
        # Header
        self.editor_header = ctk.CTkLabel(
            self.editor_frame,
            text="Select a template to edit",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.editor_header.grid(row=0, column=0, pady=(20, 15))
        
        # Template info frame
        self.info_frame = ctk.CTkFrame(self.editor_frame)
        self.info_frame.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.info_frame.grid_columnconfigure(1, weight=1)
        
        # Template name
        ctk.CTkLabel(self.info_frame, text="Template Name:", 
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.name_entry = ctk.CTkEntry(self.info_frame, height=32)
        self.name_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        
        # Account handle
        ctk.CTkLabel(self.info_frame, text="Account Handle:", 
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.handle_entry = ctk.CTkEntry(self.info_frame, height=32, placeholder_text="@your_account")
        self.handle_entry.grid(row=1, column=1, padx=10, pady=8, sticky="ew")
        
        # Description
        ctk.CTkLabel(self.info_frame, text="Description:", 
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, padx=10, pady=8, sticky="w")
        self.description_entry = ctk.CTkEntry(self.info_frame, height=32, placeholder_text="Brief description")
        self.description_entry.grid(row=2, column=1, padx=10, pady=8, sticky="ew")
        
        # Tabview for prompts
        self.tabview = ctk.CTkTabview(self.editor_frame)
        self.tabview.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="nsew")
        
        # Title prompt tab
        self.tabview.add("Title Prompt")
        title_tab = self.tabview.tab("Title Prompt")
        
        ctk.CTkLabel(title_tab, text="Title Generation Prompt:", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5), anchor="w")
        
        self.title_prompt_text = ctk.CTkTextbox(
            title_tab,
            font=ctk.CTkFont(family="Consolas", size=11),
            height=400
        )
        self.title_prompt_text.pack(fill="both", expand=True, pady=(5, 10))
        
        # Caption prompt tab
        self.tabview.add("Caption Prompt")
        caption_tab = self.tabview.tab("Caption Prompt")
        
        ctk.CTkLabel(caption_tab, text="Caption Generation Prompt:", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5), anchor="w")
        
        self.caption_prompt_text = ctk.CTkTextbox(
            caption_tab,
            font=ctk.CTkFont(family="Consolas", size=11),
            height=400
        )
        self.caption_prompt_text.pack(fill="both", expand=True, pady=(5, 10))
        
        # Action buttons
        self.action_frame = ctk.CTkFrame(self.editor_frame)
        self.action_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.save_btn = ctk.CTkButton(
            self.action_frame,
            text="💾 Save Template",
            command=self.save_template,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.save_btn.pack(side="left", padx=10, pady=10)
        
        self.use_btn = ctk.CTkButton(
            self.action_frame,
            text="✅ Use Template",
            command=self.use_template,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.use_btn.pack(side="left", padx=10, pady=10)
        
        self.cancel_btn = ctk.CTkButton(
            self.action_frame,
            text="❌ Close",
            command=self.destroy,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="gray",
            hover_color="darkgray"
        )
        self.cancel_btn.pack(side="right", padx=10, pady=10)
        
        # Initially disable editor
        self.toggle_editor_state(False)
        
    def load_templates(self):
        """Load templates into the list."""
        self.template_listbox.delete(0, tk.END)
        current_template = self.template_manager.settings.get("last_used_template")
        
        for i, (template_id, template_data) in enumerate(self.template_manager.templates.items()):
            name = template_data.get("name", template_id)
            if template_id == current_template:
                name += " ⭐"  # Mark current template
            self.template_listbox.insert(tk.END, name)
            
            # Select current template
            if template_id == current_template:
                self.template_listbox.selection_set(i)
                self.template_listbox.activate(i)
        
        # Load first template if any selected
        if self.template_listbox.curselection():
            self.load_selected_template()
            
    def on_template_select(self, event):
        """FIXED: Handle template selection."""
        self.load_selected_template()
        
    def load_selected_template(self):
        """Load the selected template into editor."""
        selection = self.template_listbox.curselection()
        if not selection or not self.template_manager:
            return
            
        # Get template ID
        template_ids = list(self.template_manager.templates.keys())
        if selection[0] >= len(template_ids):
            return
            
        template_id = template_ids[selection[0]]
        template_data = self.template_manager.get_template(template_id)
        
        if not template_data:
            return
            
        self.current_template_id = template_id
        self.is_editing = True
        
        # Load data into editor
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, template_data.get("name", ""))
        
        self.handle_entry.delete(0, tk.END)
        self.handle_entry.insert(0, template_data.get("account_handle", ""))
        
        self.description_entry.delete(0, tk.END)
        self.description_entry.insert(0, template_data.get("description", ""))
        
        self.title_prompt_text.delete("1.0", tk.END)
        self.title_prompt_text.insert("1.0", template_data.get("title_prompt", ""))
        
        self.caption_prompt_text.delete("1.0", tk.END)
        self.caption_prompt_text.insert("1.0", template_data.get("caption_prompt", ""))
        
        # Update header
        self.editor_header.configure(text=f"Editing: {template_data.get('name', template_id)}")
        
        # Enable editor
        self.toggle_editor_state(True)
        
    def toggle_editor_state(self, enabled: bool):
        """Enable/disable editor controls."""
        state = "normal" if enabled else "disabled"
        
        self.name_entry.configure(state=state)
        self.handle_entry.configure(state=state)
        self.description_entry.configure(state=state)
        self.title_prompt_text.configure(state=state)
        self.caption_prompt_text.configure(state=state)
        self.save_btn.configure(state=state)
        self.use_btn.configure(state=state)
        
    def create_new_template(self):
        """Create a new template."""
        name = simpledialog.askstring("New Template", "Enter template name:")
        if not name:
            return
            
        # Generate ID from name
        template_id = name.lower().replace(" ", "_").replace("@", "")
        
        # Check if exists
        if template_id in self.template_manager.templates:
            messagebox.showerror("Error", f"Template '{template_id}' already exists")
            return
            
        # Create new template
        new_template = {
            "name": name,
            "description": f"Custom template: {name}",
            "account_handle": "",
            "title_prompt": "Your title prompt here. Use {original_caption} to include the original caption.",
            "caption_prompt": "Your caption prompt here. Use {original_caption} to include the original caption."
        }
        
        if self.template_manager.create_template(template_id, new_template):
            self.load_templates()
            messagebox.showinfo("Success", f"Template '{name}' created successfully!")
        else:
            messagebox.showerror("Error", "Failed to create template")
            
    def duplicate_template(self):
        """Duplicate the selected template."""
        if not self.current_template_id:
            messagebox.showwarning("No Selection", "Please select a template to duplicate")
            return
            
        # Get new name
        original_name = self.template_manager.templates[self.current_template_id].get("name", self.current_template_id)
        new_name = simpledialog.askstring("Duplicate Template", f"Enter name for copy of '{original_name}':")
        if not new_name:
            return
            
        new_id = new_name.lower().replace(" ", "_").replace("@", "")
        
        if self.template_manager.duplicate_template(self.current_template_id, new_id, new_name):
            self.load_templates()
            messagebox.showinfo("Success", f"Template duplicated as '{new_name}'")
        else:
            messagebox.showerror("Error", "Failed to duplicate template")
            
    def export_template(self):
        """Export the selected template."""
        if not self.current_template_id:
            messagebox.showwarning("No Selection", "Please select a template to export")
            return
            
        template_name = self.template_manager.templates[self.current_template_id].get("name", self.current_template_id)
        
        file_path = filedialog.asksaveasfilename(
            title=f"Export Template: {template_name}",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if self.template_manager.export_template(self.current_template_id, file_path):
                messagebox.showinfo("Success", f"Template exported to {file_path}")
            else:
                messagebox.showerror("Error", "Failed to export template")
                
    def import_template(self):
        """Import a template from file."""
        file_path = filedialog.askopenfilename(
            title="Import Template",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if self.template_manager.import_template(file_path):
                self.load_templates()
                messagebox.showinfo("Success", "Template imported successfully!")
            else:
                messagebox.showerror("Error", "Failed to import template")
            
    def delete_template(self):
        """Delete the selected template."""
        if not self.current_template_id:
            messagebox.showwarning("No Selection", "Please select a template to delete")
            return
            
        template_name = self.template_manager.templates[self.current_template_id].get("name", self.current_template_id)
        
        if messagebox.askyesno("Confirm Delete", f"Delete template '{template_name}'?\n\nThis cannot be undone."):
            if self.template_manager.delete_template(self.current_template_id):
                self.current_template_id = None
                self.toggle_editor_state(False)
                self.editor_header.configure(text="Select a template to edit")
                self.load_templates()
                messagebox.showinfo("Success", "Template deleted")
            else:
                messagebox.showerror("Error", "Cannot delete template (it may be the last one)")
                
    def save_template(self):
        """Save the current template."""
        if not self.current_template_id:
            messagebox.showwarning("No Template", "No template selected for saving")
            return
            
        # Get data from editor
        template_data = {
            "name": self.name_entry.get().strip(),
            "description": self.description_entry.get().strip(),
            "account_handle": self.handle_entry.get().strip(),
            "title_prompt": self.title_prompt_text.get("1.0", tk.END).strip(),
            "caption_prompt": self.caption_prompt_text.get("1.0", tk.END).strip()
        }
        
        # Validate
        if not template_data["name"]:
            messagebox.showwarning("Validation Error", "Template name is required")
            return
            
        if not template_data["title_prompt"]:
            messagebox.showwarning("Validation Error", "Title prompt is required")
            return
            
        if not template_data["caption_prompt"]:
            messagebox.showwarning("Validation Error", "Caption prompt is required")
            return
            
        # Save
        if self.template_manager.update_template(self.current_template_id, template_data):
            self.load_templates()
            messagebox.showinfo("Success", "Template saved successfully!")
        else:
            messagebox.showerror("Error", "Failed to save template")
            
    def use_template(self):
        """Set this template as the current one."""
        if not self.current_template_id:
            messagebox.showwarning("No Template", "No template selected")
            return
            
        if self.template_manager.set_current_template(self.current_template_id):
            template_name = self.template_manager.templates[self.current_template_id].get("name", self.current_template_id)
            messagebox.showinfo("Success", f"'{template_name}' is now the active template")
            self.load_templates()
            
            # Call callback if provided
            if self.callback:
                self.callback()
        else:
            messagebox.showerror("Error", "Failed to set template as current")

# ═══════════════════════════════════════════════════════════════════════════════
# INITIALIZE EMBEDDED TEMPLATE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

# Initialize embedded template manager
try:
    template_manager = TemplateManager()
    print("✅ COMPLETE Template manager (embedded) initialized successfully")
    print(f"✅ Available templates: {template_manager.get_template_names()}")
    print(f"✅ Current template: {template_manager.get_current_template().get('name', 'None')}")
except Exception as e:
    print(f"❌ Template manager error: {e}")
    template_manager = None

# Try to import other modules (optional - graceful degradation)
config = None
BatchProcessor = None
batch_settings = None
AIContentGenerator = None


try:
    from easy_reels.core.config_manager import config
    print("✅ Config manager loaded")
except ImportError as e:
    print(f"⚠️ Config manager not found: {e}")

try:
    from easy_reels.core.batch_processor import BatchProcessor
    print("✅ Batch processor loaded")
except ImportError as e:
    print(f"⚠️ Batch processor not found: {e}")

try:
    from easy_reels.core.batch_settings_manager import batch_settings
    print("✅ Batch settings loaded")
except ImportError as e:
    print(f"⚠️ Batch settings not found: {e}")

try:
    from easy_reels.core.ai_content_generator import AIContentGenerator
    print("✅ AI content generator loaded")
except ImportError as e:
    print(f"⚠️ AI content generator not found: {e}")

print(f"\n📊 Module Status Summary:")
print(f"    Template Manager: {'✅ EMBEDDED & READY' if template_manager else '❌ FAILED'}")
print(f"    Config Manager: {'✅' if config else '❌'}")
print(f"    Batch Processor: {'✅' if BatchProcessor else '❌'}")
print(f"    AI Generator: {'✅' if AIContentGenerator else '❌'}")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION CLASS - COMPLETE BATCH SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class BatchEasyReelsApp(ctk.CTk):
    """COMPLETE batch processing window with ALL features and embedded template system."""
    
    def __init__(self):
        super().__init__()

        self.template_manager = TemplateManager()
        
        # --- Configure window ---
        self.title("Easy Reels (By Nicksen)")
        self.geometry("1200x750")
        self.minsize(1000, 700)
        self.center_window()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Initialize all variables here ---
        self.processing_thread = None
        self.stop_event = None
        self.logo_path = None
        self.profile_pic_path = None
        self._destroying = False
        self.scraper_window = None
        self.output_directory = str(Path("output").resolve())
        self.loading_label = None
        self.loading_animation_running = False
        self.ai_generator = None # Initialize as None

        # --- ✅ CORRECTED INITIALIZATION ORDER ---
        # 1. Create all widgets first.
        self.create_ui() 
        
        # 2. Now that the UI exists, initialize the AI generator for the first time.
        self.reinitialize_ai_generator() 
        
        # 3. Load settings and update the UI with loaded data.
        self.load_batch_settings()
        self.update_template_display()
        self.validate_setup()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
        # ============================================================================
        # API KEY MANAGEMENT METHODS - Add these to your BatchEasyReelsApp class
        # ============================================================================
        critical_folders = ['output', 'temp', 'config', 'config/api_keys', 'config/templates']
        for folder in critical_folders:
            Path(folder).mkdir(parents=True, exist_ok=True)
        
        # ✅ Set default output directory if not set
        if not hasattr(self, 'output_directory') or not self.output_directory:
            self.output_directory = str(Path("output").resolve())
        
    def setup_api_key_ui(self, parent):
        # API Key section in settings
        api_key_section = ctk.CTkFrame(parent) # Use the passed-in parent
        api_key_section.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(api_key_section, text="🔑 API Key Management", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))
        
        # Current API Key display
        current_key_frame = ctk.CTkFrame(api_key_section)
        current_key_frame.pack(fill="x", padx=15, pady=5)
        
        self.current_key_label = ctk.CTkLabel(current_key_frame, text="Loading API key status...", 
                                              font=ctk.CTkFont(size=11), text_color="lightgreen")
        self.current_key_label.pack(side="left", padx=10, pady=8)
        
        # API Key buttons
        key_buttons_frame = ctk.CTkFrame(api_key_section)
        key_buttons_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        ctk.CTkButton(key_buttons_frame, text="🔄 Select API Key", 
                      command=self.show_api_key_selector, height=35,
                      font=ctk.CTkFont(size=11)).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(key_buttons_frame, text="➕ Add/Manage Keys", 
                      command=self.open_api_key_manager, height=35,
                      font=ctk.CTkFont(size=11)).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(key_buttons_frame, text="✅ Test Current Key", 
                      command=self.test_current_api_key, height=35,
                      font=ctk.CTkFont(size=11)).pack(side="left", padx=5, pady=10)
        
        # Update API key display
        self.update_api_key_display()


    def update_api_key_display(self):
        try:
            if not hasattr(self, 'current_key_label'):
                return
                
            if hasattr(self, 'ai_generator') and self.ai_generator:
                status = self.ai_generator.get_api_key_status()
                
                if status["status"] == "configured":
                    text = f"🔑 {status['key_name']} ({status['total_keys']} keys available)"
                    color = "lightgreen"
                elif status["status"] == "no_key":
                    text = f"❌ No API key selected ({status['total_keys']} keys available)"
                    color = "red"
                else:
                    text = "🔧 Using legacy .env configuration"
                    color = "yellow"
                    
                self.current_key_label.configure(text=text, text_color=color)
            else:
                self.current_key_label.configure(text="⚠️ AI generator not initialized", text_color="orange")
                
        except Exception as e:
            print(f"❌ Error updating API key display: {e}")
            if hasattr(self, 'current_key_label'):
                self.current_key_label.configure(text="❌ Error loading API keys", text_color="red")


    def show_api_key_selector(self):

        try:
            if not hasattr(self, 'ai_generator') or not self.ai_generator:
                messagebox.showinfo("Not Available", "AI generator not available")
                return
                
            # Get available API keys
            key_names = self.ai_generator.get_api_keys()
            if not key_names:
                messagebox.showwarning("No API Keys", "No API keys available. Please add one first.")
                self.open_api_key_manager()
                return
                
            current_info = self.ai_generator.get_current_api_key_info()
            current = current_info["id"] if current_info else ""
            
            # Create popup window
            selector_window = ctk.CTkToplevel(self)
            selector_window.title("Select API Key")
            selector_window.geometry("450x300")
            selector_window.transient(self)
            selector_window.grab_set()
            
            # Center window
            selector_window.update_idletasks()
            x = (selector_window.winfo_screenwidth() // 2) - (450 // 2)
            y = (selector_window.winfo_screenheight() // 2) - (300 // 2)
            selector_window.geometry(f"450x300+{x}+{y}")
            
            # Selection variable
            selected_key = ctk.StringVar(value=current)
            
            # Define functions
            def apply_selection():
                chosen = selected_key.get()
                if chosen and self.ai_generator.set_current_api_key(chosen):
                    self.update_api_key_display()
                    key_info = self.ai_generator.get_api_key(chosen)
                    key_name = key_info["name"] if key_info else chosen
                    messagebox.showinfo("Success", f"Now using API key: {key_name}")
                    print(f"🔑 Switched to API key: {key_name}")
                    selector_window.destroy()
                else:
                    messagebox.showerror("Error", "Failed to change API key")
            
            def cancel_selection():
                selector_window.destroy()
            
            # UI Layout
            ctk.CTkLabel(selector_window, text="Select API Key", 
                         font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
            
            current_text = f"Current: {current_info['name']}" if current_info else "Current: None"
            ctk.CTkLabel(selector_window, text=current_text, 
                         font=ctk.CTkFont(size=12), text_color="lightgreen").pack(pady=5)
            
            # Button frame (bottom)
            button_frame = ctk.CTkFrame(selector_window)
            button_frame.pack(side="bottom", fill="x", padx=20, pady=10)
            
            # Keys frame (expandable)
            keys_frame = ctk.CTkScrollableFrame(selector_window, height=150)
            keys_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Buttons
            ctk.CTkButton(button_frame, text="✅ Use Key", command=apply_selection, height=35,
                          font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10, pady=10)
            
            ctk.CTkButton(button_frame, text="❌ Cancel", command=cancel_selection, height=35,
                          font=ctk.CTkFont(size=12), fg_color="gray").pack(side="right", padx=10, pady=10)
            
            # Create key options
            for key_id in key_names:
                key_data = self.ai_generator.get_api_key(key_id)
                key_name = key_data.get("name", key_id) if key_data else key_id
                
                # Key frame with radio button
                key_frame = ctk.CTkFrame(keys_frame)
                key_frame.pack(fill="x", pady=5)
                
                radio = ctk.CTkRadioButton(key_frame, text=key_name, variable=selected_key, value=key_id)
                radio.pack(side="left", padx=10, pady=10)
                
        except Exception as e:
            messagebox.showerror("Error", f"API key selector error: {e}")
            print(f"❌ API key selector error: {e}")


    def open_api_key_manager(self):
        try:
            if not hasattr(self, 'ai_generator') or not self.ai_generator:
                messagebox.showinfo("Not Available", "AI generator not available")
                return
            
            # Create manager window
            manager_window = ctk.CTkToplevel(self)
            manager_window.title("API Key Manager")
            manager_window.geometry("550x450")
            manager_window.transient(self)
            manager_window.grab_set()
            
            # Center window
            manager_window.update_idletasks()
            x = (manager_window.winfo_screenwidth() // 2) - (275)
            y = (manager_window.winfo_screenheight() // 2) - (225)
            manager_window.geometry(f"550x450+{x}+{y}")
            
            # Title
            ctk.CTkLabel(manager_window, text="🔑 API Key Manager", 
                         font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
            
            # Add new key section
            add_frame = ctk.CTkFrame(manager_window)
            add_frame.pack(fill="x", padx=20, pady=(0, 15))
            
            ctk.CTkLabel(add_frame, text="Add New API Key", 
                         font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
            
            # Input fields
            fields_frame = ctk.CTkFrame(add_frame)
            fields_frame.pack(fill="x", padx=15, pady=(5, 15))
            
            ctk.CTkLabel(fields_frame, text="Name:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
            name_entry = ctk.CTkEntry(fields_frame, width=250, placeholder_text="e.g., My Work API Key")
            name_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
            
            ctk.CTkLabel(fields_frame, text="API Key:").grid(row=1, column=0, padx=8, pady=8, sticky="w")
            key_entry = ctk.CTkEntry(fields_frame, width=250, show="*", placeholder_text="gsk_...")
            key_entry.grid(row=1, column=1, padx=8, pady=8, sticky="ew")
            
            ctk.CTkLabel(fields_frame, text="Description:").grid(row=2, column=0, padx=8, pady=8, sticky="w")
            desc_entry = ctk.CTkEntry(fields_frame, width=250, placeholder_text="Optional description")
            desc_entry.grid(row=2, column=1, padx=8, pady=8, sticky="ew")
            
            fields_frame.grid_columnconfigure(1, weight=1)
            
            # Add key function
            def add_new_key():
                name = name_entry.get().strip()
                api_key = key_entry.get().strip()
                description = desc_entry.get().strip()
                
                if not name or not api_key:
                    messagebox.showwarning("Missing Info", "Name and API Key are required")
                    return
                
                # Validate API key format
                if not api_key.startswith("gsk_"):
                    result = messagebox.askyesno("Invalid Format", 
                        f"API key doesn't start with 'gsk_'.\n\nContinue anyway?")
                    if not result:
                        return
                
                # Create unique key ID
                key_id = name.lower().replace(" ", "_").replace("-", "_")
                counter = 1
                original_id = key_id
                existing_keys = self.ai_generator.get_api_keys()
                
                # Make sure key ID is unique
                while key_id in existing_keys:
                    key_id = f"{original_id}_{counter}"
                    counter += 1
                
                # Add the key
                if self.ai_generator.add_api_key(key_id, name, api_key, description):
                    messagebox.showinfo("Success", f"API key '{name}' added successfully!")
                    print(f"🔑 Added new API key: {name}")
                    
                    # Update display and clear entries
                    self.update_api_key_display()
                    name_entry.delete(0, "end")
                    key_entry.delete(0, "end") 
                    desc_entry.delete(0, "end")
                    
                    # Ask if user wants to use this key immediately
                    if len(existing_keys) == 0:  # First key
                        if messagebox.askyesno("Set as Current", 
                            f"Set '{name}' as the current API key?"):
                            self.ai_generator.set_current_api_key(key_id)
                            self.update_api_key_display()
                            print(f"🔑 Set {name} as current key")
                    
                else:
                    messagebox.showerror("Error", "Failed to add API key. Check console for details.")
            
            # Add key button
            ctk.CTkButton(add_frame, text="➕ Add API Key", command=add_new_key, 
                          height=35, font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(0, 10))
            
            # Current keys section
            keys_section = ctk.CTkFrame(manager_window)
            keys_section.pack(fill="both", expand=True, padx=20, pady=(0, 15))
            
            ctk.CTkLabel(keys_section, text="Current API Keys", 
                         font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
            
            # Keys list
            keys_list = ctk.CTkScrollableFrame(keys_section, height=150)
            keys_list.pack(fill="both", expand=True, padx=15, pady=(5, 15))
            
            # Display existing keys
            existing_keys = self.ai_generator.get_api_keys()
            current_info = self.ai_generator.get_current_api_key_info()
            current_id = current_info["id"] if current_info else None
            
            if existing_keys:
                for key_id in existing_keys:
                    key_data = self.ai_generator.get_api_key(key_id)
                    key_name = key_data.get("name", key_id) if key_data else key_id
                    is_current = key_id == current_id
                    
                    key_frame = ctk.CTkFrame(keys_list)
                    key_frame.pack(fill="x", pady=2)
                    
                    # Key info
                    status_text = "🟢 CURRENT" if is_current else "⚫"
                    info_text = f"{status_text} {key_name}"
                    
                    ctk.CTkLabel(key_frame, text=info_text, 
                                 font=ctk.CTkFont(size=11, weight="bold" if is_current else "normal"),
                                 text_color="lightgreen" if is_current else "white").pack(side="left", padx=10, pady=8)
            else:
                ctk.CTkLabel(keys_list, text="No API keys found. Add one above.", 
                             font=ctk.CTkFont(size=11), text_color="gray").pack(pady=20)
            
            # Bottom buttons
            bottom_frame = ctk.CTkFrame(manager_window)
            bottom_frame.pack(fill="x", padx=20, pady=(0, 15))
            
            ctk.CTkButton(bottom_frame, text="🔄 Select Different Key", 
                          command=lambda: [manager_window.destroy(), self.show_api_key_selector()], 
                          height=35).pack(side="left", padx=5, pady=10)
            
            ctk.CTkButton(bottom_frame, text="Close", command=manager_window.destroy, 
                          height=35, fg_color="gray").pack(side="right", padx=5, pady=10)
            
            print("🔑 API key manager opened")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open API key manager: {e}")
            print(f"❌ API key manager error: {e}")



    def test_current_api_key(self):
        """Test the current API key."""
        try:
            if not hasattr(self, 'ai_generator') or not self.ai_generator:
                messagebox.showinfo("Not Available", "AI generator not available")
                return
                
            current_info = self.ai_generator.get_current_api_key_info()
            if not current_info:
                messagebox.showwarning("No Key", "No API key selected")
                return
                
            # Test the key using the AI generator's validation method
            current_key_value = current_info.get("key")
            if not current_key_value:
                messagebox.showwarning("No Key", "No API key found")
                return
            
            # Show testing dialog with progress
            test_window = ctk.CTkToplevel(self)
            test_window.title("Testing API Key...")
            test_window.geometry("300x150")
            test_window.transient(self)
            test_window.grab_set()
            
            # Center window
            test_window.update_idletasks()
            x = (test_window.winfo_screenwidth() // 2) - (300 // 2)
            y = (test_window.winfo_screenheight() // 2) - (150 // 2)
            test_window.geometry(f"300x150+{x}+{y}")
            
            ctk.CTkLabel(test_window, text="🔍 Testing API Key...", 
                         font=ctk.CTkFont(size=14)).pack(pady=20)
            
            progress = ctk.CTkProgressBar(test_window)
            progress.pack(pady=10, padx=20, fill="x")
            progress.set(0)
            
            def test_key_thread():
                try:
                    # Animate progress
                    for i in range(1, 11):
                        progress.set(i/10)
                        test_window.update()
                        import time
                        time.sleep(0.1)
                    
                    # Test the key
                    is_valid = self.ai_generator.validate_api_key(current_key_value)
                    
                    test_window.after(100, lambda: show_result(is_valid))
                    
                except Exception as e:
                    test_window.after(100, lambda: show_result(False, str(e)))
            
            def show_result(valid, error=None):
                test_window.destroy()
                
                if valid:
                    key_name = current_info.get("name", "Unknown")
                    messagebox.showinfo("✅ Success", f"API key '{key_name}' is working correctly!")
                    self.log_message(f"✅ API key validation successful: {key_name}")
                else:
                    error_msg = f"API key validation failed"
                    if error:
                        error_msg += f": {error}"
                    messagebox.showerror("❌ Failed", error_msg)
                    self.log_message(f"❌ API key validation failed: {error or 'Unknown error'}")
            
            # Start test in thread
            import threading
            threading.Thread(target=test_key_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error testing API key: {e}")
            self.log_message(f"❌ Error testing API key: {e}")


    def show_api_key_selector(self):
        try:
            if not hasattr(self, 'ai_generator') or not self.ai_generator:
                messagebox.showinfo("Not Available", "AI generator not available")
                return
                
            # Get available API keys
            key_names = self.ai_generator.get_api_keys()
            if not key_names:
                messagebox.showwarning("No API Keys", "No API keys available. Please add one first.")
                self.open_api_key_manager()
                return
                
            current_info = self.ai_generator.get_current_api_key_info()
            current = current_info["id"] if current_info else ""
            
            # Create popup window
            selector_window = ctk.CTkToplevel(self)
            selector_window.title("Select API Key")
            selector_window.geometry("500x400")
            selector_window.transient(self)
            selector_window.grab_set()
            
            # Center window
            selector_window.update_idletasks()
            x = (selector_window.winfo_screenwidth() // 2) - (250)
            y = (selector_window.winfo_screenheight() // 2) - (200)
            selector_window.geometry(f"500x400+{x}+{y}")
            
            # Selection variable
            selected_key = ctk.StringVar(value=current)
            
            # Store keys frame reference for refreshing
            keys_container = None
            
            def refresh_keys():
                """Refresh the keys list."""
                nonlocal keys_container
                if keys_container:
                    # Clear existing keys
                    for widget in keys_container.winfo_children():
                        widget.destroy()
                    
                    # Get fresh key list
                    fresh_keys = self.ai_generator.get_api_keys()
                    current_fresh = self.ai_generator.get_current_api_key_info()
                    current_id = current_fresh["id"] if current_fresh else ""
                    selected_key.set(current_id)
                    
                    # Recreate key options
                    for key_id in fresh_keys:
                        key_data = self.ai_generator.get_api_key(key_id)
                        key_name = key_data.get("name", key_id) if key_data else key_id
                        key_desc = key_data.get("description", "") if key_data else ""
                        created = key_data.get("created_date", "") if key_data else ""
                        
                        # Key container frame
                        key_frame = ctk.CTkFrame(keys_container)
                        key_frame.pack(fill="x", pady=3, padx=5)
                        
                        # Radio button
                        radio = ctk.CTkRadioButton(key_frame, text="", variable=selected_key, value=key_id, width=20)
                        radio.pack(side="left", padx=5, pady=8)
                        
                        # Key info frame
                        info_frame = ctk.CTkFrame(key_frame)
                        info_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))
                        
                        # Key name (clickable to select)
                        name_label = ctk.CTkLabel(info_frame, text=key_name, 
                                                 font=ctk.CTkFont(size=12, weight="bold"), cursor="hand2")
                        name_label.pack(anchor="w", padx=8, pady=(4, 0))
                        name_label.bind("<Button-1>", lambda e, kid=key_id: selected_key.set(kid))
                        
                        # Description and date (if available)
                        if key_desc:
                            desc_text = key_desc[:30] + "..." if len(key_desc) > 30 else key_desc
                            ctk.CTkLabel(info_frame, text=desc_text, font=ctk.CTkFont(size=9), 
                                         text_color="gray").pack(anchor="w", padx=8)
                        if created:
                            ctk.CTkLabel(info_frame, text=f"Created: {created}", font=ctk.CTkFont(size=8), 
                                         text_color="lightblue").pack(anchor="w", padx=8, pady=(0, 4))
                        
                        # Delete button
                        def delete_key(key_to_delete=key_id, key_to_delete_name=key_name):
                            result = messagebox.askyesno("Confirm Delete", 
                                f"Are you sure you want to delete API key '{key_to_delete_name}'?")
                            if result:
                                # Check if it's the current key
                                current_key_info = self.ai_generator.get_current_api_key_info()
                                is_current = current_key_info and current_key_info["id"] == key_to_delete
                                
                                # Delete the key
                                if hasattr(self.ai_generator, 'api_key_manager'):
                                    success = self.ai_generator.api_key_manager.delete_key(key_to_delete)
                                else:
                                    success = False
                                
                                if success:
                                    messagebox.showinfo("Deleted", f"API key '{key_to_delete_name}' deleted successfully!")
                                    print(f"🗑️ Deleted API key: {key_to_delete_name}")
                                    
                                    # Refresh the display
                                    refresh_keys()
                                    self.update_api_key_display()
                                    
                                    # Check if we need to close the dialog (no keys left)
                                    remaining_keys = self.ai_generator.get_api_keys()
                                    if not remaining_keys:
                                        messagebox.showinfo("No Keys", "No API keys remaining. Please add a new one.")
                                        selector_window.destroy()
                                        self.open_api_key_manager()
                                else:
                                    messagebox.showerror("Error", f"Failed to delete API key '{key_to_delete_name}'")
                        
                        delete_btn = ctk.CTkButton(key_frame, text="🗑️", width=30, height=25,
                                                 command=delete_key, fg_color="red", hover_color="darkred",
                                                 font=ctk.CTkFont(size=10))
                        delete_btn.pack(side="right", padx=5, pady=5)
            
            # Define main functions
            def apply_selection():
                chosen = selected_key.get()
                if not chosen:
                    messagebox.showwarning("No Selection", "Please select an API key")
                    return
                    
                if self.ai_generator.set_current_api_key(chosen):
                    self.update_api_key_display()
                    key_info = self.ai_generator.get_api_key(chosen)
                    key_name = key_info["name"] if key_info else chosen
                    messagebox.showinfo("Success", f"Now using API key: {key_name}")
                    print(f"🔑 Switched to API key: {key_name}")
                    selector_window.destroy()
                else:
                    messagebox.showerror("Error", "Failed to change API key")
            
            def cancel_selection():
                selector_window.destroy()
            
            def add_new_key():
                """Open add key dialog from selector."""
                selector_window.destroy()
                self.open_api_key_manager()
            
            # UI Layout
            ctk.CTkLabel(selector_window, text="🔑 Select API Key", 
                         font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
            
            current_text = f"Current: {current_info['name']}" if current_info else "Current: None"
            ctk.CTkLabel(selector_window, text=current_text, 
                         font=ctk.CTkFont(size=11), text_color="lightgreen").pack(pady=(0, 10))
            
            # Button frame (bottom)
            button_frame = ctk.CTkFrame(selector_window)
            button_frame.pack(side="bottom", fill="x", padx=15, pady=10)
            
            # Keys frame (scrollable)
            keys_frame = ctk.CTkScrollableFrame(selector_window, height=200)
            keys_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))
            keys_container = keys_frame  # Store reference
            
            # Main buttons
            ctk.CTkButton(button_frame, text="✅ Use Selected Key", command=apply_selection, height=35,
                          font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=5, pady=5)
            
            ctk.CTkButton(button_frame, text="➕ Add New Key", command=add_new_key, height=35,
                          font=ctk.CTkFont(size=11)).pack(side="left", padx=5, pady=5)
            
            ctk.CTkButton(button_frame, text="❌ Cancel", command=cancel_selection, height=35,
                          font=ctk.CTkFont(size=11), fg_color="gray").pack(side="right", padx=5, pady=5)
            
            # Initial load of keys
            refresh_keys()
            
        except Exception as e:
            messagebox.showerror("Error", f"API key selector error: {e}")
            print(f"❌ API key selector error: {e}")


        
    def center_window(self):
        """Center window on screen."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"1200x700+{x}+{y}")
        
    def open_template_editor(self):
        if not template_manager:
            messagebox.showinfo("Not Available", "Template manager not available")
            return
            
        try:
            editor = EmbeddedTemplateEditor(self, template_manager, callback=self.update_template_display)
            self.log_message("✏️ Complete template editor opened")
            self.log_message("📝 Available features: Create, Edit, Delete, Import, Export")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open template editor: {e}")
            self.log_message(f"❌ Template editor error: {e}")

    def on_closing(self):
        """Handle window closing."""
        self._destroying = True
        
        if self.processing_thread and self.processing_thread.is_alive():
            if messagebox.askyesno("Confirm Exit", "Batch processing is in progress. Are you sure you want to exit?"):
                if hasattr(self, 'batch_processor') and self.batch_processor:
                    try:
                        self.batch_processor.stop_processing()
                    except:
                        pass
                self.after(500, self.destroy)
            else:
                self._destroying = False
        else:
            self.destroy()
    
    def safe_after(self, delay, func):
        """Thread-safe after() calls."""
        if not self._destroying:
            try:
                if self.winfo_exists():
                    self.after(delay, func)
            except tk.TclError:
                pass
    
    def create_ui(self):
        """Create the complete user interface."""
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left sidebar
        self.create_sidebar()
        
        # Main content area
        self.create_main_content()
    
    # In BatchEasyReelsApp class...
    def stop_batch_processing(self):
        self.log_message("⏹️ Batch processing stop requested")
        if self.stop_event:
            self.stop_event.set()
        if hasattr(self, 'processing_thread') and self.processing_thread.is_alive():
            self.log_message("🔄 Stopping background thread... Please wait for the current step to finish.")
        self.stop_btn.configure(state="disabled")

        
    def create_sidebar(self):
        """
        --- 👇 MAJOR UI IMPROVEMENT ---
        Redesigned sidebar using a TabView for a cleaner, more organized layout.
        """
        self.sidebar = ctk.CTkFrame(self, width=340, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(2, weight=1) # Make the tabview expand

        # --- Sidebar Header ---
        ctk.CTkLabel(self.sidebar, text="Easy Reels", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 5))
        ctk.CTkLabel(self.sidebar, text="Batch Mode", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray").grid(row=1, column=0, padx=20, pady=(0, 15))

        # --- TabView for Organization ---
        self.sidebar_tabview = ctk.CTkTabview(self.sidebar)
        self.sidebar_tabview.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # --- 1. Process Tab (Primary Actions) ---
        self.process_tab = self.sidebar_tabview.add("Process")
        self.create_process_tab(self.process_tab)

        # --- 2. File Management Tab (Configuration) ---
        self.settings_tab = self.sidebar_tabview.add("File Management")
        self.create_settings_tab(self.settings_tab)

        # --- 3. Tools Tab (Extra Features) ---
        self.tools_tab = self.sidebar_tabview.add("Tools")
        self.create_tools_tab(self.tools_tab)

    def create_process_tab(self, parent):
        """Creates the primary 'Process' tab content."""
        parent.grid_columnconfigure(0, weight=1)
        
        # URLs Section
        urls_frame = ctk.CTkFrame(parent)
        urls_frame.pack(pady=10, padx=5, fill="x")
        ctk.CTkLabel(urls_frame, text="Instagram URLs (One per line)", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5))
        self.urls_textbox = ctk.CTkTextbox(urls_frame, height=150, font=ctk.CTkFont(size=10))
        self.urls_textbox.pack(padx=10, pady=10, fill="both", expand=True)

        # Progress Section
        self.progress_frame = ctk.CTkFrame(parent)
        self.progress_frame.pack(pady=10, padx=5, fill="x")
        ctk.CTkLabel(self.progress_frame, text="Progress", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5))
        self.overall_status_label = ctk.CTkLabel(self.progress_frame, text="Ready", font=ctk.CTkFont(size=10))
        self.overall_status_label.pack(pady=2)
        self.overall_progress_bar = ctk.CTkProgressBar(self.progress_frame, height=12)
        self.overall_progress_bar.pack(padx=10, pady=5, fill="x")
        self.overall_progress_bar.set(0)
        self.current_status_label = ctk.CTkLabel(self.progress_frame, text="", font=ctk.CTkFont(size=9), text_color="gray")
        self.current_status_label.pack(pady=1)

        # Action Buttons
        action_frame = ctk.CTkFrame(parent)
        action_frame.pack(pady=20, padx=5, fill="x")
        
        # --- Configure grid for side-by-side buttons ---
        action_frame.grid_columnconfigure((0, 1), weight=1)

        # --- Main "Start" button spans the full width ---
        self.start_button = ctk.CTkButton(
            action_frame, 
            text="🚀 Start Processing", 
            command=self.start_batch_processing, 
            height=40, 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.start_button.grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="ew")

        # --- Secondary buttons are side-by-side ---
        self.dummy_button = ctk.CTkButton(
            action_frame, 
            text="➕ Add Test Link", 
            command=self.add_dummy_link, 
            height=30, 
            fg_color="gray"
        )
        self.dummy_button.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="ew")

        self.stop_btn = ctk.CTkButton(
            action_frame, 
            text="⏹ Stop", 
            command=self.stop_batch_processing, 
            height=30, 
            fg_color="red", 
            hover_color="darkred", 
            state="disabled"
        )
        self.stop_btn.grid(row=1, column=1, padx=(5, 10), pady=5, sticky="ew")

    def add_dummy_link(self):
        """Adds a predefined dummy Instagram Reel URL to the textbox for testing."""
        dummy_url = "https://www.instagram.com/reels/DPhJIzjiWgm/"
        current_text = self.urls_textbox.get("1.0", "end").strip()
        
        if current_text:
            new_text = f"{current_text}\n{dummy_url}"
        else:
            new_text = dummy_url
            
        self.urls_textbox.delete("1.0", "end")
        self.urls_textbox.insert("1.0", new_text)
        self.log_message("➕ Dummy URL added for testing.")

    def start_loading_animation(self):
        """Displays a loading animation in the results tab."""
        if self.loading_label is None or not self.loading_label.winfo_exists():
            self.loading_label = ctk.CTkLabel(self.results_frame, text="Processing... |", font=ctk.CTkFont(size=18, weight="bold"), text_color="gray")
            self.loading_label.pack(pady=50, padx=20, expand=True)
        
        self.loading_animation_running = True
        self.update_loading_animation(0)

    def update_loading_animation(self, step):
        """Cycles through animation characters."""
        if not self.loading_animation_running:
            return
        
        animation_chars = ["|", "/", "—", "\\"]
        char = animation_chars[step % len(animation_chars)]
        self.loading_label.configure(text=f"Processing... {char}")
        self.after(200, lambda: self.update_loading_animation(step + 1))

    def create_settings_tab(self, parent):
        """Creates the 'File Management' tab content."""
        parent.grid_columnconfigure(0, weight=1)
        
        settings_scroll_frame = ctk.CTkScrollableFrame(parent)
        settings_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Output Directory
        output_dir_frame = ctk.CTkFrame(settings_scroll_frame)
        output_dir_frame.pack(pady=10, fill="x")
        ctk.CTkLabel(output_dir_frame, text="📁 Output Directory", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.output_dir_btn = ctk.CTkButton(output_dir_frame, text="Select Folder", command=self.select_output_directory)
        self.output_dir_btn.pack(padx=10, pady=5, fill="x")
        self.output_dir_label = ctk.CTkLabel(output_dir_frame, text=f"Current: {self.output_directory}", font=ctk.CTkFont(size=9), text_color="gray", wraplength=250, justify="left")
        self.output_dir_label.pack(pady=5, padx=10, anchor="w")
        
        # Daily Limit Configuration
        daily_limit_frame = ctk.CTkFrame(settings_scroll_frame)
        daily_limit_frame.pack(pady=10, fill="x")
        ctk.CTkLabel(daily_limit_frame, text="📊 Daily Limit", font=ctk.CTkFont(weight="bold")).pack(pady=5)

        # Enable/Disable Daily Limit
        self.use_daily_limit_var = ctk.BooleanVar(value=True)
        self.use_daily_limit_check = ctk.CTkCheckBox(
            daily_limit_frame, 
            text="Enable Daily Limit (e.g., 6-1.mp4, 6-2.mp4)", 
            variable=self.use_daily_limit_var,
            command=self.toggle_daily_limit
        )
        self.use_daily_limit_check.pack(padx=10, pady=5, anchor="w")

        # Starting Day Number
        start_day_frame = ctk.CTkFrame(daily_limit_frame)
        start_day_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(start_day_frame, text="Starting Day:", width=100).pack(side="left", padx=5)
        self.start_day_entry = ctk.CTkEntry(start_day_frame, placeholder_text="e.g., 6", width=150)
        self.start_day_entry.pack(side="left", padx=5)
        self.start_day_entry.insert(0, "1")  # Default to day 1

        # Daily Video Limit
        limit_frame = ctk.CTkFrame(daily_limit_frame)
        limit_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(limit_frame, text="Videos per Day:", width=100).pack(side="left", padx=5)
        self.daily_video_limit_entry = ctk.CTkEntry(limit_frame, placeholder_text="e.g., 12", width=150)
        self.daily_video_limit_entry.pack(side="left", padx=5)
        self.daily_video_limit_entry.insert(0, "12")  # Default to 12 videos per day

        # Example preview
        self.daily_limit_example = ctk.CTkLabel(
            daily_limit_frame, 
            text="Example: 6-1.mp4, 6-2.mp4, ..., 6-12.mp4, then 7-1.mp4", 
            font=ctk.CTkFont(size=9), 
            text_color="gray"
        )
        self.daily_limit_example.pack(pady=5, padx=10, anchor="w")

        # --- 👇 ADD THIS ENTIRE "ASSETS" SECTION BACK ---
        assets_frame = ctk.CTkFrame(settings_scroll_frame)
        assets_frame.pack(pady=10, fill="x", expand=True)
        ctk.CTkLabel(assets_frame, text="🖼️ Branding Assets", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        # Logo Upload
        logo_frame = ctk.CTkFrame(assets_frame)
        logo_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(logo_frame, text="Upload Logo", command=self.upload_logo).pack(side="left", padx=(0, 10))
        self.logo_status = ctk.CTkLabel(logo_frame, text="No logo uploaded", font=ctk.CTkFont(size=10), text_color="gray")
        self.logo_status.pack(side="left")

        # Profile Picture Upload
        profile_frame = ctk.CTkFrame(assets_frame)
        profile_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(profile_frame, text="Upload Profile Pic", command=self.upload_profile_pic).pack(side="left", padx=(0, 10))
        self.profile_status = ctk.CTkLabel(profile_frame, text="No profile pic uploaded", font=ctk.CTkFont(size=10), text_color="gray")
        self.profile_status.pack(side="left")

    def toggle_daily_limit(self):
        enabled = self.use_daily_limit_var.get()
        state = "normal" if enabled else "disabled"
        self.start_day_entry.configure(state=state)
        self.daily_video_limit_entry.configure(state=state)
        self.log_message(f"📊 Daily limit {'enabled' if enabled else 'disabled'}")

    def get_next_filename(self, output_dir):
        '''
        Generate the next filename based on daily limit system.
        Returns tuple: (video_filename, caption_filename, day_number, video_number)
        '''
        try:
            # Check if daily limit is enabled
            if not self.use_daily_limit_var.get():
                # Fallback to timestamp-based naming
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                video_name = f"video_{timestamp}.mp4"
                caption_name = f"video_{timestamp}_caption.txt"
                return video_name, caption_name, None, None
            
            # Get configuration
            start_day = int(self.start_day_entry.get().strip() or "1")
            daily_limit = int(self.daily_video_limit_entry.get().strip() or "12")
            
            # Scan existing files to find the current count
            existing_files = []
            if os.path.exists(output_dir):
                for file in os.listdir(output_dir):
                    if file.endswith('.mp4') and '-' in file:
                        try:
                            # Extract day and number from filename (e.g., "6-5.mp4" -> day=6, num=5)
                            base = file.replace('.mp4', '')
                            parts = base.split('-')
                            if len(parts) == 2:
                                day = int(parts[0])
                                num = int(parts[1])
                                existing_files.append((day, num))
                        except:
                            continue
            
            # Determine next day and number
            if not existing_files:
                # No files exist, start fresh
                current_day = start_day
                current_num = 1
            else:
                # Find the highest day and number
                existing_files.sort()
                last_day, last_num = existing_files[-1]
                
                # Check if we need to move to next day
                if last_num >= daily_limit:
                    current_day = last_day + 1
                    current_num = 1
                else:
                    current_day = last_day
                    current_num = last_num + 1
            
            # Generate filenames
            video_name = f"{current_day}-{current_num}.mp4"
            caption_name = f"{current_day}-{current_num}_caption.txt"
            
            self.log_message(f"📝 Generated filename: {video_name} (Day {current_day}, Video {current_num}/{daily_limit})")
            
            return video_name, caption_name, current_day, current_num
            
        except Exception as e:
            self.log_message(f"❌ Error generating filename: {e}")
            # Fallback to timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"video_{timestamp}.mp4", f"video_{timestamp}_caption.txt", None, None

    def create_tools_tab(self, parent):
        """Creates the 'Tools' tab content with corrected variable names."""
        parent.grid_columnconfigure(0, weight=1)

        # Template Management
        template_frame = ctk.CTkFrame(parent)
        template_frame.pack(pady=10, padx=5, fill="x")
        ctk.CTkLabel(template_frame, text="🎨 AI Template", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5))
        self.current_template_label = ctk.CTkLabel(template_frame, text="Loading...", font=ctk.CTkFont(size=10), text_color="lightgreen")
        self.current_template_label.pack(pady=2)
        ctk.CTkButton(template_frame, text="✏️ Manage Templates", command=self.open_template_editor).pack(padx=10, pady=10, fill="x")

        # API Key Management
        api_frame = ctk.CTkFrame(parent)
        api_frame.pack(pady=10, padx=5, fill="x")
        ctk.CTkLabel(api_frame, text="🔑 API Keys", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5))
        ctk.CTkButton(api_frame, text="⚙️ Manage API Keys", command=self.open_api_key_manager).pack(padx=10, pady=10, fill="x")
        
        # Scraper Tool
        scraper_frame = ctk.CTkFrame(parent)
        scraper_frame.pack(pady=10, padx=5, fill="x")
        ctk.CTkLabel(scraper_frame, text="🔍 Reel Scraper", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5))
        ctk.CTkButton(scraper_frame, text="Open Scraper Tool", command=self.open_reel_scraper, fg_color="#FF6347", hover_color="#E5533D").pack(padx=10, pady=10, fill="x")
        
        # --- 👇 BUG FIX: Use 'self.switch_frame' consistently ---
        self.switch_frame = ctk.CTkFrame(parent)
        self.switch_frame.pack(pady=10, padx=5, fill="x")
        ctk.CTkLabel(self.switch_frame, text="🔄 Application Control", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10, 5))
        ctk.CTkButton(self.switch_frame, text="🎬 Switch to Single Mode", command=self.switch_to_single_mode, fg_color=("gray70", "gray30")).pack(padx=10, pady=5, fill="x")
        
        ctk.CTkButton(self.switch_frame, text="🔄 Restart Application", command=self.restart_app, fg_color="#E67E22", hover_color="#D35400").pack(padx=10, pady=5, fill="x")
    # Add this new method anywhere inside the BatchEasyReelsApp class
    def restart_app(self):
        """Restarts the current application by re-running the main.py script."""
        self.log_message("🔄 Restarting application...")
        
        # This safely closes the current window
        self.destroy() 
        
        # --- 👇 CRITICAL FIX ---
        # We explicitly tell Python to run the main.py script from the project root.
        main_script_path = os.path.join(project_root, "main.py")
        os.execl(sys.executable, f'"{sys.executable}"', f'"{main_script_path}"')

    def select_output_directory(self):
        """Open a dialog to select the output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self.output_directory
        )
        if directory:
            self.output_directory = directory
            self.output_dir_label.configure(text=f"Current: {self.output_directory}")
            self.log_message(f"📁 Output directory set to: {self.output_directory}")
            # Optionally, auto-save this setting
            self.save_batch_settings()

    def open_reel_scraper(self):
        """Opens the Reel Scraper window."""
        if self.scraper_window is None or not self.scraper_window.winfo_exists():
            self.scraper_window = ReelScraperApp(self)  # Create a new instance if it doesn't exist
            self.log_message("🔍 Reel Scraper opened.")
        else:
            self.scraper_window.focus()  # If it exists, bring it to the front
            self.log_message("🔍 Reel Scraper is already open.")
            
    def create_main_content(self):
        """Create main content area with tabs."""
        
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=12, pady=12, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        ctk.CTkLabel(
            self.main_frame,
            text="IG Reels URL -> New video + New Caption",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, pady=(15, 8))
        
        # Content tabs
        self.content_tabs = ctk.CTkTabview(self.main_frame)
        self.content_tabs.grid(row=1, column=0, padx=15, pady=8, sticky="nsew")
        
        # Results tab
        self.content_tabs.add("Results")
        results_tab = self.content_tabs.tab("Results")
        
        self.results_frame = ctk.CTkScrollableFrame(results_tab)
        self.results_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Template info display
        self.template_info_frame = ctk.CTkFrame(self.results_frame)
        self.template_info_frame.pack(fill="x", pady=(5, 15))
        
        self.template_info_label = ctk.CTkLabel(
            self.template_info_frame,
            text="Batch will use template: @theanomalists",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="lightblue"
        )
        self.template_info_label.pack(pady=8)
        
        # System status display
        ctk.CTkLabel(
            self.results_frame,
            # Correctly formatted string literal
            text = "📊\n\n✅ COMPLETE BATCH SYSTEM READY!\n\n🎨 EMBEDDED TEMPLATE SYSTEM:\n• Full TemplateManager class embedded\n• Complete template editor with all features\n• Create, edit, delete, import, export templates\n• No import errors - everything self-contained\n\n📎 ASSET MANAGEMENT:\n• Logo upload with optimization\n• Profile picture upload with cropping\n\n🔧 FILE NAMING & SETTINGS:\n• Custom naming with prefix/limits\n• Complete settings persistence\n\n📊 INTERFACE FEATURES:\n• Progress tracking with dual bars\n• Real-time logging system\n• Tabbed interface with all options\n\nReady for production batch processing!",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(expand=True)
        
        # Logs tab
        self.content_tabs.add("Logs")
        logs_tab = self.content_tabs.tab("Logs")
        
        self.logs_text = ctk.CTkTextbox(
            logs_tab, 
            font=ctk.CTkFont(family="Consolas", size=9)
        )
        self.logs_text.configure(spacing3=8)  # Adds 8 pixels of space after each line
        self.logs_text.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Settings tab
        self.content_tabs.add("Settings")
        settings_tab = self.content_tabs.tab("Settings")
        
        self.create_settings_panel(settings_tab)
        
        # Initial log entries
        self.log_message("✅ COMPLETE batch mode initialized with embedded templates")
        if template_manager:
            self.log_message(f"✅ Templates available: {template_manager.get_template_names()}")
            current = template_manager.get_current_template()
            self.log_message(f"✅ Current template: {current.get('name', 'Unknown')}")
            
            # Show template stats
            stats = template_manager.get_template_stats()
            self.log_message(f"📊 Template stats: {stats['total_templates']} total templates")
        else:
            self.log_message("❌ Template system failed to initialize")
        
        self.log_message("✅ All features ready: Templates, Assets, Settings, Progress tracking")
        
    def create_settings_panel(self, parent):
        
        settings_frame = ctk.CTkScrollableFrame(parent)
        settings_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # ============================================================================
        # API KEY MANAGEMENT SECTION - ADD THIS FIRST
        # ============================================================================
        
        self.setup_api_key_ui(settings_frame) 
        
        # ============================================================================
        # EXISTING PROCESSING OPTIONS SECTION
        # ============================================================================
        
        ctk.CTkLabel(settings_frame, text="Processing Options", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(8, 10), anchor="w")
        
        # 🔽 NEW: ADD A BOOLEAN VARIABLE FOR TITLE GENERATION
        self.generate_title_var = ctk.BooleanVar(value=True)
        self.generate_title_check = ctk.CTkCheckBox(
            settings_frame,
            text="🤖 Generate AI Title for video", # Descriptive text
            variable=self.generate_title_var,
            font=ctk.CTkFont(size=10)
        )
        self.generate_title_check.pack(padx=10, pady=3, anchor="w")

        ## 🔽 NEW: Add a checkbox for the logo
        self.add_logo_var = ctk.BooleanVar(value=True)
        self.add_logo_check = ctk.CTkCheckBox(
            settings_frame, text="📎 Add Logo Watermark",
            variable=self.add_logo_var, font=ctk.CTkFont(size=10)
        )
        self.add_logo_check.pack(padx=10, pady=3, anchor="w")

        self.auto_crop_var = ctk.BooleanVar(value=True)
        self.auto_crop_check = ctk.CTkCheckBox(
            settings_frame,
            text="Auto-crop to vertical format",
            variable=self.auto_crop_var,
            font=ctk.CTkFont(size=10)
        )
        self.auto_crop_check.pack(padx=10, pady=3, anchor="w")
        
        self.add_branding_var = ctk.BooleanVar(value=True)
        self.add_branding_check = ctk.CTkCheckBox(
            settings_frame,
            text="👤 Add Profile Picture & Account Handle", # <-- RENAMED from "Add branding overlay"
            variable=self.add_branding_var,
            font=ctk.CTkFont(size=10)
        ).pack(padx=10, pady=3, anchor="w")
        
        self.continue_on_error_var = ctk.BooleanVar(value=True)
        self.continue_on_error_check = ctk.CTkCheckBox(
            settings_frame,
            text="Continue processing on error",
            variable=self.continue_on_error_var,
            font=ctk.CTkFont(size=10)
        )
        self.continue_on_error_check.pack(padx=10, pady=3, anchor="w")
        
        self.save_settings_btn = ctk.CTkButton(
            settings_frame,
            text="💾 Save Settings",
            command=self.save_batch_settings,
            height=35,
            font=ctk.CTkFont(size=11)
        )
        self.save_settings_btn.pack(pady=15)

        
    # ═══════════════════════════════════════════════════════════════════════════════
    # TEMPLATE METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    def setup_api_key_ui(self, parent):
        # API Key section in settings
        api_key_section = ctk.CTkFrame(parent) # Use the passed-in parent
        api_key_section.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(api_key_section, text="🔑 API Key Management", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))
        
        # Current API Key display
        current_key_frame = ctk.CTkFrame(api_key_section)
        current_key_frame.pack(fill="x", padx=15, pady=5)
        
        self.current_key_label = ctk.CTkLabel(current_key_frame, text="Loading API key status...", 
                                              font=ctk.CTkFont(size=11), text_color="lightgreen")
        self.current_key_label.pack(side="left", padx=10, pady=8)
        
        # API Key buttons
        key_buttons_frame = ctk.CTkFrame(api_key_section)
        key_buttons_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        ctk.CTkButton(key_buttons_frame, text="🔄 Select API Key", 
                      command=self.show_api_key_selector, height=35,
                      font=ctk.CTkFont(size=11)).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(key_buttons_frame, text="➕ Add/Manage Keys", 
                      command=self.open_api_key_manager, height=35,
                      font=ctk.CTkFont(size=11)).pack(side="left", padx=5, pady=10)
        
        ctk.CTkButton(key_buttons_frame, text="✅ Test Current Key", 
                      command=self.test_current_api_key, height=35,
                      font=ctk.CTkFont(size=11)).pack(side="left", padx=5, pady=10)
        
        # Update API key display
        self.update_api_key_display()
        
    def update_template_display(self):
        """Update template display and re-initialize AI generator."""
        if self.template_manager:
            try:
                current_template = self.template_manager.get_current_template()
                template_name = current_template.get("name", "No template")
                
                if hasattr(self, 'current_template_label'):
                    self.current_template_label.configure(text=template_name)
                if hasattr(self, 'template_info_label'):
                    self.template_info_label.configure(text=f"Batch will use template: {template_name}")
                
                # --- 👇 LOGIC FIX: Re-initialize AI generator on template change ---
                self.reinitialize_ai_generator()
                self.log_message(f"🔄 Switched to template: {template_name}")
            except Exception as e:
                self.log_message(f"❌ Template display error: {e}")

    def show_template_selector(self):
        if not template_manager:
            messagebox.showinfo("Not Available", "Template manager not available")
            return
            
        try:
            templates = template_manager.get_template_names()
            if not templates:
                messagebox.showwarning("No Templates", "No templates available")
                return
                
            current = template_manager.settings.get("last_used_template", "")
            
            # Create popup window for template selection
            selector_window = ctk.CTkToplevel(self)
            selector_window.title("Select Template")
            selector_window.geometry("400x350")
            selector_window.transient(self)
            selector_window.grab_set()
            
            # Center the window
            selector_window.update_idletasks()
            x = (selector_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (selector_window.winfo_screenheight() // 2) - (350 // 2)
            selector_window.geometry(f"400x350+{x}+{y}")
            
            # Template selection variable
            selected_template = ctk.StringVar(value=current)
            
            # Define functions first
            def apply_selection():
                chosen = selected_template.get()
                if chosen and chosen in templates:
                    if template_manager.set_current_template(chosen):
                        self.update_template_display()
                        template_name = template_manager.templates[chosen].get("name", chosen)
                        messagebox.showinfo("Success", f"Now using template: {template_name}")
                        self.log_message(f"🔄 Switched to template: {template_name}")
                        selector_window.destroy()
                    else:
                        messagebox.showerror("Error", "Failed to change template")
                else:
                    messagebox.showwarning("Invalid Selection", "Please select a valid template")
            
            def cancel_selection():
                selector_window.destroy()
            
            # ✅ CORRECT LAYOUT ORDER: PACK NON-EXPANDING ELEMENTS FIRST!
            
            # 1. TITLE (pack to top)
            ctk.CTkLabel(selector_window, text="Select AI Template", 
                         font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
            
            # 2. CURRENT TEMPLATE INFO (pack to top) 
            ctk.CTkLabel(selector_window, text=f"Current: {current}", 
                         font=ctk.CTkFont(size=12), text_color="lightgreen").pack(pady=5)
            
            # 3. ⚡ BUTTON FRAME FIRST! (pack to bottom BEFORE expanding frame)
            button_frame = ctk.CTkFrame(selector_window)
            button_frame.pack(side="bottom", fill="x", padx=20, pady=10)
            
            # 4. SCROLLABLE FRAME LAST (pack with expand - fills remaining space)
            templates_frame = ctk.CTkScrollableFrame(selector_window, height=150)
            templates_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # ✅ ADD BUTTONS TO BUTTON FRAME (now it's guaranteed to be visible!)
            ctk.CTkButton(button_frame, text="✅ Use Template", 
                          command=apply_selection, height=35,
                          font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10, pady=10)
            
            ctk.CTkButton(button_frame, text="❌ Cancel", 
                          command=cancel_selection, height=35,
                          font=ctk.CTkFont(size=12), fg_color="gray").pack(side="right", padx=10, pady=10)
            
            # CREATE TEMPLATE OPTIONS
            for template_id in templates:
                template_data = template_manager.get_template(template_id)
                template_name = template_data.get("name", template_id)
                template_desc = template_data.get("description", "")
                handle = template_data.get("account_handle", "")
                
                # Template info frame
                template_frame = ctk.CTkFrame(templates_frame)
                template_frame.pack(fill="x", pady=5)
                
                # Radio button for selection
                radio = ctk.CTkRadioButton(
                    template_frame, 
                    text="",
                    variable=selected_template, 
                    value=template_id,
                    width=20
                )
                radio.pack(side="left", padx=10, pady=10)
                
                # Template details frame
                details_frame = ctk.CTkFrame(template_frame)
                details_frame.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)
                
                # Template name (clickable)
                name_label = ctk.CTkLabel(
                    details_frame, 
                    text=template_name, 
                    font=ctk.CTkFont(size=14, weight="bold"),
                    cursor="hand2"
                )
                name_label.pack(anchor="w", padx=10, pady=(5, 0))
                
                # Make name clickable to select radio button
                name_label.bind("<Button-1>", lambda e, tid=template_id: selected_template.set(tid))
                
                # Handle and description
                if handle:
                    ctk.CTkLabel(details_frame, text=handle, 
                                 font=ctk.CTkFont(size=10), text_color="lightblue").pack(anchor="w", padx=10)
                if template_desc:
                    desc_text = template_desc[:50] + "..." if len(template_desc) > 50 else template_desc
                    ctk.CTkLabel(details_frame, text=desc_text,
                                 font=ctk.CTkFont(size=9), text_color="gray").pack(anchor="w", padx=10, pady=(0, 5))
            
        except Exception as e:
            messagebox.showerror("Error", f"Template selector error: {e}")
            self.log_message(f"❌ Template selector error: {e}")


# ✅ ADD THIS AS A SEPARATE METHOD (NOT INSIDE show_template_selector)
    def open_template_editor(self):
        """Open the COMPLETE embedded template editor."""
        if not template_manager:
            messagebox.showinfo("Not Available", "Template manager not available")
            return
            
        try:
            editor = EmbeddedTemplateEditor(self, self.template_manager, callback=self.update_template_display)
            self.log_message("✏️ Complete template editor opened")
            self.log_message("📝 Available features: Create, Edit, Delete, Import, Export")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open template editor: {e}")
            self.log_message(f"❌ Template editor error: {e}")

    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ASSET UPLOAD METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def upload_logo(self):
        """Handle logo upload with optimization."""
        file_path = filedialog.askopenfilename(
            title="Select Logo",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if file_path:
            try:
                assets_dir = Path("assets")
                assets_dir.mkdir(exist_ok=True)
                logo_dest = assets_dir / "logo.png"
                
                with Image.open(file_path) as img:
                    # Handle transparency
                    if img.mode == "RGBA":
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    elif img.mode != "RGB":
                        img = img.convert("RGB")
                    
                    # Resize if too large
                    if img.width > 500 or img.height > 500:
                        img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                    
                    img.save(logo_dest, "PNG", optimize=True)
                
                self.logo_path = str(logo_dest)
                self.logo_status.configure(text="✅ Uploaded", text_color="green")
                self.log_message(f"📎 Logo uploaded: {logo_dest}")
                self.log_message(f"📏 Logo size: {img.width}x{img.height}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload logo: {e}")
                self.log_message(f"❌ Logo upload error: {e}")
                
    def upload_profile_pic(self):
        """Handle profile picture upload with cropping."""
        file_path = filedialog.askopenfilename(
            title="Select Profile Picture",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if file_path:
            try:
                assets_dir = Path("assets")
                assets_dir.mkdir(exist_ok=True)
                profile_dest = assets_dir / "profpic.jpg"
                
                with Image.open(file_path) as img:
                    # Convert to RGB
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    

                    
                    img.save(profile_dest, "JPEG", quality=90, optimize=True)
                
                self.profile_pic_path = str(profile_dest)
                self.profile_status.configure(text="✅ Uploaded", text_color="green")
                self.log_message(f"👤 Profile pic uploaded: {profile_dest}")
                self.log_message(f"📏 Profile pic size: {img.width}x{img.height} (square)")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload profile picture: {e}")
                self.log_message(f"❌ Profile pic upload error: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SETTINGS METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def load_batch_settings(self):
        try:
            settings_path = Path("config/batch_settings.json")
            if not settings_path.exists():
                self.log_message("🔧 No saved settings file found, using defaults.")
                # Set default output path display
                self.output_dir_label.configure(text=f"Current: {self.output_directory}")
                return

            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # Load output directory
            self.output_directory = settings.get("output_directory", str(Path("output").resolve()))
            self.output_dir_label.configure(text=f"Current: {self.output_directory}")

            # Load all other settings
            self.use_daily_limit_var.set(settings.get("use_daily_limit", True))
            self.start_day_entry.delete(0, "end")
            self.start_day_entry.insert(0, settings.get("start_day", "1"))
            self.daily_video_limit_entry.delete(0, "end")
            self.daily_video_limit_entry.insert(0, settings.get("daily_video_limit", "12"))
            self.generate_title_var.set(settings.get("generate_title", True))
            self.add_branding_var.set(settings.get("add_branding", True))
            self.add_logo_var.set(settings.get("add_logo", True))
            self.auto_crop_var.set(settings.get("auto_crop", True))
            self.continue_on_error_var.set(settings.get("continue_on_error", True))
            self.toggle_daily_limit()
            self.log_message("✅ All settings loaded successfully from config/batch_settings.json")

        except Exception as e:
            self.log_message(f"⚠️ Failed to load settings: {e}")
            
    def save_batch_settings(self):
        try:
            settings = {
                "output_directory": self.output_directory,
                "use_daily_limit": self.use_daily_limit_var.get(),
                "start_day": self.start_day_entry.get().strip(),
                "daily_video_limit": self.daily_video_limit_entry.get().strip(),
                "auto_crop": self.auto_crop_var.get(),
                "generate_title": self.generate_title_var.get(), 
                "add_branding": self.add_branding_var.get(),
                "add_logo": self.add_logo_var.get(),
                "continue_on_error": self.continue_on_error_var.get(),
                "saved_date": datetime.datetime.now().isoformat()
            }
            
            # Save to config file
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            with open(config_dir / "batch_settings.json", 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            self.log_message("💾 Complete settings saved to config/batch_settings.json")
            self.log_message(f"📊 Daily Limit: {settings['use_daily_limit']}, Start Day: {settings['start_day']}, Limit: {settings['daily_video_limit']}")

            messagebox.showinfo("Settings", "Complete settings saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings: {e}")
            self.log_message(f"❌ Settings save error: {e}")
        
    def load_batch_settings(self):
        try:
            settings_path = Path("config/batch_settings.json")
            if not settings_path.exists():
                self.log_message("🔧 No saved settings file found, using defaults.")
                self.output_dir_label.configure(text=f"Current: {self.output_directory}")
                return

            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # Load output directory
            self.output_directory = settings.get("output_directory", str(Path("output").resolve()))
            self.output_dir_label.configure(text=f"Current: {self.output_directory}")

            # Load daily limit settings
            self.use_daily_limit_var.set(settings.get("use_daily_limit", True))
            self.start_day_entry.delete(0, "end")
            self.start_day_entry.insert(0, settings.get("start_day", "1"))
            self.daily_video_limit_entry.delete(0, "end")
            self.daily_video_limit_entry.insert(0, settings.get("daily_video_limit", "12"))

            # Load other settings
            self.generate_title_var.set(settings.get("generate_title", True))
            self.add_branding_var.set(settings.get("add_branding", True))
            self.add_logo_var.set(settings.get("add_logo", True))
            self.auto_crop_var.set(settings.get("auto_crop", True))
            self.continue_on_error_var.set(settings.get("continue_on_error", True))

            self.toggle_daily_limit()  # Update UI state
            self.log_message("✅ All settings loaded successfully from config/batch_settings.json")

        except Exception as e:
            self.log_message(f"⚠️ Failed to load settings: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def switch_to_single_mode(self):
        """Switch to single mode."""
        messagebox.showinfo("Mode Switch", "Single mode switching not implemented yet")
        self.log_message("🎬 Single mode switch requested")
        
    def validate_setup(self):
        """Validate setup."""
        try:
            validation_results = []
            
            if template_manager:
                validation_results.append("✅ Template system operational")
                stats = template_manager.get_template_stats()
                validation_results.append(f"✅ {stats['total_templates']} templates available")
            else:
                validation_results.append("❌ Template system not available")
            
            if config and hasattr(config, 'validate_credentials'):
                validation_results.append("✅ Config manager operational")
                self.overall_status_label.configure(text="Ready")
            else:
                validation_results.append("⚠️ Config manager limited")
                self.overall_status_label.configure(text="Limited mode")
                
            if self.ai_generator:
                validation_results.append("✅ AI generator ready")
            else:
                validation_results.append("⚠️ AI generator not available")
            
            for result in validation_results:
                self.log_message(result)
                
            self.log_message("📊 System validation complete")
            
        except Exception as e:
            self.log_message(f"Setup error: {e}")
            self.overall_status_label.configure(text="Setup error")
            
    def log_message(self, message):
        """Add message to logs with error handling."""
        if self._destroying:
            return
            
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            if hasattr(self, 'logs_text') and self.logs_text.winfo_exists():
                self.logs_text.insert("end", log_entry)
                self.logs_text.see("end")
        except (tk.TclError, AttributeError):
            pass  # Widget destroyed or not created yet
            
    def start_batch_processing(self):

        urls_text = self.urls_textbox.get("1.0", "end").strip()
        
        if not urls_text:
            messagebox.showwarning("No URLs", "Please enter Instagram URLs")
            return
        
        # Parse and validate URLs
        urls = [line.strip() for line in urls_text.split('\n') if line.strip()]
        valid_urls = [url for url in urls if 'instagram.com' in url or 'instagr.am' in url]
        
        if not valid_urls:
            messagebox.showwarning("No Valid URLs", "No valid Instagram URLs found")
            return
        
        self.stop_event = threading.Event()

        # Log batch info
        self.log_message("🚀 Starting REAL batch processing")
        self.log_message(f"📊 Processing {len(valid_urls)} URLs")
        
        if template_manager:
            current_template = template_manager.get_current_template()
            template_name = current_template.get("name", "Unknown")
            self.log_message(f"🎨 Using template: {template_name}")
        
        # Show confirmation dialog
        confirm_msg = f"Start batch processing?\n\n"
        confirm_msg += f"📋 URLs to process: {len(valid_urls)}\n"
        confirm_msg += f"📝 Template: {template_name}\n"
        confirm_msg += f"🤖 AI Title: {'✅' if self.generate_title_var.get() else '❌'}\n"
        confirm_msg += f"📎 Logo Watermark: {'✅' if self.add_logo_var.get() else '❌'}\n"
        confirm_msg += f"👤 Profile & Handle: {'✅' if self.add_branding_var.get() else '❌'}\n"
        confirm_msg += f"✂️ Auto-crop: {'✅' if self.auto_crop_var.get() else '❌'}"
        
        if not messagebox.askyesno("Confirm Batch Processing", confirm_msg):
                self.log_message("❌ Batch processing cancelled by user")
                return
        
        self.stop_event = threading.Event()

        for widget in self.results_frame.winfo_children():
            widget.destroy()
        self.log_message("📋 Previous results cleared.")
        
        self.start_loading_animation()
            
        # Disable UI during processing
        self.disable_ui_for_processing()
        
        # Start processing in separate thread
        self.processing_thread = threading.Thread(
            target=self.process_batch_worker,
            args=(valid_urls,),
            daemon=True
        )
        self.processing_thread.start()
        
        self.log_message("✅ Batch processing started in background")
    
    def add_result_card(self, result_data: dict):
        """Creates a card in the Results tab for a processed video."""
        if self.loading_animation_running:
            self.loading_animation_running = False
            if self.loading_label and self.loading_label.winfo_exists():
                self.loading_label.destroy()
            self.loading_label = None

        try:
            video_path = result_data.get('video_path')
            caption_path = result_data.get('caption_path')

            if not video_path or not os.path.exists(video_path):
                self.log_message(f"Error: Video file not found: {video_path}")
                return
                
            
            card = ctk.CTkFrame(self.results_frame, border_width=1, border_color="gray20")
            card.pack(fill="x", padx=10, pady=5)

            # --- Thumbnail (Placeholder for now) ---
            # Creating actual video thumbnails is complex, so we'll use an icon
            thumbnail_label = ctk.CTkLabel(card, text="🎬", font=ctk.CTkFont(size=40))
            thumbnail_label.pack(side="left", padx=15, pady=10)

            # --- Info Frame ---
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=10)

            filename_label = ctk.CTkLabel(info_frame, text=os.path.basename(video_path), font=ctk.CTkFont(size=12, weight="bold"))
            filename_label.pack(anchor="w")

            path_label = ctk.CTkLabel(info_frame, text=os.path.dirname(video_path), font=ctk.CTkFont(size=9), text_color="gray")
            path_label.pack(anchor="w")
            
            # --- Button Frame ---
            button_frame = ctk.CTkFrame(card, fg_color="transparent")
            button_frame.pack(side="right", padx=15, pady=10)

            def open_video():
                try:
                    os.startfile(video_path)
                except Exception as e:
                    self.log_message(f"❌ Error opening video: {e}")

            def open_caption():
                try:
                    os.startfile(caption_path)
                except Exception as e:
                    self.log_message(f"❌ Error opening caption: {e}")
            
            if video_path and os.path.exists(video_path):
                open_video_btn = ctk.CTkButton(button_frame, text='View Video', width=80, command=open_video)
                open_video_btn.pack(pady=3)

            if caption_path and os.path.exists(caption_path):
                open_caption_btn = ctk.CTkButton(button_frame, text='View Caption', width=80, command=open_caption)
                open_caption_btn.pack(pady=3)
            else:
                self.log_message(f"Warning: Caption not available for {os.path.basename(video_path)}")

        except Exception as e:
            self.log_message(f"❌ Error creating result card: {e}")

    def disable_ui_for_processing(self):
        """Disable UI elements during processing."""
        try:
            self.urls_textbox.configure(state="disabled")
            if hasattr(self, 'stop_btn'):
                self.stop_btn.configure(state="normal")
            self.overall_status_label.configure(text="Processing...")
        except:
            pass

    def enable_ui_after_processing(self):
        """Re-enable UI elements after processing."""
        try:
            self.urls_textbox.configure(state="normal")
            if hasattr(self, 'stop_btn'):
                self.stop_btn.configure(state="disabled")
            self.overall_status_label.configure(text="Ready")
            self.overall_progress_bar.set(0)
        except:
            pass

    def process_batch_worker(self, urls):
        try:
            total_urls = len(urls)
            self.log_message(f"🔄 Processing {total_urls} URLs...")
            
            for i, url in enumerate(urls):
                if self.stop_event.is_set():
                    self.log_message("🛑 Process stopped by user.")
                    break
                    
                # Update overall progress
                progress = (i + 1) / total_urls
                self.safe_after(0, lambda p=progress: self.overall_progress_bar.set(p))
                self.safe_after(0, lambda idx=i: self.overall_status_label.configure(text=f"Processing {idx+1}/{total_urls}"))
                
                self.log_message(f"🎬 Processing URL {i+1}: {url[:50]}...")
                
                try:
                    options = {
                        'output_directory': self.output_directory,
                        'auto_crop': self.auto_crop_var.get(),
                        'add_branding': self.add_branding_var.get(),
                        'add_logo': self.add_logo_var.get(),
                        'daily_limit': int(self.daily_video_limit_entry.get() or 50),
                        'output_quality': 'high'
                    }
                    
                    # STEP 1: DOWNLOAD (SAME AS MAIN_WINDOW)
                    self.safe_after(0, lambda: self.current_status_label.configure(text="Downloading video from Instagram..."))
                    self.safe_after(0, lambda: self.overall_progress_bar.set(0.2))
                    
                    downloader = InstagramDownloader()
                    metadata = downloader.download_reel(url)  # ← NEW: Returns dict

                    video_path = metadata['video_path']
                    caption = metadata['original_caption']
                    ocr_text = metadata['original_title']  # ← OCR extracted text!
                    
                    self.log_message(f"📥 Video downloaded: {video_path}")
                    self.log_message(f"📝 Original caption: {caption[:100]}...")
                    
                    # ===== ADD THIS =====
                    if ocr_text:
                        self.log_message(f"✅ OCR extracted text: {ocr_text[:100]}...")
                    else:
                        self.log_message("No text detected in video (OCR)")
# ===================

                    if self.stop_event.is_set(): break
                    
                    # STEP 2: GENERATE AI CONTENT (SAME AS MAIN_WINDOW)
                    self.safe_after(0, lambda: self.current_status_label.configure(text="Generating AI content..."))
                    self.safe_after(0, lambda: self.overall_progress_bar.set(0.5))
                    
                

                    if self.generate_title_var.get():
                        self.log_message("Generating AI title as per settings...")
                        ai_content = self.ai_generator.generate_complete_content(caption, ocr_text=ocr_text)
                        self.log_message(f"AI title generated: {ai_content.get('title', '')}")
                    else:
                        self.log_message("Skipping AI title generation (disabled in settings).")
                        # STILL generate complete content, but just don't use the title in the filename
                        ai_content = self.ai_generator.generate_complete_content(caption, ocr_text=ocr_text)
                        ai_content['title'] = ""
                    if self.stop_event.is_set(): break
                    
                    # STEP 3: PROCESS VIDEO (SAME AS MAIN_WINDOW)
                    self.safe_after(0, lambda: self.current_status_label.configure(text="Processing video with AI content..."))
                    self.safe_after(0, lambda: self.overall_progress_bar.set(0.7))
                    
                    processor = VideoProcessor()
                    if self.stop_event.is_set(): break
                    # Prepare branding assets (SAME AS MAIN_WINDOW)
                    branding_assets = {}
                    if self.logo_path and os.path.exists(self.logo_path):
                        branding_assets['logo_path'] = self.logo_path
                    if self.profile_pic_path and os.path.exists(self.profile_pic_path):
                        branding_assets['profile_pic_path'] = self.profile_pic_path
                    if self.stop_event.is_set(): break

                    if not options['output_directory'] or options['output_directory'] == 'None':
                        options['output_directory'] = str(Path("output").resolve())
                        Path(options['output_directory']).mkdir(parents=True, exist_ok=True)
                        self.log_message(f"⚠️ Using default output: {options['output_directory']}")
                    
                    # Processing options (SAME AS MAIN_WINDOW)

                    if self.stop_event.is_set(): break
                    # PROCESS VIDEO (SAME AS MAIN_WINDOW)
                    # STEP 3: PROCESS VIDEO
                    # Generate filename using daily limit system BEFORE processing
                    video_filename, caption_filename, day_num, vid_num = self.get_next_filename(self.output_directory)
                    final_output_path = os.path.join(self.output_directory, video_filename)
                    caption_output_path = os.path.join(self.output_directory, caption_filename)

                    # Log the filename being used
                    if day_num and vid_num:
                        self.log_message(f"📝 Will save as Day {day_num}, Video {vid_num}: {video_filename}")
                    else:
                        self.log_message(f"📝 Will save as: {video_filename}")

                    # Update options to include the specific output path
                    options['output_path'] = final_output_path

                    original_metadata = {
                        'original_title': ocr_text,
                        'original_caption': caption
                    }

                    final_video = processor.process_video(
                        video_path,
                        ai_content,
                        original_metadata=original_metadata,  # ← NEW PARAMETER
                        branding_assets=branding_assets,
                        options=options
                    )
                    
                    captionoutputpath = f"{os.path.splitext(final_video)[0]}_caption.txt"
                    if ai_content and 'caption' in ai_content:
                        try:
                            with open(captionoutputpath, 'w', encoding='utf-8') as f:
                                f.write(ai_content['caption'])
                            self.log_message(f"Caption saved: {os.path.basename(captionoutputpath)}")
                        except Exception as e:
                            self.log_message(f"Caption save error: {e}")
                            captionoutputpath = None
                    else:
                        captionoutputpath = None
                    
                    if self.stop_event.is_set():
                        break
                        
                    # If processor didn't use our output_path, rename the file
                    if final_video != final_output_path and os.path.exists(final_video):
                        try:
                            shutil.move(final_video, final_output_path)
                            final_video = final_output_path
                            self.log_message(f"✅ Video renamed to: {video_filename}")
                        except Exception as e:
                            self.log_message(f"⚠️ Could not rename video: {e}")

                    self.log_message(f"✅ Video processed: {final_video}")

                    # Save caption with matching filename
                    if ai_content and 'caption' in ai_content:
                        try:
                            with open(caption_output_path, 'w', encoding='utf-8') as f:
                                f.write(ai_content['caption'])
                            self.log_message(f"✅ Caption saved: {caption_filename}")
                        except Exception as e:
                            self.log_message(f"⚠️ Caption save error: {e}")

                    result_data = {
                        'video_path': final_video,
                        'caption_path': captionoutputpath,
                        'original_url': url
                    }

                    self.safe_after(0, lambda data=result_data: self.add_result_card(data))
                    if self.stop_event.is_set(): break

                    # Cleanup temp file (SAME AS MAIN_WINDOW)
                    if os.path.exists(video_path):
                        try:
                            os.remove(video_path)
                            self.log_message("🧹 Temporary files cleaned up")
                        except:
                            pass
                    if self.stop_event.is_set(): break
                    
                    # COMPLETE
                    self.safe_after(0, lambda: self.overall_progress_bar.set(1.0))
                    self.log_message(f"✅ SUCCESS: URL {i+1} processed completely!")
                    if self.stop_event.is_set(): break
                    # Small delay between URLs
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    error_msg = str(e)
                    self.log_message(f"❌ Error processing URL {i+1}: {error_msg}")
                    if not hasattr(self, 'continue_on_error_var') or not self.continue_on_error_var.get():
                        break
            
            # All URLs processed
            self.safe_after(0, self.processing_completed)
            
        except Exception as e:
            self.log_message(f"❌ Batch processing error: {e}")
            self.safe_after(0, self.processing_completed)

    def reinitialize_ai_generator(self):
        """Safely initializes or re-initializes the AI content generator."""
        try:
            self.ai_generator = AIContentGenerator(template_manager_instance=self.template_manager)
            print("✅ AI generator initialized/reloaded with current templates.")
            if hasattr(self, 'current_key_label'): # Check if UI is built
                self.update_api_key_display()
        except Exception as e:
            print(f"⚠️ AI generator init error: {e}")
            self.ai_generator = None


    def processing_completed(self):
        """Called when batch processing is completed."""
        self.log_message("🎉 Batch processing completed!")
        self.enable_ui_after_processing()
        messagebox.showinfo("Batch Complete", "Batch processing finished!\n\nCheck the logs for details.")




def main():
    """Main entry point."""
    print("🚀 Starting COMPLETE Easy Reels Batch Mode with Embedded Templates...")
    print("✅ All features included: Templates, Assets, Settings, Progress")
    print("✅ No import issues - everything embedded")
    app = BatchEasyReelsApp()
    app.mainloop()


if __name__ == "__main__":
    main()
