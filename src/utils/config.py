"""
Configuration management for the Google Drive Sync application.
"""

import os
import yaml
import json
import tempfile
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
        
        Checks environment variables first, then the config file.
        Environment variables should be in the format GDRIVE_SYNC_SECTION_KEY.
        For example, GDRIVE_SYNC_GOOGLE_DRIVE_POLLING_INTERVAL for google_drive.polling_interval.
        
        Args:
            key (str): Configuration key.
            default: Default value to return if key is not found.
            
        Returns:
            The configuration value or default if not found.
        """
        # Check environment variables first
        env_key = f"GDRIVE_SYNC_{key.upper().replace('.', '_')}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            logger.debug(f"Using environment variable {env_key} for {key}")
            # Try to convert to appropriate type based on default value
            if default is not None:
                if isinstance(default, int):
                    try:
                        return int(env_value)
                    except ValueError:
                        pass
                elif isinstance(default, float):
                    try:
                        return float(env_value)
                    except ValueError:
                        pass
                elif isinstance(default, bool):
                    return env_value.lower() in ('true', 'yes', '1', 'y')
            return env_value
            
        # Fall back to config file
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
            
    def get_service_account_path(self):
        """
        Get the path to the service account key file.
        
        If the service account JSON is provided as an environment variable,
        it will be written to a temporary file and the path to that file will be returned.
        
        Returns:
            Path: Path to the service account key file.
        """
        # Check if service account JSON is provided as an environment variable
        env_key = "GDRIVE_SYNC_GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE"
        service_account_json = os.environ.get(env_key)
        
        if service_account_json:
            try:
                # Parse the JSON to validate it
                json_data = json.loads(service_account_json)
                
                # Create a temporary file for the service account key
                fd, temp_path = tempfile.mkstemp(suffix='.json')
                with os.fdopen(fd, 'w') as temp_file:
                    json.dump(json_data, temp_file)
                
                logger.info(f"Created temporary service account key file at {temp_path}")
                return Path(temp_path)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid service account JSON in environment variable: {e}")
        
        # Fall back to the path in the config file
        service_account_path = self.get('google_drive.service_account_file')
        if service_account_path:
            return Path(service_account_path)
        
        logger.error("No service account key file found in environment or config")
        return None
