import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class TemplateManager:
    """Manages AI prompt templates for different accounts."""
    
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
        """Create default template structure."""
        default_templates = {
            "theanomalists": {
                "name": "@theanomalists",
                "description": "The Anomalists - History and mystery investigations",
                "account_handle": "@theanomalists",
                "created_date": datetime.now().isoformat(),
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

    # ✅ REMOVED the hardcoded 'last_used_template'
        default_settings = {
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
                
        # If file doesn't exist or is corrupt, return the basic defaults
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
    
        # 1. Try to get the last used template ID from settings.
        #    If it doesn't exist, current_id will be None.
        current_id = self.settings.get("last_used_template")

        # 2. Check if the ID is invalid (either not set or points to a deleted template).
        if not current_id or current_id not in self.templates:
            # 3. If invalid, try to find a new fallback.
            if self.templates:
                # Fallback to the very first template available in the file.
                new_default_id = list(self.templates.keys())[0]
                print(f"--> Current template '{current_id}' not found. Falling back to '{new_default_id}'.")
                # Save this new valid fallback so the app is always in a good state.
                self.set_current_template(new_default_id)
                current_id = new_default_id
            else:
                # If there are no templates at all, return an empty dictionary.
                print("--> No templates found.")
                return {}
                
        # 4. Return the valid template.
        return self.templates.get(current_id, {})
        
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
        template_data["created_date"] = datetime.now().isoformat()
        template_data["modified_date"] = datetime.now().isoformat()
        
        self.templates[template_id] = template_data
        return self.save_templates()
        
    def update_template(self, template_id: str, template_data: Dict) -> bool:
        """Update an existing template."""
        if template_id not in self.templates:
            return False
            
        # Preserve created date, update modified date
        if "created_date" in self.templates[template_id]:
            template_data["created_date"] = self.templates[template_id]["created_date"]
        template_data["modified_date"] = datetime.now().isoformat()
        
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
        source_template["created_date"] = datetime.now().isoformat()
        source_template["modified_date"] = datetime.now().isoformat()
        
        self.templates[new_id] = source_template
        return self.save_templates()
        
    def export_template(self, template_id: str, file_path: str) -> bool:
        """Export a template to file."""
        if template_id not in self.templates:
            return False
            
        try:
            export_data = {
                "template": self.templates[template_id],
                "exported_date": datetime.now().isoformat(),
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
    