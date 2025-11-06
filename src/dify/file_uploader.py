"""
File uploader for Dify API.

This module provides functionality to upload files to the Dify API.
"""

import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple

from src.dify.dify_client import DifyClient
from src.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

# Type definitions
PathLike = Union[str, Path]
FileDict = Dict[str, Any]


class FileUploader:
    """Uploads files to the Dify API and tracks upload status."""
    
    # File status constants
    STATUS_PENDING = 'pending'
    STATUS_UPLOADING = 'uploading'
    STATUS_UPLOADED = 'uploaded'
    STATUS_FAILED = 'failed'
    
    def __init__(self, dify_client: DifyClient, db_manager: DatabaseManager):
        """
        Initialize the file uploader.
        
        Args:
            dify_client: The Dify API client.
            db_manager: The database manager for tracking file status.
        """
        self.dify_client = dify_client
        self.db_manager = db_manager
        
        # Track upload status
        self.upload_status: Dict[str, Dict[str, Any]] = {}
    
    def upload_file(self, file_data: FileDict, file_path: PathLike) -> Tuple[bool, Dict[str, Any]]:
        """
        Upload a file to the Dify API.
        
        Args:
            file_data: File metadata dictionary.
            file_path: Path to the downloaded file.
            
        Returns:
            Tuple of (success, response_data).
        """
        if not file_data or 'id' not in file_data:
            logger.error("Invalid file data: missing ID")
            return False, {"error": "Invalid file data: missing ID"}
            
        file_id = file_data['id']
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            self._update_status(file_id, self.STATUS_FAILED, {"error": "File not found"})
            return False, {"error": "File not found"}
        
        try:
            # Update status to uploading
            self._update_status(file_id, self.STATUS_UPLOADING)
            
            # Prepare metadata
            metadata = {
                'name': file_data.get('name', file_path.name),
                'google_drive_id': file_id,
                'mime_type': file_data.get('mimeType', ''),
                'modified_time': file_data.get('modifiedTime', ''),
                'size': file_data.get('size', 0),
                'path': file_data.get('path', '')
            }
            
            # Upload the file
            success, response = self.dify_client.upload_file(file_path, metadata)
            
            if success:
                # Update database with document ID
                document_id = response.get('id')
                if document_id:
                    self.db_manager.update_file_status(
                        file_id, 
                        self.STATUS_UPLOADED, 
                        {'dify_document_id': document_id}
                    )
                
                # Update status to uploaded
                self._update_status(file_id, self.STATUS_UPLOADED, response)
                return True, response
            else:
                # Update status to failed
                self._update_status(file_id, self.STATUS_FAILED, response)
                return False, response
                
        except Exception as e:
            logger.exception(f"Error uploading file {file_data.get('name', 'unknown')}: {e}")
            self._update_status(file_id, self.STATUS_FAILED, {"error": str(e)})
            return False, {"error": str(e)}
    
    def upload_files(self, files: List[Tuple[FileDict, PathLike]]) -> Dict[str, Dict[str, Any]]:
        """
        Upload multiple files to the Dify API.
        
        Args:
            files: List of (file_data, file_path) tuples.
            
        Returns:
            Dictionary mapping file IDs to upload results.
        """
        results = {}
        
        for file_data, file_path in files:
            file_id = file_data['id']
            success, response = self.upload_file(file_data, file_path)
            results[file_id] = {
                'success': success,
                'response': response
            }
        
        return results
    
    def delete_document(self, file_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Delete a document from the Dify API.
        
        Args:
            file_id: The Google Drive file ID.
            
        Returns:
            Tuple of (success, response_data).
        """
        try:
            # Get the Dify document ID from the database
            file_info = self.db_manager.get_file(file_id)
            
            if not file_info:
                logger.error(f"File not found in database: {file_id}")
                return False, {"error": "File not found in database"}
            
            document_id = file_info.get('dify_document_id')
            
            if not document_id:
                logger.error(f"No Dify document ID found for file: {file_id}")
                return False, {"error": "No Dify document ID found"}
            
            # Delete the document
            success, response = self.dify_client.delete_document(document_id)
            
            if success:
                # Update database
                self.db_manager.update_file_status(file_id, 'deleted')
                return True, response
            else:
                return False, response
                
        except Exception as e:
            logger.exception(f"Error deleting document for file {file_id}: {e}")
            return False, {"error": str(e)}
    
    def get_upload_status(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the upload status of a file.
        
        Args:
            file_id: The Google Drive file ID.
            
        Returns:
            Upload status dictionary or None if not found.
        """
        return self.upload_status.get(file_id)
    
    def _update_status(self, file_id: str, status: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Update the upload status of a file.
        
        Args:
            file_id: The Google Drive file ID.
            status: The new status.
            data: Optional additional data.
        """
        if data is None:
            data = {}
        
        self.upload_status[file_id] = {
            'status': status,
            'timestamp': time.time(),
            'data': data
        }
