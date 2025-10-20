# adapters/obsidian/template_engine.py
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from jinja2 import Template, TemplateSyntaxError, UndefinedError, Environment, meta

from core.interfaces.obsidian_template_engine import ObsidianTemplateEngine
from core.exceptions import ObsidianTemplateError


class MarkdownTemplateEngine:
    """
    Implementation of ObsidianTemplateEngine using Jinja2.

    This engine processes Markdown templates with {{placeholder}} syntax,
    supports date formatting, and handles missing placeholders gracefully.
    """

    def __init__(self):
        """Initialize the template engine."""
        self.logger = logging.getLogger(__name__)

        # Create Jinja2 environment with custom settings
        self.env = Environment(
            variable_start_string='{{',
            variable_end_string='}}',
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )

        # Register custom filters
        self.env.filters['date_format'] = self._date_format_filter

    def render(self, template: str, data: Dict[str, Any]) -> str:
        """
        Render a template with provided data.

        Args:
            template: Template string with {{placeholder}} syntax
            data: Dictionary mapping placeholder names to values

        Returns:
            Rendered template as string

        Raises:
            ObsidianTemplateError: If template rendering fails
        """
        try:
            # Pre-process template to handle DATE placeholders
            template = self._preprocess_date_placeholders(template)

            # Create Jinja2 template
            jinja_template = self.env.from_string(template)

            # Render with data, using empty string for undefined variables
            rendered = jinja_template.render(**data)

            # Post-process to clean up any remaining undefined placeholders
            rendered = self._clean_undefined_placeholders(rendered)

            self.logger.debug(f"Template rendered successfully ({len(rendered)} chars)")
            return rendered

        except TemplateSyntaxError as e:
            error_msg = f"Template syntax error at line {e.lineno}: {e.message}"
            self.logger.error(error_msg)
            raise ObsidianTemplateError(error_msg) from e

        except Exception as e:
            error_msg = f"Template rendering failed: {str(e)}"
            self.logger.error(error_msg)
            raise ObsidianTemplateError(error_msg) from e

    def validate_template(self, template: str) -> Tuple[bool, Optional[str]]:
        """
        Validate template syntax without rendering.

        Args:
            template: Template string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to parse the template
            self.env.from_string(template)
            self.logger.debug("Template validation successful")
            return True, None

        except TemplateSyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.message}"
            self.logger.warning(f"Template validation failed: {error_msg}")
            return False, error_msg

        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            self.logger.warning(f"Template validation failed: {error_msg}")
            return False, error_msg

    def get_placeholders(self, template: str) -> List[str]:
        """
        Extract all placeholder names from a template.

        Args:
            template: Template string

        Returns:
            List of placeholder names (without {{ }})
        """
        try:
            # Parse template to get AST
            ast = self.env.parse(template)
            # Extract undeclared variables (placeholders)
            placeholders = list(meta.find_undeclared_variables(ast))

            self.logger.debug(f"Found {len(placeholders)} placeholders: {placeholders}")
            return placeholders

        except Exception as e:
            self.logger.warning(f"Failed to extract placeholders: {str(e)}")
            # Fallback to regex extraction
            return self._extract_placeholders_regex(template)

    def _preprocess_date_placeholders(self, template: str) -> str:
        """
        Convert {{DATE:format}} placeholders to Jinja2 date filter syntax.

        Args:
            template: Original template string

        Returns:
            Template with processed date placeholders
        """
        # Pattern to match {{DATE:format}}
        date_pattern = r'\{\{DATE:([^}]+)\}\}'

        def replace_date(match):
            format_str = match.group(1)
            # Convert common format tokens to Python strftime format
            # YYYY -> %Y, MM -> %m, DD -> %d, HH -> %H, mm -> %M, ss -> %S
            python_format = format_str.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d')
            python_format = python_format.replace('HH', '%H').replace('mm', '%M').replace('ss', '%S')

            # Convert to current datetime with format
            current_date = datetime.now().strftime(python_format)
            return current_date

        processed = re.sub(date_pattern, replace_date, template)
        return processed

    def _clean_undefined_placeholders(self, rendered: str) -> str:
        """
        Clean up any remaining undefined placeholders (show as empty).

        Args:
            rendered: Rendered template string

        Returns:
            Cleaned string with undefined placeholders removed
        """
        # Remove any remaining {{ }} that weren't replaced
        cleaned = re.sub(r'\{\{[^}]*\}\}', '', rendered)
        return cleaned

    def _extract_placeholders_regex(self, template: str) -> List[str]:
        """
        Extract placeholders using regex (fallback method).

        Args:
            template: Template string

        Returns:
            List of placeholder names
        """
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, template)

        # Clean up placeholder names (remove spaces, filters, etc.)
        placeholders = []
        for match in matches:
            # Extract variable name before any filters or formatting
            var_name = match.split('|')[0].split(':')[0].strip()
            if var_name and var_name not in placeholders and not var_name.startswith('DATE'):
                placeholders.append(var_name)

        return placeholders

    def _date_format_filter(self, value, format_str='%Y-%m-%d'):
        """
        Jinja2 filter for date formatting.

        Args:
            value: Date value (datetime object or string)
            format_str: Format string (strftime format)

        Returns:
            Formatted date string
        """
        if isinstance(value, datetime):
            return value.strftime(format_str)
        elif isinstance(value, str):
            try:
                # Try to parse string as datetime
                dt = datetime.fromisoformat(value)
                return dt.strftime(format_str)
            except Exception:
                return value
        else:
            return str(value) if value else ''
