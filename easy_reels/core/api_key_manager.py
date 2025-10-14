"""
API Key Manager - Similar to TemplateManager but for API keys
Stores and manages multiple Groq API keys securely
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import base64

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
            from groq import Groq
            client = Groq(api_key=api_key)
            
            # Simple test request
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "Hi"}],
                model="openai/gpt-oss-120b",
                max_tokens=10
            )
            return True
        except Exception as e:
            print(f"API key validation failed: {e}")
            return False

# Global instance
api_key_manager = ApiKeyManager()
