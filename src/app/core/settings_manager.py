"""
Settings manager for handling application settings persistence.
"""

import json
from pathlib import Path
from typing import Optional
from ..ui.settings_dialog import Settings

class SettingsManager:
    """Manages application settings persistence."""
    
    def __init__(self, settings_path: Optional[Path] = None) -> None:
        """
        Initialize settings manager.
        
        Args:
            settings_path: Path to settings file. If None, uses default path.
        """
        if settings_path is None:
            settings_path = Path.home() / ".ssh_copilot" / "settings.json"
        
        self.settings_path = settings_path
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or create default settings
        self._settings = self._load_settings()
    
    def _load_settings(self) -> Settings:
        """
        Load settings from file or create defaults.
        
        Returns:
            Settings object with loaded or default values
        """
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r') as f:
                    data = json.load(f)
                return Settings(**data)
            except (json.JSONDecodeError, KeyError):
                # If settings file is corrupted, use defaults
                return self._get_default_settings()
        else:
            return self._get_default_settings()
    
    def _get_default_settings(self) -> Settings:
        """
        Get default settings.
        
        Returns:
            Settings object with default values
        """
        return Settings(
            ssh={
                'timeout': 30,
                'keepalive': True,
                'keepalive_interval': 60,
                'compression': True
            },
            llm={
                'model': 'llama-7b',
                'max_memory_mb': 4096,
                'max_cpu_percent': 50,
                'offline_mode': True
            },
            ui={
                'theme': 'System',
                'font_size': 10,
                'font_family': 'Consolas'
            }
        )
    
    def save_settings(self, settings: Settings) -> None:
        """
        Save settings to file.
        
        Args:
            settings: Settings object to save
        """
        # Convert settings to dictionary
        data = {
            'ssh': settings.ssh,
            'llm': settings.llm,
            'ui': settings.ui
        }
        
        # Save to file
        with open(self.settings_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_settings(self) -> Settings:
        """
        Get current settings.
        
        Returns:
            Current settings object
        """
        return self._settings
    
    def update_settings(self, settings: Settings) -> None:
        """
        Update and save new settings.
        
        Args:
            settings: New settings to apply
        """
        self._settings = settings
        self.save_settings(settings) 