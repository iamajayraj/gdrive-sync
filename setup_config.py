#!/usr/bin/env python3
"""
Script to set up configuration for Render deployment.
This script creates a config.yaml file from environment variables.
"""

import os
import json
import yaml
from pathlib import Path

def setup_config():
    """Create config.yaml file from environment variables."""
    print("Setting up configuration for Render deployment...")
    
    # Create config directory if it doesn't exist
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Create config file
    config_path = config_dir / "config.yaml"
    
    # Default configuration
    config = {
        "google_drive": {
            "service_account_file": "service_account.json",
            "folder_id": os.environ.get("GDRIVE_FOLDER_ID", ""),
            "polling_interval": int(os.environ.get("POLLING_INTERVAL", "300"))
        },
        "database": {
            "path": os.environ.get("DATABASE_PATH", "data/file_metadata.db")
        },
        "dify": {
            "api_url": os.environ.get("DIFY_API_URL", "https://api.dify.ai/v1/datasets/{dataset_id}/document/create-by-file"),
            "dataset_id": os.environ.get("DIFY_DATASET_ID", ""),
            "api_key": os.environ.get("DIFY_API_KEY", "")
        },
        "downloads": {
            "path": os.environ.get("DOWNLOADS_PATH", "data/downloads"),
            "cleanup_interval": int(os.environ.get("CLEANUP_INTERVAL", "3600")),
            "max_age_seconds": int(os.environ.get("MAX_AGE_SECONDS", "86400"))
        }
    }
    
    # Write config to file
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    print(f"Created configuration file at {config_path}")
    
    # Create service account file if provided as environment variable
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        try:
            service_account_data = json.loads(service_account_json)
            service_account_path = Path("service_account.json")
            with open(service_account_path, "w") as f:
                json.dump(service_account_data, f, indent=2)
            print(f"Created service account file at {service_account_path}")
        except json.JSONDecodeError:
            print("Error: Invalid service account JSON")
    
    # Create necessary directories
    Path("data").mkdir(exist_ok=True)
    Path("data/downloads").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    print("Configuration setup complete!")

if __name__ == "__main__":
    setup_config()
