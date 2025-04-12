# core/services/notion_export_service.py
import logging
import csv
from typing import Dict, Any, Optional, List, Tuple

from core.domain.notion_export_config import NotionExportConfig
from core.interfaces.notion_api_client import NotionApiClient
from core.interfaces.notion_database_verifier import NotionDatabaseVerifier
from core.interfaces.notion_database_creator import NotionDatabaseCreator
from core.interfaces.notion_record_mapper import NotionRecordMapper

class NotionExportError(Exception):
    """Exception raised for errors during Notion export."""
    pass

class NotionExportService:
    """Service for exporting data to Notion."""
    
    def __init__(
        self,
        api_client: NotionApiClient,
        db_verifier: NotionDatabaseVerifier,
        db_creator: NotionDatabaseCreator,
        record_mapper: NotionRecordMapper,
        config: NotionExportConfig
    ):
        """
        Initializes the export service.
        
        Args:
            api_client: Notion API client
            db_verifier: Database structure verifier
            db_creator: Database creator
            record_mapper: Record to properties mapper
            config: Export configuration
        """
        self.api_client = api_client
        self.db_verifier = db_verifier
        self.db_creator = db_creator
        self.record_mapper = record_mapper
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def export_csv_to_notion(self, csv_path: str) -> Tuple[bool, int, int, List[str]]:
        """
        Exports data from a CSV file to Notion.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Tuple of (success, success_count, error_count, error_messages)
            
        Raises:
            NotionExportError: If export fails
        """
        # Ensure we have a database ID
        database_id = self._ensure_database_exists()
        if not database_id:
            raise NotionExportError("Failed to get or create a valid database")
        
        # Process the CSV file
        try:
            success_count = 0
            error_count = 0
            error_messages = []
            
            # Read CSV and count rows
            total_rows = sum(1 for _ in open(csv_path, 'r', encoding='utf-8')) - 1  # -1 for header
            self.logger.info(f"Starting export of {total_rows} records from {csv_path}")
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for i, record in enumerate(reader):
                    try:
                        # Map record to Notion properties
                        properties = self.record_mapper.map_to_notion_properties(record)
                        
                        # Create page in Notion
                        self.api_client.create_page(database_id, properties)
                        success_count += 1
                        
                        # Log progress
                        if i % 10 == 0 or i == total_rows - 1:
                            self.logger.info(f"Progress: {i+1}/{total_rows} records processed")
                            
                    except Exception as e:
                        error_count += 1
                        error_msg = f"Error exporting record {i+1}: {str(e)}"
                        error_messages.append(error_msg)
                        self.logger.error(error_msg)
                        
                        # Only store up to 10 error messages to avoid excessive memory usage
                        if len(error_messages) > 10:
                            error_messages.append("Additional errors omitted...")
                            break
            
            self.logger.info(f"Export completed: {success_count} succeeded, {error_count} failed")
            return success_count > 0, success_count, error_count, error_messages
            
        except Exception as e:
            error_msg = f"Failed to export CSV to Notion: {str(e)}"
            self.logger.error(error_msg)
            raise NotionExportError(error_msg) from e
    
    def _ensure_database_exists(self) -> Optional[str]:
        """
        Ensures a valid database exists, creating one if necessary.
        
        Returns:
            Database ID if available/created, None otherwise
        """
        # If we have a database ID, verify it
        if self.config.database_id:
            is_valid, missing_props, db_info = self.db_verifier.verify_database(self.config.database_id)
            
            if is_valid:
                self.logger.info(f"Using existing database: {self.config.database_id}")
                return self.config.database_id
            elif not is_valid and not self.config.create_database_if_not_exists:
                self.logger.error(f"Database {self.config.database_id} is invalid. Missing properties: {missing_props}")
                return None
        
        # If we need to create a database, we need a page ID
        if self.config.create_database_if_not_exists and self.config.page_id:
            self.logger.info(f"Creating new database in page {self.config.page_id}")
            database_id = self.db_creator.create_database(
                self.config.page_id, 
                self.config.database_name
            )
            
            if database_id:
                self.logger.info(f"Created new database: {database_id}")
                return database_id
            else:
                self.logger.error("Failed to create new database")
                return None
        
        self.logger.error("No valid database ID and no page ID to create a new database")
        return None
