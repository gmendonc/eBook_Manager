# adapters/notion/database_verifier.py
import logging
from typing import Dict, Any, Tuple, List

from core.interfaces.notion_api_client import NotionApiClient
from core.interfaces.notion_database_verifier import NotionDatabaseVerifier

class DefaultNotionDatabaseVerifier(NotionDatabaseVerifier):
    """Implementation of NotionDatabaseVerifier."""
    
    def __init__(self, api_client: NotionApiClient):
        """
        Initializes the verifier.
        
        Args:
            api_client: Notion API client
        """
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
    
    def verify_database(self, database_id: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Verifies if a database exists and has the expected structure.
        
        Args:
            database_id: Database ID
            
        Returns:
            Tuple of (is_valid, missing_properties, database_info)
        """
        try:
            database = self.api_client.get_database(database_id)
            properties = database.get("properties", {})
            
            expected_properties = self.get_expected_properties()
            missing_properties = []
            
            for prop_name, prop_type in expected_properties.items():
                if prop_name not in properties:
                    missing_properties.append(prop_name)
                    continue
                
                actual_type = properties[prop_name].get("type")
                expected_type = prop_type.get("type")
                
                if actual_type != expected_type:
                    self.logger.warning(
                        f"Property '{prop_name}' has type '{actual_type}' instead of '{expected_type}'"
                    )
                    missing_properties.append(f"{prop_name} (wrong type: {actual_type})")
            
            is_valid = len(missing_properties) == 0
            
            if is_valid:
                self.logger.info(f"Database {database_id} has a valid structure")
            else:
                self.logger.warning(
                    f"Database {database_id} is missing {len(missing_properties)} properties: {missing_properties}"
                )
            
            return is_valid, missing_properties, database
            
        except Exception as e:
            self.logger.error(f"Error verifying database {database_id}: {str(e)}")
            return False, ["<Database not accessible>"], {}
    
    def get_expected_properties(self) -> Dict[str, Dict[str, Any]]:
        """
        Gets the expected properties for a database.
        
        Returns:
            Dictionary of property definitions
        """
        return {
            "Title": {"type": "title"},
            "Author": {"type": "rich_text"},
            "Format": {"type": "select"},
            "Size (MB)": {"type": "number"},
            "Modified Date": {"type": "date"},
            "Path": {"type": "url"},
            "Reading Status": {"type": "select"},
            "Topics": {"type": "multi_select"},
            "Publisher": {"type": "rich_text"},
            "Publication Date": {"type": "rich_text"},
            "ISBN": {"type": "rich_text"},
            "Notes": {"type": "rich_text"}
        }
