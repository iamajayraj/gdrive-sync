"""
Logging configuration for the Google Drive Sync application.
"""

import os
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logger(log_level='INFO', log_file=None):
    """
    Set up the application logger.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file (str, optional): Path to the log file. If None, logs will be stored
                                 in the default location.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # If log file is specified or use default
    if log_file is None:
        log_dir = Path(__file__).resolve().parent.parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / 'gdrive_sync.log'
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(exist_ok=True)
    
    # Create file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    
    # Add file handler to logger
    logger.addHandler(file_handler)
    
    logger.info(f"Logger initialized with level {log_level}")
    logger.info(f"Log file: {log_file}")
    
    return logger
