"""
Database manager for tracking file metadata.

This module provides functionality to store and retrieve file metadata
for tracking changes in Google Drive files.
"""

import os
import sqlite3
import logging
import threading
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Thread-safe database manager for file metadata tracking."""
    
    def __init__(self, db_path):
        """
        Initialize the database manager.
        
        Args:
            db_path (str or Path): Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._lock = threading.RLock()
        
        # Initialize the database schema
        with self._get_connection() as conn:
            self._initialize_schema(conn)
    
    def _get_connection(self):
        """
        Get a thread-local database connection.
        
        Returns:
            sqlite3.Connection: A database connection for the current thread.
        """
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            try:
                self._local.conn = sqlite3.connect(self.db_path)
                self._local.conn.row_factory = sqlite3.Row
                logger.debug(f"Created new database connection for thread {threading.get_ident()}")
            except sqlite3.Error as e:
                logger.error(f"Database connection error: {e}")
                raise
        return self._local.conn
    
    def _initialize_schema(self, conn):
        """
        Initialize the database schema.
        
        Args:
            conn (sqlite3.Connection): The database connection.
            
        Returns:
            bool: True if initialization is successful, False otherwise.
        """
        try:
            cursor = conn.cursor()
            
            # Create files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    parent_id TEXT,
                    mime_type TEXT,
                    modified_time TEXT,
                    size INTEGER,
                    md5_checksum TEXT,
                    path TEXT,
                    last_checked TEXT,
                    status TEXT
                )
            ''')
            
            # Create sync_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT,
                    action TEXT,
                    timestamp TEXT,
                    details TEXT,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            ''')
            
            conn.commit()
            logger.info("Database schema initialized")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            conn.rollback()
            return False
    
    def close(self):
        """Close all database connections."""
        with self._lock:
            if hasattr(self._local, 'conn') and self._local.conn is not None:
                self._local.conn.close()
                self._local.conn = None
                logger.debug(f"Closed database connection for thread {threading.get_ident()}")
    
    def initialize_db(self):
        """
        Initialize the database schema.
        
        Returns:
            bool: True if initialization is successful, False otherwise.
        """
        try:
            with self._get_connection() as conn:
                return self._initialize_schema(conn)
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            return False
    
    def upsert_file(self, file_data):
        """
        Insert or update file metadata.
        
        Args:
            file_data (dict): File metadata.
            
        Returns:
            bool: True if operation is successful, False otherwise.
        """
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Check if file exists
                cursor.execute(
                    "SELECT id FROM files WHERE id = ?",
                    (file_data['id'],)
                )
                exists = cursor.fetchone()
                
                current_time = datetime.now().isoformat()
                
                if exists:
                    # Update existing file
                    cursor.execute('''
                        UPDATE files
                        SET name = ?,
                            parent_id = ?,
                            mime_type = ?,
                            modified_time = ?,
                            size = ?,
                            md5_checksum = ?,
                            path = ?,
                            last_checked = ?,
                            status = ?
                        WHERE id = ?
                    ''', (
                        file_data['name'],
                        file_data.get('parent_id'),
                        file_data.get('mimeType'),
                        file_data.get('modifiedTime'),
                        file_data.get('size'),
                        file_data.get('md5Checksum'),
                        file_data.get('path'),
                        current_time,
                        file_data.get('status', 'synced'),
                        file_data['id']
                    ))
                else:
                    # Insert new file
                    cursor.execute('''
                        INSERT INTO files (
                            id, name, parent_id, mime_type, modified_time,
                            size, md5_checksum, path, last_checked, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        file_data['id'],
                        file_data['name'],
                        file_data.get('parent_id'),
                        file_data.get('mimeType'),
                        file_data.get('modifiedTime'),
                        file_data.get('size'),
                        file_data.get('md5Checksum'),
                        file_data.get('path'),
                        current_time,
                        file_data.get('status', 'new')
                    ))
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error upserting file {file_data.get('id')}: {e}")
            return False
    
    def add_sync_history(self, file_id, action, details=None):
        """
        Add a record to the sync history.
        
        Args:
            file_id (str): The ID of the file.
            action (str): The action performed (e.g., 'new', 'modified', 'deleted').
            details (str, optional): Additional details about the action.
            
        Returns:
            bool: True if operation is successful, False otherwise.
        """
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                current_time = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT INTO sync_history (
                        file_id, action, timestamp, details
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    file_id,
                    action,
                    current_time,
                    details
                ))
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error adding sync history for file {file_id}: {e}")
            return False
    
    def get_file(self, file_id):
        """
        Get file metadata by ID.
        
        Args:
            file_id (str): The ID of the file.
            
        Returns:
            dict: File metadata or None if not found.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM files WHERE id = ?",
                (file_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting file {file_id}: {e}")
            return None
    
    def get_all_files(self):
        """
        Get all files in the database.
        
        Returns:
            list: List of file metadata dictionaries.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM files")
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting all files: {e}")
            return []
    
    def get_files_by_status(self, status):
        """
        Get files by status.
        
        Args:
            status (str): The status to filter by (e.g., 'new', 'modified', 'synced').
            
        Returns:
            list: List of file metadata dictionaries.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM files WHERE status = ?",
                (status,)
            )
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting files by status {status}: {e}")
            return []
    
    def update_file_status(self, file_id, status):
        """
        Update the status of a file.
        
        Args:
            file_id (str): The ID of the file.
            status (str): The new status.
            
        Returns:
            bool: True if operation is successful, False otherwise.
        """
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE files SET status = ? WHERE id = ?",
                    (status, file_id)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error updating status for file {file_id}: {e}")
            return False
    
    def delete_file(self, file_id):
        """
        Delete a file from the database.
        
        Args:
            file_id (str): The ID of the file.
            
        Returns:
            bool: True if operation is successful, False otherwise.
        """
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    "DELETE FROM files WHERE id = ?",
                    (file_id,)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False
