import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from easy_reels.core.template_manager import TemplateManager

except ImportError:
    print("Template manager not found")
    template_manager = None


class TemplateEditorWindow(ctk.CTkToplevel):
    """Template editor window for managing AI prompts."""
    
    def __init__(self, parent, template_manager_instance, callback=None):
        super().__init__(parent)

        self.template_manager = template_manager_instance
        
        self.callback = callback  # Callback when template changes
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
        """Create the template editor interface."""
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left panel - Template list
        self.create_template_list()
        
        # Right panel - Template editor
        self.create_template_editor()
        
    def create_template_list(self):
        """Create template list panel."""
        
        self.list_frame = ctk.CTkFrame(self, width=250)
        self.list_frame.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        self.list_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        ctk.CTkLabel(self.list_frame, text="Templates", 
                    font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=(20, 10))
        
        # Template listbox
        self.template_listbox = tk.Listbox(
            self.list_frame,
            bg="#2b2b2b",
            fg="white",
            selectbackground="#1f538d",
            font=("Arial", 11),
            height=15
        )
        self.template_listbox.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
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
        if not self.template_manager:
            return
            
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
        """Handle template selection."""
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
        if not self.template_manager:
            messagebox.showerror("Error", "Template manager not available")
            return
            
        # Get new template name
        name = tk.simpledialog.askstring("New Template", "Enter template name:")
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
        if not self.current_template_id or not self.template_manager:
            messagebox.showwarning("No Selection", "Please select a template to duplicate")
            return
            
        # Get new name
        original_name = self.template_manager.templates[self.current_template_id].get("name", self.current_template_id)
        new_name = tk.simpledialog.askstring("Duplicate Template", f"Enter name for copy of '{original_name}':")
        if not new_name:
            return
            
        new_id = new_name.lower().replace(" ", "_").replace("@", "")
        
        if self.template_manager.duplicate_template(self.current_template_id, new_id, new_name):
            self.load_templates()
            messagebox.showinfo("Success", f"Template duplicated as '{new_name}'")
        else:
            messagebox.showerror("Error", "Failed to duplicate template")
            
    def delete_template(self):
        """Delete the selected template."""
        if not self.current_template_id or not self.template_manager:
            messagebox.showwarning("No Selection", "Please select a template to delete")
            return
            
        template_name = self.template_manager.templates[self.current_template_id].get("name", self.current_template_id)
        
        if messagebox.askyesno("Confirm Delete", f"Delete template '{template_name}'?\\n\\nThis cannot be undone."):
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
        if not self.current_template_id or not self.template_manager:
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
        if not self.current_template_id or not self.template_manager:
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


def open_template_editor(parent, callback=None):
    """Open the template editor window."""
    editor = TemplateEditorWindow(parent, callback)
    return editor