# tests/adapters/obsidian/test_template_engine.py
import unittest
from datetime import datetime
from adapters.obsidian.template_engine import MarkdownTemplateEngine
from core.exceptions import ObsidianTemplateError


class TestMarkdownTemplateEngine(unittest.TestCase):
    """Unit tests for MarkdownTemplateEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = MarkdownTemplateEngine()

    def test_render_simple_template(self):
        """Test rendering a simple template with basic placeholders."""
        template = "# {{title}}\n\nBy {{author}}"
        data = {"title": "Test Book", "author": "Test Author"}

        result = self.engine.render(template, data)

        self.assertIn("# Test Book", result)
        self.assertIn("By Test Author", result)

    def test_render_with_missing_placeholders(self):
        """Test that missing placeholders render as empty strings."""
        template = "# {{title}}\n\n{{description}}\n\n{{missing}}"
        data = {"title": "Test Book", "description": "A test book"}

        result = self.engine.render(template, data)

        self.assertIn("# Test Book", result)
        self.assertIn("A test book", result)
        # Missing placeholder should not appear
        self.assertNotIn("{{missing}}", result)

    def test_render_with_date_placeholder(self):
        """Test DATE placeholder with format string."""
        template = "Created: {{DATE:YYYY-MM-DD}}"
        data = {}

        result = self.engine.render(template, data)

        # Should contain current date in YYYY-MM-DD format
        current_year = datetime.now().strftime("%Y")
        self.assertIn(current_year, result)
        self.assertIn("Created:", result)

    def test_render_with_date_placeholder_with_time(self):
        """Test DATE placeholder with datetime format."""
        template = "{{DATE:YYYY-MM-DD HH:mm:ss}}"
        data = {}

        result = self.engine.render(template, data)

        # Should contain date and time
        current_year = datetime.now().strftime("%Y")
        self.assertIn(current_year, result)
        # Should have time format (HH:mm:ss)
        self.assertRegex(result, r'\d{2}:\d{2}:\d{2}')

    def test_render_complex_template(self):
        """Test rendering a complex template with YAML frontmatter."""
        template = """---
title: "{{title}}"
author: [{{author}}]
status: {{status}}
---

# {{title}}

{{description}}

**Author:** {{author}}
"""
        data = {
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "status": "unread",
            "description": "A handbook of agile software craftsmanship"
        }

        result = self.engine.render(template, data)

        self.assertIn('title: "Clean Code"', result)
        self.assertIn('author: [Robert C. Martin]', result)
        self.assertIn('status: unread', result)
        self.assertIn('# Clean Code', result)
        self.assertIn('A handbook of agile software craftsmanship', result)

    def test_render_with_special_characters(self):
        """Test rendering with special characters in data."""
        template = "# {{title}}\n\n{{description}}"
        data = {
            "title": "Book: A Test & Example",
            "description": 'Contains "quotes" and other <special> chars'
        }

        result = self.engine.render(template, data)

        self.assertIn("Book: A Test & Example", result)
        self.assertIn('Contains "quotes"', result)
        self.assertIn("<special>", result)

    def test_render_with_unicode(self):
        """Test rendering with Unicode characters."""
        template = "# {{title}}\n\n{{author}}"
        data = {
            "title": "Título com Acentuação",
            "author": "José María García"
        }

        result = self.engine.render(template, data)

        self.assertIn("Título com Acentuação", result)
        self.assertIn("José María García", result)

    def test_render_with_empty_values(self):
        """Test rendering with empty string values."""
        template = "Title: {{title}}\nAuthor: {{author}}\nPublisher: {{publisher}}"
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "publisher": ""
        }

        result = self.engine.render(template, data)

        self.assertIn("Title: Test Book", result)
        self.assertIn("Author: Test Author", result)
        self.assertIn("Publisher:", result)

    def test_validate_template_valid(self):
        """Test validation of a valid template."""
        template = "# {{title}}\n\n{{description}}"

        is_valid, error = self.engine.validate_template(template)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_template_invalid_syntax(self):
        """Test validation of template with syntax error."""
        template = "# {{title}\n\n{{description}}"  # Missing closing brace

        is_valid, error = self.engine.validate_template(template)

        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("Syntax error", error)

    def test_validate_template_empty(self):
        """Test validation of empty template."""
        template = ""

        is_valid, error = self.engine.validate_template(template)

        self.assertTrue(is_valid)  # Empty template is technically valid
        self.assertIsNone(error)

    def test_get_placeholders(self):
        """Test extracting placeholders from template."""
        template = "# {{title}}\n\nBy {{author}}\n\n{{description}}\n\nStatus: {{status}}"

        placeholders = self.engine.get_placeholders(template)

        self.assertIn("title", placeholders)
        self.assertIn("author", placeholders)
        self.assertIn("description", placeholders)
        self.assertIn("status", placeholders)
        self.assertEqual(len(placeholders), 4)

    def test_get_placeholders_with_duplicates(self):
        """Test that duplicate placeholders are not repeated."""
        template = "{{title}} by {{author}}\n\n# {{title}}"

        placeholders = self.engine.get_placeholders(template)

        # Should only list each placeholder once
        self.assertEqual(placeholders.count("title"), 1)
        self.assertEqual(placeholders.count("author"), 1)

    def test_get_placeholders_no_placeholders(self):
        """Test extracting placeholders from template without any."""
        template = "This is plain text with no placeholders"

        placeholders = self.engine.get_placeholders(template)

        self.assertEqual(len(placeholders), 0)

    def test_render_invalid_template_raises_error(self):
        """Test that rendering invalid template raises appropriate error."""
        template = "# {{title}\n{{description}}"  # Invalid syntax
        data = {"title": "Test"}

        with self.assertRaises(ObsidianTemplateError) as context:
            self.engine.render(template, data)

        self.assertIn("syntax error", str(context.exception).lower())

    def test_render_with_conditional_blocks(self):
        """Test rendering with Jinja2 conditional blocks."""
        template = """# {{title}}

{% if description %}
{{description}}
{% endif %}

{% if author %}
**Author:** {{author}}
{% endif %}"""

        # Test with description
        data = {"title": "Book 1", "description": "A great book", "author": "John Doe"}
        result = self.engine.render(template, data)
        self.assertIn("A great book", result)
        self.assertIn("**Author:** John Doe", result)

        # Test without description
        data = {"title": "Book 2", "author": "Jane Doe"}
        result = self.engine.render(template, data)
        self.assertNotIn("A great book", result)
        self.assertIn("**Author:** Jane Doe", result)

    def test_render_multiline_description(self):
        """Test rendering with multi-line description."""
        template = "# {{title}}\n\n{{description}}"
        data = {
            "title": "Test Book",
            "description": "Line 1\nLine 2\nLine 3"
        }

        result = self.engine.render(template, data)

        self.assertIn("Line 1", result)
        self.assertIn("Line 2", result)
        self.assertIn("Line 3", result)


if __name__ == '__main__':
    unittest.main()
