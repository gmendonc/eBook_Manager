# core/services/obsidian_export_service.py
import logging
import csv
from typing import Tuple, List, Optional, Callable
from pathlib import Path

from core.domain.obsidian_export_config import ObsidianExportConfig
from core.interfaces.obsidian_file_manager import ObsidianFileManager
from core.interfaces.obsidian_template_engine import ObsidianTemplateEngine
from core.interfaces.obsidian_record_mapper import ObsidianRecordMapper
from core.exceptions import ObsidianExportError, ObsidianTemplateError
from adapters.obsidian.templates import DEFAULT_TEMPLATE


class ObsidianExportService:
    """
    Service for exporting ebook library to Obsidian vault.

    This service orchestrates the entire export workflow:
    1. Load and validate template
    2. Read CSV file
    3. For each record:
       - Map to template data
       - Render template
       - Generate filename
       - Create/update note in vault
    4. Track progress and errors
    """

    # Maximum number of error messages to collect
    MAX_ERROR_MESSAGES = 50

    def __init__(
        self,
        config: ObsidianExportConfig,
        file_manager: ObsidianFileManager,
        template_engine: ObsidianTemplateEngine,
        record_mapper: ObsidianRecordMapper,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """
        Initialize the export service.

        Args:
            config: Export configuration
            file_manager: File manager for vault operations
            template_engine: Template rendering engine
            record_mapper: Record to template data mapper
            progress_callback: Optional callback for progress updates (current, total)
        """
        self.config = config
        self.file_manager = file_manager
        self.template_engine = template_engine
        self.record_mapper = record_mapper
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)

        # Load and cache template
        self.template = self._load_template()

    def export_csv_to_obsidian(self, csv_path: str) -> Tuple[bool, int, int, int, List[str]]:
        """
        Export ebooks from CSV to Obsidian vault.

        Args:
            csv_path: Path to CSV file with ebook data

        Returns:
            Tuple of (overall_success, successful_count, skipped_count, error_count, error_messages)

        Raises:
            ObsidianExportError: If export fails critically (e.g., CSV not found)
        """
        self.logger.info(f"Starting Obsidian export from {csv_path}")

        # Validate CSV file exists
        if not Path(csv_path).exists():
            raise ObsidianExportError(f"CSV file not found: {csv_path}")

        # Ensure notes folder exists
        try:
            self.logger.info(f"Ensuring notes folder exists: {self.config.notes_folder}")
            self.file_manager.ensure_folder_exists(self.config.notes_folder)
            self.logger.debug(f"Notes folder ready: {self.config.notes_folder}")
        except Exception as e:
            self.logger.error(f"Failed to create notes folder: {str(e)}")
            raise ObsidianExportError(f"Failed to create notes folder: {str(e)}") from e

        # Counters
        success_count = 0
        skipped_count = 0
        error_count = 0
        error_messages = []

        try:
            # Read CSV and count total rows
            with open(csv_path, 'r', encoding='utf-8') as f:
                total_rows = sum(1 for _ in f) - 1  # -1 for header

            self.logger.info(f"Processing {total_rows} records from {csv_path}")
            self.logger.info(f"Export settings: overwrite={self.config.overwrite_existing}, use_mcp={self.config.use_mcp_tools}")
            self.logger.info(f"Filename pattern: '{self.config.filename_pattern}'")

            # Notify progress start
            if self.progress_callback:
                self.progress_callback(0, total_rows)

            # Process each record
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for i, record in enumerate(reader):
                    try:
                        # Process this record
                        result = self._process_record(record, i + 1)

                        if result == "success":
                            success_count += 1
                        elif result == "skipped":
                            skipped_count += 1

                        # Update progress
                        if self.progress_callback:
                            self.progress_callback(i + 1, total_rows)

                        # Log progress periodically
                        if (i + 1) % 10 == 0 or (i + 1) == total_rows:
                            self.logger.info(
                                f"Progress: {i + 1}/{total_rows} "
                                f"(✓{success_count} ⊘{skipped_count} ✗{error_count})"
                            )

                    except Exception as e:
                        error_count += 1
                        error_msg = self._format_error_message(record, i + 1, e)
                        error_messages.append(error_msg)
                        self.logger.error(error_msg)

                        # Limit error messages to prevent memory issues
                        if len(error_messages) >= self.MAX_ERROR_MESSAGES:
                            error_messages.append(
                                f"... and {total_rows - i - 1} more records not processed"
                            )
                            break

            # Final summary
            # Success if no errors, or if we have any successes and errors are less than total
            overall_success = (total_rows == 0) or (error_count == 0) or (error_count < total_rows and success_count > 0)
            self.logger.info(
                f"Export completed: {success_count} successful, "
                f"{skipped_count} skipped, {error_count} errors"
            )

            return overall_success, success_count, skipped_count, error_count, error_messages

        except Exception as e:
            error_msg = f"Failed to export CSV: {str(e)}"
            self.logger.error(error_msg)
            raise ObsidianExportError(error_msg) from e

    def _process_record(self, record: dict, record_num: int) -> str:
        """
        Process a single record.

        Args:
            record: CSV record
            record_num: Record number (for logging)

        Returns:
            "success" if created, "skipped" if already exists and not overwriting

        Raises:
            Exception: If processing fails
        """
        # Get book title for logging context
        book_title = record.get("GB_Titulo") or record.get("Titulo_Extraido") or record.get("Nome", "Unknown")
        self.logger.debug(f"Processing record {record_num}: '{book_title}'")

        # Map record to template data
        template_data = self.record_mapper.map_record(record, self.config)
        self.logger.debug(f"Mapped {len(template_data)} fields for '{book_title}'")

        # Generate filename
        filename = self.record_mapper.generate_filename(
            record,
            self.config.filename_pattern,
            self.config.max_filename_length
        )
        self.logger.debug(f"Generated filename: '{filename}'")

        # Check if note already exists
        if self.file_manager.note_exists(self.config.notes_folder, filename):
            if not self.config.overwrite_existing:
                self.logger.info(f"Skipping existing note ({record_num}): {filename}")
                return "skipped"

            # Will overwrite
            self.logger.info(f"Overwriting existing note ({record_num}): {filename}")

        # Render template
        content = self.template_engine.render(self.template, template_data)
        self.logger.debug(f"Rendered template: {len(content)} characters")

        # Create/update note
        if self.config.overwrite_existing or not self.file_manager.note_exists(
            self.config.notes_folder, filename
        ):
            self.file_manager.create_note(self.config.notes_folder, filename, content)
            self.logger.info(f"✓ Created note ({record_num}): {filename}")
        else:
            self.file_manager.update_note(self.config.notes_folder, filename, content)
            self.logger.info(f"✓ Updated note ({record_num}): {filename}")

        return "success"

    def _load_template(self) -> str:
        """
        Load template from config or use default.

        Returns:
            Template string

        Raises:
            ObsidianExportError: If template loading fails critically
        """
        # If no custom template specified, use default
        if not self.config.template_path:
            self.logger.info("Using default template")
            return DEFAULT_TEMPLATE

        # Try to load custom template
        template_path = Path(self.config.template_path)

        if not template_path.exists():
            self.logger.warning(
                f"Custom template not found: {self.config.template_path}, using default"
            )
            return DEFAULT_TEMPLATE

        try:
            # Read template file
            template = template_path.read_text(encoding='utf-8')

            # Validate template
            is_valid, error = self.template_engine.validate_template(template)

            if not is_valid:
                self.logger.warning(
                    f"Custom template validation failed: {error}, using default"
                )
                return DEFAULT_TEMPLATE

            self.logger.info(f"Loaded custom template from {self.config.template_path}")
            return template

        except Exception as e:
            self.logger.warning(
                f"Failed to load custom template: {str(e)}, using default"
            )
            return DEFAULT_TEMPLATE

    def _format_error_message(self, record: dict, record_num: int, error: Exception) -> str:
        """
        Format an error message for a failed record.

        Args:
            record: CSV record that failed
            record_num: Record number
            error: Exception that occurred

        Returns:
            Formatted error message
        """
        # Try to get book title for context
        title = record.get("GB_Titulo") or record.get("Titulo_Extraido") or record.get("Nome", "Unknown")

        return f"Record {record_num} ('{title}'): {str(error)}"
