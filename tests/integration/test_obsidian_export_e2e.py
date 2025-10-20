# tests/integration/test_obsidian_export_e2e.py
import unittest
import tempfile
import shutil
import csv
from pathlib import Path
from core.domain.obsidian_export_config import ObsidianExportConfig
from core.services.obsidian_export_service import ObsidianExportService
from adapters.obsidian.filesystem_file_manager import FilesystemFileManager
from adapters.obsidian.template_engine import MarkdownTemplateEngine
from adapters.obsidian.record_mapper import GoogleBooksObsidianRecordMapper


class TestObsidianExportEndToEnd(unittest.TestCase):
    """End-to-end integration tests for Obsidian export."""

    def setUp(self):
        """Set up temporary vault and test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / "test_vault"
        self.vault_path.mkdir()

    def tearDown(self):
        """Clean up temporary directories."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def create_test_csv(self, records):
        """Helper to create a test CSV file."""
        csv_path = Path(self.temp_dir) / "test_books.csv"
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            if records:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
        return str(csv_path)

    def test_export_single_book_with_full_metadata(self):
        """Test exporting a single book with complete Google Books metadata."""
        records = [{
            "Nome": "clean_code.pdf",
            "Formato": "pdf",
            "Tamanho(MB)": "5.2",
            "Data Modificação": "2024-01-15",
            "Caminho": "/path/to/clean_code.pdf",
            "GB_Titulo": "Clean Code",
            "GB_Autores": "Robert C. Martin",
            "GB_Editora": "Prentice Hall",
            "GB_Data_Publicacao": "2008",
            "GB_Paginas": "464",
            "GB_ISBN10": "0132350882",
            "GB_ISBN13": "9780132350884",
            "GB_Capa_Link": "https://example.com/cover.jpg",
            "GB_Descricao": "A handbook of agile software craftsmanship",
            "GB_Categorias": "Computers, Programming",
            "GB_Idioma": "en",
            "GB_Preview_Link": "https://books.google.com/preview"
        }]

        csv_path = self.create_test_csv(records)

        # Create export configuration
        config = ObsidianExportConfig(
            vault_path=str(self.vault_path),
            notes_folder="Books",
            filename_pattern="{title} - {author}"
        )

        # Create service with real implementations
        file_manager = FilesystemFileManager(str(self.vault_path))
        template_engine = MarkdownTemplateEngine()
        record_mapper = GoogleBooksObsidianRecordMapper()

        service = ObsidianExportService(
            config=config,
            file_manager=file_manager,
            template_engine=template_engine,
            record_mapper=record_mapper
        )

        # Perform export
        success, success_count, skipped_count, error_count, error_messages = \
            service.export_csv_to_obsidian(csv_path)

        # Verify results
        self.assertTrue(success)
        self.assertEqual(success_count, 1)
        self.assertEqual(skipped_count, 0)
        self.assertEqual(error_count, 0)

        # Verify note was created
        note_path = self.vault_path / "Books" / "Clean Code - Robert C. Martin.md"
        self.assertTrue(note_path.exists())

        # Verify note content
        content = note_path.read_text(encoding='utf-8')
        self.assertIn("Clean Code", content)
        self.assertIn("Robert C. Martin", content)
        self.assertIn("Prentice Hall", content)
        self.assertIn("unread", content)  # Default status
        self.assertIn("---", content)  # YAML frontmatter

    def test_export_multiple_books(self):
        """Test exporting multiple books."""
        records = [
            {
                "Nome": "book1.pdf",
                "Formato": "pdf",
                "GB_Titulo": "Design Patterns",
                "GB_Autores": "Gang of Four"
            },
            {
                "Nome": "book2.pdf",
                "Formato": "epub",
                "GB_Titulo": "Refactoring",
                "GB_Autores": "Martin Fowler"
            },
            {
                "Nome": "book3.pdf",
                "Formato": "mobi",
                "GB_Titulo": "The Pragmatic Programmer",
                "GB_Autores": "Andrew Hunt, David Thomas"
            }
        ]

        csv_path = self.create_test_csv(records)

        config = ObsidianExportConfig(
            vault_path=str(self.vault_path),
            notes_folder="Books"
        )

        file_manager = FilesystemFileManager(str(self.vault_path))
        template_engine = MarkdownTemplateEngine()
        record_mapper = GoogleBooksObsidianRecordMapper()

        service = ObsidianExportService(
            config=config,
            file_manager=file_manager,
            template_engine=template_engine,
            record_mapper=record_mapper
        )

        success, success_count, skipped_count, error_count, error_messages = \
            service.export_csv_to_obsidian(csv_path)

        # Verify all books exported
        self.assertTrue(success)
        self.assertEqual(success_count, 3)
        self.assertEqual(error_count, 0)

        # Verify all notes exist
        books_folder = self.vault_path / "Books"
        self.assertEqual(len(list(books_folder.glob("*.md"))), 3)

    def test_export_with_overwrite_disabled(self):
        """Test that existing notes are skipped when overwrite is disabled."""
        records = [
            {"Nome": "book1.pdf", "Formato": "pdf", "GB_Titulo": "Book 1"},
            {"Nome": "book2.pdf", "Formato": "pdf", "GB_Titulo": "Book 2"}
        ]

        csv_path = self.create_test_csv(records)

        config = ObsidianExportConfig(
            vault_path=str(self.vault_path),
            notes_folder="Books",
            overwrite_existing=False
        )

        file_manager = FilesystemFileManager(str(self.vault_path))
        template_engine = MarkdownTemplateEngine()
        record_mapper = GoogleBooksObsidianRecordMapper()

        service = ObsidianExportService(
            config=config,
            file_manager=file_manager,
            template_engine=template_engine,
            record_mapper=record_mapper
        )

        # First export
        service.export_csv_to_obsidian(csv_path)

        # Second export (should skip existing)
        success, success_count, skipped_count, error_count, error_messages = \
            service.export_csv_to_obsidian(csv_path)

        self.assertTrue(success)
        self.assertEqual(success_count, 0)
        self.assertEqual(skipped_count, 2)
        self.assertEqual(error_count, 0)

    def test_export_with_overwrite_enabled(self):
        """Test that existing notes are updated when overwrite is enabled."""
        records = [{"Nome": "book1.pdf", "Formato": "pdf", "GB_Titulo": "Test Book"}]

        csv_path = self.create_test_csv(records)

        # First export
        config1 = ObsidianExportConfig(
            vault_path=str(self.vault_path),
            notes_folder="Books",
            overwrite_existing=False
        )

        file_manager = FilesystemFileManager(str(self.vault_path))
        template_engine = MarkdownTemplateEngine()
        record_mapper = GoogleBooksObsidianRecordMapper()

        service1 = ObsidianExportService(
            config=config1,
            file_manager=file_manager,
            template_engine=template_engine,
            record_mapper=record_mapper
        )

        service1.export_csv_to_obsidian(csv_path)

        # Get original modification time
        note_path = self.vault_path / "Books" / "Test Book - Unknown Author.md"
        original_mtime = note_path.stat().st_mtime

        # Wait a bit
        import time
        time.sleep(0.1)

        # Second export with overwrite enabled
        config2 = ObsidianExportConfig(
            vault_path=str(self.vault_path),
            notes_folder="Books",
            overwrite_existing=True
        )

        service2 = ObsidianExportService(
            config=config2,
            file_manager=file_manager,
            template_engine=template_engine,
            record_mapper=record_mapper
        )

        success, success_count, skipped_count, error_count, error_messages = \
            service2.export_csv_to_obsidian(csv_path)

        self.assertTrue(success)
        self.assertEqual(success_count, 1)
        self.assertEqual(skipped_count, 0)

        # Verify file was updated (modification time changed)
        new_mtime = note_path.stat().st_mtime
        self.assertGreater(new_mtime, original_mtime)

    def test_export_with_custom_filename_pattern(self):
        """Test export with custom filename pattern."""
        records = [{
            "Nome": "book.pdf",
            "Formato": "pdf",
            "GB_Titulo": "Test Book",
            "GB_Autores": "Test Author"
        }]

        csv_path = self.create_test_csv(records)

        config = ObsidianExportConfig(
            vault_path=str(self.vault_path),
            notes_folder="Books",
            filename_pattern="[{format}] {title}"
        )

        file_manager = FilesystemFileManager(str(self.vault_path))
        template_engine = MarkdownTemplateEngine()
        record_mapper = GoogleBooksObsidianRecordMapper()

        service = ObsidianExportService(
            config=config,
            file_manager=file_manager,
            template_engine=template_engine,
            record_mapper=record_mapper
        )

        service.export_csv_to_obsidian(csv_path)

        # Verify filename matches pattern
        note_path = self.vault_path / "Books" / "[pdf] Test Book.md"
        self.assertTrue(note_path.exists())

    def test_export_with_unicode_characters(self):
        """Test export with Unicode characters in data."""
        records = [{
            "Nome": "livro.pdf",
            "Formato": "pdf",
            "GB_Titulo": "Título com Acentuação",
            "GB_Autores": "José María García"
        }]

        csv_path = self.create_test_csv(records)

        config = ObsidianExportConfig(
            vault_path=str(self.vault_path),
            notes_folder="Books"
        )

        file_manager = FilesystemFileManager(str(self.vault_path))
        template_engine = MarkdownTemplateEngine()
        record_mapper = GoogleBooksObsidianRecordMapper()

        service = ObsidianExportService(
            config=config,
            file_manager=file_manager,
            template_engine=template_engine,
            record_mapper=record_mapper
        )

        success, success_count, skipped_count, error_count, error_messages = \
            service.export_csv_to_obsidian(csv_path)

        self.assertTrue(success)
        self.assertEqual(success_count, 1)

        # Verify note content has Unicode
        note_path = self.vault_path / "Books" / "Título com Acentuação - José María García.md"
        self.assertTrue(note_path.exists())

        content = note_path.read_text(encoding='utf-8')
        self.assertIn("Título com Acentuação", content)
        self.assertIn("José María García", content)

    def test_export_with_long_titles(self):
        """Test export handles long titles by truncating filenames."""
        long_title = "A" * 250  # Very long title

        records = [{
            "Nome": "book.pdf",
            "Formato": "pdf",
            "GB_Titulo": long_title,
            "GB_Autores": "Test Author"
        }]

        csv_path = self.create_test_csv(records)

        config = ObsidianExportConfig(
            vault_path=str(self.vault_path),
            notes_folder="Books",
            max_filename_length=100  # Reduced for Windows path length limits
        )

        file_manager = FilesystemFileManager(str(self.vault_path))
        template_engine = MarkdownTemplateEngine()
        record_mapper = GoogleBooksObsidianRecordMapper()

        service = ObsidianExportService(
            config=config,
            file_manager=file_manager,
            template_engine=template_engine,
            record_mapper=record_mapper
        )

        success, success_count, skipped_count, error_count, error_messages = \
            service.export_csv_to_obsidian(csv_path)

        self.assertTrue(success)
        self.assertEqual(success_count, 1)

        # Verify filename was truncated
        books_folder = self.vault_path / "Books"
        created_files = list(books_folder.glob("*.md"))
        self.assertEqual(len(created_files), 1)
        self.assertLessEqual(len(created_files[0].name), 100)

    def test_export_with_special_characters_in_filenames(self):
        """Test that special characters are sanitized in filenames."""
        records = [{
            "Nome": "book.pdf",
            "Formato": "pdf",
            "GB_Titulo": "Book: A Test?",
            "GB_Autores": "Author/Name"
        }]

        csv_path = self.create_test_csv(records)

        config = ObsidianExportConfig(
            vault_path=str(self.vault_path),
            notes_folder="Books"
        )

        file_manager = FilesystemFileManager(str(self.vault_path))
        template_engine = MarkdownTemplateEngine()
        record_mapper = GoogleBooksObsidianRecordMapper()

        service = ObsidianExportService(
            config=config,
            file_manager=file_manager,
            template_engine=template_engine,
            record_mapper=record_mapper
        )

        success, success_count, skipped_count, error_count, error_messages = \
            service.export_csv_to_obsidian(csv_path)

        self.assertTrue(success)
        self.assertEqual(success_count, 1)

        # Verify filename has no special characters
        books_folder = self.vault_path / "Books"
        created_files = list(books_folder.glob("*.md"))
        self.assertEqual(len(created_files), 1)

        filename = created_files[0].name
        self.assertNotIn(":", filename)
        self.assertNotIn("?", filename)
        self.assertNotIn("/", filename)

    def test_export_creates_nested_folders(self):
        """Test export creates nested folder structure."""
        records = [{"Nome": "book.pdf", "Formato": "pdf", "GB_Titulo": "Test"}]

        csv_path = self.create_test_csv(records)

        config = ObsidianExportConfig(
            vault_path=str(self.vault_path),
            notes_folder="Books/Fiction/SciFi"
        )

        file_manager = FilesystemFileManager(str(self.vault_path))
        template_engine = MarkdownTemplateEngine()
        record_mapper = GoogleBooksObsidianRecordMapper()

        service = ObsidianExportService(
            config=config,
            file_manager=file_manager,
            template_engine=template_engine,
            record_mapper=record_mapper
        )

        success, success_count, skipped_count, error_count, error_messages = \
            service.export_csv_to_obsidian(csv_path)

        self.assertTrue(success)

        # Verify nested folder structure was created
        nested_folder = self.vault_path / "Books" / "Fiction" / "SciFi"
        self.assertTrue(nested_folder.exists())
        self.assertTrue(nested_folder.is_dir())


if __name__ == '__main__':
    unittest.main()
