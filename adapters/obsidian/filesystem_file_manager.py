# adapters/obsidian/filesystem_file_manager.py
import logging
from pathlib import Path
from typing import Optional

from core.interfaces.obsidian_file_manager import ObsidianFileManager
from core.exceptions import ObsidianFileError


class FilesystemFileManager:
    """
    Implementation of ObsidianFileManager using direct filesystem operations.

    This is the fallback implementation that works without any external tools.
    It uses Python's pathlib for cross-platform path handling and provides
    robust error handling for file operations.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the filesystem file manager.

        Args:
            vault_path: Absolute path to the Obsidian vault directory

        Raises:
            ObsidianFileError: If vault_path is invalid or doesn't exist
        """
        self.vault_path = Path(vault_path)
        self.logger = logging.getLogger(__name__)

        # Validate vault path
        if not self.vault_path.exists():
            error_msg = f"Vault path does not exist: {vault_path}"
            self.logger.error(error_msg)
            raise ObsidianFileError(error_msg)

        if not self.vault_path.is_dir():
            error_msg = f"Vault path is not a directory: {vault_path}"
            self.logger.error(error_msg)
            raise ObsidianFileError(error_msg)

        self.logger.info(f"Initialized FilesystemFileManager for vault: {vault_path}")

    def create_note(self, folder: str, filename: str, content: str) -> bool:
        """
        Create a new note in the vault.

        Args:
            folder: Folder path relative to vault root
            filename: Note filename including .md extension
            content: Markdown content

        Returns:
            True if successful

        Raises:
            ObsidianFileError: If file creation fails
        """
        try:
            # Ensure folder exists
            self.ensure_folder_exists(folder)

            # Build full path
            file_path = self.vault_path / folder / filename

            # Write file
            file_path.write_text(content, encoding='utf-8')

            self.logger.debug(f"Created note: {file_path}")
            return True

        except Exception as e:
            error_msg = f"Failed to create note '{filename}': {str(e)}"
            self.logger.error(error_msg)
            raise ObsidianFileError(error_msg) from e

    def update_note(self, folder: str, filename: str, content: str) -> bool:
        """
        Update an existing note.

        Args:
            folder: Folder path relative to vault root
            filename: Note filename including .md extension
            content: New markdown content

        Returns:
            True if successful

        Raises:
            ObsidianFileError: If file update fails
        """
        try:
            # Build full path
            file_path = self.vault_path / folder / filename

            # Check if file exists
            if not file_path.exists():
                error_msg = f"Note does not exist: {filename}"
                self.logger.warning(error_msg)
                raise ObsidianFileError(error_msg)

            # Write file (overwrite)
            file_path.write_text(content, encoding='utf-8')

            self.logger.debug(f"Updated note: {file_path}")
            return True

        except Exception as e:
            error_msg = f"Failed to update note '{filename}': {str(e)}"
            self.logger.error(error_msg)
            raise ObsidianFileError(error_msg) from e

    def note_exists(self, folder: str, filename: str) -> bool:
        """
        Check if a note exists.

        Args:
            folder: Folder path relative to vault root
            filename: Note filename including .md extension

        Returns:
            True if note exists, False otherwise
        """
        try:
            file_path = self.vault_path / folder / filename
            exists = file_path.exists() and file_path.is_file()

            self.logger.debug(f"Note exists check for '{filename}': {exists}")
            return exists

        except Exception as e:
            self.logger.warning(f"Error checking if note exists: {str(e)}")
            return False

    def get_note_content(self, folder: str, filename: str) -> Optional[str]:
        """
        Get the content of an existing note.

        Args:
            folder: Folder path relative to vault root
            filename: Note filename including .md extension

        Returns:
            Note content or None if note doesn't exist

        Raises:
            ObsidianFileError: If file reading fails
        """
        try:
            file_path = self.vault_path / folder / filename

            if not file_path.exists():
                self.logger.debug(f"Note not found: {filename}")
                return None

            content = file_path.read_text(encoding='utf-8')
            self.logger.debug(f"Read note: {filename} ({len(content)} chars)")
            return content

        except Exception as e:
            error_msg = f"Failed to read note '{filename}': {str(e)}"
            self.logger.error(error_msg)
            raise ObsidianFileError(error_msg) from e

    def ensure_folder_exists(self, folder: str) -> bool:
        """
        Ensure a folder exists in the vault, creating it if necessary.

        Args:
            folder: Folder path relative to vault root

        Returns:
            True if folder exists or was created

        Raises:
            ObsidianFileError: If folder creation fails
        """
        try:
            folder_path = self.vault_path / folder

            if folder_path.exists():
                if not folder_path.is_dir():
                    error_msg = f"Path exists but is not a directory: {folder}"
                    self.logger.error(error_msg)
                    raise ObsidianFileError(error_msg)

                self.logger.debug(f"Folder already exists: {folder}")
                return True

            # Create folder and any parent folders
            folder_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created folder: {folder}")
            return True

        except Exception as e:
            error_msg = f"Failed to create folder '{folder}': {str(e)}"
            self.logger.error(error_msg)
            raise ObsidianFileError(error_msg) from e
