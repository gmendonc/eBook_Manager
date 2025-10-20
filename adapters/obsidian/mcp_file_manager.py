# adapters/obsidian/mcp_file_manager.py
import logging
from typing import Optional

from core.interfaces.obsidian_file_manager import ObsidianFileManager
from core.exceptions import ObsidianFileError
from adapters.obsidian.filesystem_file_manager import FilesystemFileManager


class McpFileManager:
    """
    Implementation of ObsidianFileManager using MCP tools.

    This implementation attempts to use Obsidian MCP tools when available,
    falling back to FilesystemFileManager if MCP tools are unavailable or fail.

    MCP Tools Used:
    - obsidian-mcp-tools:create_vault_file - Create/update files
    - obsidian-mcp-tools:get_vault_file - Read files
    - obsidian-mcp-tools:list_vault_files - List files (for existence check)
    """

    def __init__(self, vault_path: str):
        """
        Initialize the MCP file manager with filesystem fallback.

        Args:
            vault_path: Absolute path to the Obsidian vault directory
        """
        self.vault_path = vault_path
        self.logger = logging.getLogger(__name__)

        # Create filesystem fallback
        self.fallback = FilesystemFileManager(vault_path)

        # Check if MCP tools are available
        self.mcp_available = self._check_mcp_availability()

        if self.mcp_available:
            self.logger.info("MCP tools detected and available")
        else:
            self.logger.warning("MCP tools not available, using filesystem fallback")

    def create_note(self, folder: str, filename: str, content: str) -> bool:
        """
        Create a new note using MCP tools or fallback.

        Args:
            folder: Folder path relative to vault root
            filename: Note filename including .md extension
            content: Markdown content

        Returns:
            True if successful

        Raises:
            ObsidianFileError: If file creation fails
        """
        if not self.mcp_available:
            return self.fallback.create_note(folder, filename, content)

        try:
            # Use MCP tool to create file
            vault_path = f"{folder}/{filename}"
            self._mcp_create_vault_file(vault_path, content)

            self.logger.debug(f"Created note via MCP: {vault_path}")
            return True

        except Exception as e:
            self.logger.warning(f"MCP create failed, using fallback: {str(e)}")
            return self.fallback.create_note(folder, filename, content)

    def update_note(self, folder: str, filename: str, content: str) -> bool:
        """
        Update an existing note using MCP tools or fallback.

        Args:
            folder: Folder path relative to vault root
            filename: Note filename including .md extension
            content: New markdown content

        Returns:
            True if successful

        Raises:
            ObsidianFileError: If file update fails
        """
        # MCP's create_vault_file can also update existing files
        return self.create_note(folder, filename, content)

    def note_exists(self, folder: str, filename: str) -> bool:
        """
        Check if a note exists using MCP tools or fallback.

        Args:
            folder: Folder path relative to vault root
            filename: Note filename including .md extension

        Returns:
            True if note exists, False otherwise
        """
        if not self.mcp_available:
            return self.fallback.note_exists(folder, filename)

        try:
            vault_path = f"{folder}/{filename}"
            # Try to get the file; if it exists, this will succeed
            content = self._mcp_get_vault_file(vault_path)
            return content is not None

        except Exception:
            # If MCP fails, fall back to filesystem check
            return self.fallback.note_exists(folder, filename)

    def get_note_content(self, folder: str, filename: str) -> Optional[str]:
        """
        Get note content using MCP tools or fallback.

        Args:
            folder: Folder path relative to vault root
            filename: Note filename including .md extension

        Returns:
            Note content or None if note doesn't exist

        Raises:
            ObsidianFileError: If file reading fails
        """
        if not self.mcp_available:
            return self.fallback.get_note_content(folder, filename)

        try:
            vault_path = f"{folder}/{filename}"
            content = self._mcp_get_vault_file(vault_path)

            if content:
                self.logger.debug(f"Read note via MCP: {vault_path} ({len(content)} chars)")

            return content

        except Exception as e:
            self.logger.warning(f"MCP get failed, using fallback: {str(e)}")
            return self.fallback.get_note_content(folder, filename)

    def ensure_folder_exists(self, folder: str) -> bool:
        """
        Ensure folder exists (uses fallback as MCP doesn't require explicit folder creation).

        Args:
            folder: Folder path relative to vault root

        Returns:
            True if folder exists or was created

        Raises:
            ObsidianFileError: If folder creation fails
        """
        # MCP tools automatically create folders when creating files
        # But we still use fallback to ensure folder exists upfront
        return self.fallback.ensure_folder_exists(folder)

    def _check_mcp_availability(self) -> bool:
        """
        Check if MCP tools are available in the environment.

        Returns:
            True if MCP tools are available, False otherwise
        """
        try:
            # Try to import the MCP tool function (if integrated in environment)
            # This is a placeholder - actual implementation depends on MCP integration
            # For now, we'll return False and rely on filesystem fallback
            return False

        except Exception:
            return False

    def _mcp_create_vault_file(self, vault_path: str, content: str):
        """
        Create or update a file using MCP tools.

        Args:
            vault_path: Path relative to vault root (e.g., "Books/BookTitle.md")
            content: File content

        Raises:
            Exception: If MCP tool call fails
        """
        # Placeholder for actual MCP tool call
        # In real implementation, this would call:
        # mcp_tools.obsidian.create_vault_file(vault_path=vault_path, content=content)
        raise NotImplementedError("MCP tools not yet integrated")

    def _mcp_get_vault_file(self, vault_path: str) -> Optional[str]:
        """
        Get file content using MCP tools.

        Args:
            vault_path: Path relative to vault root

        Returns:
            File content or None if file doesn't exist

        Raises:
            Exception: If MCP tool call fails
        """
        # Placeholder for actual MCP tool call
        # In real implementation, this would call:
        # return mcp_tools.obsidian.get_vault_file(vault_path=vault_path)
        raise NotImplementedError("MCP tools not yet integrated")
