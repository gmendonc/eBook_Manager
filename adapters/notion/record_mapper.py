# adapters/notion/record_mapper.py
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.interfaces.notion_record_mapper import NotionRecordMapper

class GoogleBooksNotionRecordMapper(NotionRecordMapper):
    """
    Implementation of NotionRecordMapper that prioritizes Google Books data.
    """
    
    def __init__(self):
        """Initializes the mapper."""
        self.logger = logging.getLogger(__name__)
    
    def map_to_notion_properties(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps a record to Notion properties, prioritizing Google Books data.
        
        Args:
            record: Record data from CSV
            
        Returns:
            Dictionary of Notion properties
        """
        properties = {}
        
        # Title (GB_Titulo > Titulo_Extraido > Nome)
        title = self._get_value_by_priority(record, ["GB_Titulo", "Titulo_Extraido", "Nome"], "")
        if title and isinstance(title, str) and "." in title and not any(substring in title for substring in ["Mr.", "Dr.", "Ph.D"]):
            # Try to extract title from filename if it looks like a filename
            title = title.split('.')[0]
            
        properties["Title"] = self._format_title_property(title)
        
        # Author (GB_Autores > Autor_Extraido > "Unknown")
        author = self._get_value_by_priority(record, ["GB_Autores", "Autor_Extraido"], "Unknown")
        properties["Author"] = self._format_text_property(author)
        
        # Format
        format_value = record.get("Formato", "Unknown")
        properties["Format"] = self._format_select_property(format_value)
        
        # Size
        if "Tamanho(MB)" in record:
            try:
                size = float(record["Tamanho(MB)"])
                properties["Size (MB)"] = self._format_number_property(size)
            except (ValueError, TypeError):
                pass
        
        # Modified Date
        if "Data Modificação" in record:
            try:
                date_str = record["Data Modificação"]
                date_obj = self._parse_date(date_str)
                if date_obj:
                    properties["Modified Date"] = self._format_date_property(date_obj)
            except Exception as e:
                self.logger.warning(f"Error parsing date: {str(e)}")
        
        # Path
        path = record.get("Caminho", "")
        if path:
            if not path.startswith(("http://", "https://", "file://")):
                path = f"file://{path}"
            properties["Path"] = self._format_url_property(path)
        
        # Reading Status - Default to "Unread"
        properties["Reading Status"] = self._format_select_property("Unread")
        
        # Publisher (GB_Editora > "Unknown")
        publisher = self._get_value_by_priority(record, ["GB_Editora"], "")
        if publisher:
            properties["Publisher"] = self._format_text_property(publisher)
        
        # Publication Date (GB_Data_Publicacao)
        pub_date = self._get_value_by_priority(record, ["GB_Data_Publicacao"], "")
        if pub_date:
            properties["Publication Date"] = self._format_text_property(pub_date)
        
        # ISBN (GB_ISBN13 > GB_ISBN10)
        isbn = self._get_value_by_priority(record, ["GB_ISBN13", "GB_ISBN10"], "")
        if isbn:
            properties["ISBN"] = self._format_text_property(isbn)
        
        # Topics (Temas_Sugeridos > GB_Categorias)
        topics = self._get_topics(record)
        if topics:
            properties["Topics"] = self._format_multi_select_property(topics)
        
        return properties
    
    def get_property_maps(self) -> List[Dict[str, Any]]:
        """
        Gets the property mappings used by this mapper.
        
        Returns:
            List of property mapping definitions
        """
        return [
            {"notion_property": "Title", "csv_columns": ["GB_Titulo", "Titulo_Extraido", "Nome"]},
            {"notion_property": "Author", "csv_columns": ["GB_Autores", "Autor_Extraido"]},
            {"notion_property": "Format", "csv_columns": ["Formato"]},
            {"notion_property": "Size (MB)", "csv_columns": ["Tamanho(MB)"]},
            {"notion_property": "Modified Date", "csv_columns": ["Data Modificação"]},
            {"notion_property": "Path", "csv_columns": ["Caminho"]},
            {"notion_property": "Publisher", "csv_columns": ["GB_Editora"]},
            {"notion_property": "Publication Date", "csv_columns": ["GB_Data_Publicacao"]},
            {"notion_property": "ISBN", "csv_columns": ["GB_ISBN13", "GB_ISBN10"]},
            {"notion_property": "Topics", "csv_columns": ["Temas_Sugeridos", "GB_Categorias"]}
        ]
    
    def _get_value_by_priority(self, record: Dict[str, Any], keys: List[str], default: Any = "") -> Any:
        """Gets the first non-empty value from the list of keys."""
        for key in keys:
            if key in record and record[key]:
                return record[key]
        return default
    
    def _get_topics(self, record: Dict[str, Any]) -> List[str]:
        """Extracts topics from the record."""
        topics = []
        
        # Try Temas_Sugeridos first
        if "Temas_Sugeridos" in record and record["Temas_Sugeridos"]:
            topics_str = record["Temas_Sugeridos"]
            topics.extend(self._split_topics(topics_str))
        
        # Then try GB_Categorias
        elif "GB_Categorias" in record and record["GB_Categorias"]:
            topics_str = record["GB_Categorias"]
            topics.extend(self._split_topics(topics_str))
        
        # Deduplicate and return
        return list(set(topics))
    
    def _split_topics(self, topics_str: str) -> List[str]:
        """Splits a comma/semicolon-separated string into a list of topics."""
        topics = []
        for topic in re.split(r'[,;]', topics_str):
            topic = topic.strip()
            if topic:
                topics.append(topic)
        return topics
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parses a date string into a datetime object."""
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    # Notion property formatters
    def _format_title_property(self, value: str) -> Dict[str, Any]:
        return {"title": [{"type": "text", "text": {"content": value}}]}
    
    def _format_text_property(self, value: str) -> Dict[str, Any]:
        return {"rich_text": [{"type": "text", "text": {"content": str(value)}}]}
    
    def _format_select_property(self, value: str) -> Dict[str, Any]:
        return {"select": {"name": value}}
    
    def _format_multi_select_property(self, values: List[str]) -> Dict[str, Any]:
        return {"multi_select": [{"name": value} for value in values]}
    
    def _format_number_property(self, value: float) -> Dict[str, Any]:
        return {"number": value}
    
    def _format_date_property(self, value: datetime) -> Dict[str, Any]:
        return {"date": {"start": value.isoformat()}}
    
    def _format_url_property(self, value: str) -> Dict[str, Any]:
        return {"url": value}