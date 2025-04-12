# adapters/notion/exporter.py
import logging
from typing import Dict, Any, Optional

from core.interfaces.exporter import Exporter
from core.services.notion_export_service import NotionExportService, NotionExportError

class NotionExporter(Exporter):
    """Implementation of Exporter for Notion."""
    
    def __init__(self, export_service: NotionExportService):
        """
        Initializes the exporter.
        
        Args:
            export_service: Notion export service
        """
        self.export_service = export_service
        self.logger = logging.getLogger(__name__)
    
    def export(self, csv_path: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Exports data from a CSV file to Notion.
        
        Args:
            csv_path: Path to CSV file
            config: Additional configuration (optional)
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            # Update configuration if provided
            if config:
                self._update_config(config)
            
            # Perform the export
            success, success_count, error_count, error_messages = self.export_service.export_csv_to_notion(csv_path)
            
            # Log results
            if success:
                self.logger.info(f"Exported {success_count} records to Notion ({error_count} errors)")
                
                if error_count > 0:
                    for error in error_messages[:5]:  # Log the first 5 errors
                        self.logger.warning(error)
                    
                    if len(error_messages) > 5:
                        self.logger.warning(f"...and {len(error_messages) - 5} more errors")
            else:
                self.logger.error(f"Failed to export to Notion: {success_count} succeeded, {error_count} failed")
                for error in error_messages:
                    self.logger.error(error)
            
            return success
            
        except NotionExportError as e:
            self.logger.error(f"Export error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during export: {str(e)}")
            return False
    
    def _update_config(self, config: Dict[str, Any]) -> None:
        """
        Updates the export service configuration.
        
        Args:
            config: New configuration values
        """
        # Update token if provided
        if "token" in config and config["token"]:
            self.export_service.config.token = config["token"]
            # Also update API client headers
            self.export_service.api_client.headers["Authorization"] = f"Bearer {config['token']}"
        
        # Update database ID if provided
        if "database_id" in config:
            self.export_service.config.database_id = config["database_id"]
        
        # Update page ID if provided
        if "page_id" in config:
            self.export_service.config.page_id = config["page_id"]
        
        # Update database name if provided
        if "database_name" in config:
            self.export_service.config.database_name = config["database_name"]
        
        # Update database creation flag if provided
        if "create_database_if_not_exists" in config:
            self.export_service.config.create_database_if_not_exists = config["create_database_if_not_exists"]