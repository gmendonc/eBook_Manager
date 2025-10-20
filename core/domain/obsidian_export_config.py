# core/domain/obsidian_export_config.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ObsidianExportConfig:
    """Configuration for Obsidian export."""

    # Required settings
    vault_path: str
    """Path to the Obsidian vault directory"""

    notes_folder: str = "Books"
    """Folder within the vault where notes will be created"""

    # Template settings
    template_path: Optional[str] = None
    """Path to custom template file. If None, uses default template"""

    # File naming
    filename_pattern: str = "{title} - {author}"
    """Pattern for generating note filenames. Available placeholders: {title}, {author}, {publisher}, {isbn}"""

    # Default field values (for template placeholders)
    default_status: str = "unread"
    """Default reading status"""

    default_priority: str = "medium"
    """Default priority level"""

    default_device: str = "computer"
    """Default reading device"""

    default_purpose: list = field(default_factory=lambda: ["read", "reference"])
    """Default purpose tags"""

    # Export options
    overwrite_existing: bool = False
    """Whether to overwrite existing notes or skip them"""

    use_mcp_tools: bool = True
    """Whether to use MCP tools (if available) or direct filesystem"""

    # Technical settings
    max_filename_length: int = 200
    """Maximum length for generated filenames"""

    chunk_description: bool = True
    """Whether to split long descriptions into multiple paragraphs"""

    description_chunk_size: int = 1900
    """Maximum size of each description chunk"""

    def __post_init__(self):
        """Validates configuration after initialization."""
        if not self.vault_path:
            raise ValueError("vault_path is required")

        if not self.notes_folder:
            raise ValueError("notes_folder is required")

        if self.max_filename_length < 50:
            raise ValueError("max_filename_length must be at least 50 characters")
