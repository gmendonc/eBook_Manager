# adapters/notion/api_client.py
import logging
import requests
import json
import time
from typing import Dict, Any, List, Optional

from core.domain.notion_export_config import NotionExportConfig
from core.interfaces.notion_api_client import NotionApiClient

class NotionApiError(Exception):
    """Exception raised for Notion API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(message)

class HttpNotionApiClient(NotionApiClient):
    """Implementation of NotionApiClient using HTTP requests."""
    
    def __init__(self, config: NotionExportConfig):
        """
        Initializes the client.
        
        Args:
            config: Notion export configuration
        """
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.token}",
            "Content-Type": "application/json",
            "Notion-Version": config.api_version
        }
        self.logger = logging.getLogger(__name__)
    
    def get_database(self, database_id: str) -> Dict[str, Any]:
        """
        Gets a database by ID.
        
        Args:
            database_id: Database ID
            
        Returns:
            Database object
            
        Raises:
            NotionApiError: If API request fails
        """
        url = f"{self.config.base_url}/databases/{database_id}"
        return self._make_request("GET", url)
    
    def create_database(self, page_id: str, title: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new database.
        
        Args:
            page_id: Page ID where to create database
            title: Database title
            properties: Database properties definition
            
        Returns:
            Created database object
            
        Raises:
            NotionApiError: If API request fails
        """
        url = f"{self.config.base_url}/databases"
        
        payload = {
            "parent": {"page_id": page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties
        }
        
        return self._make_request("POST", url, json_data=payload)
    
    def create_page(self, database_id: str, properties: Dict[str, Any], 
                icon: Optional[Dict[str, Any]] = None,
                cover: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Creates a new page in a database.
        
        Args:
            database_id: Database ID
            properties: Page properties
            icon: Optional icon configuration
            cover: Optional cover configuration
            
        Returns:
            Created page object
            
        Raises:
            NotionApiError: If API request fails
        """
        url = f"{self.config.base_url}/pages"
        
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        
        # Add icon if provided
        if icon:
            payload["icon"] = icon
        
        # Add cover if provided
        if cover:
            payload["cover"] = cover
        
        return self._make_request("POST", url, json_data=payload)
    
    def append_blocks_to_page(self, page_id: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Appends blocks to a page.

        Args:
            page_id: Page ID
            blocks: List of block objects

        Returns:
            Response from the API

        Raises:
            NotionApiError: If API request fails
        """
        url = f"{self.config.base_url}/blocks/{page_id}/children"

        payload = {
            "children": blocks
        }
    
        return self._make_request("PATCH", url, json_data=payload)
    
    def get_users(self) -> List[Dict[str, Any]]:
        """
        Gets a list of users.
        
        Returns:
            List of user objects
            
        Raises:
            NotionApiError: If API request fails
        """
        url = f"{self.config.base_url}/users"
        response = self._make_request("GET", url)
        return response.get("results", [])
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Gets a page by ID.
        
        Args:
            page_id: Page ID
            
        Returns:
            Page object
            
        Raises:
            NotionApiError: If API request fails
        """
        url = f"{self.config.base_url}/pages/{page_id}"
        return self._make_request("GET", url)
    
    def _make_request(
        self, 
        method: str, 
        url: str, 
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Makes an HTTP request to the Notion API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            json_data: JSON data for request body
            retry_count: Current retry attempt
            
        Returns:
            Response data as dictionary
            
        Raises:
            NotionApiError: If request fails
        """
        try:
            self.logger.debug(f"Making {method} request to {url}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=json_data,
                timeout=self.config.timeout
            )
            
            # Handle rate limiting
            if response.status_code == 429 and retry_count < self.config.max_retries:
                retry_after = int(response.headers.get('Retry-After', 1))
                self.logger.warning(f"Rate limited. Retrying after {retry_after} seconds")
                time.sleep(retry_after)
                return self._make_request(method, url, json_data, retry_count + 1)
            
            # Handle other errors
            if response.status_code >= 400:
                error_msg = f"Notion API error: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg = f"{error_msg} - {error_data.get('message', 'Unknown error')}"
                    except json.JSONDecodeError:
                        error_msg = f"{error_msg} - {response.text}"
                
                self.logger.error(error_msg)
                raise NotionApiError(error_msg, response.status_code, response.text)
            
            return response.json()
            
        except requests.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            self.logger.error(error_msg)
            raise NotionApiError(error_msg) from e