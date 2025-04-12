# core/interfaces/notion_database_creator.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class NotionDatabaseCreator(ABC):
    """Interface for creating Notion databases."""
    
    @abstractmethod
    def create_database(self, page_id: str, title: str) -> Optional[str]:
        """
        Creates a new database with the expected structure.
        
        Args:
            page_id: Page ID where to create database
            title: Database title
            
        Returns:
            Database ID if created successfully, None otherwise
            
        Raises:
            NotionApiError: If API request fails
        """
        pass