"""
Google Drive API authentication using service account credentials.

This module handles authentication with the Google Drive API using a service account.
"""

import os
import ssl
import logging
from pathlib import Path
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

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
        """Authenticate with the Google Drive API using service account."""
        if not self.service_account_file.exists():
            raise FileNotFoundError(f"Service account file not found: {self.service_account_file}")
        
        try:
            logger.info("Authenticating with service account")
            
            # Create custom SSL context with modern protocols
            ssl_context = ssl.create_default_context()
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            # Set SSL context as default
            ssl._create_default_https_context = lambda: ssl_context
            
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=SCOPES
            )
            return True
        except Exception as e:
            logger.error(f"Service account authentication failed: {e}")
            return False
    
    def build_service(self):
        """
        Build and return the Google Drive service with custom transport.
        
        Returns:
            googleapiclient.discovery.Resource: The Google Drive service.
        """
        logger.debug("Building Google Drive service with service account")
        
        from googleapiclient.http import build_http
        import httplib2
        
        # Create a custom HTTP object with specific timeout and retry settings
        http = httplib2.Http(timeout=60)
        
        # Create an authorized HTTP session
        authorized_http = self.credentials.authorize(http)
        
        # Build the service with the custom HTTP object and disable cache
        self.service = build('drive', 'v3', http=authorized_http, cache_discovery=False)
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
