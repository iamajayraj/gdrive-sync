"""
File processor for handling different file types.

This module provides functionality to process different file types.
"""

import os
import logging
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple

logger = logging.getLogger(__name__)

# Type definitions
PathLike = Union[str, Path]


class FileProcessor:
    """Processes different file types."""
    
    # Common MIME types
    MIME_PDF = 'application/pdf'
    MIME_WORD = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    MIME_EXCEL = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    MIME_POWERPOINT = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    MIME_TEXT = 'text/plain'
    MIME_CSV = 'text/csv'
    MIME_JSON = 'application/json'
    MIME_XML = 'application/xml'
    MIME_HTML = 'text/html'
    MIME_MARKDOWN = 'text/markdown'
    
    # Google Workspace MIME types
    MIME_GDOC = 'application/vnd.google-apps.document'
    MIME_GSHEET = 'application/vnd.google-apps.spreadsheet'
    MIME_GSLIDES = 'application/vnd.google-apps.presentation'
    
    # Export formats for Google Workspace files
    EXPORT_FORMATS = {
        MIME_GDOC: {'mime': 'application/pdf', 'extension': '.pdf'},
        MIME_GSHEET: {'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'extension': '.xlsx'},
        MIME_GSLIDES: {'mime': 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'extension': '.pptx'}
    }
    
    def __init__(self):
        """Initialize the file processor."""
        # Initialize mimetypes
        mimetypes.init()
        
        # Add additional MIME types
        mimetypes.add_type('text/markdown', '.md')
        mimetypes.add_type('text/markdown', '.markdown')
    
    def get_mime_type(self, file_path: PathLike) -> str:
        """
        Get the MIME type of a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            MIME type of the file.
        """
        file_path = Path(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def is_text_file(self, file_path: PathLike) -> bool:
        """
        Check if a file is a text file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            True if the file is a text file, False otherwise.
        """
        mime_type = self.get_mime_type(file_path)
        return mime_type.startswith('text/') or mime_type in [
            'application/json', 
            'application/xml',
            'application/javascript',
            'application/x-yaml'
        ]
    
    def is_binary_file(self, file_path: PathLike) -> bool:
        """
        Check if a file is a binary file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            True if the file is a binary file, False otherwise.
        """
        return not self.is_text_file(file_path)
    
    def get_file_info(self, file_path: PathLike) -> Dict[str, Any]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Dictionary with file information.
        """
        file_path = Path(file_path)
        
        try:
            stat = file_path.stat()
            
            return {
                'name': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'mime_type': self.get_mime_type(file_path),
                'extension': file_path.suffix.lower(),
                'is_text': self.is_text_file(file_path)
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {
                'name': file_path.name,
                'path': str(file_path),
                'error': str(e)
            }
    
    def get_export_format(self, mime_type: str) -> Optional[Dict[str, str]]:
        """
        Get the export format for a Google Workspace file.
        
        Args:
            mime_type: MIME type of the Google Workspace file.
            
        Returns:
            Dictionary with export format information or None if not a Google Workspace file.
        """
        return self.EXPORT_FORMATS.get(mime_type)
    
    def is_google_workspace_file(self, mime_type: str) -> bool:
        """
        Check if a file is a Google Workspace file.
        
        Args:
            mime_type: MIME type of the file.
            
        Returns:
            True if the file is a Google Workspace file, False otherwise.
        """
        return mime_type.startswith('application/vnd.google-apps.')
    
    def validate_file(self, file_path: PathLike, max_size_mb: float = 100) -> Tuple[bool, Optional[str]]:
        """
        Validate a file.
        
        Args:
            file_path: Path to the file.
            max_size_mb: Maximum file size in megabytes.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        file_path = Path(file_path)
        
        # Check if file exists
        if not file_path.exists():
            return False, f"File does not exist: {file_path}"
        
        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            return False, f"File is not readable: {file_path}"
        
        # Check file size
        max_size_bytes = max_size_mb * 1024 * 1024
        file_size = file_path.stat().st_size
        
        if file_size > max_size_bytes:
            return False, f"File is too large: {file_size / (1024 * 1024):.2f} MB (max: {max_size_mb} MB)"
        
        # Check if file is empty
        if file_size == 0:
            return False, f"File is empty: {file_path}"
        
        return True, None
