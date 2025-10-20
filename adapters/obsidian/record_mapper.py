# adapters/obsidian/record_mapper.py
import logging
import re
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from core.interfaces.obsidian_record_mapper import ObsidianRecordMapper
from core.domain.obsidian_export_config import ObsidianExportConfig


class GoogleBooksObsidianRecordMapper:
    """
    Implementation of ObsidianRecordMapper that prioritizes Google Books enriched data.

    Field Priority:
    1. Google Books fields (GB_*)
    2. Extracted fields (Titulo_Extraido, Autor_Extraido)
    3. Basic file metadata (Nome, Formato, etc.)
    4. Config defaults for user-configurable fields
    """

    def __init__(self):
        """Initialize the record mapper."""
        self.logger = logging.getLogger(__name__)

    def map_record(self, record: Dict[str, Any], config: ObsidianExportConfig) -> Dict[str, Any]:
        """
        Map a CSV record to template placeholder data.

        Args:
            record: CSV row data
            config: Export configuration

        Returns:
            Dictionary mapping placeholders to values
        """
        self.logger.debug(f"Mapping record with {len(record)} fields")

        # Current timestamp for created/updated
        now = datetime.now()

        # Build template data dictionary
        data = {
            # Book metadata (with priority fallback)
            "title": self._get_title(record),
            "author": self._get_author(record),
            "publisher": self._get_field(record, ["GB_Editora"], ""),
            "publishDate": self._get_field(record, ["GB_Data_Publicacao"], ""),
            "totalPage": self._get_field(record, ["GB_Paginas"], ""),
            "isbn10": self._get_field(record, ["GB_ISBN10"], ""),
            "isbn13": self._get_field(record, ["GB_ISBN13"], ""),
            "coverUrl": self._get_field(record, ["GB_Capa_Link"], ""),
            "description": self._get_field(record, ["GB_Descricao"], ""),
            "categories": self._get_field(record, ["GB_Categorias"], ""),
            "topics": self._format_topics_list(self._get_topics(record)),
            "language": self._get_field(record, ["GB_Idioma"], ""),
            "preview_link": self._get_field(record, ["GB_Preview_Link"], ""),

            # File metadata
            "format": self._get_format(record),
            "file_size": self._get_field(record, ["Tamanho(MB)"], ""),
            "file_path": self._get_field(record, ["Caminho"], ""),
            "modified_date": self._get_field(record, ["Data Modificação"], ""),

            # Date fields (current timestamp)
            "created": now.strftime("%Y-%m-%d %H:%M:%S"),
            "updated": now.strftime("%Y-%m-%d %H:%M:%S"),

            # User-configurable defaults from config
            "status": config.default_status,
            "priority": config.default_priority,
            "device": config.default_device,
            "purpose": self._format_purpose_list(config.default_purpose),
        }

        self.logger.debug(f"Mapped to {len(data)} template fields")
        return data

    def sanitize_filename(self, filename: str, max_length: int) -> str:
        """
        Sanitize a filename for filesystem compatibility.

        Args:
            filename: Original filename
            max_length: Maximum allowed length

        Returns:
            Sanitized filename
        """
        # Remove .md extension temporarily if present
        has_md_ext = filename.endswith('.md')
        if has_md_ext:
            filename = filename[:-3]

        # Remove invalid characters for Windows/Unix filesystems
        invalid_chars = r'[:<>/\\|*?""]'
        sanitized = re.sub(invalid_chars, '', filename)

        # Collapse multiple spaces to single space
        sanitized = re.sub(r'\s+', ' ', sanitized)

        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()

        # If empty after sanitization, use default
        if not sanitized:
            sanitized = "untitled"

        # Truncate to max length (leaving room for .md extension)
        max_base_length = max_length - 3  # Reserve 3 chars for .md
        if len(sanitized) > max_base_length:
            sanitized = sanitized[:max_base_length].strip()

        # Add .md extension back
        sanitized += '.md'

        self.logger.debug(f"Sanitized filename: '{filename}' -> '{sanitized}'")
        return sanitized

    def generate_filename(self, record: Dict[str, Any], pattern: str, max_length: int) -> str:
        """
        Generate a filename from a pattern and record data.

        Args:
            record: CSV record data
            pattern: Filename pattern with {placeholder} syntax
            max_length: Maximum allowed filename length

        Returns:
            Sanitized filename with .md extension
        """
        # Get field values for placeholders
        placeholders = {
            "title": self._get_title(record),
            "author": self._get_author(record),
            "publisher": self._get_field(record, ["GB_Editora"], "Unknown"),
            "isbn": self._get_field(record, ["GB_ISBN13", "GB_ISBN10"], ""),
            "format": self._get_format(record),
        }

        # Replace placeholders in pattern
        filename = pattern
        for key, value in placeholders.items():
            placeholder = f"{{{key}}}"
            if placeholder in filename:
                # Use value or empty if not available
                filename = filename.replace(placeholder, str(value) if value else "")

        # Remove any remaining unreplaced placeholders
        filename = re.sub(r'\{[^}]+\}', '', filename)

        # Sanitize the result
        sanitized = self.sanitize_filename(filename, max_length)

        self.logger.debug(f"Generated filename from pattern '{pattern}': '{sanitized}'")
        return sanitized

    def _get_title(self, record: Dict[str, Any]) -> str:
        """Get book title with priority fallback."""
        title = self._get_field(record, ["GB_Titulo", "Titulo_Extraido"], "")

        # If no title, use filename without extension
        if not title:
            nome = record.get("Nome", "Untitled")
            title = Path(nome).stem  # Remove extension

        # Clean up title if it looks like a filename
        if '.' in title and not any(word in title for word in ["Dr.", "Mr.", "Ph.D"]):
            title = title.split('.')[0]

        return title.strip()

    def _get_author(self, record: Dict[str, Any]) -> str:
        """Get book author with priority fallback."""
        author = self._get_field(record, ["GB_Autores", "Autor_Extraido"], "Unknown Author")
        return author.strip()

    def _get_format(self, record: Dict[str, Any]) -> str:
        """Get file format in lowercase."""
        format_value = record.get("Formato", "unknown")
        return format_value.lower() if format_value else "unknown"

    def _get_field(self, record: Dict[str, Any], keys: list, default: Any = "") -> Any:
        """
        Get first non-empty value from list of keys.

        Args:
            record: Data record
            keys: List of keys to try in order
            default: Default value if all keys are empty

        Returns:
            First non-empty value or default
        """
        for key in keys:
            if key in record and record[key]:
                value = record[key]
                # Convert to string and strip whitespace
                if isinstance(value, str):
                    value = value.strip()
                    if value:
                        return value
                elif value:  # Non-string but truthy
                    return value

        return default

    def _format_purpose_list(self, purpose_list: list) -> str:
        """
        Format purpose list for template (comma-separated or as list).

        Args:
            purpose_list: List of purpose tags

        Returns:
            Formatted string
        """
        if not purpose_list:
            return "[]"

        # Return as list format for YAML: [item1, item2]
        return "[" + ", ".join(purpose_list) + "]"

    def _get_topics(self, record: Dict[str, Any]) -> List[str]:
        """
        Extract topics from the record.

        Tries Temas_Sugeridos first, then GB_Categorias.
        Splits comma/semicolon-separated strings into individual topics.

        Args:
            record: CSV record data

        Returns:
            List of unique topic strings
        """
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
        """
        Split a comma/semicolon-separated string into individual topics.

        Args:
            topics_str: String with topics separated by commas or semicolons

        Returns:
            List of cleaned topic strings
        """
        topics = []
        for topic in re.split(r'[,;]', topics_str):
            topic = topic.strip()
            if topic:
                topics.append(topic)
        return topics

    def _format_topics_list(self, topics: List[str]) -> str:
        """
        Format topics list for YAML frontmatter.

        Args:
            topics: List of topic strings

        Returns:
            Formatted string like [topic1, topic2, topic3]
        """
        if not topics:
            return "[]"

        # Return as list format for YAML: [item1, item2]
        return "[" + ", ".join(topics) + "]"
