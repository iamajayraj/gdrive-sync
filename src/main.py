#!/usr/bin/env python3
"""Google Drive Sync and Dify API Integration

This application monitors a Google Drive folder (and its subfolders) for new or
modified files and pushes them to the Dify API.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.drive.service_drive_client import ServiceDriveClient


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Google Drive Sync and Dify API Integration'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to the configuration file'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set the logging level'
    )
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logger(args.log_level)
    
    try:
        # Load configuration
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        
        config = Config(config_path)
        logger.info(f"Configuration loaded from {config_path}")
        
        # Initialize Google Drive client
        drive_client = ServiceDriveClient(config)
        if not drive_client.connect():
            logger.error("Failed to connect to Google Drive API")
            sys.exit(1)
        
        logger.info("Connected to Google Drive API successfully")
        
        # TODO: Implement the file change detection and Dify API integration
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.exception(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
