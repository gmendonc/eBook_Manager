# core/interfaces/obsidian_file_manager.py
from typing import Protocol, Optional


class ObsidianFileManager(Protocol):
    """
    Interface for managing files in an Obsidian vault.

    This interface defines the contract for file operations within an Obsidian vault.
    Implementations may use direct filesystem access or MCP tools.

    Implementations must ensure that:
    - All file operations use UTF-8 encoding
    - Paths are properly joined (vault_path / folder / filename)
    - Folders are created if they don't exist
    - Errors are handled gracefully with appropriate exceptions
    """

    def create_note(self, folder: str, filename: str, content: str) -> bool:
        """
        Create a new note in the Obsidian vault.

        Args:
            folder: Folder path relative to vault root (e.g., "Books")
            filename: Name of the note file including .md extension
            content: Markdown content for the note

        Returns:
            True if note was created successfully, False otherwise

        Raises:
            ObsidianFileError: If file creation fails due to permissions,
                              disk space, or other I/O errors
        """
        ...

    def update_note(self, folder: str, filename: str, content: str) -> bool:
        """
        Update an existing note in the Obsidian vault.

        This method overwrites the existing file content.

        Args:
            folder: Folder path relative to vault root
            filename: Name of the note file including .md extension
            content: New Markdown content for the note

        Returns:
            True if note was updated successfully, False otherwise

        Raises:
            ObsidianFileError: If file update fails
        """
        ...

    def note_exists(self, folder: str, filename: str) -> bool:
        """
        Check if a note exists in the vault.

        Args:
            folder: Folder path relative to vault root
            filename: Name of the note file including .md extension

        Returns:
            True if note exists, False otherwise
        """
        ...

    def get_note_content(self, folder: str, filename: str) -> Optional[str]:
        """
        Get the content of an existing note.

        Args:
            folder: Folder path relative to vault root
            filename: Name of the note file including .md extension

        Returns:
            Note content as string if note exists, None otherwise

        Raises:
            ObsidianFileError: If file reading fails
        """
        ...

    def ensure_folder_exists(self, folder: str) -> bool:
        """
        Ensure a folder exists in the vault, creating it if necessary.

        Args:
            folder: Folder path relative to vault root

        Returns:
            True if folder exists or was created successfully, False otherwise

        Raises:
            ObsidianFileError: If folder creation fails
        """
        ...
