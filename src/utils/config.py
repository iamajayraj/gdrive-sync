"""
Configuration management for the Google Drive Sync application.
"""

import os
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for the application."""
    
    def __init__(self, config_path):
        """
        Initialize the configuration manager.
        
        Args:
            config_path (Path or str): Path to the configuration file.
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self):
        """
        Load configuration from the YAML file.
        
        Returns:
            dict: Configuration dictionary.
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.debug(f"Configuration loaded from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def get(self, key, default=None):
        """
        Get a configuration value.
        
        Args:
            key (str): Configuration key.
            default: Default value to return if key is not found.
            
        Returns:
            The configuration value or default if not found.
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            logger.warning(f"Configuration key not found: {key}, using default: {default}")
            return default
    
    def set(self, key, value):
        """
        Set a configuration value.
        
        Args:
            key (str): Configuration key.
            value: Value to set.
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the nested dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def save(self):
        """Save the configuration to the YAML file."""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
                logger.debug(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
