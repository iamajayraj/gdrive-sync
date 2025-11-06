"""
Google Drive client module using service account authentication.

This module provides functionality to interact with Google Drive using a service account.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from src.drive.service_auth import DriveServiceAuth

logger = logging.getLogger(__name__)


class ServiceDriveClient:
    """Google Drive client using service account authentication."""
    
    def __init__(self, config):
        """
        Initialize the Google Drive client.
        
        Args:
            config (Config): The application configuration.
        """
        self.config = config
        self.folder_id = config.get('google_drive.folder_id')
        service_account_file = config.get('google_drive.service_account_file')
        
        self.auth = DriveServiceAuth(service_account_file)
        self.service = None
    
    def connect(self):
        """
        Connect to the Google Drive API.
        
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            self.service = self.auth.authenticate()
            logger.info("Successfully connected to Google Drive API with service account")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Google Drive API: {e}")
            return False
    
    def list_files(self, folder_id=None, page_size=100, page_token=None):
        """
        List files in a folder.
        
        Args:
            folder_id (str, optional): The ID of the folder to list files from.
                                      If None, uses the configured folder_id.
            page_size (int, optional): The maximum number of files to return per page.
            page_token (str, optional): The page token for pagination.
        
        Returns:
            tuple: (files, next_page_token) where files is a list of file metadata
                  and next_page_token is the token for the next page (or None).
        """
        if not self.service:
            if not self.connect():
                return [], None
        
        folder_id = folder_id or self.folder_id
        
        try:
            # Query for files in the specified folder
            query = f"'{folder_id}' in parents and trashed = false"
            
            results = self.service.files().list(
                q=query,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)",
                pageToken=page_token
            ).execute()
            
            files = results.get('files', [])
            next_page_token = results.get('nextPageToken')
            
            logger.debug(f"Found {len(files)} files in folder {folder_id}")
            return files, next_page_token
        
        except HttpError as error:
            logger.error(f"Error listing files: {error}")
            return [], None
    
    def list_all_files(self, folder_id=None):
        """
        List all files in a folder and its subfolders.
        
        Args:
            folder_id (str, optional): The ID of the folder to list files from.
                                      If None, uses the configured folder_id.
        
        Returns:
            list: A list of file metadata.
        """
        folder_id = folder_id or self.folder_id
        all_files = []
        folders_to_process = [folder_id]
        processed_folders = set()
        
        while folders_to_process:
            current_folder = folders_to_process.pop(0)
            
            if current_folder in processed_folders:
                continue
            
            processed_folders.add(current_folder)
            
            # List files in the current folder
            page_token = None
            while True:
                files, page_token = self.list_files(current_folder, page_token=page_token)
                
                for file in files:
                    # If it's a folder, add it to the list of folders to process
                    if file['mimeType'] == 'application/vnd.google-apps.folder':
                        folders_to_process.append(file['id'])
                    else:
                        all_files.append(file)
                
                if not page_token:
                    break
        
        logger.info(f"Found {len(all_files)} files in folder {folder_id} and its subfolders")
        return all_files
    
    def download_file(self, file_id, output_path):
        """
        Download a file from Google Drive.
        
        Args:
            file_id (str): The ID of the file to download.
            output_path (str or Path): The path where the file will be saved.
        
        Returns:
            bool: True if download is successful, False otherwise.
        """
        if not self.service:
            if not self.connect():
                return False
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get file metadata to check if it's a Google Workspace file
            file_metadata = self.get_file_metadata(file_id)
            if not file_metadata:
                logger.error(f"Could not get metadata for file {file_id}")
                return False
            
            mime_type = file_metadata.get('mimeType', '')
            
            # Handle Google Workspace files (Docs, Sheets, Slides)
            if mime_type.startswith('application/vnd.google-apps.'):
                return self._export_google_workspace_file(file_id, mime_type, output_path)
            
            # Regular file download
            request = self.service.files().get_media(fileId=file_id)
            
            with open(output_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    logger.debug(f"Download progress: {int(status.progress() * 100)}%")
            
            logger.info(f"File {file_id} downloaded to {output_path}")
            return True
        
        except HttpError as error:
            logger.error(f"Error downloading file {file_id}: {error}")
            return False
    
    def _export_google_workspace_file(self, file_id, mime_type, output_path):
        """
        Export a Google Workspace file to a downloadable format.
        
        Args:
            file_id (str): The ID of the file to export.
            mime_type (str): The MIME type of the Google Workspace file.
            output_path (Path): The path where the exported file will be saved.
            
        Returns:
            bool: True if export is successful, False otherwise.
        """
        try:
            # Define export formats based on the Google Workspace file type
            export_formats = {
                'application/vnd.google-apps.document': 'application/pdf',
                'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'application/vnd.google-apps.drawing': 'application/pdf',
                'application/vnd.google-apps.script': 'application/vnd.google-apps.script+json'
            }
            
            # Get the appropriate export format
            export_mime_type = export_formats.get(mime_type)
            
            if not export_mime_type:
                logger.error(f"Unsupported Google Workspace file type: {mime_type}")
                return False
            
            # Update file extension based on export format
            extension_map = {
                'application/pdf': '.pdf',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
                'application/vnd.google-apps.script+json': '.json'
            }
            
            new_extension = extension_map.get(export_mime_type, '.pdf')
            new_output_path = output_path.with_suffix(new_extension)
            
            # Export the file
            request = self.service.files().export_media(fileId=file_id, mimeType=export_mime_type)
            
            with open(new_output_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    logger.debug(f"Export progress: {int(status.progress() * 100)}%")
            
            logger.info(f"Google Workspace file {file_id} exported to {new_output_path}")
            return True
            
        except HttpError as error:
            logger.error(f"Error exporting Google Workspace file {file_id}: {error}")
            return False
    
    def get_file_metadata(self, file_id):
        """
        Get metadata for a specific file.
        
        Args:
            file_id (str): The ID of the file.
        
        Returns:
            dict: The file metadata or None if not found.
        """
        if not self.service:
            if not self.connect():
                return None
        
        try:
            return self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, size, parents"
            ).execute()
        
        except HttpError as error:
            logger.error(f"Error getting file metadata for {file_id}: {error}")
            return None
