# core/interfaces/obsidian_record_mapper.py
from typing import Protocol, Dict, Any

from core.domain.obsidian_export_config import ObsidianExportConfig


class ObsidianRecordMapper(Protocol):
    """
    Interface for mapping CSV records to template data.

    This interface defines the contract for transforming raw CSV data
    into a format suitable for template rendering. Implementations should:
    - Prioritize enriched data (GB_*) over extracted data
    - Provide sensible defaults for missing fields
    - Handle date formatting consistently
    - Sanitize data for Markdown output

    Field Priority:
    - Google Books fields (GB_*) are highest priority
    - Extracted fields (Titulo_Extraido, Autor_Extraido) are second
    - File metadata fields (Nome, Formato, etc.) are third
    - Config defaults are fallback for user-configurable fields
    """

    def map_record(self, record: Dict[str, Any], config: ObsidianExportConfig) -> Dict[str, Any]:
        """
        Map a CSV record to template placeholder data.

        Args:
            record: Dictionary containing CSV row data with keys like:
                   - Basic: Nome, Formato, Tamanho(MB), Data Modificação, Caminho
                   - Extracted: Titulo_Extraido, Autor_Extraido
                   - Google Books: GB_Titulo, GB_Autores, GB_Editora, etc.
            config: Export configuration with default values

        Returns:
            Dictionary mapping template placeholders to string values.
            All values should be strings suitable for template rendering.

        Example:
            >>> mapper.map_record(
            ...     {"GB_Titulo": "Clean Code", "GB_Autores": "Robert C. Martin"},
            ...     config
            ... )
            {
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "publisher": "",
                "status": "unread",
                ...
            }
        """
        ...

    def sanitize_filename(self, filename: str, max_length: int) -> str:
        """
        Sanitize a filename for filesystem compatibility.

        This method should:
        - Remove invalid characters: : / \\ * ? " < > |
        - Collapse multiple spaces to single space
        - Strip leading/trailing whitespace
        - Truncate to max_length (preserving extension)
        - Handle Unicode characters appropriately

        Args:
            filename: Original filename (may include .md extension)
            max_length: Maximum allowed length

        Returns:
            Sanitized filename safe for filesystem use

        Example:
            >>> mapper.sanitize_filename("Book: Title/Name?.md", 50)
            "Book Title Name.md"
        """
        ...

    def generate_filename(self, record: Dict[str, Any], pattern: str, max_length: int) -> str:
        """
        Generate a filename from a pattern and record data.

        Supported placeholders in pattern:
        - {title}: Book title
        - {author}: Book author
        - {publisher}: Publisher name
        - {isbn}: ISBN (prefers ISBN13, falls back to ISBN10)
        - {format}: File format

        Args:
            record: CSV record data
            pattern: Filename pattern with {placeholder} syntax
            max_length: Maximum allowed filename length

        Returns:
            Sanitized filename with .md extension

        Example:
            >>> mapper.generate_filename(
            ...     {"GB_Titulo": "Clean Code", "GB_Autores": "Robert Martin"},
            ...     "{title} - {author}",
            ...     200
            ... )
            "Clean Code - Robert Martin.md"
        """
        ...
