#!/usr/bin/env python3
"""
Test script for the logging configuration.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.logger import setup_logger


def test_logger():
    """Test the logger setup."""
    try:
        # Test with default settings
        logger = setup_logger()
        print("Logger initialized with default settings")
        
        # Log messages at different levels
        logger.debug("This is a DEBUG message")
        logger.info("This is an INFO message")
        logger.warning("This is a WARNING message")
        logger.error("This is an ERROR message")
        logger.critical("This is a CRITICAL message")
        
        # Test with custom log level
        debug_logger = setup_logger('DEBUG')
        print("Logger initialized with DEBUG level")
        
        # Log messages at different levels
        debug_logger.debug("This is a DEBUG message (should be visible)")
        debug_logger.info("This is an INFO message")
        
        # Check if log file was created
        log_dir = Path(__file__).resolve().parent / 'logs'
        log_file = log_dir / 'gdrive_sync.log'
        
        if log_file.exists():
            print(f"Log file created at: {log_file}")
            print(f"Log file size: {log_file.stat().st_size} bytes")
        else:
            print(f"Log file not found at: {log_file}")
        
        print("Logger test completed successfully!")
        
    except Exception as e:
        print(f"Error testing logger: {e}")


if __name__ == "__main__":
    test_logger()
