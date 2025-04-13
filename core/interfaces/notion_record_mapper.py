# core/interfaces/notion_record_mapper.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional

class NotionRecordMapper(ABC):
    """Interface for mapping records to Notion properties."""
    
    @abstractmethod
    def map_to_notion_properties(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps a record to Notion properties.
        
        Args:
            record: Record data from CSV
            
        Returns:
            Dictionary of Notion properties
        """
        pass
    
    @abstractmethod
    def get_property_maps(self) -> List[Dict[str, Any]]:
        """
        Gets the property mappings used by this mapper.
        
        Returns:
            List of property mapping definitions
        """
        pass

    @abstractmethod
    def map_to_notion_properties_and_icon(self, record: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Maps a record to Notion properties and icon.
        
        Args:
            record: Record data from CSV
            
        Returns:
            Tuple of (properties, icon)
        """
        pass
        
    @abstractmethod
    def create_page_content_blocks(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Creates content blocks for a Notion page.
        
        Args:
            record: Record data from CSV
            
        Returns:
            List of block objects
        """
        pass
