from groq import Groq
from typing import Dict, Optional, List
import sys
import json
import os
import base64
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from easy_reels.core.config_manager import config
    from easy_reels.core.template_manager import TemplateManager
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback imports
    import config
    try:
        from easy_reels.core.template_manager import TemplateManager
    except ImportError:
        print("Template manager not found, using legacy mode")
        template_manager = None

template_manager = None

# ============================================================================
# API KEY MANAGER - MERGED INTO AI CONTENT GENERATOR
# ============================================================================

class ApiKeyManager:
    """Manages multiple API keys with names and descriptions."""
    
    def __init__(self):
        self.keys_dir = Path("config/api_keys")
        self.keys_file = self.keys_dir / "api_keys.json"
        self.settings_file = self.keys_dir / "key_settings.json"
        
        # Ensure directories exist
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        self.api_keys = self.load_keys()
        self.settings = self.load_settings()
    
    def load_keys(self) -> Dict:
        """Load API keys from file or create defaults."""
        if self.keys_file.exists():
            try:
                with open(self.keys_file, 'r', encoding='utf-8') as f:
                    encrypted_keys = json.load(f)
                    # Decrypt keys
                    return {k: self._decrypt_key(v) for k, v in encrypted_keys.items()}
            except Exception as e:
                print(f"Error loading API keys: {e}")
                return {}
        else:
            # Create default from .env if available
            default_keys = {}
            env_key = os.getenv('GROQ_API_KEY')
            if env_key:
                default_keys["default"] = {
                    "name": "Default (.env)",
                    "key": env_key,
                    "description": "API key from environment file",
                    "created_date": "2024-01-01"
                }
                self.save_keys(default_keys)
            return default_keys
    
    def load_settings(self) -> Dict:
        """Load API key settings."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading API key settings: {e}")
                return {}
        
        # Default settings
        default_settings = {
            "last_used_key": "default" if "default" in self.api_keys else None,
            "auto_validate": True
        }
        self.save_settings(default_settings)
        return default_settings
    
    def _encrypt_key(self, key_data: Dict) -> Dict:
        """Simple encryption for API keys (base64)."""
        encrypted = key_data.copy()
        if 'key' in encrypted:
            encrypted['key'] = base64.b64encode(encrypted['key'].encode()).decode()
        return encrypted
    
    def _decrypt_key(self, key_data: Dict) -> Dict:
        """Simple decryption for API keys."""
        decrypted = key_data.copy()
        if 'key' in decrypted:
            try:
                decrypted['key'] = base64.b64decode(decrypted['key'].encode()).decode()
            except:
                pass  # If decryption fails, assume it's not encrypted
        return decrypted
    
    def save_keys(self, keys: Dict = None) -> bool:
        """Save API keys to file with encryption."""
        if keys is None:
            keys = self.api_keys
            
        try:
            # Encrypt keys before saving
            encrypted_keys = {k: self._encrypt_key(v) for k, v in keys.items()}
            
            with open(self.keys_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_keys, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving API keys: {e}")
            return False
    
    def save_settings(self, settings: Dict = None) -> bool:
        """Save settings to file."""
        if settings is None:
            settings = self.settings
            
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving API key settings: {e}")
            return False
    
    def add_key(self, key_id: str, name: str, api_key: str, description: str = "") -> bool:
        """Add new API key."""
        import datetime
        
        self.api_keys[key_id] = {
            "name": name,
            "key": api_key,
            "description": description,
            "created_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        return self.save_keys()
    
    def update_key(self, key_id: str, name: str = None, api_key: str = None, description: str = None) -> bool:
        """Update existing API key."""
        if key_id not in self.api_keys:
            return False
        
        if name is not None:
            self.api_keys[key_id]["name"] = name
        if api_key is not None:
            self.api_keys[key_id]["key"] = api_key
        if description is not None:
            self.api_keys[key_id]["description"] = description
            
        return self.save_keys()
    
    def delete_key(self, key_id: str) -> bool:
        """Delete API key."""
        if key_id in self.api_keys:
            del self.api_keys[key_id]
            
            # Update settings if this was the current key
            if self.settings.get("last_used_key") == key_id:
                remaining_keys = list(self.api_keys.keys())
                self.settings["last_used_key"] = remaining_keys[0] if remaining_keys else None
                self.save_settings()
            
            return self.save_keys()
        return False
    
    def get_key(self, key_id: str) -> Optional[Dict]:
        """Get specific API key."""
        return self.api_keys.get(key_id)
    
    def get_key_names(self) -> List[str]:
        """Get list of all API key IDs."""
        return list(self.api_keys.keys())
    
    def get_current_key(self) -> Optional[str]:
        """Get currently selected API key."""
        current_id = self.settings.get("last_used_key")
        if current_id and current_id in self.api_keys:
            return self.api_keys[current_id]["key"]
        return None
    
    def get_current_key_info(self) -> Optional[Dict]:
        """Get info about currently selected API key."""
        current_id = self.settings.get("last_used_key")
        if current_id and current_id in self.api_keys:
            return {
                "id": current_id,
                **self.api_keys[current_id]
            }
        return None
    
    def set_current_key(self, key_id: str) -> bool:
        """Set current API key."""
        if key_id in self.api_keys:
            self.settings["last_used_key"] = key_id
            return self.save_settings()
        return False
    
    def validate_key(self, api_key: str) -> bool:
        """Validate API key by making a test request."""
        try:
            client = Groq(api_key=api_key)
            
            # Simple test request
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "Hi"}],
                model="llama-3.1-8b-instant",
                max_tokens=10
            )
            return True
        except Exception as e:
            print(f"API key validation failed: {e}")
            return False


class AIContentGenerator:
    """Generates AI content using customizable templates."""
    
    def __init__(self, template_manager_instance: TemplateManager):
        self.client = None
        self.api_key_manager = ApiKeyManager()
        self.template_manager = template_manager_instance
        self.configure_groq()
        
    
    def configure_groq(self, api_key: str = None):
        """Configure Groq API client with API key manager support."""
        try:
            # Priority order:
            # 1. Passed api_key parameter
            # 2. API key manager current key
            # 3. Config file
            # 4. Environment variable
            
            if api_key:
                selected_key = api_key
                source = "parameter"
            elif self.api_key_manager:
                selected_key = self.api_key_manager.get_current_key()
                source = "API Key Manager"
            else:
                # Fallback to old method
                selected_key = getattr(config, 'GROQ_API_KEY', None)
                source = "config"
                if not selected_key:
                    selected_key = os.getenv('GROQ_API_KEY')
                    source = "environment"
            
            if selected_key:
                self.client = Groq(api_key=selected_key)
                print(f"✅ Groq API client configured from {source}")
                
                # Log current API key info if using manager
                if self.api_key_manager and not api_key:
                    key_info = self.api_key_manager.get_current_key_info()
                    if key_info:
                        print(f"🔑 Using API key: {key_info['name']}")
            else:
                print("❌ No GROQ API key found")
                
        except Exception as e:
            print(f"❌ Error configuring Groq API: {e}")
    
    def add_api_key(self, key_id: str, name: str, api_key: str, description: str = "") -> bool:
        """Add new API key."""
        return self.api_key_manager.add_key(key_id, name, api_key, description)
    
    def get_api_keys(self) -> List[str]:
        """Get list of all API key IDs."""
        return self.api_key_manager.get_key_names()
    
    def get_api_key(self, key_id: str) -> Optional[Dict]:
        """Get specific API key."""
        return self.api_key_manager.get_key(key_id)
    
    def set_current_api_key(self, key_id: str) -> bool:
        """Set current API key and reconfigure."""
        if self.api_key_manager.set_current_key(key_id):
            key_data = self.api_key_manager.get_key(key_id)
            if key_data:
                self.configure_groq(key_data["key"])
                return True
        return False
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key."""
        return self.api_key_manager.validate_key(api_key)
    
    def get_current_api_key_info(self) -> Optional[Dict]:
        """Get current API key info."""
        return self.api_key_manager.get_current_key_info()
    
    def get_api_key_status(self) -> Dict:
        """Get current API key status and information."""
        if self.api_key_manager:
            key_info = self.api_key_manager.get_current_key_info()
            if key_info:
                return {
                    "status": "configured",
                    "key_name": key_info["name"],
                    "key_id": key_info["id"],
                    "created_date": key_info.get("created_date", "Unknown"),
                    "has_client": bool(self.client),
                    "total_keys": len(self.api_key_manager.get_key_names())
                }
            else:
                return {
                    "status": "no_key",
                    "message": "No API key selected",
                    "has_client": False,
                    "total_keys": len(self.api_key_manager.get_key_names())
                }
        else:
            return {
                "status": "legacy",
                "message": "Using legacy .env configuration",
                "has_client": bool(self.client)
            }

            
    def _get_groq_completion(self, prompt: str) -> str:
        if not self.client:
            return "Groq client not configured."
        
        try:
            print(f"🔍 Sending prompt to API: '{prompt[:100]}...'")
            
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",  # Changed from "openai/gpt-oss-20b"
                temperature=0.7,
                max_tokens=1000
            )
            
            print(f"🔍 Full API response structure exists: {bool(chat_completion.choices)}")
            
            # Check if choices exist
            if not chat_completion.choices:
                print("⚠️ WARNING: API returned no choices")
                return "API returned no choices - using original caption"
            
            # Check if message exists
            message = chat_completion.choices[0].message
            if not message:
                print("⚠️ WARNING: API returned no message")
                return "API returned no message - using original caption"
            
            # Check content
            content = message.content
            print(f"🔍 Raw API response: '{content}'")
            print(f"🔍 Response type: {type(content)}")
            print(f"🔍 Response length: {len(content) if content else 'None'}")
            
            if content is None:
                print("⚠️ WARNING: API returned None content")
                return "API returned None content - check your API key and model"
            elif content == "":
                print("⚠️ WARNING: API returned empty string")
                return "API returned empty content - try a different prompt"
            else:
                stripped_content = content.strip()
                print(f"🔍 Stripped content: '{stripped_content}'")
                print(f"🔍 Stripped length: {len(stripped_content)}")
                
                if stripped_content:
                    return stripped_content
                else:
                    print("⚠️ WARNING: API returned only whitespace")
                    return "API returned whitespace only - try a different prompt"
                    
        except Exception as e:
            print(f"❌ Groq API error: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            return f"API Error: {e} - check your API key"
            
    def get_current_template(self) -> Dict:
        """Get the current template or fallback to default."""
        if self.template_manager:
            return self.template_manager.get_current_template()
        else:
            # Legacy fallback
            return self._get_legacy_template()
            
    def _get_legacy_template(self) -> Dict:
        """Fallback template if template manager not available."""
        return {
            "name": "@theanomalists (Legacy)",
            "account_handle": "@theanomalists",
            "title_prompt": """You are a young and wild headline editor for a viral news publication, specializing in crafting short, relateable, and irresistible titles.

# Video's Original Caption:
{original_caption}

# Write a single, clickbait video title.
# - Word Count: Maximum 12 words.
# - No punctuation marks.
# - Light, funny, and relateable tone.""",
            
            "caption_prompt": """You are a captivating storyteller. Write a short Instagram caption.

# Video's Original Caption:  
{original_caption}

# Include: Hook, Story, Question, Follow @theanomalists, 10 hashtags.
# Keep it engaging and relatable."""
        }
        
    def generate_title(self, original_caption: str, ocr_text: str = "", template_id: str = None) -> str:
        try:
            if not original_caption or not original_caption.strip():
                original_caption = "No caption provided."
            if not ocr_text or not ocr_text.strip():
                ocr_text = "No text detected in video"
            
            template = self.template_manager.get_template(template_id) if template_id and self.template_manager else self.get_current_template()
            
            if not template or 'title_prompt' not in template:
                print("❌ Template error: template not found or missing title_prompt")
                return "Template Error"
            
            # Try with both variables
            try:
                prompt = template['title_prompt'].format(
                    original_caption=original_caption,
                    ocr_text=ocr_text
                )
            except KeyError:
                prompt = template['title_prompt'].format(original_caption=original_caption)
            
            print(f"🔍 Sending title prompt to API...")
            title = self._get_groq_completion(prompt)
            print(f"🔍 Received title: '{title}'")
            
            return title.split('\n')[0].strip()
            
        except Exception as e:
            print(f"❌ Title generation error: {e}")
            import traceback
            print(traceback.format_exc())
            return f"Generation Failed: {str(e)}"

    def generate_caption(self, original_caption: str, ocr_text: str = "", generated_title: str = "", template_id: str = None) -> str:
        """Generate caption using original caption, OCR text, and the newly generated title."""
        if not original_caption or not original_caption.strip():
            original_caption = "No caption provided."
        
        if not ocr_text or not ocr_text.strip():
            ocr_text = "No text detected in video"

        # <--- NEW: Add a fallback for the generated title --->
        if not generated_title or not generated_title.strip():
            generated_title = "No title generated"
                
        template = self.template_manager.get_template(template_id) if template_id and self.template_manager else self.get_current_template()
                
        if not template or 'caption_prompt' not in template:
            return "Template not found or invalid"
                
        # <--- MODIFICATION IS HERE --->
        # Use a flexible formatting approach to handle templates that may or may not
        # have the new {generated_title} placeholder.
        try:
            prompt = template['caption_prompt']
            
            # Replace all available placeholders
            prompt = prompt.replace('{original_caption}', original_caption)
            prompt = prompt.replace('{ocr_text}', ocr_text)
            prompt = prompt.replace('{generated_title}', generated_title)

        except Exception as e:
            print(f"Error formatting prompt: {e}")
            # Fallback to a simpler format if complex replacement fails
            prompt = template['caption_prompt'].format(original_caption=original_caption)

        try:
            return self._get_groq_completion(prompt)
        except Exception as e:
            print(f"❌ Caption generation error: {e}")
            return f"AI Caption Generation Failed. Original Caption:\n\n{original_caption}"

    def generate_complete_content(self, original_caption: str, ocr_text: str = "", template_id: str = None) -> Dict:
        current_template = template_id or (self.template_manager.settings.get("last_used_template") if self.template_manager else None)
        print(f"🎨 Generating content with template: {current_template or 'default'}")
        
        # Generate title with validation
        title = self.generate_title(original_caption, ocr_text, template_id)
        print(f"🔍 Raw title generated: '{title}'")
        print(f"🔍 Title length: {len(title)}")
        print(f"🔍 Title is empty: {not title}")
        print(f"🔍 Original caption: '{original_caption[:100]}'")
        print(f"🔍 OCR text: '{ocr_text[:100] if ocr_text else 'None'}'")
        
        # Validate title - reject error messages
        error_messages = [
            'AI Title Generation Failed',
            'Template not found or invalid',
            'Groq client not configured',
            'API Error',
            'Generation Failed',  # Add this
            'generated_title',
            ''
        ]
        
        # Check each error message individually
        triggered_errors = [err for err in error_messages if err and err in title]
        if triggered_errors:
            print(f"⚠️ Title contained error keywords: {triggered_errors}")
        
        if not title or not title.strip() or any(err in title for err in error_messages if err):
            print('⚠️ Title generation failed, extracting fallback from caption')
            # Extract first sentence from original caption as fallback
            if original_caption and original_caption.strip():
                fallback = original_caption.split('.')[0][:80]
                if fallback.strip():
                    title = fallback.strip()
                else:
                    title = "Untold Story"
            else:
                title = "Untold Story"  # Changed from "Viral Story"
            print(f"📝 Using fallback title: '{title}'")
        
        # Pass validated title to caption generator
        caption = self.generate_caption(original_caption, ocr_text, generated_title=title, template_id=template_id)
        
        return {
            'title': title,
            'caption': caption,
            'template_used': current_template,
            'original_caption': original_caption,
            'ocr_text': ocr_text
        }
                
    def preview_template(self, template_id: str, sample_caption: str) -> Dict:
        """Preview what content would look like with a specific template."""
        if not self.template_manager:
            return {"error": "Template manager not available"}
            
        template = self.template_manager.get_template(template_id) if template_id and self.template_manager else self.get_current_template()

        # ADD THIS:
        print(f"🔍 Template title_prompt preview: '{template.get('title_prompt', 'MISSING')[:200]}'")
        if not template:
            return {"error": "Template not found"}
            
        return {
            "template_name": template.get("name", template_id),
            "preview_title": self.generate_title(sample_caption, template_id),
            "preview_caption": self.generate_caption(sample_caption, template_id)[:200] + "...",
            "template_id": template_id
        }
        
    def get_available_templates(self) -> List[Dict]:
        """Get list of available templates with metadata."""
        if not self.template_manager:
            return [{"id": "legacy", "name": "@theanomalists (Legacy)", "description": "Default template"}]
            
        templates = []
        for template_id, template_data in self.template_manager.templates.items():
            templates.append({
                "id": template_id,
                "name": template_data.get("name", template_id),
                "description": template_data.get("description", "No description"),
                "account_handle": template_data.get("account_handle", ""),
                "is_current": template_id == self.template_manager.settings.get("last_used_template")
            })
            
        return templates
