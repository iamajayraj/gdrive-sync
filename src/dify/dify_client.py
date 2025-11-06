"""
Dify API client for uploading files to Dify datasets.

This module provides functionality to interact with the Dify API.
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple

logger = logging.getLogger(__name__)

# Type definitions
PathLike = Union[str, Path]


class DifyClient:
    """Client for interacting with the Dify API."""
    
    def __init__(self, config):
        """
        Initialize the Dify API client.
        
        Args:
            config: Configuration object containing Dify API settings.
        """
        self.api_url = config.get('dify.api_url')
        self.api_key = config.get('dify.api_key')
        self.dataset_id = config.get('dify.dataset_id')
        
        # Validate configuration
        if not self.api_url:
            logger.error("Dify API URL not configured")
            raise ValueError("Dify API URL not configured")
        
        if not self.api_key:
            logger.error("Dify API key not configured")
            raise ValueError("Dify API key not configured")
        
        if not self.dataset_id:
            logger.error("Dify dataset ID not configured")
            raise ValueError("Dify dataset ID not configured")
        
        # Replace dataset_id placeholder in URL if needed
        self.api_url = self.api_url.replace('{dataset_id}', self.dataset_id)
        
        logger.info(f"Dify API client initialized for dataset {self.dataset_id}")
    
    def upload_file(self, file_path: PathLike, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Upload a file to the Dify API.
        
        Args:
            file_path: Path to the file to upload.
            metadata: Optional metadata to include with the file.
            
        Returns:
            Tuple of (success, response_data).
        """
        if not file_path:
            logger.error("Invalid file path: path is empty")
            return False, {"error": "Invalid file path: path is empty"}
            
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False, {"error": "File not found"}
        
        try:
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            # Add file name to metadata if not present
            if 'name' not in metadata:
                metadata['name'] = file_path.name
            
            # Prepare the file for upload
            with open(file_path, 'rb') as file:
                files = {
                    'file': (file_path.name, file, self._get_mime_type(file_path))
                }
                
                # Prepare form data
                data = {
                    'metadata': json.dumps(metadata)
                }
                
                logger.info(f"Uploading file {file_path.name} to Dify API")
                
                # Make the request
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    data=data,
                    files=files
                )
                
                # Check response
                if response.status_code == 200 or response.status_code == 201:
                    response_data = response.json()
                    logger.info(f"File {file_path.name} uploaded successfully. Document ID: {response_data.get('id', 'unknown')}")
                    return True, response_data
                else:
                    logger.error(f"Failed to upload file {file_path.name}. Status code: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return False, {"error": f"API error: {response.status_code}", "details": response.text}
                
        except requests.RequestException as e:
            logger.exception(f"Request error uploading file {file_path.name}: {e}")
            return False, {"error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.exception(f"Error uploading file {file_path.name}: {e}")
            return False, {"error": str(e)}
    
    def delete_document(self, document_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Delete a document from the Dify dataset.
        
        Args:
            document_id: The ID of the document to delete.
            
        Returns:
            Tuple of (success, response_data).
        """
        try:
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Construct delete URL
            delete_url = f"{self.api_url.replace('document/create-by-file', 'document')}/{document_id}"
            
            logger.info(f"Deleting document {document_id} from Dify API")
            
            # Make the request
            response = requests.delete(
                delete_url,
                headers=headers
            )
            
            # Check response
            if response.status_code == 200 or response.status_code == 204:
                logger.info(f"Document {document_id} deleted successfully")
                return True, {"success": True}
            else:
                logger.error(f"Failed to delete document {document_id}. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False, {"error": f"API error: {response.status_code}", "details": response.text}
            
        except requests.RequestException as e:
            logger.exception(f"Request error deleting document {document_id}: {e}")
            return False, {"error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.exception(f"Error deleting document {document_id}: {e}")
            return False, {"error": str(e)}
    
    def get_document_status(self, document_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get the status of a document in the Dify dataset.
        
        Args:
            document_id: The ID of the document to check.
            
        Returns:
            Tuple of (success, response_data).
        """
        try:
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Construct status URL
            status_url = f"{self.api_url.replace('document/create-by-file', 'document')}/{document_id}"
            
            logger.debug(f"Checking status of document {document_id}")
            
            # Make the request
            response = requests.get(
                status_url,
                headers=headers
            )
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                logger.debug(f"Document {document_id} status: {response_data.get('status', 'unknown')}")
                return True, response_data
            else:
                logger.error(f"Failed to get document status {document_id}. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False, {"error": f"API error: {response.status_code}", "details": response.text}
            
        except requests.RequestException as e:
            logger.exception(f"Request error getting document status {document_id}: {e}")
            return False, {"error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.exception(f"Error getting document status {document_id}: {e}")
            return False, {"error": str(e)}
    
    def list_documents(self, limit: int = 10, offset: int = 0) -> Tuple[bool, Dict[str, Any]]:
        """
        List documents in the Dify dataset.
        
        Args:
            limit: Maximum number of documents to return.
            offset: Offset for pagination.
            
        Returns:
            Tuple of (success, response_data).
        """
        try:
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Construct list URL
            list_url = f"{self.api_url.replace('document/create-by-file', 'documents')}?limit={limit}&offset={offset}"
            
            logger.info(f"Listing documents from Dify API (limit={limit}, offset={offset})")
            
            # Make the request
            response = requests.get(
                list_url,
                headers=headers
            )
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Retrieved {len(response_data.get('data', []))} documents")
                return True, response_data
            else:
                logger.error(f"Failed to list documents. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False, {"error": f"API error: {response.status_code}", "details": response.text}
            
        except requests.RequestException as e:
            logger.exception(f"Request error listing documents: {e}")
            return False, {"error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.exception(f"Error listing documents: {e}")
            return False, {"error": str(e)}
    
    def _get_mime_type(self, file_path: Path) -> str:
        """
        Get the MIME type of a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            MIME type of the file.
        """
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
