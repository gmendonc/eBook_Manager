# core/interfaces/notion_api_client.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class NotionApiClient(ABC):
    """Interface for Notion API client."""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def create_page(self, database_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new page in a database.
        
        Args:
            database_id: Database ID
            properties: Page properties
            
        Returns:
            Created page object
            
        Raises:
            NotionApiError: If API request fails
        """
        pass
    
    @abstractmethod
    def get_users(self) -> List[Dict[str, Any]]:
        """
        Gets a list of users.
        
        Returns:
            List of user objects
            
        Raises:
            NotionApiError: If API request fails
        """
        pass
    
    @abstractmethod
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
        pass
