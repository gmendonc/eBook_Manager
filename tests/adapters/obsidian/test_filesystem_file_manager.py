# tests/adapters/obsidian/test_filesystem_file_manager.py
import unittest
import tempfile
import shutil
from pathlib import Path
from adapters.obsidian.filesystem_file_manager import FilesystemFileManager
from core.exceptions import ObsidianFileError


class TestFilesystemFileManager(unittest.TestCase):
    """Unit tests for FilesystemFileManager."""

    def setUp(self):
        """Set up test fixtures with temporary vault directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / "test_vault"
        self.vault_path.mkdir()
        self.manager = FilesystemFileManager(str(self.vault_path))

    def tearDown(self):
        """Clean up temporary directories."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_initialization_with_valid_vault(self):
        """Test initialization with valid vault path."""
        manager = FilesystemFileManager(str(self.vault_path))
        self.assertIsNotNone(manager)

    def test_initialization_with_nonexistent_vault_raises_error(self):
        """Test initialization with non-existent vault raises error."""
        nonexistent_path = str(Path(self.temp_dir) / "nonexistent")

        with self.assertRaises(ObsidianFileError) as context:
            FilesystemFileManager(nonexistent_path)

        self.assertIn("does not exist", str(context.exception))

    def test_initialization_with_file_instead_of_directory_raises_error(self):
        """Test initialization with file path instead of directory raises error."""
        file_path = Path(self.temp_dir) / "file.txt"
        file_path.write_text("test")

        with self.assertRaises(ObsidianFileError) as context:
            FilesystemFileManager(str(file_path))

        self.assertIn("not a directory", str(context.exception))

    def test_create_note_success(self):
        """Test creating a new note successfully."""
        content = "# Test Note\n\nThis is a test."

        result = self.manager.create_note("Books", "test.md", content)

        self.assertTrue(result)
        note_path = self.vault_path / "Books" / "test.md"
        self.assertTrue(note_path.exists())
        self.assertEqual(note_path.read_text(encoding='utf-8'), content)

    def test_create_note_creates_folder_if_not_exists(self):
        """Test that create_note creates folder if it doesn't exist."""
        content = "# Test"

        self.manager.create_note("NewFolder", "test.md", content)

        folder_path = self.vault_path / "NewFolder"
        self.assertTrue(folder_path.exists())
        self.assertTrue(folder_path.is_dir())

    def test_create_note_with_unicode_content(self):
        """Test creating note with Unicode content."""
        content = "# Título com Acentuação\n\nConteúdo em português."

        result = self.manager.create_note("Books", "test.md", content)

        self.assertTrue(result)
        note_path = self.vault_path / "Books" / "test.md"
        self.assertEqual(note_path.read_text(encoding='utf-8'), content)

    def test_create_note_with_nested_folders(self):
        """Test creating note in nested folder structure."""
        content = "# Test"

        result = self.manager.create_note("Books/Fiction/SciFi", "test.md", content)

        self.assertTrue(result)
        note_path = self.vault_path / "Books" / "Fiction" / "SciFi" / "test.md"
        self.assertTrue(note_path.exists())

    def test_update_note_success(self):
        """Test updating an existing note."""
        # Create initial note
        original_content = "# Original"
        self.manager.create_note("Books", "test.md", original_content)

        # Update note
        new_content = "# Updated"
        result = self.manager.update_note("Books", "test.md", new_content)

        self.assertTrue(result)
        note_path = self.vault_path / "Books" / "test.md"
        self.assertEqual(note_path.read_text(encoding='utf-8'), new_content)

    def test_update_nonexistent_note_raises_error(self):
        """Test updating non-existent note raises error."""
        with self.assertRaises(ObsidianFileError) as context:
            self.manager.update_note("Books", "nonexistent.md", "# Test")

        self.assertIn("does not exist", str(context.exception))

    def test_note_exists_returns_true_for_existing_note(self):
        """Test note_exists returns True for existing note."""
        self.manager.create_note("Books", "test.md", "# Test")

        exists = self.manager.note_exists("Books", "test.md")

        self.assertTrue(exists)

    def test_note_exists_returns_false_for_nonexistent_note(self):
        """Test note_exists returns False for non-existent note."""
        exists = self.manager.note_exists("Books", "nonexistent.md")

        self.assertFalse(exists)

    def test_note_exists_returns_false_for_nonexistent_folder(self):
        """Test note_exists returns False when folder doesn't exist."""
        exists = self.manager.note_exists("NonexistentFolder", "test.md")

        self.assertFalse(exists)

    def test_get_note_content_success(self):
        """Test getting content of existing note."""
        content = "# Test Note\n\nContent here."
        self.manager.create_note("Books", "test.md", content)

        retrieved_content = self.manager.get_note_content("Books", "test.md")

        self.assertEqual(retrieved_content, content)

    def test_get_note_content_returns_none_for_nonexistent(self):
        """Test get_note_content returns None for non-existent note."""
        content = self.manager.get_note_content("Books", "nonexistent.md")

        self.assertIsNone(content)

    def test_get_note_content_with_unicode(self):
        """Test getting content with Unicode characters."""
        content = "# Título\n\nConteúdo em português com acentuação."
        self.manager.create_note("Books", "test.md", content)

        retrieved_content = self.manager.get_note_content("Books", "test.md")

        self.assertEqual(retrieved_content, content)

    def test_ensure_folder_exists_creates_new_folder(self):
        """Test ensure_folder_exists creates folder if it doesn't exist."""
        result = self.manager.ensure_folder_exists("NewFolder")

        self.assertTrue(result)
        folder_path = self.vault_path / "NewFolder"
        self.assertTrue(folder_path.exists())
        self.assertTrue(folder_path.is_dir())

    def test_ensure_folder_exists_with_existing_folder(self):
        """Test ensure_folder_exists with folder that already exists."""
        # Create folder first
        folder_path = self.vault_path / "ExistingFolder"
        folder_path.mkdir()

        # Should succeed without error
        result = self.manager.ensure_folder_exists("ExistingFolder")

        self.assertTrue(result)

    def test_ensure_folder_exists_with_nested_path(self):
        """Test ensure_folder_exists with nested folder path."""
        result = self.manager.ensure_folder_exists("Books/Fiction/SciFi")

        self.assertTrue(result)
        folder_path = self.vault_path / "Books" / "Fiction" / "SciFi"
        self.assertTrue(folder_path.exists())

    def test_ensure_folder_exists_with_file_at_path_raises_error(self):
        """Test ensure_folder_exists raises error if path is a file."""
        # Create a file at the path
        file_path = self.vault_path / "Books"
        file_path.write_text("test")

        with self.assertRaises(ObsidianFileError) as context:
            self.manager.ensure_folder_exists("Books")

        self.assertIn("not a directory", str(context.exception))

    def test_create_multiple_notes_in_same_folder(self):
        """Test creating multiple notes in the same folder."""
        self.manager.create_note("Books", "book1.md", "# Book 1")
        self.manager.create_note("Books", "book2.md", "# Book 2")
        self.manager.create_note("Books", "book3.md", "# Book 3")

        self.assertTrue(self.manager.note_exists("Books", "book1.md"))
        self.assertTrue(self.manager.note_exists("Books", "book2.md"))
        self.assertTrue(self.manager.note_exists("Books", "book3.md"))

    def test_create_note_with_yaml_frontmatter(self):
        """Test creating note with YAML frontmatter."""
        content = """---
title: "Test Book"
author: Test Author
status: unread
---

# Test Book

Content here."""

        self.manager.create_note("Books", "test.md", content)

        note_path = self.vault_path / "Books" / "test.md"
        retrieved = note_path.read_text(encoding='utf-8')
        self.assertIn("---", retrieved)
        self.assertIn('title: "Test Book"', retrieved)
        self.assertIn("# Test Book", retrieved)

    def test_large_note_content(self):
        """Test creating note with large content."""
        # Create content with 10,000 lines
        content = "# Large Note\n\n" + "\n".join([f"Line {i}" for i in range(10000)])

        result = self.manager.create_note("Books", "large.md", content)

        self.assertTrue(result)
        retrieved = self.manager.get_note_content("Books", "large.md")
        self.assertIn("Line 9999", retrieved)


if __name__ == '__main__':
    unittest.main()
