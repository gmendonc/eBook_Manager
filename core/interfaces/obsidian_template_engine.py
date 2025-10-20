# core/interfaces/obsidian_template_engine.py
from typing import Protocol, Dict, Any, List, Tuple, Optional


class ObsidianTemplateEngine(Protocol):
    """
    Interface for processing Markdown templates with placeholders.

    This interface defines the contract for template rendering operations.
    Implementations should support Jinja2-style {{ placeholder }} syntax
    and handle missing placeholders gracefully.

    Template Processing Rules:
    - Placeholders use {{ variable_name }} syntax
    - Missing placeholders should render as empty strings (not error)
    - Date placeholders support format strings: {{DATE:YYYY-MM-DD}}
    - Template must be valid Markdown with YAML frontmatter
    """

    def render(self, template: str, data: Dict[str, Any]) -> str:
        """
        Render a template with provided data.

        Args:
            template: Template string with {{placeholder}} syntax
            data: Dictionary mapping placeholder names to values

        Returns:
            Rendered template as string

        Raises:
            ObsidianTemplateError: If template rendering fails due to
                                  syntax errors or other issues

        Example:
            >>> engine.render("# {{title}}\n{{description}}",
            ...               {"title": "Book", "description": "A great book"})
            "# Book\nA great book"
        """
        ...

    def validate_template(self, template: str) -> Tuple[bool, Optional[str]]:
        """
        Validate template syntax without rendering.

        Args:
            template: Template string to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if template is valid, False otherwise
            - error_message: Description of error if invalid, None if valid

        Example:
            >>> engine.validate_template("# {{title}}")
            (True, None)
            >>> engine.validate_template("# {{title")
            (False, "Unclosed placeholder at line 1")
        """
        ...

    def get_placeholders(self, template: str) -> List[str]:
        """
        Extract all placeholder names from a template.

        Args:
            template: Template string

        Returns:
            List of placeholder names (without {{ }})

        Example:
            >>> engine.get_placeholders("# {{title}}\n{{author}}")
            ["title", "author"]
        """
        ...
