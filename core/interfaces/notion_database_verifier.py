# core/interfaces/notion_database_verifier.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List

class NotionDatabaseVerifier(ABC):
    """Interface for verifying Notion database structure."""
    
    @abstractmethod
    def verify_database(self, database_id: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Verifies if a database exists and has the expected structure.
        
        Args:
            database_id: Database ID
            
        Returns:
            Tuple of (is_valid, missing_properties, database_info)
            
        Raises:
            NotionApiError: If API request fails
        """
        pass
    
    @abstractmethod
    def get_expected_properties(self) -> Dict[str, Dict[str, Any]]:
        """
        Gets the expected properties for a database.
        
        Returns:
            Dictionary of property definitions
        """
        pass