# core/domain/notion_property_map.py
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class NotionPropertyDefinition:
    """Definition of a Notion property."""
    name: str  # Property name in Notion
    type: str  # Property type in Notion (title, rich_text, select, etc.)
    options: Optional[List[Dict[str, Any]]] = None  # For select/multi_select properties
    
    def to_api_format(self) -> Dict[str, Any]:
        """Converts to Notion API format for database creation."""
        result = {self.type: {}}
        
        if self.options and self.type in ('select', 'multi_select'):
            result[self.type]['options'] = self.options
            
        return result

@dataclass
class NotionPropertyMap:
    """Mapping between CSV data and Notion properties."""
    property_name: str  # Notion property name
    csv_columns: List[str]  # Ordered list of CSV columns to try (priority order)
    default_value: Any = None  # Default value if no CSV column has data
    formatter: Optional[str] = None  # Name of formatter to use
    
    def get_value_from_record(self, record: Dict[str, Any]) -> Any:
        """
        Gets value from record based on priority order of CSV columns.
        
        Args:
            record: Dictionary containing record data
            
        Returns:
            The first non-empty value found or default_value
        """
        for column in self.csv_columns:
            if column in record and record[column]:
                return record[column]
        return self.default_value