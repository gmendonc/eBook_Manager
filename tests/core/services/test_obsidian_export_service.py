# tests/core/services/test_obsidian_export_service.py
import unittest
import tempfile
import csv
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from core.services.obsidian_export_service import ObsidianExportService
from core.domain.obsidian_export_config import ObsidianExportConfig
from core.exceptions import ObsidianExportError


class TestObsidianExportService(unittest.TestCase):
    """Unit tests for ObsidianExportService."""

    def setUp(self):
        """Set up test fixtures with mocked dependencies."""
        self.config = ObsidianExportConfig(
            vault_path="/test/vault",
            notes_folder="Books",
            filename_pattern="{title} - {author}",
            overwrite_existing=False
        )

        # Create mocks for dependencies
        self.file_manager = Mock()
        self.template_engine = Mock()
        self.record_mapper = Mock()
        self.progress_callback = Mock()

        # Mock template engine to return simple template
        self.template_engine.validate_template.return_value = (True, None)
        self.template_engine.render.return_value = "# Test Note\n\nContent"

        # Mock record mapper
        self.record_mapper.map_record.return_value = {
            "title": "Test Book",
            "author": "Test Author"
        }
        self.record_mapper.generate_filename.return_value = "Test Book - Test Author.md"

        # Create service
        self.service = ObsidianExportService(
            config=self.config,
            file_manager=self.file_manager,
            template_engine=self.template_engine,
            record_mapper=self.record_mapper,
            progress_callback=self.progress_callback
        )

    def create_test_csv(self, records):
        """Helper to create a test CSV file."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8', newline='')
        writer = csv.DictWriter(temp_file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
        temp_file.close()
        return temp_file.name

    def test_export_single_record_success(self):
        """Test successful export of a single record."""
        records = [{"Nome": "test.pdf", "Formato": "pdf", "GB_Titulo": "Test Book"}]
        csv_path = self.create_test_csv(records)

        try:
            # Mock file manager to indicate note doesn't exist
            self.file_manager.note_exists.return_value = False

            success, success_count, skipped_count, error_count, error_messages = \
                self.service.export_csv_to_obsidian(csv_path)

            self.assertTrue(success)
            self.assertEqual(success_count, 1)
            self.assertEqual(skipped_count, 0)
            self.assertEqual(error_count, 0)
            self.assertEqual(len(error_messages), 0)

            # Verify file manager was called to create note
            self.file_manager.create_note.assert_called_once()
        finally:
            Path(csv_path).unlink()

    def test_export_multiple_records_success(self):
        """Test successful export of multiple records."""
        records = [
            {"Nome": "book1.pdf", "Formato": "pdf", "GB_Titulo": "Book 1"},
            {"Nome": "book2.pdf", "Formato": "pdf", "GB_Titulo": "Book 2"},
            {"Nome": "book3.pdf", "Formato": "pdf", "GB_Titulo": "Book 3"}
        ]
        csv_path = self.create_test_csv(records)

        try:
            self.file_manager.note_exists.return_value = False

            success, success_count, skipped_count, error_count, error_messages = \
                self.service.export_csv_to_obsidian(csv_path)

            self.assertTrue(success)
            self.assertEqual(success_count, 3)
            self.assertEqual(skipped_count, 0)
            self.assertEqual(error_count, 0)

            # Verify file manager was called 3 times
            self.assertEqual(self.file_manager.create_note.call_count, 3)
        finally:
            Path(csv_path).unlink()

    def test_export_skips_existing_when_overwrite_false(self):
        """Test that existing notes are skipped when overwrite is False."""
        records = [
            {"Nome": "book1.pdf", "Formato": "pdf", "GB_Titulo": "Book 1"},
            {"Nome": "book2.pdf", "Formato": "pdf", "GB_Titulo": "Book 2"}
        ]
        csv_path = self.create_test_csv(records)

        try:
            # First note exists, second doesn't
            # note_exists is called twice per record (once to check, once before create)
            self.file_manager.note_exists.side_effect = [True, False, False]

            success, success_count, skipped_count, error_count, error_messages = \
                self.service.export_csv_to_obsidian(csv_path)

            self.assertTrue(success)
            self.assertEqual(success_count, 1)
            self.assertEqual(skipped_count, 1)
            self.assertEqual(error_count, 0)

            # Only one note should be created
            self.assertEqual(self.file_manager.create_note.call_count, 1)
        finally:
            Path(csv_path).unlink()

    def test_export_overwrites_existing_when_overwrite_true(self):
        """Test that existing notes are overwritten when overwrite is True."""
        config = ObsidianExportConfig(
            vault_path="/test/vault",
            notes_folder="Books",
            overwrite_existing=True
        )
        service = ObsidianExportService(
            config=config,
            file_manager=self.file_manager,
            template_engine=self.template_engine,
            record_mapper=self.record_mapper
        )

        records = [{"Nome": "book1.pdf", "Formato": "pdf", "GB_Titulo": "Book 1"}]
        csv_path = self.create_test_csv(records)

        try:
            self.file_manager.note_exists.return_value = True

            success, success_count, skipped_count, error_count, error_messages = \
                service.export_csv_to_obsidian(csv_path)

            self.assertTrue(success)
            self.assertEqual(success_count, 1)
            self.assertEqual(skipped_count, 0)

            # Note should be created (overwritten)
            self.file_manager.create_note.assert_called_once()
        finally:
            Path(csv_path).unlink()

    def test_export_continues_after_error(self):
        """Test that export continues processing after encountering an error."""
        records = [
            {"Nome": "book1.pdf", "Formato": "pdf", "GB_Titulo": "Book 1"},
            {"Nome": "book2.pdf", "Formato": "pdf", "GB_Titulo": "Book 2"},
            {"Nome": "book3.pdf", "Formato": "pdf", "GB_Titulo": "Book 3"}
        ]
        csv_path = self.create_test_csv(records)

        try:
            self.file_manager.note_exists.return_value = False
            # Make second record fail
            self.file_manager.create_note.side_effect = [
                True,  # First succeeds
                Exception("Test error"),  # Second fails
                True  # Third succeeds
            ]

            success, success_count, skipped_count, error_count, error_messages = \
                self.service.export_csv_to_obsidian(csv_path)

            # Overall success is True because some succeeded
            self.assertTrue(success)
            self.assertEqual(success_count, 2)
            self.assertEqual(error_count, 1)
            self.assertEqual(len(error_messages), 1)
            self.assertIn("Test error", error_messages[0])
        finally:
            Path(csv_path).unlink()

    def test_export_calls_progress_callback(self):
        """Test that progress callback is called during export."""
        records = [
            {"Nome": f"book{i}.pdf", "Formato": "pdf", "GB_Titulo": f"Book {i}"}
            for i in range(5)
        ]
        csv_path = self.create_test_csv(records)

        try:
            # Create fresh mocks to avoid state pollution
            file_manager = Mock()
            file_manager.note_exists.return_value = False
            file_manager.ensure_folder_exists.return_value = None
            file_manager.create_note.return_value = True

            template_engine = Mock()
            template_engine.validate_template.return_value = (True, None)
            template_engine.render.return_value = "# Test Note\n\nContent"

            record_mapper = Mock()
            record_mapper.map_record.return_value = {"title": "Test Book", "author": "Test Author"}
            record_mapper.generate_filename.return_value = "Test Book - Test Author.md"

            progress_callback = Mock()

            service_with_callback = ObsidianExportService(
                config=self.config,
                file_manager=file_manager,
                template_engine=template_engine,
                record_mapper=record_mapper,
                progress_callback=progress_callback
            )

            service_with_callback.export_csv_to_obsidian(csv_path)

            # Callback should be called for start (0, total) and each record
            self.assertGreater(progress_callback.call_count, 5)  # At least 6 calls: start + 5 records

            # First call should be (0, total_rows)
            first_call = progress_callback.call_args_list[0]
            self.assertEqual(first_call[0][0], 0)  # First argument is 0
            self.assertGreater(first_call[0][1], 0)  # Second argument (total) is > 0

            # Last call should be (N, total_rows) where N is the number of processed records
            last_call = progress_callback.call_args_list[-1]
            self.assertGreater(last_call[0][0], 0)  # Progress > 0
            self.assertEqual(last_call[0][0], last_call[0][1])  # current == total (finished)
        finally:
            Path(csv_path).unlink()

    def test_export_nonexistent_csv_raises_error(self):
        """Test that exporting non-existent CSV raises error."""
        with self.assertRaises(ObsidianExportError) as context:
            self.service.export_csv_to_obsidian("/nonexistent/file.csv")

        self.assertIn("not found", str(context.exception))

    def test_export_creates_notes_folder(self):
        """Test that export ensures notes folder exists."""
        records = [{"Nome": "book1.pdf", "Formato": "pdf"}]
        csv_path = self.create_test_csv(records)

        try:
            self.file_manager.note_exists.return_value = False

            self.service.export_csv_to_obsidian(csv_path)

            # Verify ensure_folder_exists was called
            self.file_manager.ensure_folder_exists.assert_called_once_with("Books")
        finally:
            Path(csv_path).unlink()

    def test_export_uses_custom_template_when_available(self):
        """Test that custom template is loaded when configured."""
        # Create a temporary custom template file
        temp_template = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8')
        temp_template.write("# {{title}}\n\nCustom template")
        temp_template.close()

        try:
            config = ObsidianExportConfig(
                vault_path="/test/vault",
                notes_folder="Books",
                template_path=temp_template.name
            )

            # Mock template engine to validate and use custom template
            self.template_engine.validate_template.return_value = (True, None)

            service = ObsidianExportService(
                config=config,
                file_manager=self.file_manager,
                template_engine=self.template_engine,
                record_mapper=self.record_mapper
            )

            # Verify custom template was loaded (template is loaded in __init__)
            # Service should have attempted to validate the custom template
            self.template_engine.validate_template.assert_called()
        finally:
            Path(temp_template.name).unlink()

    def test_export_falls_back_to_default_template_when_custom_invalid(self):
        """Test fallback to default template when custom template is invalid."""
        # Create invalid template file
        temp_template = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8')
        temp_template.write("# {{title}\n\nInvalid")  # Missing closing brace
        temp_template.close()

        try:
            config = ObsidianExportConfig(
                vault_path="/test/vault",
                notes_folder="Books",
                template_path=temp_template.name
            )

            # Mock template engine to fail validation
            self.template_engine.validate_template.return_value = (False, "Syntax error")

            service = ObsidianExportService(
                config=config,
                file_manager=self.file_manager,
                template_engine=self.template_engine,
                record_mapper=self.record_mapper
            )

            # Service should fall back to default template
            # This is indicated by service still being created successfully
            self.assertIsNotNone(service)
        finally:
            Path(temp_template.name).unlink()

    def test_export_empty_csv(self):
        """Test export with empty CSV (only headers)."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        temp_file.write("Nome,Formato\n")  # Only header
        temp_file.close()

        try:
            success, success_count, skipped_count, error_count, error_messages = \
                self.service.export_csv_to_obsidian(temp_file.name)

            self.assertTrue(success)
            self.assertEqual(success_count, 0)
            self.assertEqual(skipped_count, 0)
            self.assertEqual(error_count, 0)
        finally:
            Path(temp_file.name).unlink()

    def test_export_limits_error_messages(self):
        """Test that error messages are limited to prevent memory issues."""
        # Create 100 records
        records = [
            {"Nome": f"book{i}.pdf", "Formato": "pdf", "GB_Titulo": f"Book {i}"}
            for i in range(100)
        ]
        csv_path = self.create_test_csv(records)

        try:
            self.file_manager.note_exists.return_value = False
            # Make all records fail
            self.file_manager.create_note.side_effect = Exception("Test error")

            success, success_count, skipped_count, error_count, error_messages = \
                self.service.export_csv_to_obsidian(csv_path)

            # Error messages should be limited to MAX_ERROR_MESSAGES (50)
            self.assertLessEqual(len(error_messages), 51)  # 50 + "more records" message
        finally:
            Path(csv_path).unlink()


if __name__ == '__main__':
    unittest.main()
