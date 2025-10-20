# core/exceptions.py
"""
Custom exceptions for the eBook Manager application.

All application-specific exceptions should inherit from EbookManagerError
to allow for centralized error handling.
"""


class EbookManagerError(Exception):
    """Base exception for all eBook Manager application errors."""
    pass


# Obsidian Export Exceptions

class ObsidianExportError(EbookManagerError):
    """
    Base exception for Obsidian export errors.

    Raised when any error occurs during the Obsidian export process.
    """
    pass


class ObsidianConfigError(ObsidianExportError):
    """
    Configuration validation or loading error.

    Raised when:
    - Required configuration fields are missing
    - Configuration values are invalid
    - Configuration file cannot be loaded or saved
    """
    pass


class ObsidianTemplateError(ObsidianExportError):
    """
    Template processing error.

    Raised when:
    - Template file cannot be found or read
    - Template syntax is invalid
    - Template rendering fails
    """
    pass


class ObsidianFileError(ObsidianExportError):
    """
    File operation error.

    Raised when:
    - Vault path does not exist or is not accessible
    - File cannot be created or written
    - Permissions are insufficient
    - Disk space is insufficient
    """
    pass


# Notion Export Exceptions (for completeness)

class NotionExportError(EbookManagerError):
    """Exception raised for errors during Notion export."""
    pass


# Scanner Exceptions

class ScannerError(EbookManagerError):
    """Errors during scanning operations."""
    pass


# Enricher Exceptions

class EnricherError(EbookManagerError):
    """Errors during enrichment operations."""
    pass
