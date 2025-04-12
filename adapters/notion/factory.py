# adapters/notion/factory.py
from typing import Dict, Any, Optional

from core.domain.notion_export_config import NotionExportConfig
from core.interfaces.notion_api_client import NotionApiClient
from core.interfaces.notion_database_verifier import NotionDatabaseVerifier
from core.interfaces.notion_database_creator import NotionDatabaseCreator
from core.interfaces.notion_record_mapper import NotionRecordMapper
from core.interfaces.exporter import Exporter

from core.services.notion_export_service import NotionExportService

from adapters.notion.api_client import HttpNotionApiClient
from adapters.notion.database_verifier import DefaultNotionDatabaseVerifier
from adapters.notion.database_creator import DefaultNotionDatabaseCreator
from adapters.notion.record_mapper import GoogleBooksNotionRecordMapper
from adapters.notion.exporter import NotionExporter

class NotionExporterFactory:
    """Factory for creating NotionExporter instances with all dependencies."""
    
    @staticmethod
    def create_exporter(config_dict: Dict[str, Any]) -> Exporter:
        """
        Creates a NotionExporter with all required components.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Configured NotionExporter instance
        """
        # Create configuration
        config = NotionExporterFactory._create_config(config_dict)
        
        # Create API client
        api_client = HttpNotionApiClient(config)
        
        # Create database verifier
        db_verifier = DefaultNotionDatabaseVerifier(api_client)
        
        # Create database creator
        db_creator = DefaultNotionDatabaseCreator(api_client, db_verifier)
        
        # Create record mapper
        record_mapper = GoogleBooksNotionRecordMapper()
        
        # Create export service
        export_service = NotionExportService(
            api_client,
            db_verifier,
            db_creator,
            record_mapper,
            config
        )
        
        # Create exporter
        return NotionExporter(export_service)
    
    @staticmethod
    def _create_config(config_dict: Dict[str, Any]) -> NotionExportConfig:
        """
        Creates a NotionExportConfig from a dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            NotionExportConfig instance
        """
        return NotionExportConfig(
            token=config_dict.get("token", ""),
            database_id=config_dict.get("database_id"),
            page_id=config_dict.get("page_id"),
            database_name=config_dict.get("database_name", "Biblioteca de Ebooks"),
            create_database_if_not_exists=config_dict.get("create_database_if_not_exists", False)
        )