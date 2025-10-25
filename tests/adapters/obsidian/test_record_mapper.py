# tests/adapters/obsidian/test_record_mapper.py
import unittest
from datetime import datetime
from adapters.obsidian.record_mapper import GoogleBooksObsidianRecordMapper
from core.domain.obsidian_export_config import ObsidianExportConfig


class TestGoogleBooksObsidianRecordMapper(unittest.TestCase):
    """Unit tests for GoogleBooksObsidianRecordMapper."""

    def setUp(self):
        """Set up test fixtures."""
        self.mapper = GoogleBooksObsidianRecordMapper()
        self.config = ObsidianExportConfig(
            vault_path="/test/vault",
            notes_folder="Books",
            default_status="unread",
            default_priority="medium",
            default_device="computer",
            default_purpose=["read", "reference"]
        )

    def test_map_record_with_google_books_data(self):
        """Test mapping record with full Google Books data."""
        record = {
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
            "GB_Preview_Link": "https://books.google.com/preview",
            "Formato": "pdf",
            "Tamanho(MB)": "5.2",
            "Caminho": "/path/to/book.pdf",
            "Data Modificação": "2024-01-15"
        }

        result = self.mapper.map_record(record, self.config)

        self.assertEqual(result["title"], "Clean Code")
        self.assertEqual(result["author"], "Robert C. Martin")
        self.assertEqual(result["publisher"], "Prentice Hall")
        self.assertEqual(result["publishDate"], "2008")
        self.assertEqual(result["totalPage"], "464")
        self.assertEqual(result["isbn10"], "0132350882")
        self.assertEqual(result["isbn13"], "9780132350884")
        self.assertEqual(result["coverUrl"], "https://example.com/cover.jpg")
        # Description should now include file path at the end
        self.assertIn("A handbook of agile software craftsmanship", result["description"])
        self.assertIn("/path/to/book.pdf", result["description"])
        self.assertIn("File Location:", result["description"])
        self.assertEqual(result["categories"], "Computers, Programming")
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["preview_link"], "https://books.google.com/preview")
        self.assertEqual(result["format"], "pdf")
        self.assertEqual(result["file_size"], "5.2")
        self.assertEqual(result["file_path"], "/path/to/book.pdf")
        self.assertEqual(result["modified_date"], "2024-01-15")
        self.assertEqual(result["status"], "unread")
        self.assertEqual(result["priority"], "medium")
        self.assertEqual(result["device"], "computer")
        self.assertEqual(result["purpose"], "[read, reference]")
        self.assertIn("created", result)
        self.assertIn("updated", result)

    def test_map_record_fallback_to_extracted(self):
        """Test fallback from GB fields to extracted fields."""
        record = {
            "Titulo_Extraido": "Test Book",
            "Autor_Extraido": "Test Author",
            "Formato": "epub",
            "Nome": "test_book.epub"
        }

        result = self.mapper.map_record(record, self.config)

        self.assertEqual(result["title"], "Test Book")
        self.assertEqual(result["author"], "Test Author")
        self.assertEqual(result["format"], "epub")

    def test_map_record_fallback_to_filename(self):
        """Test fallback to filename when no title available."""
        record = {
            "Nome": "my_awesome_book.pdf",
            "Formato": "pdf"
        }

        result = self.mapper.map_record(record, self.config)

        self.assertEqual(result["title"], "my_awesome_book")  # Without extension
        self.assertEqual(result["author"], "Unknown Author")

    def test_map_record_with_empty_fields(self):
        """Test mapping record with empty/missing fields."""
        record = {
            "Nome": "book.pdf",
            "Formato": "pdf"
        }

        result = self.mapper.map_record(record, self.config)

        # Should have empty strings for missing fields
        self.assertEqual(result["publisher"], "")
        self.assertEqual(result["publishDate"], "")
        self.assertEqual(result["totalPage"], "")
        self.assertEqual(result["isbn10"], "")
        self.assertEqual(result["isbn13"], "")
        # Description will be empty when no file path is provided
        self.assertEqual(result["description"], "")
        # Should have defaults from config
        self.assertEqual(result["status"], "unread")
        self.assertEqual(result["priority"], "medium")

    def test_sanitize_filename_removes_invalid_chars(self):
        """Test filename sanitization removes invalid characters."""
        invalid_filename = 'Book: Title/Name?.md'

        result = self.mapper.sanitize_filename(invalid_filename, 200)

        self.assertNotIn(":", result)
        self.assertNotIn("/", result)
        self.assertNotIn("?", result)
        self.assertIn("Book", result)
        self.assertIn("Title", result)
        self.assertIn("Name", result)
        self.assertTrue(result.endswith(".md"))

    def test_sanitize_filename_collapses_spaces(self):
        """Test filename sanitization collapses multiple spaces."""
        filename = "Book    with    spaces.md"

        result = self.mapper.sanitize_filename(filename, 200)

        self.assertNotIn("  ", result)  # No double spaces
        self.assertEqual(result, "Book with spaces.md")

    def test_sanitize_filename_truncates_long_names(self):
        """Test filename sanitization truncates to max length."""
        long_filename = "A" * 300 + ".md"

        result = self.mapper.sanitize_filename(long_filename, 200)

        self.assertLessEqual(len(result), 200)
        self.assertTrue(result.endswith(".md"))

    def test_sanitize_filename_handles_empty_string(self):
        """Test filename sanitization with empty string."""
        filename = ""

        result = self.mapper.sanitize_filename(filename, 200)

        self.assertEqual(result, "untitled.md")

    def test_sanitize_filename_preserves_unicode(self):
        """Test filename sanitization preserves Unicode characters."""
        filename = "Título com Acentuação.md"

        result = self.mapper.sanitize_filename(filename, 200)

        self.assertEqual(result, "Título com Acentuação.md")

    def test_generate_filename_with_title_author(self):
        """Test filename generation with title and author pattern."""
        record = {
            "GB_Titulo": "Clean Code",
            "GB_Autores": "Robert C. Martin",
            "Formato": "pdf"
        }
        pattern = "{title} - {author}"

        result = self.mapper.generate_filename(record, pattern, 200)

        self.assertEqual(result, "Clean Code - Robert C. Martin.md")

    def test_generate_filename_with_format_prefix(self):
        """Test filename generation with format prefix."""
        record = {
            "GB_Titulo": "Design Patterns",
            "Formato": "epub"
        }
        pattern = "[{format}] {title}"

        result = self.mapper.generate_filename(record, pattern, 200)

        self.assertEqual(result, "[epub] Design Patterns.md")

    def test_generate_filename_with_missing_placeholders(self):
        """Test filename generation with missing placeholder values."""
        record = {
            "GB_Titulo": "Test Book",
            "Formato": "pdf"
        }
        pattern = "{title} - {author} - {publisher}"

        result = self.mapper.generate_filename(record, pattern, 200)

        # Should remove unreplaced placeholders gracefully
        self.assertIn("Test Book", result)
        self.assertNotIn("{author}", result)
        self.assertNotIn("{publisher}", result)
        self.assertTrue(result.endswith(".md"))

    def test_generate_filename_sanitizes_result(self):
        """Test that generated filename is sanitized."""
        record = {
            "GB_Titulo": "Book: A Test?",
            "GB_Autores": "Author/Name",
            "Formato": "pdf"
        }
        pattern = "{title} - {author}"

        result = self.mapper.generate_filename(record, pattern, 200)

        self.assertNotIn(":", result)
        self.assertNotIn("?", result)
        self.assertNotIn("/", result)
        self.assertIn("Book A Test", result)
        self.assertIn("AuthorName", result)

    def test_generate_filename_uses_isbn_when_available(self):
        """Test filename generation can use ISBN."""
        record = {
            "GB_Titulo": "Test Book",
            "GB_ISBN13": "9780132350884",
            "Formato": "pdf"
        }
        pattern = "{title} - {isbn}"

        result = self.mapper.generate_filename(record, pattern, 200)

        self.assertIn("Test Book", result)
        self.assertIn("9780132350884", result)

    def test_map_record_dates_are_current(self):
        """Test that created and updated dates are current."""
        record = {"Nome": "test.pdf", "Formato": "pdf"}

        result = self.mapper.map_record(record, self.config)

        # Dates should be current
        created = datetime.strptime(result["created"], "%Y-%m-%d %H:%M:%S")
        updated = datetime.strptime(result["updated"], "%Y-%m-%d %H:%M:%S")

        now = datetime.now()
        # Should be within last minute
        self.assertLess((now - created).total_seconds(), 60)
        self.assertLess((now - updated).total_seconds(), 60)

    def test_map_record_purpose_formatting(self):
        """Test purpose list is formatted correctly."""
        config = ObsidianExportConfig(
            vault_path="/test/vault",
            default_purpose=["read", "reference", "study"]
        )
        record = {"Nome": "test.pdf", "Formato": "pdf"}

        result = self.mapper.map_record(record, config)

        self.assertEqual(result["purpose"], "[read, reference, study]")

    def test_map_record_empty_purpose_list(self):
        """Test empty purpose list."""
        config = ObsidianExportConfig(
            vault_path="/test/vault",
            default_purpose=[]
        )
        record = {"Nome": "test.pdf", "Formato": "pdf"}

        result = self.mapper.map_record(record, config)

        self.assertEqual(result["purpose"], "[]")

    def test_map_record_topics_from_temas_sugeridos(self):
        """Test topics extraction from Temas_Sugeridos."""
        record = {
            "Nome": "test.pdf",
            "Formato": "pdf",
            "Temas_Sugeridos": "Data Science, Machine Learning, Python"
        }

        result = self.mapper.map_record(record, self.config)

        # Should be formatted as list and deduplicated
        self.assertIn("topics", result)
        self.assertIn("Data Science", result["topics"])
        self.assertIn("Machine Learning", result["topics"])
        self.assertIn("Python", result["topics"])

    def test_map_record_topics_from_gb_categorias(self):
        """Test topics extraction fallback to GB_Categorias."""
        record = {
            "Nome": "test.pdf",
            "Formato": "pdf",
            "GB_Categorias": "Computers; Programming; Software"
        }

        result = self.mapper.map_record(record, self.config)

        # Should split by semicolons
        self.assertIn("topics", result)
        self.assertIn("Computers", result["topics"])
        self.assertIn("Programming", result["topics"])
        self.assertIn("Software", result["topics"])

    def test_map_record_topics_empty_when_missing(self):
        """Test topics is empty list when no source available."""
        record = {
            "Nome": "test.pdf",
            "Formato": "pdf"
        }

        result = self.mapper.map_record(record, self.config)

        self.assertEqual(result["topics"], "[]")

    def test_map_record_topics_deduplicates(self):
        """Test topics are deduplicated."""
        record = {
            "Nome": "test.pdf",
            "Formato": "pdf",
            "Temas_Sugeridos": "Python, Data, Python, Analysis"
        }

        result = self.mapper.map_record(record, self.config)

        # Should have Python only once
        self.assertIn("topics", result)
        topics_str = result["topics"]
        # Count occurrences of "Python" in the string
        self.assertEqual(topics_str.count("Python"), 1)

    def test_get_title_removes_extension_from_filename(self):
        """Test that title extraction removes file extension from Nome."""
        record = {"Nome": "clean_code.pdf"}

        result = self.mapper.map_record(record, self.config)

        self.assertEqual(result["title"], "clean_code")
        self.assertNotIn(".pdf", result["title"])

    def test_get_format_lowercase(self):
        """Test that format is returned in lowercase."""
        record = {
            "Nome": "test.PDF",
            "Formato": "PDF"
        }

        result = self.mapper.map_record(record, self.config)

        self.assertEqual(result["format"], "pdf")

    def test_build_description_with_path_appends_file_location(self):
        """Test that file path is appended to description."""
        description = "This is a book description"
        file_path = "/home/user/books/mybook.pdf"

        result = self.mapper._build_description_with_path(description, file_path)

        self.assertIn("This is a book description", result)
        self.assertIn("File Location:", result)
        self.assertIn("/home/user/books/mybook.pdf", result)
        self.assertIn("---", result)

    def test_build_description_with_path_no_path(self):
        """Test description when file path is empty."""
        description = "This is a book description"
        file_path = ""

        result = self.mapper._build_description_with_path(description, file_path)

        self.assertEqual(result, description)
        self.assertNotIn("File Location:", result)

    def test_build_description_with_path_empty_description(self):
        """Test file path section when description is empty."""
        description = ""
        file_path = "/home/user/books/mybook.pdf"

        result = self.mapper._build_description_with_path(description, file_path)

        self.assertIn("File Location:", result)
        self.assertIn("/home/user/books/mybook.pdf", result)
        self.assertIn("---", result)

    def test_build_description_with_path_both_empty(self):
        """Test when both description and path are empty."""
        description = ""
        file_path = ""

        result = self.mapper._build_description_with_path(description, file_path)

        self.assertEqual(result, "")


if __name__ == '__main__':
    unittest.main()
