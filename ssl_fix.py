#!/usr/bin/env python3
"""
SSL Certificate Fix for Google Drive Sync

This script updates the SSL certificates used by the application to ensure
proper SSL/TLS connections to Google APIs.
"""

import os
import sys
import ssl
import certifi
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_ssl_certificates():
    """Update SSL certificates using certifi."""
    try:
        # Get the path to certifi's certificate bundle
        cert_path = certifi.where()
        logger.info(f"Certifi certificate path: {cert_path}")
        
        # Set environment variables to use certifi's certificate bundle
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path
        os.environ['SSL_CERT_FILE'] = cert_path
        
        # Create a custom SSL context with modern protocols
        ssl_context = ssl.create_default_context()
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        # Set as default SSL context
        ssl._create_default_https_context = lambda: ssl_context
        
        logger.info("SSL certificates updated successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to update SSL certificates: {e}")
        return False

def verify_ssl_connection():
    """Verify SSL connection to Google APIs."""
    import requests
    
    try:
        response = requests.get('https://www.googleapis.com/drive/v3/about', timeout=10)
        logger.info(f"Connection test status code: {response.status_code}")
        logger.info("SSL connection verification successful")
        return True
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL verification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

def main():
    """Main entry point."""
    logger.info("Starting SSL certificate update")
    
    # Update SSL certificates
    if update_ssl_certificates():
        # Verify SSL connection
        if verify_ssl_connection():
            logger.info("SSL fix completed successfully")
        else:
            logger.warning("SSL fix applied but verification failed")
    else:
        logger.error("SSL fix failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
