#!/usr/bin/env python3
"""
Test script for the file change detection system.
"""

import os
import sys
import time
import shutil
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.drive.service_drive_client import ServiceDriveClient
from src.database.db_manager import DatabaseManager
from src.drive.change_detector import ChangeDetector


def test_change_detection():
    """Test the file change detection system."""
    logger = setup_logger('INFO')
    print("Testing file change detection system...")
    
    # Load configuration
    config_path = Path('config/config.yaml')
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        return
    
    config = Config(config_path)
    
    # Create a temporary database for testing
    temp_db_path = 'data/test_file_metadata.db'
    os.makedirs(os.path.dirname(temp_db_path), exist_ok=True)
    
    # Initialize database
    db_manager = DatabaseManager(temp_db_path)
    if not db_manager.initialize_db():
        print("Failed to initialize database")
        return
    
    print(f"Database initialized at {temp_db_path}")
    
    # Initialize Google Drive client
    drive_client = ServiceDriveClient(config)
    if not drive_client.connect():
        print("Failed to connect to Google Drive API")
        return
    
    print("Connected to Google Drive API successfully")
    
    # Initialize change detector
    change_detector = ChangeDetector(drive_client, db_manager)
    
    # First run - should detect all files as new
    print("\nFirst run - detecting initial files...")
    new_files, modified_files, deleted_files = change_detector.detect_changes()
    
    print(f"Detected {len(new_files)} new files, {len(modified_files)} modified files, "
          f"and {len(deleted_files)} deleted files")
    
    # Display some of the new files
    if new_files:
        print("\nSample of new files:")
        for i, file in enumerate(new_files[:5]):
            print(f"{i+1}. {file['name']} ({file['id']})")
        
        if len(new_files) > 5:
            print(f"... and {len(new_files) - 5} more files")
    
    # Second run - should not detect any changes
    print("\nSecond run - should not detect any changes...")
    new_files2, modified_files2, deleted_files2 = change_detector.detect_changes()
    
    print(f"Detected {len(new_files2)} new files, {len(modified_files2)} modified files, "
          f"and {len(deleted_files2)} deleted files")
    
    # Check database contents
    all_files = db_manager.get_all_files()
    print(f"\nTotal files in database: {len(all_files)}")
    
    # Get files by status
    new_status_files = db_manager.get_files_by_status('new')
    modified_status_files = db_manager.get_files_by_status('modified')
    synced_status_files = db_manager.get_files_by_status('synced')
    
    print(f"Files with 'new' status: {len(new_status_files)}")
    print(f"Files with 'modified' status: {len(modified_status_files)}")
    print(f"Files with 'synced' status: {len(synced_status_files)}")
    
    # Clean up
    db_manager.close()
    try:
        os.remove(temp_db_path)
        print(f"\nRemoved temporary database: {temp_db_path}")
    except:
        print(f"\nFailed to remove temporary database: {temp_db_path}")
    
    print("\nFile change detection test completed!")


if __name__ == "__main__":
    test_change_detection()
