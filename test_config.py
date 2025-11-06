#!/usr/bin/env python3
"""
Test script for the configuration management.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.config import Config
from src.utils.logger import setup_logger


def test_config():
    """Test the configuration loading."""
    # Setup logging
    logger = setup_logger('DEBUG')
    
    # Check if config.yaml exists
    config_path = Path('config/config.yaml')
    if not config_path.exists():
        # Create a test config file from the example
        example_path = Path('config/config.yaml.example')
        if example_path.exists():
            print(f"Creating test config from example: {example_path}")
            with open(example_path, 'r') as f:
                example_content = f.read()
            
            # Create a test config with placeholder values
            with open(config_path, 'w') as f:
                f.write(example_content)
            
            print(f"Test config created at: {config_path}")
        else:
            print(f"Example config not found: {example_path}")
            return
    
    try:
        # Load the configuration
        config = Config(config_path)
        print(f"Configuration loaded successfully from: {config_path}")
        
        # Test getting configuration values
        folder_id = config.get('google_drive.folder_id')
        print(f"Google Drive folder ID: {folder_id}")
        
        dataset_id = config.get('dify.dataset_id')
        print(f"Dify dataset ID: {dataset_id}")
        
        # Test getting a value with a default
        max_file_size = config.get('app.max_file_size', 10485760)
        print(f"Max file size: {max_file_size} bytes")
        
        # Test getting a non-existent value
        non_existent = config.get('non.existent.key', 'default_value')
        print(f"Non-existent key: {non_existent}")
        
        print("Configuration test completed successfully!")
        
    except Exception as e:
        print(f"Error testing configuration: {e}")


if __name__ == "__main__":
    test_config()
