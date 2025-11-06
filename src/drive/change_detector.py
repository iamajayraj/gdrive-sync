"""
File change detector for Google Drive.

This module detects new and modified files in Google Drive.
"""

import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ChangeDetector:
    """Detects changes in Google Drive files."""
    
    def __init__(self, drive_client, db_manager):
        """
        Initialize the change detector.
        
        Args:
            drive_client: The Google Drive client.
            db_manager: The database manager.
        """
        self.drive_client = drive_client
        self.db_manager = db_manager
        
    def build_file_path(self, file_id, parent_id=None, file_name=None):
        """
        Build the file path for a file.
        
        Args:
            file_id (str): The ID of the file.
            parent_id (str, optional): The ID of the parent folder.
            file_name (str, optional): The name of the file.
            
        Returns:
            str: The file path.
        """
        if parent_id is None or parent_id == self.drive_client.folder_id:
            # Root folder
            return file_name if file_name else ""
        
        # Get parent file
        parent_file = self.db_manager.get_file(parent_id)
        if parent_file and parent_file.get('path'):
            # Parent path exists in database
            return os.path.join(parent_file['path'], file_name if file_name else "")
        
        # Try to get parent metadata from Google Drive
        parent_metadata = self.drive_client.get_file_metadata(parent_id)
        if parent_metadata:
            parent_path = self.build_file_path(
                parent_metadata['id'],
                parent_metadata.get('parents', [None])[0] if 'parents' in parent_metadata else None,
                parent_metadata['name']
            )
            return os.path.join(parent_path, file_name if file_name else "")
        
        # Fallback
        return file_name if file_name else ""
    
    def detect_changes(self, folder_id=None):
        """
        Detect changes in files.
        
        Args:
            folder_id (str, optional): The ID of the folder to check.
                                      If None, uses the configured folder_id.
                                      
        Returns:
            tuple: (new_files, modified_files, deleted_files)
        """
        folder_id = folder_id or self.drive_client.folder_id
        
        # Get all files from Google Drive
        drive_files = self.drive_client.list_all_files(folder_id)
        
        # Get all files from database
        db_files = self.db_manager.get_all_files()
        
        # Create dictionaries for easier lookup
        drive_files_dict = {file['id']: file for file in drive_files}
        db_files_dict = {file['id']: file for file in db_files}
        
        # Find new and modified files
        new_files = []
        modified_files = []
        
        for file_id, file_data in drive_files_dict.items():
            # Add parent_id to file_data
            if 'parents' in file_data:
                file_data['parent_id'] = file_data['parents'][0]
            
            # Build file path
            file_data['path'] = self.build_file_path(
                file_id,
                file_data.get('parent_id'),
                file_data['name']
            )
            
            if file_id not in db_files_dict:
                # New file
                file_data['status'] = 'new'
                new_files.append(file_data)
                self.db_manager.upsert_file(file_data)
                self.db_manager.add_sync_history(file_id, 'new')
            else:
                # Existing file, check if modified
                db_file = db_files_dict[file_id]
                
                # Convert string timestamps to datetime objects for comparison
                drive_modified = self._parse_timestamp(file_data.get('modifiedTime'))
                db_modified = self._parse_timestamp(db_file.get('modified_time'))
                
                if drive_modified and db_modified and drive_modified > db_modified:
                    # File was modified
                    file_data['status'] = 'modified'
                    modified_files.append(file_data)
                    self.db_manager.upsert_file(file_data)
                    self.db_manager.add_sync_history(
                        file_id, 'modified',
                        f"Modified time: {file_data.get('modifiedTime')}"
                    )
                else:
                    # File unchanged
                    file_data['status'] = 'synced'
                    self.db_manager.upsert_file(file_data)
        
        # Find deleted files
        deleted_files = []
        for file_id, file_data in db_files_dict.items():
            if file_id not in drive_files_dict:
                # File was deleted from Google Drive
                file_data['status'] = 'deleted'
                deleted_files.append(file_data)
                self.db_manager.update_file_status(file_id, 'deleted')
                self.db_manager.add_sync_history(file_id, 'deleted')
        
        logger.info(f"Detected {len(new_files)} new files, {len(modified_files)} modified files, "
                   f"and {len(deleted_files)} deleted files")
        
        return new_files, modified_files, deleted_files
    
    def _parse_timestamp(self, timestamp_str):
        """
        Parse a timestamp string to a datetime object.
        
        Args:
            timestamp_str (str): The timestamp string.
            
        Returns:
            datetime: The parsed datetime or None if parsing fails.
        """
        if not timestamp_str:
            return None
        
        try:
            # Handle different timestamp formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds
                "%Y-%m-%dT%H:%M:%SZ",     # ISO format without microseconds
                "%Y-%m-%dT%H:%M:%S.%f",   # ISO format with microseconds, no Z
                "%Y-%m-%dT%H:%M:%S"       # ISO format without microseconds, no Z
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # If none of the formats match
            logger.warning(f"Could not parse timestamp: {timestamp_str}")
            return None
        except Exception as e:
            logger.error(f"Error parsing timestamp {timestamp_str}: {e}")
            return None
