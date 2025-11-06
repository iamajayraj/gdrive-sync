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
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.drive.service_drive_client import ServiceDriveClient
from src.database.db_manager import DatabaseManager
from src.drive.change_detector import ChangeDetector
from src.drive.polling_system import PollingSystem

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
    return parser.parse_args()


# File event handlers
def handle_new_file(file: Dict[str, Any]) -> None:
    """Handle a new file event.
    
    Args:
        file: File metadata dictionary.
    """
    logger.info(f"New file detected: {file['name']} ({file['id']})")
    # TODO: Implement file download and Dify API upload


def handle_modified_file(file: Dict[str, Any]) -> None:
    """Handle a modified file event.
    
    Args:
        file: File metadata dictionary.
    """
    logger.info(f"Modified file detected: {file['name']} ({file['id']})")
    # TODO: Implement file download and Dify API upload


def handle_deleted_file(file: Dict[str, Any]) -> None:
    """Handle a deleted file event.
    
    Args:
        file: File metadata dictionary.
    """
    logger.info(f"Deleted file detected: {file['id']}")
    # TODO: Implement Dify API deletion if needed


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


def setup_components(config_path: Path) -> Tuple[Config, DatabaseManager, ServiceDriveClient, ChangeDetector, PollingSystem]:
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
        
    Raises:
        FileNotFoundError: If the configuration file is not found.
        RuntimeError: If database initialization or Google Drive connection fails.
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
    
    return config, db_manager, drive_client, change_detector, polling_system


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
        polling_system.stop()
        db_manager.close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Setup logging
    setup_logger(args.log_level)
    
    try:
        # Set up components
        config_path = Path(args.config)
        config, db_manager, drive_client, change_detector, polling_system = setup_components(config_path)
        
        # Register event handlers
        register_event_handlers(polling_system)
        
        if args.poll_now:
            # Poll once and exit
            logger.info("Polling for changes...")
            new_files, modified_files, deleted_files = polling_system.poll_now()
            logger.info(
                f"Poll complete: {len(new_files)} new, {len(modified_files)} modified, "
                f"{len(deleted_files)} deleted"
            )
            return
        
        # Start polling system
        polling_system.start()
        polling_interval = config.get('google_drive.polling_interval', 300)
        logger.info(f"Polling system started with interval of {polling_interval} seconds")
        
        # Set up signal handlers
        setup_signal_handlers(polling_system, db_manager)
        
        logger.info("Application started successfully. Press Ctrl+C to exit.")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Shutting down...")
            polling_system.stop()
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
