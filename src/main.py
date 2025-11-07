#!/usr/bin/env python3
"""Google Drive Sync and Dify API Integration

This application monitors a Google Drive folder (and its subfolders) for new or
modified files and pushes them to the Dify API.
"""

import os
import sys
import time
import signal
import logging
import argparse
import ssl
import certifi
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.file_processor import FileProcessor
from src.drive.service_drive_client import ServiceDriveClient
from src.database.db_manager import DatabaseManager
from src.drive.change_detector import ChangeDetector
from src.drive.polling_system import PollingSystem
from src.drive.download_manager import DownloadManager
from src.dify.dify_client import DifyClient
from src.dify.file_uploader import FileUploader
from src.scheduler import Scheduler
from src.error_handler import ErrorHandler

# Configure module logger
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='Google Drive Sync and Dify API Integration'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to the configuration file'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set the logging level'
    )
    parser.add_argument(
        '--poll-now',
        action='store_true',
        help='Poll for changes immediately and exit'
    )
    parser.add_argument(
        '--no-scheduler',
        action='store_true',
        help='Disable the scheduler and use the legacy polling loop'
    )
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run the sync process once and exit (same as --poll-now)'
    )
    return parser.parse_args()


# File event handlers
def handle_new_file(file: Dict[str, Any]) -> None:
    """Handle a new file event.
    
    Args:
        file: File metadata dictionary.
    """
    logger.info(f"New file detected: {file['name']} ({file['id']})")
    
    # Download the file
    download_path = download_manager.download_file(file)
    
    if download_path:
        # Process the file
        file_info = file_processor.get_file_info(download_path)
        logger.info(f"Downloaded file: {file_info['name']} ({file_info['size']} bytes)")
        
        try:
            # Upload to Dify API if available
            if file_uploader:
                logger.info(f"Uploading file to Dify API: {file['name']}")
                success, response = file_uploader.upload_file(file, download_path)
                
                if success:
                    document_id = response.get('id', 'unknown')
                    logger.info(f"File uploaded successfully to Dify API. Document ID: {document_id}")
                    
                    # Delete the file after successful upload
                    if download_path.exists():
                        download_path.unlink()
                        # Remove from tracking dictionary
                        download_manager.remove_tracking(file['id'])
                        logger.info(f"Deleted downloaded file after successful upload: {download_path}")
                else:
                    error = response.get('error', 'unknown error')
                    logger.error(f"Failed to upload file to Dify API: {error}")
            else:
                logger.warning("Dify API integration is disabled. Skipping upload.")
        except Exception as e:
            logger.exception(f"Error during file processing or upload: {e}")
    else:
        logger.error(f"Failed to download file: {file['name']} ({file['id']})")



def handle_modified_file(file: Dict[str, Any]) -> None:
    """Handle a modified file event.
    
    Args:
        file: File metadata dictionary.
    """
    logger.info(f"Modified file detected: {file['name']} ({file['id']})")
    
    # Download the file
    download_path = download_manager.download_file(file)
    
    if download_path:
        # Process the file
        file_info = file_processor.get_file_info(download_path)
        logger.info(f"Downloaded modified file: {file_info['name']} ({file_info['size']} bytes)")
        
        try:
            # Upload to Dify API if available
            if file_uploader:
                logger.info(f"Uploading modified file to Dify API: {file['name']}")
                success, response = file_uploader.upload_file(file, download_path)
                
                if success:
                    document_id = response.get('id', 'unknown')
                    logger.info(f"Modified file uploaded successfully to Dify API. Document ID: {document_id}")
                    
                    # Delete the file after successful upload
                    if download_path.exists():
                        download_path.unlink()
                        # Remove from tracking dictionary
                        download_manager.remove_tracking(file['id'])
                        logger.info(f"Deleted downloaded file after successful upload: {download_path}")
                else:
                    error = response.get('error', 'unknown error')
                    logger.error(f"Failed to upload modified file to Dify API: {error}")
            else:
                logger.warning("Dify API integration is disabled. Skipping upload.")
        except Exception as e:
            logger.exception(f"Error during file processing or upload: {e}")
    else:
        logger.error(f"Failed to download modified file: {file['name']} ({file['id']})")



def handle_deleted_file(file: Dict[str, Any]) -> None:
    """Handle a deleted file event.
    
    Args:
        file: File metadata dictionary.
    """
    logger.info(f"Deleted file detected: {file['id']}")
    
    # Check if we have a local copy
    local_path = download_manager.get_downloaded_file(file['id'])
    if local_path and local_path.exists():
        logger.info(f"Removing local copy of deleted file: {local_path}")
        try:
            local_path.unlink()
            # Remove from tracking dictionary
            download_manager.remove_tracking(file['id'])
        except Exception as e:
            logger.error(f"Error removing local file {local_path}: {e}")
    
    # Delete from Dify API if available
    if file_uploader:
        logger.info(f"Deleting file from Dify API: {file['id']}")
        success, response = file_uploader.delete_document(file['id'])
        
        if success:
            logger.info(f"File deleted successfully from Dify API")
        else:
            error = response.get('error', 'unknown error')
            logger.error(f"Failed to delete file from Dify API: {error}")
    else:
        logger.warning("Dify API integration is disabled. Skipping deletion.")


def handle_poll_complete(
    new_files: List[Dict[str, Any]],
    modified_files: List[Dict[str, Any]],
    deleted_files: List[Dict[str, Any]]
) -> None:
    """Handle poll completion event.
    
    Args:
        new_files: List of new file metadata.
        modified_files: List of modified file metadata.
        deleted_files: List of deleted file metadata.
    """
    logger.info(
        f"Poll complete: {len(new_files)} new, {len(modified_files)} modified, "
        f"{len(deleted_files)} deleted"
    )


def setup_components(config_path: Path) -> Tuple[Config, DatabaseManager, ServiceDriveClient, ChangeDetector, PollingSystem, DownloadManager, FileProcessor, DifyClient, FileUploader, Scheduler, ErrorHandler]:
    """Set up application components.
    
    Args:
        config_path: Path to the configuration file.
        
    Returns:
        Tuple containing the initialized components:
        - Config: Application configuration.
        - DatabaseManager: Database manager for file metadata.
        - ServiceDriveClient: Google Drive client.
        - ChangeDetector: File change detector.
        - PollingSystem: Polling system for checking changes.
        - DownloadManager: File download manager.
        - FileProcessor: File processor for handling different file types.
        - DifyClient: Dify API client.
        - FileUploader: File uploader for Dify API.
        - Scheduler: Task scheduler for running operations at regular intervals.
        - ErrorHandler: Error handling and recovery mechanisms.
        
    Raises:
        FileNotFoundError: If the configuration file is not found.
        RuntimeError: If database initialization or Google Drive connection fails.
        ValueError: If Dify API configuration is invalid.
    """
    # Load configuration
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    config = Config(config_path)
    logger.info(f"Configuration loaded from {config_path}")
    
    # Initialize database
    db_path = config.get('database.path', 'data/file_metadata.db')
    db_manager = DatabaseManager(db_path)
    if not db_manager.initialize_db():
        raise RuntimeError("Failed to initialize database")
    
    logger.info(f"Database initialized at {db_path}")
    
    # Initialize Google Drive client
    drive_client = ServiceDriveClient(config)
    if not drive_client.connect():
        raise RuntimeError("Failed to connect to Google Drive API")
    
    logger.info("Connected to Google Drive API successfully")
    
    # Initialize change detector
    change_detector = ChangeDetector(drive_client, db_manager)
    
    # Initialize polling system
    polling_interval = config.get('google_drive.polling_interval', 300)
    polling_system = PollingSystem(change_detector, polling_interval)
    
    # Initialize file processor
    file_processor = FileProcessor()
    logger.info("File processor initialized")
    
    # Initialize download manager
    download_dir = config.get('downloads.path', 'data/downloads')
    download_manager = DownloadManager(drive_client, download_dir)
    logger.info(f"Download manager initialized with directory: {download_dir}")
    
    # Initialize Dify client
    try:
        dify_client = DifyClient(config)
        logger.info("Dify API client initialized")
    except ValueError as e:
        logger.error(f"Failed to initialize Dify API client: {e}")
        logger.warning("Dify API integration will be disabled")
        dify_client = None
    
    # Initialize file uploader if Dify client is available
    if dify_client:
        file_uploader = FileUploader(dify_client, db_manager)
        logger.info("File uploader initialized")
    else:
        file_uploader = None
        logger.warning("File uploader disabled due to missing Dify API configuration")
    
    # Initialize scheduler
    scheduler = Scheduler()
    logger.info("Task scheduler initialized")
    
    # Initialize error handler
    max_retries = config.get('scheduler.error_recovery.max_retries', 3)
    retry_delay = config.get('scheduler.error_recovery.retry_delay_seconds', 30)
    continue_on_error = config.get('scheduler.error_recovery.continue_on_error', True)
    error_handler = ErrorHandler(max_retries, retry_delay, continue_on_error)
    logger.info(f"Error handler initialized with max_retries={max_retries}, retry_delay={retry_delay}s")
    
    return config, db_manager, drive_client, change_detector, polling_system, download_manager, file_processor, dify_client, file_uploader, scheduler, error_handler


def register_event_handlers(polling_system: PollingSystem) -> None:
    """Register event handlers for the polling system.
    
    Args:
        polling_system: The polling system to register handlers with.
    """
    polling_system.register_callback('new_file', handle_new_file)
    polling_system.register_callback('modified_file', handle_modified_file)
    polling_system.register_callback('deleted_file', handle_deleted_file)
    polling_system.register_callback('poll_complete', handle_poll_complete)


def setup_signal_handlers(polling_system: PollingSystem, db_manager: DatabaseManager) -> None:
    """Set up signal handlers for graceful shutdown.
    
    Args:
        polling_system: The polling system to stop on shutdown.
        db_manager: The database manager to close on shutdown.
    """
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        
        # Stop the polling system if it's running
        if polling_system:
            polling_system.stop()
            logger.info("Polling system stopped")
        
        # Stop the scheduler if it's running
        if scheduler is not None:
            scheduler.stop()
            logger.info("Scheduler stopped")
        
        # Close the database connection
        if db_manager:
            db_manager.close()
            logger.info("Database connection closed")
        
        # Clean up downloaded files
        if download_manager is not None:
            logger.info("Cleaning up downloaded files...")
            download_manager.clear_downloads()
            logger.info("Downloaded files cleaned up")
        
        # Log error statistics if available
        if error_handler is not None:
            error_stats = error_handler.get_error_stats()
            if error_stats:
                logger.info("Error statistics during this run:")
                for op_name, stats in error_stats.items():
                    logger.info(f"  {op_name}: {stats['count']} errors, last error: {stats['last_error']}")
            else:
                logger.info("No errors occurred during this run")
                
        logger.info("Shutdown complete")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


# Global variables for file handling components
download_manager: Optional[DownloadManager] = None
file_processor: Optional[FileProcessor] = None
file_uploader: Optional[FileUploader] = None
dify_client: Optional[DifyClient] = None
scheduler: Optional[Scheduler] = None
error_handler: Optional[ErrorHandler] = None


def main() -> None:
    """Main entry point for the application."""
    global download_manager, file_processor, file_uploader, dify_client, scheduler, error_handler
    
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logger(args.log_level)
    logger.info(f"Starting Google Drive Sync with log level: {args.log_level}")
    
    # Apply SSL fixes
    try:
        import ssl
        import certifi
        
        # Get the path to certifi's certificate bundle
        cert_path = certifi.where()
        logger.info(f"Using SSL certificates from: {cert_path}")
        
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
        
        logger.info("SSL security configuration applied")
    except Exception as e:
        logger.warning(f"Failed to apply SSL fixes: {e}. Continuing with default SSL configuration.")
    
    
    try:
        # Set up components
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
            
        config, db_manager, drive_client, change_detector, polling_system, download_manager, file_processor, dify_client, file_uploader, scheduler, error_handler = setup_components(config_path)
        
        # Register event handlers
        register_event_handlers(polling_system)
        
        # Handle run-once mode (same as poll-now)
        if args.poll_now or args.run_once:
            # Poll once and exit
            logger.info("Polling for changes...")
            new_files, modified_files, deleted_files = polling_system.poll_now()
            logger.info(
                f"Poll complete: {len(new_files)} new, {len(modified_files)} modified, "
                f"{len(deleted_files)} deleted"
            )
            
            # Clean up old downloaded files
            download_manager.cleanup_old_files()
            return
        
        # Set up signal handlers
        setup_signal_handlers(polling_system, db_manager)
        
        # Get configuration values
        polling_interval = config.get('google_drive.polling_interval', 300)
        cleanup_interval = config.get('downloads.cleanup_interval', 3600)  # Default: 1 hour
        
        # Get scheduler settings
        scheduler_enabled = config.get('scheduler.enabled', True)
        scheduler_polling_interval = config.get('scheduler.polling_interval', polling_interval)
        scheduler_cleanup_interval = config.get('scheduler.cleanup_interval', cleanup_interval)
        
        # Use the scheduler or legacy polling system based on user preference and config
        if args.no_scheduler or not scheduler_enabled:
            # Legacy polling system
            logger.info("Using legacy polling system (scheduler disabled)")
            polling_system.start()
            logger.info(f"Polling system started with interval of {polling_interval} seconds")
            
            logger.info("Application started successfully. Press Ctrl+C to exit.")
            
            # Keep the main thread alive
            try:
                last_cleanup = time.time()
                
                while True:
                    current_time = time.time()
                    
                    # Clean up old files if needed
                    if current_time - last_cleanup > cleanup_interval:
                        download_manager.cleanup_old_files()
                        last_cleanup = current_time
                    
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received. Shutting down...")
                polling_system.stop()
                db_manager.close()
        else:
            # Use the scheduler
            logger.info("Using task scheduler for orchestration")
            
            # Define the poll function
            def poll_for_changes():
                logger.info("Scheduled polling for changes...")
                success, result, exc = error_handler.execute_with_retry(
                    polling_system.poll_now,
                    operation_name="poll_for_changes"
                )
                
                if success:
                    if result is None:
                        # Extra protection in case poll_now still returns None
                        logger.warning("Polling returned None, treating as empty results")
                        new_files, modified_files, deleted_files = [], [], []
                    else:
                        try:
                            new_files, modified_files, deleted_files = result
                        except (TypeError, ValueError) as e:
                            logger.error(f"Error processing polling results: {e}")
                            logger.debug(f"Received result: {result}")
                            return
                    
                    logger.info(
                        f"Poll complete: {len(new_files)} new, {len(modified_files)} modified, "
                        f"{len(deleted_files)} deleted"
                    )
                else:
                    logger.error(f"Polling failed: {exc}")
            
            # Define the cleanup function
            def cleanup_downloads():
                logger.info("Scheduled cleanup of downloaded files...")
                success, result, exc = error_handler.execute_with_retry(
                    download_manager.cleanup_old_files,
                    operation_name="cleanup_downloads"
                )
                
                if success:
                    num_deleted = result
                    logger.info(f"Cleaned up {num_deleted} old files")
                else:
                    logger.error(f"Cleanup failed: {exc}")
            
            # Add tasks to the scheduler
            scheduler.add_task('poll', poll_for_changes, scheduler_polling_interval)
            scheduler.add_task('cleanup', cleanup_downloads, scheduler_cleanup_interval)
            
            # Start the scheduler
            scheduler.start()
            logger.info(f"Scheduler started with polling interval of {scheduler_polling_interval} seconds")
            logger.info(f"File cleanup scheduled every {scheduler_cleanup_interval} seconds")
            
            logger.info("Application started successfully. Press Ctrl+C to exit.")
            
            # Run initial poll
            poll_for_changes()
            
            # Keep the main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received. Shutting down...")
                scheduler.stop()
                db_manager.close()
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
