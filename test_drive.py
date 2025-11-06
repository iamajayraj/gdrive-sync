#!/usr/bin/env python3
"""
Test script for Google Drive functionality.
Counts files in each folder and subfolder.
"""

import os
import sys
import tempfile
from pathlib import Path
from collections import defaultdict

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.drive.service_drive_client import ServiceDriveClient


def count_files_in_folders(drive_client, root_folder_id):
    """
    Count files in each folder and subfolder.
    
    Args:
        drive_client: The Google Drive client
        root_folder_id: The ID of the root folder
        
    Returns:
        dict: A dictionary with folder IDs as keys and file counts as values
        dict: A dictionary with folder IDs as keys and folder names as values
    """
    # Initialize dictionaries to store counts and folder names
    file_counts = defaultdict(int)
    folder_names = {}
    folder_paths = {}
    
    # Queue for BFS traversal
    queue = [(root_folder_id, "Root", "/")]
    processed = set()
    
    while queue:
        current_id, current_name, current_path = queue.pop(0)
        
        if current_id in processed:
            continue
            
        processed.add(current_id)
        folder_names[current_id] = current_name
        folder_paths[current_id] = current_path
        
        # Get files in the current folder
        files, _ = drive_client.list_files(current_id)
        
        # Count files and add subfolders to the queue
        file_count = 0
        for file in files:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                # It's a folder, add to queue
                subfolder_path = f"{current_path}{file['name']}/"
                queue.append((file['id'], file['name'], subfolder_path))
            else:
                # It's a file, count it
                file_count += 1
        
        file_counts[current_id] = file_count
    
    return file_counts, folder_names, folder_paths


def test_drive():
    """Test Google Drive functionality and count files in folders."""
    logger = setup_logger('INFO')
    print("Testing Google Drive functionality...")
    
    # Load configuration
    config_path = Path('config/config.yaml')
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        return
    
    config = Config(config_path)
    
    # Create a drive client
    drive_client = ServiceDriveClient(config)
    
    # Test connection
    print("Connecting to Google Drive...")
    if not drive_client.connect():
        print("Failed to connect to Google Drive API.")
        return
    
    print("Connection successful!")
    
    # Get the root folder ID
    root_folder_id = config.get('google_drive.folder_id')
    print(f"\nCounting files in folder: {root_folder_id} and all subfolders...")
    
    # Count files in all folders
    file_counts, folder_names, folder_paths = count_files_in_folders(drive_client, root_folder_id)
    
    if not file_counts:
        print("No folders found.")
        return
    
    # Sort folders by path for a hierarchical display
    sorted_folders = sorted(folder_paths.items(), key=lambda x: x[1])
    
    # Display file counts for each folder
    print("\nFile counts by folder:")
    print("-" * 80)
    print(f"{'Folder Path':<50} {'Files':>10}")
    print("-" * 80)
    
    total_files = 0
    total_folders = len(file_counts)
    
    for folder_id, path in sorted_folders:
        folder_name = folder_names[folder_id]
        file_count = file_counts[folder_id]
        total_files += file_count
        
        # Format the display path
        display_path = path
        if display_path == "/":
            display_path = "/ (Root)"
            
        print(f"{display_path:<50} {file_count:>10}")
    
    print("-" * 80)
    print(f"{'Total':<50} {total_files:>10}")
    print(f"Total folders: {total_folders}")
    
    # Test downloading a sample file
    files, _ = drive_client.list_files(root_folder_id)
    non_folder_files = [f for f in files if f['mimeType'] != 'application/vnd.google-apps.folder']
    
    if non_folder_files:
        print("\nTesting file download...")
        file_to_download = non_folder_files[0]
        print(f"Downloading file: {file_to_download['name']}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / file_to_download['name']
            
            if drive_client.download_file(file_to_download['id'], output_path):
                print(f"File downloaded successfully to {output_path}")
                print(f"File size: {output_path.stat().st_size} bytes")
            else:
                print("Failed to download file.")
    
    print("\nGoogle Drive functionality test completed successfully!")


if __name__ == "__main__":
    test_drive()
