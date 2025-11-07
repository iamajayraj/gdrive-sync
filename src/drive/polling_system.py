"""
Polling system for Google Drive changes.

This module provides a polling system to check for changes in Google Drive periodically.
"""

import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Tuple, Callable, Any, Optional, Union

logger = logging.getLogger(__name__)

# Type definitions
FileDict = Dict[str, Any]
FileList = List[FileDict]
CallbackFunc = Callable[[FileDict], None]
PollCompleteCallbackFunc = Callable[[FileList, FileList, FileList], None]
EventCallbacks = Dict[str, List[Union[CallbackFunc, PollCompleteCallbackFunc]]]


class PollingSystem:
    """Polling system for checking Google Drive changes periodically."""
    
    # Valid event types
    EVENT_NEW_FILE = 'new_file'
    EVENT_MODIFIED_FILE = 'modified_file'
    EVENT_DELETED_FILE = 'deleted_file'
    EVENT_POLL_COMPLETE = 'poll_complete'
    
    def __init__(self, change_detector, interval: int = 300):
        """
        Initialize the polling system.
        
        Args:
            change_detector: The change detector instance.
            interval: The polling interval in seconds (default: 300).
        """
        self.change_detector = change_detector
        self.interval = interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_poll_time: Optional[datetime] = None
        self.callbacks: EventCallbacks = {
            self.EVENT_NEW_FILE: [],
            self.EVENT_MODIFIED_FILE: [],
            self.EVENT_DELETED_FILE: [],
            self.EVENT_POLL_COMPLETE: []
        }
    
    def start(self) -> bool:
        """
        Start the polling system.
        
        Returns:
            True if started successfully, False otherwise.
        """
        if self.running:
            logger.warning("Polling system is already running")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._polling_loop)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info(f"Polling system started with interval of {self.interval} seconds")
        return True
    
    def stop(self) -> bool:
        """
        Stop the polling system.
        
        Returns:
            True if stopped successfully, False otherwise.
        """
        if not self.running:
            logger.warning("Polling system is not running")
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        
        logger.info("Polling system stopped")
        return True
    
    def _trigger_callbacks(self, event_type: str, files: FileList) -> None:
        """
        Trigger callbacks for a specific event type.
        
        Args:
            event_type: The event type.
            files: List of file metadata dictionaries.
        """
        for file in files:
            for callback in self.callbacks[event_type]:
                try:
                    callback(file)  # type: ignore
                except Exception as e:
                    logger.error(f"Error in {event_type} callback: {e}")
    
    def _trigger_poll_complete_callbacks(
        self, new_files: FileList, modified_files: FileList, deleted_files: FileList
    ) -> None:
        """
        Trigger poll_complete callbacks.
        
        Args:
            new_files: List of new file metadata.
            modified_files: List of modified file metadata.
            deleted_files: List of deleted file metadata.
        """
        for callback in self.callbacks[self.EVENT_POLL_COMPLETE]:
            try:
                callback(new_files, modified_files, deleted_files)  # type: ignore
            except Exception as e:
                logger.error(f"Error in poll_complete callback: {e}")
    
    def _polling_loop(self) -> None:
        """Main polling loop that runs in a separate thread."""
        while self.running:
            try:
                logger.debug("Polling for changes...")
                self.last_poll_time = datetime.now()
                
                # Detect changes
                new_files, modified_files, deleted_files = self.change_detector.detect_changes()
                
                # Trigger callbacks
                self._trigger_callbacks(self.EVENT_NEW_FILE, new_files)
                self._trigger_callbacks(self.EVENT_MODIFIED_FILE, modified_files)
                self._trigger_callbacks(self.EVENT_DELETED_FILE, deleted_files)
                self._trigger_poll_complete_callbacks(new_files, modified_files, deleted_files)
                
                logger.info(f"Polling complete. Next poll in {self.interval} seconds")
                
                # Sleep until next poll, checking every second if we should stop
                for _ in range(self.interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                # Sleep for a short time before retrying
                time.sleep(10)
    
    def poll_now(self) -> Optional[Tuple[FileList, FileList, FileList]]:
        """
        Trigger an immediate poll.
        
        Returns:
            Tuple of (new_files, modified_files, deleted_files) or empty lists if error occurs.
        """
        try:
            logger.info("Manual polling triggered")
            self.last_poll_time = datetime.now()
            
            # Detect changes
            try:
                new_files, modified_files, deleted_files = self.change_detector.detect_changes()
            except Exception as e:
                # Handle SSL errors and other connection issues
                if 'SSL' in str(e) or 'socket' in str(e) or 'connection' in str(e).lower():
                    logger.error(f"Network or SSL error during polling: {e}")
                    logger.info("Returning empty results due to connection error")
                    # Return empty lists instead of None to avoid unpacking errors
                    return [], [], []
                else:
                    # Re-raise other exceptions
                    raise
            
            # Trigger callbacks
            self._trigger_callbacks(self.EVENT_NEW_FILE, new_files)
            self._trigger_callbacks(self.EVENT_MODIFIED_FILE, modified_files)
            self._trigger_callbacks(self.EVENT_DELETED_FILE, deleted_files)
            self._trigger_poll_complete_callbacks(new_files, modified_files, deleted_files)
            
            return new_files, modified_files, deleted_files
        except Exception as e:
            logger.error(f"Error in manual polling: {e}")
            # Return empty lists instead of None to avoid unpacking errors
            return [], [], []
    
    def register_callback(self, event_type: str, callback: Union[CallbackFunc, PollCompleteCallbackFunc]) -> bool:
        """
        Register a callback for an event.
        
        Args:
            event_type: The event type ('new_file', 'modified_file', 'deleted_file', 'poll_complete').
            callback: The callback function.
            
        Returns:
            True if registered successfully, False otherwise.
        """
        if event_type not in self.callbacks:
            logger.error(f"Unknown event type: {event_type}")
            return False
        
        if not callable(callback):
            logger.error("Callback must be callable")
            return False
        
        self.callbacks[event_type].append(callback)  # type: ignore
        logger.debug(f"Registered callback for event: {event_type}")
        return True
    
    def unregister_callback(self, event_type: str, callback: Union[CallbackFunc, PollCompleteCallbackFunc]) -> bool:
        """
        Unregister a callback for an event.
        
        Args:
            event_type: The event type.
            callback: The callback function.
            
        Returns:
            True if unregistered successfully, False otherwise.
        """
        if event_type not in self.callbacks:
            logger.error(f"Unknown event type: {event_type}")
            return False
        
        callback_list = self.callbacks[event_type]
        if callback in callback_list:
            callback_list.remove(callback)  # type: ignore
            logger.debug(f"Unregistered callback for event: {event_type}")
            return True
        
        logger.warning(f"Callback not found for event: {event_type}")
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the polling system.
        
        Returns:
            Status information dictionary.
        """
        return {
            'running': self.running,
            'interval': self.interval,
            'last_poll_time': self.last_poll_time.isoformat() if self.last_poll_time else None,
            'registered_callbacks': {
                event_type: len(callbacks)
                for event_type, callbacks in self.callbacks.items()
            }
        }
