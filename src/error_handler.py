#!/usr/bin/env python3
"""
Error handling and recovery mechanisms for the application.
"""

import time
import logging
import traceback
from typing import Callable, Dict, Any, Optional, List, Tuple

# Configure module logger
logger = logging.getLogger(__name__)


class ErrorHandler:
    """Error handling and recovery mechanisms."""
    
    def __init__(self, max_retries: int = 3, retry_delay_seconds: int = 30, 
                 continue_on_error: bool = True):
        """
        Initialize the error handler.
        
        Args:
            max_retries: Maximum number of retries for failed operations.
            retry_delay_seconds: Delay between retries in seconds.
            continue_on_error: Whether to continue execution when an error occurs.
        """
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.continue_on_error = continue_on_error
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, Exception] = {}
    
    def execute_with_retry(self, func: Callable, *args, operation_name: str = None, 
                           **kwargs) -> Tuple[bool, Any, Optional[Exception]]:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute.
            operation_name: Name of the operation for logging purposes.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
            
        Returns:
            Tuple of (success, result, exception).
        """
        op_name = operation_name or func.__name__
        retries = 0
        
        while retries <= self.max_retries:
            try:
                if retries > 0:
                    logger.info(f"Retry {retries}/{self.max_retries} for {op_name}...")
                
                result = func(*args, **kwargs)
                
                # Reset error count on success
                if op_name in self.error_counts:
                    self.error_counts[op_name] = 0
                
                return True, result, None
                
            except Exception as e:
                # Increment error count
                self.error_counts[op_name] = self.error_counts.get(op_name, 0) + 1
                self.last_errors[op_name] = e
                
                if retries < self.max_retries:
                    logger.warning(
                        f"Error in {op_name} (attempt {retries + 1}/{self.max_retries + 1}): {e}"
                    )
                    # Wait before retrying
                    time.sleep(self.retry_delay_seconds)
                    retries += 1
                else:
                    logger.error(
                        f"Operation {op_name} failed after {self.max_retries + 1} attempts: {e}"
                    )
                    logger.debug(f"Error details: {traceback.format_exc()}")
                    return False, None, e
        
        # This should never be reached
        return False, None, None
    
    def get_error_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get error statistics.
        
        Returns:
            Dictionary mapping operation names to error statistics.
        """
        stats = {}
        for op_name in self.error_counts:
            stats[op_name] = {
                'count': self.error_counts[op_name],
                'last_error': str(self.last_errors.get(op_name, None))
            }
        return stats
    
    def reset_error_stats(self, operation_name: Optional[str] = None) -> None:
        """
        Reset error statistics.
        
        Args:
            operation_name: Name of the operation to reset. If None, reset all.
        """
        if operation_name:
            if operation_name in self.error_counts:
                self.error_counts[operation_name] = 0
                self.last_errors.pop(operation_name, None)
        else:
            self.error_counts.clear()
            self.last_errors.clear()
    
    def should_continue(self, operation_name: str) -> bool:
        """
        Determine if execution should continue after an error.
        
        Args:
            operation_name: Name of the operation that failed.
            
        Returns:
            True if execution should continue, False otherwise.
        """
        if not self.continue_on_error:
            return False
        
        # Add additional logic here if needed
        return True
