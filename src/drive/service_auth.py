"""
Google Drive API authentication using service account credentials.

This module handles authentication with the Google Drive API using a service account.
"""

import os
import logging
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class DriveServiceAuth:
    """Google Drive API authentication handler using service account."""
    
    def __init__(self, service_account_file):
        """
        Initialize the authentication handler.
        
        Args:
            service_account_file (str): Path to the service account JSON file.
        """
        self.service_account_file = Path(service_account_file)
        self.credentials = None
        self.service = None
    
    def authenticate(self):
        """
        Authenticate with the Google Drive API using service account.
        
        Returns:
            googleapiclient.discovery.Resource: The authenticated Google Drive service.
        """
        if not self.service_account_file.exists():
            raise FileNotFoundError(
                f"Service account file not found: {self.service_account_file}. "
                "Please download the service account JSON file from the Google Cloud Console."
            )
        
        try:
            logger.info("Authenticating with service account")
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=SCOPES
            )
            return self.build_service()
        except Exception as e:
            logger.error(f"Service account authentication failed: {e}")
            raise
    
    def build_service(self):
        """
        Build and return the Google Drive service.
        
        Returns:
            googleapiclient.discovery.Resource: The Google Drive service.
        """
        logger.debug("Building Google Drive service with service account")
        self.service = build('drive', 'v3', credentials=self.credentials)
        return self.service
    
    def get_service(self):
        """
        Get the authenticated Google Drive service.
        
        Returns:
            googleapiclient.discovery.Resource: The authenticated Google Drive service.
        """
        if not self.service:
            return self.authenticate()
        return self.service
