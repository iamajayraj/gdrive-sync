"""
File download manager for Google Drive files.

This module provides functionality to download files from Google Drive.
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union

logger = logging.getLogger(__name__)

# Type definitions
FileDict = Dict[str, Any]
PathLike = Union[str, Path]


class DownloadManager:
    """Manages downloading files from Google Drive."""
    
    def __init__(self, drive_client, download_dir: Optional[PathLike] = None):
        """
        Initialize the download manager.
        
        Args:
            drive_client: The Google Drive client.
            download_dir: Directory to store downloaded files. If None, uses a temp directory.
        """
        self.drive_client = drive_client
        
        if download_dir is None:
            self.download_dir = Path(tempfile.gettempdir()) / "gdrive_sync_downloads"
        else:
            self.download_dir = Path(download_dir)
        
        # Create download directory if it doesn't exist
        self.download_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Download directory: {self.download_dir}")
        
        # Track downloaded files
        self.downloaded_files: Dict[str, Path] = {}
    
    def download_file(self, file_data: Dict[str, Any]) -> Optional[Path]:
        """
        Download a file from Google Drive.
        
        Args:
            file_data: File metadata dictionary.
            
        Returns:
            Path to the downloaded file or None if download failed.
        """
        if not file_data:
            logger.error("Invalid file data: empty dictionary")
            return None
            
        if 'id' not in file_data or 'name' not in file_data:
            logger.error("Invalid file data: missing required fields (id or name)")
            return None
            
        file_id = file_data['id']
        file_name = file_data['name']
        
        logger.info(f"Downloading file: {file_name} ({file_id})")
        
        # Create a safe filename
        safe_name = self._create_safe_filename(file_name)
        
        # Create output path
        output_path = self.download_dir / safe_name
        
        # Check if file is already downloaded
        if file_id in self.downloaded_files:
            existing_path = self.downloaded_files[file_id]
            if existing_path.exists():
                logger.debug(f"File {file_name} already downloaded to {existing_path}")
                return existing_path
        
        # Download the file
        try:
            logger.info(f"Downloading file: {file_name} ({file_id})")
            
            # Ensure we have a unique filename
            if output_path.exists():
                base_name = output_path.stem
                extension = output_path.suffix
                counter = 1
                while output_path.exists():
                    output_path = self.download_dir / f"{base_name}_{counter}{extension}"
                    counter += 1
            
            # Download the file
            success = self.drive_client.download_file(file_id, output_path)
            
            if success:
                # Check if the file exists with a different extension (for Google Workspace files)
                if not output_path.exists():
                    # Look for files with the same stem but different extension
                    parent_dir = output_path.parent
                    file_stem = output_path.stem
                    possible_files = list(parent_dir.glob(f"{file_stem}.*"))
                    
                    if possible_files:
                        # Use the first matching file
                        output_path = possible_files[0]
                
                logger.info(f"File downloaded successfully to {output_path}")
                self.downloaded_files[file_id] = output_path
                return output_path
            else:
                logger.error(f"Failed to download file {file_name} ({file_id})")
                return None
                
        except Exception as e:
            logger.exception(f"Error downloading file {file_name} ({file_id}): {e}")
            return None
    
    def download_files(self, file_list: List[FileDict]) -> Dict[str, Path]:
        """
        Download multiple files from Google Drive.
        
        Args:
            file_list: List of file metadata dictionaries.
            
        Returns:
            Dictionary mapping file IDs to downloaded file paths.
        """
        results = {}
        
        for file_data in file_list:
            file_id = file_data['id']
            file_path = self.download_file(file_data)
            
            if file_path:
                results[file_id] = file_path
        
        logger.info(f"Downloaded {len(results)} files out of {len(file_list)} requested")
        return results
    
    def get_downloaded_file(self, file_id: str) -> Optional[Path]:
        """Get the path to a downloaded file.
        
        Args:
            file_id: The ID of the file.
            
        Returns:
            Path to the downloaded file or None if not found.
        """
        return self.downloaded_files.get(file_id)
        
    def remove_tracking(self, file_id: str) -> None:
        """Remove a file from the tracking dictionary.
        
        Args:
            file_id: The ID of the file to remove.
        """
        if file_id in self.downloaded_files:
            del self.downloaded_files[file_id]
            logger.debug(f"Removed file {file_id} from tracking dictionary")
    
    def cleanup_old_files(self, max_age_seconds: int = 86400) -> int:
        """
        Clean up old downloaded files.
        
        Args:
            max_age_seconds: Maximum age of files in seconds (default: 24 hours).
            
        Returns:
            Number of files deleted.
        """
        import time
        
        now = time.time()
        deleted_count = 0
        to_delete = []
        
        for file_id, file_path in self.downloaded_files.items():
            if not file_path.exists():
                to_delete.append(file_id)
                continue
                
            file_age = now - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    to_delete.append(file_id)
                    deleted_count += 1
                    logger.debug(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {e}")
        
        # Remove deleted files from tracking
        for file_id in to_delete:
            self.downloaded_files.pop(file_id, None)
        
        logger.info(f"Cleaned up {deleted_count} old files")
        return deleted_count
    
    def _create_safe_filename(self, filename: str) -> str:
        """
        Create a safe filename from the original filename.
        
        Args:
            filename: Original filename.
            
        Returns:
            Safe filename.
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        safe_name = filename
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Limit filename length
        if len(safe_name) > 255:
            base, ext = os.path.splitext(safe_name)
            safe_name = base[:255-len(ext)] + ext
            
        return safe_name
    
    def clear_downloads(self) -> bool:
        """
        Clear all downloaded files.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            for file_id, file_path in list(self.downloaded_files.items()):
                if file_path.exists():
                    file_path.unlink()
                self.downloaded_files.pop(file_id, None)
            
            logger.info("All downloaded files cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing downloads: {e}")
            return False
