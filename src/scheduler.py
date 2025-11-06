#!/usr/bin/env python3
"""
Scheduler for running the sync process at regular intervals.
"""

import time
import signal
import logging
import threading
from typing import Callable, Dict, Any, Optional, List
from datetime import datetime, timedelta

# Configure module logger
logger = logging.getLogger(__name__)


class Scheduler:
    """Scheduler for running tasks at regular intervals."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.last_run_times: Dict[str, datetime] = {}
    
    def add_task(self, task_id: str, func: Callable, interval_seconds: int, 
                 args: Optional[List] = None, kwargs: Optional[Dict] = None) -> None:
        """
        Add a task to the scheduler.
        
        Args:
            task_id: Unique identifier for the task.
            func: Function to call.
            interval_seconds: Interval between calls in seconds.
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """
        with self.lock:
            self.tasks[task_id] = {
                'func': func,
                'interval': interval_seconds,
                'args': args or [],
                'kwargs': kwargs or {},
                'last_run': None,
                'next_run': datetime.now()
            }
            logger.info(f"Task '{task_id}' added to scheduler with interval {interval_seconds} seconds")
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a task from the scheduler.
        
        Args:
            task_id: Unique identifier for the task.
            
        Returns:
            True if the task was removed, False if it wasn't found.
        """
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                logger.info(f"Task '{task_id}' removed from scheduler")
                return True
            return False
    
    def update_task_interval(self, task_id: str, interval_seconds: int) -> bool:
        """
        Update the interval for a task.
        
        Args:
            task_id: Unique identifier for the task.
            interval_seconds: New interval between calls in seconds.
            
        Returns:
            True if the task was updated, False if it wasn't found.
        """
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id]['interval'] = interval_seconds
                logger.info(f"Task '{task_id}' interval updated to {interval_seconds} seconds")
                return True
            return False
    
    def _run_task(self, task_id: str, task_info: Dict[str, Any]) -> None:
        """
        Run a task and handle any exceptions.
        
        Args:
            task_id: Unique identifier for the task.
            task_info: Task information dictionary.
        """
        try:
            logger.info(f"Running task '{task_id}'")
            task_info['func'](*task_info['args'], **task_info['kwargs'])
            task_info['last_run'] = datetime.now()
            self.last_run_times[task_id] = task_info['last_run']
            logger.info(f"Task '{task_id}' completed successfully")
        except Exception as e:
            logger.exception(f"Error running task '{task_id}': {e}")
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        logger.info("Scheduler loop started")
        
        while self.running:
            now = datetime.now()
            
            with self.lock:
                for task_id, task_info in self.tasks.items():
                    if now >= task_info['next_run']:
                        # Run the task
                        self._run_task(task_id, task_info)
                        
                        # Schedule next run
                        task_info['next_run'] = now + timedelta(seconds=task_info['interval'])
                        logger.debug(f"Task '{task_id}' next run scheduled for {task_info['next_run']}")
            
            # Sleep for a short time to avoid high CPU usage
            time.sleep(1)
        
        logger.info("Scheduler loop stopped")
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop)
        self.thread.daemon = True  # Allow the thread to be terminated when the main program exits
        self.thread.start()
        logger.info("Scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                logger.warning("Scheduler thread did not stop gracefully")
            else:
                logger.info("Scheduler stopped")
        
        self.thread = None
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a task.
        
        Args:
            task_id: Unique identifier for the task.
            
        Returns:
            Dictionary with task status information or None if the task wasn't found.
        """
        with self.lock:
            if task_id in self.tasks:
                task_info = self.tasks[task_id]
                return {
                    'interval': task_info['interval'],
                    'last_run': task_info['last_run'],
                    'next_run': task_info['next_run']
                }
            return None
    
    def get_all_task_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the status of all tasks.
        
        Returns:
            Dictionary mapping task IDs to status dictionaries.
        """
        statuses = {}
        with self.lock:
            for task_id in self.tasks:
                statuses[task_id] = self.get_task_status(task_id)
        return statuses
    
    def run_task_now(self, task_id: str) -> bool:
        """
        Run a task immediately, regardless of its schedule.
        
        Args:
            task_id: Unique identifier for the task.
            
        Returns:
            True if the task was run, False if it wasn't found.
        """
        with self.lock:
            if task_id in self.tasks:
                task_info = self.tasks[task_id]
                self._run_task(task_id, task_info)
                # Reset the next run time
                task_info['next_run'] = datetime.now() + timedelta(seconds=task_info['interval'])
                return True
            return False
