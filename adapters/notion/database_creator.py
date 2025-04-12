# adapters/notion/database_creator.py
import logging
from typing import Dict, Any, Optional

from core.interfaces.notion_api_client import NotionApiClient
from core.interfaces.notion_database_creator import NotionDatabaseCreator
from core.interfaces.notion_database_verifier import NotionDatabaseVerifier

class DefaultNotionDatabaseCreator(NotionDatabaseCreator):
    """Implementation of NotionDatabaseCreator."""
    
    def __init__(self, api_client: NotionApiClient, db_verifier: NotionDatabaseVerifier):
        """
        Initializes the creator.
        
        Args:
            api_client: Notion API client
            db_verifier: Database structure verifier
        """
        self.api_client = api_client
        self.db_verifier = db_verifier
        self.logger = logging.getLogger(__name__)
    
    def create_database(self, page_id: str, title: str) -> Optional[str]:
        """
        Creates a new database with the expected structure.
        
        Args:
            page_id: Page ID where to create database
            title: Database title
            
        Returns:
            Database ID if created successfully, None otherwise
        """
        try:
            # Define properties using the expected structure from the verifier
            properties = {}
            expected_properties = self.db_verifier.get_expected_properties()
            
            # Convert to the API format
            for prop_name, prop_details in expected_properties.items():
                prop_type = prop_details.get("type")
                properties[prop_name] = {prop_type: {}}
                
                # Add options for select and multi_select properties
                if prop_type == "select":
                    if prop_name == "Reading Status":
                        properties[prop_name][prop_type]["options"] = [
                            {"name": "Unread", "color": "gray"},
                            {"name": "Reading", "color": "blue"},
                            {"name": "Read", "color": "green"},
                            {"name": "To Read", "color": "yellow"},
                            {"name": "Reference", "color": "purple"}
                        ]
                    elif prop_name == "Format":
                        properties[prop_name][prop_type]["options"] = [
                            {"name": "EPUB", "color": "blue"},
                            {"name": "PDF", "color": "red"},
                            {"name": "MOBI", "color": "green"},
                            {"name": "AZW3", "color": "orange"},
                            {"name": "TXT", "color": "gray"},
                            {"name": "Unknown", "color": "default"}
                        ]
            
            # Create the database
            database = self.api_client.create_database(page_id, title, properties)
            database_id = database.get("id")
            
            if database_id:
                self.logger.info(f"Created database {database_id} with title '{title}'")
                return database_id
            else:
                self.logger.error("Failed to create database: No ID in response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating database: {str(e)}")
            return None
