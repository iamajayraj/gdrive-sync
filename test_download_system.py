#!/usr/bin/env python3
"""
Test script for the file download system.
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
from src.utils.file_processor import FileProcessor
from src.drive.service_drive_client import ServiceDriveClient
from src.drive.download_manager import DownloadManager


def test_download_system():
    """Test the file download system."""
    logger = setup_logger('INFO')
    print("Testing file download system...")
    
    # Load configuration
    config_path = Path('config/config.yaml')
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        return
    
    config = Config(config_path)
    
    # Create a temporary download directory
    temp_download_dir = Path('data/test_downloads')
    temp_download_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created temporary download directory: {temp_download_dir}")
    
    try:
        # Initialize Google Drive client
        drive_client = ServiceDriveClient(config)
        if not drive_client.connect():
            print("Failed to connect to Google Drive API")
            return
        
        print("Connected to Google Drive API successfully")
        
        # Initialize file processor
        file_processor = FileProcessor()
        print("File processor initialized")
        
        # Initialize download manager
        download_manager = DownloadManager(drive_client, temp_download_dir)
        print(f"Download manager initialized with directory: {temp_download_dir}")
        
        # Get files from Google Drive
        folder_id = config.get('google_drive.folder_id')
        print(f"Listing files in folder: {folder_id}")
        
        # First, list all files to find a subfolder with regular files
        files, _ = drive_client.list_files(folder_id)
        
        # Find a subfolder
        subfolders = [f for f in files if f['mimeType'] == 'application/vnd.google-apps.folder']
        
        if subfolders:
            # Use the first subfolder
            subfolder = subfolders[0]
            print(f"Using subfolder: {subfolder['name']} ({subfolder['id']})")
            
            # List files in the subfolder
            files, _ = drive_client.list_files(subfolder['id'])
        
        if not files:
            print("No files found in the folder")
            return
        
        print(f"Found {len(files)} files in the root folder")
        
        # Filter out folders and get only regular files
        regular_files = [f for f in files if f['mimeType'] != 'application/vnd.google-apps.folder']
        
        if not regular_files:
            print("No regular files found in the folder")
            return
        
        # Download up to 3 files for testing
        test_files = regular_files[:3]
        print(f"\nDownloading {len(test_files)} files for testing:")
        
        for i, file in enumerate(test_files):
            print(f"\n{i+1}. Downloading: {file['name']} ({file['id']})")
            
            # Download the file
            download_path = download_manager.download_file(file)
            
            if download_path:
                # Process the file
                file_info = file_processor.get_file_info(download_path)
                print(f"   Downloaded to: {download_path}")
                print(f"   File size: {file_info['size']} bytes")
                print(f"   MIME type: {file_info['mime_type']}")
                print(f"   Is text file: {file_info['is_text']}")
                
                # Validate the file
                is_valid, error = file_processor.validate_file(download_path)
                if is_valid:
                    print(f"   File validation: PASSED")
                else:
                    print(f"   File validation: FAILED - {error}")
            else:
                print(f"   Failed to download file")
        
        # Test getting a downloaded file
        if test_files:
            file_id = test_files[0]['id']
            print(f"\nGetting previously downloaded file: {file_id}")
            file_path = download_manager.get_downloaded_file(file_id)
            
            if file_path:
                print(f"Found at: {file_path}")
            else:
                print("File not found in download cache")
        
        # Test cleanup
        print("\nTesting cleanup of downloaded files...")
        deleted_count = download_manager.cleanup_old_files(0)  # Clean up all files
        print(f"Cleaned up {deleted_count} files")
        
        print("\nFile download system test completed successfully!")
        
    finally:
        # Clean up the temporary directory
        if temp_download_dir.exists():
            try:
                shutil.rmtree(temp_download_dir)
                print(f"\nRemoved temporary download directory: {temp_download_dir}")
            except Exception as e:
                print(f"Error removing temporary directory: {e}")


if __name__ == "__main__":
    test_download_system()
