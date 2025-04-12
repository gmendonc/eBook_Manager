# core/domain/notion_export_config.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class NotionExportConfig:
    """Configuration for Notion export."""
    token: str
    database_id: Optional[str] = None
    page_id: Optional[str] = None
    database_name: str = "Biblioteca de Ebooks"
    create_database_if_not_exists: bool = False
    
    # Additional API parameters
    api_version: str = "2022-06-28"
    base_url: str = "https://api.notion.com/v1"
    
    # Request configurations
    timeout: int = 30
    max_retries: int = 3
    
    # Additional options
    batch_size: int = 10
    retry_on_error: bool = True