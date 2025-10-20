# Obsidian Export Feature - Detailed Task Breakdown

## Overview

This document provides a detailed breakdown of all tasks required to implement the Obsidian export feature. Tasks are organized by phase and include acceptance criteria, dependencies, and estimated complexity.

---

## Phase 1: Domain and Infrastructure (Foundation)

### Task 1.1: Create ObsidianExportConfig Dataclass

**File**: `core/domain/obsidian_export_config.py`

**Description**: Create configuration dataclass with all necessary fields for Obsidian export

**Acceptance Criteria**:
- [ ] Dataclass with all required fields defined
- [ ] Field validation in `__post_init__`
- [ ] Sensible default values
- [ ] Type hints for all fields
- [ ] Comprehensive docstrings

**Fields**:
- `vault_path: str` (required)
- `notes_folder: str` (default: "Books")
- `template_path: Optional[str]` (default: None)
- `filename_pattern: str` (default: "{title} - {author}")
- `default_status: str` (default: "unread")
- `default_priority: str` (default: "medium")
- `default_device: str` (default: "computer")
- `default_purpose: list` (default: ["read", "reference"])
- `overwrite_existing: bool` (default: False)
- `use_mcp_tools: bool` (default: True)
- `max_filename_length: int` (default: 200)
- `chunk_description: bool` (default: True)
- `description_chunk_size: int` (default: 1900)

**Complexity**: Low
**Estimated Time**: 30 minutes

---

### Task 1.2: Create ObsidianConfigRepository

**File**: `core/repositories/obsidian_config_repository.py`

**Description**: Repository for persisting and loading Obsidian configuration

**Acceptance Criteria**:
- [ ] `save_config(config: Dict[str, Any]) -> bool`
- [ ] `load_config() -> Dict[str, Any]`
- [ ] `update_session_state()` (for Streamlit)
- [ ] `save_from_session_state() -> bool`
- [ ] Uses JSON file: `obsidian_config.json`
- [ ] Handles file not found gracefully
- [ ] Handles JSON parsing errors
- [ ] Follows same pattern as NotionConfigRepository

**Dependencies**: Task 1.1

**Complexity**: Low
**Estimated Time**: 30 minutes

---

### Task 1.3: Create Default Template Constant

**File**: `adapters/obsidian/templates.py`

**Description**: Define default Markdown template as module constant

**Acceptance Criteria**:
- [ ] Module with `DEFAULT_TEMPLATE` constant
- [ ] Template includes YAML frontmatter
- [ ] All placeholders documented
- [ ] Valid Markdown structure
- [ ] Matches spec from requirements

**Template Structure**:
```markdown
---
tag: 📚Book
title: "{{title}}"
author: [{{author}}]
publisher: {{publisher}}
publish: {{publishDate}}
total: {{totalPage}}
isbn: {{isbn10}} {{isbn13}}
cover: {{coverUrl}}
status: {{status}}
created: {{created}}
updated: {{updated}}
format: [{{format}}]
priority: {{priority}}
macrotemas: []
purpose: {{purpose}}
device: {{device}}
---

![cover|150]({{coverUrl}})

# {{title}}

{{description}}

---

**Publisher:** {{publisher}}
**Published:** {{publishDate}}
**Pages:** {{totalPage}}
**ISBN:** {{isbn13}}
**Language:** {{language}}
**Categories:** {{categories}}

**Preview:** {{preview_link}}
```

**Complexity**: Low
**Estimated Time**: 15 minutes

---

### Task 1.4: Create Custom Exceptions

**File**: `core/exceptions.py` (modify existing or create)

**Description**: Define custom exceptions for Obsidian export

**Acceptance Criteria**:
- [ ] `ObsidianExportError(Exception)` - Base exception
- [ ] `ObsidianConfigError(ObsidianExportError)` - Configuration errors
- [ ] `ObsidianTemplateError(ObsidianExportError)` - Template errors
- [ ] `ObsidianFileError(ObsidianExportError)` - File operation errors
- [ ] All inherit from base application exception
- [ ] Docstrings explain when to use each

**Complexity**: Low
**Estimated Time**: 15 minutes

---

## Phase 2: Core Interfaces (Contracts)

### Task 2.1: Create ObsidianFileManager Interface

**File**: `core/interfaces/obsidian_file_manager.py`

**Description**: Define interface for file operations in Obsidian vault

**Acceptance Criteria**:
- [ ] Protocol-based interface (like Notion interfaces)
- [ ] `create_note(folder: str, filename: str, content: str) -> bool`
- [ ] `update_note(folder: str, filename: str, content: str) -> bool`
- [ ] `note_exists(folder: str, filename: str) -> bool`
- [ ] `get_note_content(folder: str, filename: str) -> Optional[str]`
- [ ] `ensure_folder_exists(folder: str) -> bool`
- [ ] All methods have comprehensive docstrings
- [ ] Type hints for all parameters and returns

**Complexity**: Low
**Estimated Time**: 30 minutes

---

### Task 2.2: Create ObsidianTemplateEngine Interface

**File**: `core/interfaces/obsidian_template_engine.py`

**Description**: Define interface for template processing

**Acceptance Criteria**:
- [ ] Protocol-based interface
- [ ] `render(template: str, data: Dict[str, Any]) -> str`
- [ ] `validate_template(template: str) -> Tuple[bool, Optional[str]]`
- [ ] `get_placeholders(template: str) -> List[str]`
- [ ] All methods have comprehensive docstrings
- [ ] Type hints for all parameters and returns

**Complexity**: Low
**Estimated Time**: 20 minutes

---

### Task 2.3: Create ObsidianRecordMapper Interface

**File**: `core/interfaces/obsidian_record_mapper.py`

**Description**: Define interface for mapping CSV records to template data

**Acceptance Criteria**:
- [ ] Protocol-based interface
- [ ] `map_record(record: Dict[str, Any], config: ObsidianExportConfig) -> Dict[str, Any]`
- [ ] `sanitize_filename(filename: str, max_length: int) -> str`
- [ ] `generate_filename(record: Dict[str, Any], pattern: str, max_length: int) -> str`
- [ ] All methods have comprehensive docstrings
- [ ] Type hints for all parameters and returns

**Dependencies**: Task 1.1

**Complexity**: Low
**Estimated Time**: 20 minutes

---

## Phase 3: Template Engine (Markdown Generation)

### Task 3.1: Implement MarkdownTemplateEngine

**File**: `adapters/obsidian/template_engine.py`

**Description**: Implement template processing with Jinja2

**Acceptance Criteria**:
- [ ] Implements `ObsidianTemplateEngine` interface
- [ ] Uses Jinja2 for template rendering
- [ ] Supports `{{placeholder}}` syntax
- [ ] Supports date formatting: `{{DATE:YYYY-MM-DD}}`
- [ ] Handles missing placeholders gracefully (empty string)
- [ ] `render()` method works with template and data dict
- [ ] `validate_template()` checks syntax and returns errors
- [ ] `get_placeholders()` extracts all placeholders from template
- [ ] Comprehensive error handling
- [ ] Logging for debugging

**Dependencies**: Task 2.2

**Complexity**: Medium
**Estimated Time**: 2 hours

**Technical Details**:
- Use Jinja2 `Template` class
- Configure to use `{{` and `}}` delimiters
- Add custom filter for date formatting
- Handle Jinja2 exceptions gracefully

---

### Task 3.2: Add Date Formatting Support

**File**: `adapters/obsidian/template_engine.py` (extend Task 3.1)

**Description**: Add custom Jinja2 filter for date formatting

**Acceptance Criteria**:
- [ ] Custom filter `date_format` registered with Jinja2
- [ ] Supports format strings: YYYY, MM, DD, HH, mm, ss
- [ ] `{{DATE:YYYY-MM-DD}}` renders current date
- [ ] `{{DATE:YYYY-MM-DD HH:mm:ss}}` renders current datetime
- [ ] Handles invalid format strings gracefully

**Dependencies**: Task 3.1

**Complexity**: Low
**Estimated Time**: 30 minutes

---

### Task 3.3: Write Unit Tests for Template Engine

**File**: `tests/adapters/obsidian/test_template_engine.py`

**Description**: Comprehensive unit tests for template engine

**Test Cases**:
- [ ] Render simple template with basic placeholders
- [ ] Render template with missing placeholders (should use empty string)
- [ ] Date formatting with various format strings
- [ ] Invalid template syntax (should return validation error)
- [ ] Extract placeholders from template
- [ ] Edge cases: empty template, template with no placeholders
- [ ] Special characters in placeholder values

**Dependencies**: Task 3.1, Task 3.2

**Complexity**: Medium
**Estimated Time**: 1 hour

---

## Phase 4: Record Mapper (Data Transformation)

### Task 4.1: Implement GoogleBooksObsidianRecordMapper

**File**: `adapters/obsidian/record_mapper.py`

**Description**: Map CSV records to template data with priority fallback

**Acceptance Criteria**:
- [ ] Implements `ObsidianRecordMapper` interface
- [ ] `map_record()` returns Dict[str, Any] with all placeholders
- [ ] Priority mapping: GB_* fields > extracted fields > defaults
- [ ] All placeholders from template supported
- [ ] Date fields formatted correctly
- [ ] URL fields validated
- [ ] Multi-value fields (authors, categories) handled
- [ ] Missing fields use empty string or config defaults
- [ ] Logging for debugging mapping decisions

**Dependencies**: Task 2.3, Task 1.1

**Complexity**: Medium
**Estimated Time**: 2 hours

**Field Mappings to Implement**:
- `title`: GB_Titulo > Titulo_Extraido > Nome (no extension)
- `author`: GB_Autores > Autor_Extraido > "Unknown Author"
- `publisher`: GB_Editora > ""
- `publishDate`: GB_Data_Publicacao > ""
- `totalPage`: GB_Paginas > ""
- `isbn10`: GB_ISBN10 > ""
- `isbn13`: GB_ISBN13 > ""
- `coverUrl`: GB_Capa_Link > ""
- `description`: GB_Descricao > ""
- `categories`: GB_Categorias > ""
- `language`: GB_Idioma > ""
- `preview_link`: GB_Preview_Link > ""
- `format`: Formato (lowercase)
- `file_size`: Tamanho(MB)
- `file_path`: Caminho
- `modified_date`: Data Modificação
- `created`: current datetime
- `updated`: current datetime
- `status`: config.default_status
- `priority`: config.default_priority
- `device`: config.default_device
- `purpose`: config.default_purpose (as comma-separated string)

---

### Task 4.2: Implement Filename Sanitization

**File**: `adapters/obsidian/record_mapper.py` (extend Task 4.1)

**Description**: Sanitize filenames for filesystem compatibility

**Acceptance Criteria**:
- [ ] `sanitize_filename()` removes invalid characters
- [ ] Removes: `:`, `/`, `\`, `*`, `?`, `"`, `<`, `>`, `|`
- [ ] Collapses multiple spaces to single space
- [ ] Strips leading/trailing whitespace
- [ ] Truncates to max_length
- [ ] Preserves `.md` extension
- [ ] Handles empty filename (returns default)
- [ ] Handles Unicode characters correctly

**Dependencies**: Task 4.1

**Complexity**: Medium
**Estimated Time**: 1 hour

---

### Task 4.3: Implement Filename Generation from Pattern

**File**: `adapters/obsidian/record_mapper.py` (extend Task 4.1)

**Description**: Generate filename from pattern with placeholder substitution

**Acceptance Criteria**:
- [ ] `generate_filename()` processes pattern
- [ ] Supports placeholders: `{title}`, `{author}`, `{publisher}`, `{isbn}`, `{format}`
- [ ] Replaces placeholders with record data
- [ ] Sanitizes result
- [ ] Truncates to max_length
- [ ] Adds `.md` extension if not present
- [ ] Handles missing data in pattern placeholders

**Dependencies**: Task 4.2

**Complexity**: Medium
**Estimated Time**: 1 hour

**Examples**:
- Pattern: `{title} - {author}` → `Clean Code - Robert C. Martin.md`
- Pattern: `[{format}] {title}` → `[pdf] Clean Code.md`
- Pattern: `{author}/{title}` → Invalid (/ removed) → `author title.md`

---

### Task 4.4: Write Unit Tests for Record Mapper

**File**: `tests/adapters/obsidian/test_record_mapper.py`

**Description**: Comprehensive unit tests for record mapper

**Test Cases**:
- [ ] Map record with all Google Books fields present
- [ ] Map record with only basic fields (no GB_*)
- [ ] Map record with missing fields (uses defaults)
- [ ] Filename sanitization with various invalid characters
- [ ] Filename generation with different patterns
- [ ] Filename truncation when too long
- [ ] Unicode in titles and authors
- [ ] Edge case: empty record
- [ ] Edge case: all fields empty except Nome

**Dependencies**: Task 4.1, Task 4.2, Task 4.3

**Complexity**: Medium
**Estimated Time**: 1.5 hours

---

## Phase 5: File Managers (File Operations)

### Task 5.1: Implement FilesystemFileManager

**File**: `adapters/obsidian/filesystem_file_manager.py`

**Description**: Direct filesystem operations for Obsidian vault

**Acceptance Criteria**:
- [ ] Implements `ObsidianFileManager` interface
- [ ] `create_note()` creates file in vault
- [ ] `update_note()` overwrites existing file
- [ ] `note_exists()` checks if file exists
- [ ] `get_note_content()` reads file content
- [ ] `ensure_folder_exists()` creates directory if needed
- [ ] Uses pathlib for path operations
- [ ] UTF-8 encoding for all file operations
- [ ] Comprehensive error handling
- [ ] Logging for all operations

**Dependencies**: Task 2.1

**Complexity**: Medium
**Estimated Time**: 2 hours

**Technical Details**:
- Use `pathlib.Path` for all path operations
- `vault_path / notes_folder / filename`
- Create parent directories with `mkdir(parents=True, exist_ok=True)`
- Write with `open(..., 'w', encoding='utf-8')`
- Handle `FileNotFoundError`, `PermissionError`, `IOError`

---

### Task 5.2: Implement McpFileManager

**File**: `adapters/obsidian/mcp_file_manager.py`

**Description**: Use MCP tools for Obsidian vault operations

**Acceptance Criteria**:
- [ ] Implements `ObsidianFileManager` interface
- [ ] Uses `obsidian-mcp-tools:create_vault_file` for creation
- [ ] Uses `obsidian-mcp-tools:get_vault_file` for reading
- [ ] Handles MCP tool unavailability gracefully
- [ ] Falls back to FilesystemFileManager on error
- [ ] Logs when using fallback
- [ ] All operations work through MCP when available

**Dependencies**: Task 2.1, Task 5.1

**Complexity**: Medium
**Estimated Time**: 1.5 hours

**Technical Details**:
- Check if MCP tools available before using
- Wrap MCP calls in try-except
- Fall back to filesystem manager on exception
- Log MCP availability status

---

### Task 5.3: Write Unit Tests for FilesystemFileManager

**File**: `tests/adapters/obsidian/test_filesystem_file_manager.py`

**Description**: Unit tests for filesystem file manager

**Test Cases**:
- [ ] Create note in existing folder
- [ ] Create note in non-existing folder (creates folder)
- [ ] Update existing note
- [ ] Check if note exists (exists)
- [ ] Check if note exists (doesn't exist)
- [ ] Get note content (exists)
- [ ] Get note content (doesn't exist, returns None)
- [ ] Ensure folder exists (creates if needed)
- [ ] Handle permission errors gracefully
- [ ] Handle invalid paths

**Dependencies**: Task 5.1

**Complexity**: Medium
**Estimated Time**: 1.5 hours

**Setup**:
- Use `pytest` with `tmp_path` fixture
- Create temporary vault for testing
- Clean up after each test

---

### Task 5.4: Write Unit Tests for McpFileManager

**File**: `tests/adapters/obsidian/test_mcp_file_manager.py`

**Description**: Unit tests for MCP file manager with mocking

**Test Cases**:
- [ ] Create note via MCP (success)
- [ ] Create note via MCP (fails, uses fallback)
- [ ] Get note content via MCP (success)
- [ ] Get note content via MCP (fails, uses fallback)
- [ ] Check note exists via MCP
- [ ] MCP tools unavailable (uses fallback for all operations)

**Dependencies**: Task 5.2

**Complexity**: Medium
**Estimated Time**: 1 hour

**Setup**:
- Mock MCP tool functions
- Test both success and failure paths
- Verify fallback is used when needed

---

## Phase 6: Export Service (Orchestration)

### Task 6.1: Implement ObsidianExportService

**File**: `core/services/obsidian_export_service.py`

**Description**: Orchestrate entire export workflow

**Acceptance Criteria**:
- [ ] Constructor accepts all dependencies via DI
- [ ] `export_csv_to_obsidian(csv_path: str) -> Tuple[bool, int, int, int, List[str]]`
- [ ] Returns: (success, success_count, skipped_count, error_count, error_messages)
- [ ] Reads CSV file
- [ ] Processes each record:
  - Map record to template data
  - Render template
  - Generate filename
  - Check if exists (skip if needed)
  - Create/update note
  - Track progress
- [ ] Collects errors (max 50)
- [ ] Comprehensive logging
- [ ] Yields progress for UI (generator pattern or callback)

**Dependencies**: Task 1.1, Task 2.1, Task 2.2, Task 2.3

**Complexity**: High
**Estimated Time**: 3 hours

**Constructor Signature**:
```python
def __init__(
    self,
    config: ObsidianExportConfig,
    file_manager: ObsidianFileManager,
    template_engine: ObsidianTemplateEngine,
    record_mapper: ObsidianRecordMapper
):
```

**Method Signature**:
```python
def export_csv_to_obsidian(
    self,
    csv_path: str
) -> Tuple[bool, int, int, int, List[str]]:
    """
    Returns:
        (overall_success, successful_count, skipped_count, error_count, error_messages)
    """
```

---

### Task 6.2: Add Progress Tracking to Export Service

**File**: `core/services/obsidian_export_service.py` (extend Task 6.1)

**Description**: Add callback mechanism for progress updates

**Acceptance Criteria**:
- [ ] Constructor accepts optional `progress_callback` parameter
- [ ] Callback signature: `Callable[[int, int], None]` (current, total)
- [ ] Callback called after each record processed
- [ ] Callback called at start (0, total) and end (total, total)
- [ ] Handles callback exceptions gracefully

**Dependencies**: Task 6.1

**Complexity**: Low
**Estimated Time**: 30 minutes

---

### Task 6.3: Add Template Loading Logic

**File**: `core/services/obsidian_export_service.py` (extend Task 6.1)

**Description**: Load custom or default template

**Acceptance Criteria**:
- [ ] Private method `_load_template() -> str`
- [ ] If config.template_path exists, read and validate
- [ ] If validation fails, log warning and use default
- [ ] If template_path is None, use default template
- [ ] Handle file read errors gracefully
- [ ] Cache loaded template (don't re-read for each record)

**Dependencies**: Task 6.1, Task 1.3

**Complexity**: Medium
**Estimated Time**: 1 hour

---

### Task 6.4: Write Unit Tests for Export Service

**File**: `tests/core/services/test_obsidian_export_service.py`

**Description**: Unit tests for export service with mocked dependencies

**Test Cases**:
- [ ] Export with all records successful
- [ ] Export with some records failing (collects errors, continues)
- [ ] Export with all records failing
- [ ] Export with overwrite_existing=True (updates existing)
- [ ] Export with overwrite_existing=False (skips existing)
- [ ] Custom template loaded and used
- [ ] Custom template invalid (falls back to default)
- [ ] Progress callback called correctly
- [ ] CSV file not found (raises error)
- [ ] Empty CSV file (no errors, 0 exports)

**Dependencies**: Task 6.1, Task 6.2, Task 6.3

**Complexity**: High
**Estimated Time**: 3 hours

**Setup**:
- Mock all dependencies (FileManager, TemplateEngine, RecordMapper)
- Use pytest fixtures for common setups
- Test with sample CSV data

---

## Phase 7: UI Configuration (User Settings)

### Task 7.1: Create Obsidian Config Page

**File**: `ui/pages/obsidian_config_page.py`

**Description**: Streamlit page for configuring Obsidian export

**Acceptance Criteria**:
- [ ] Function `render_obsidian_config_page(library_service, app_state)`
- [ ] Form with all configuration fields
- [ ] Vault path input with validation
- [ ] Notes folder input
- [ ] Template selection (default/custom)
- [ ] Custom template file upload
- [ ] Filename pattern input with preview
- [ ] Default values section (status, priority, device, purpose)
- [ ] Advanced options (overwrite, use MCP)
- [ ] Save button saves to repository
- [ ] Load existing configuration on page load
- [ ] Success/error messages

**Dependencies**: Task 1.2

**Complexity**: High
**Estimated Time**: 3 hours

**Fields**:
1. Vault path (text input + validation)
2. Notes folder (text input, default: "Books")
3. Template option (radio: default/custom)
4. Custom template upload (file uploader, shown if custom selected)
5. Filename pattern (text input, default: "{title} - {author}")
6. Filename preview (shows example with sample data)
7. Default status (select: unread, reading, finished)
8. Default priority (select: low, medium, high, top)
9. Default device (select: computer, kindle, ipad)
10. Default purpose (multiselect: read, reference)
11. Overwrite existing (checkbox)
12. Use MCP tools (checkbox)

---

### Task 7.2: Add Vault Path Validation

**File**: `ui/pages/obsidian_config_page.py` (extend Task 7.1)

**Description**: Validate vault path exists and is accessible

**Acceptance Criteria**:
- [ ] Check if path exists (filesystem check)
- [ ] Show warning if path doesn't exist
- [ ] Show info about creating folder if needed
- [ ] Visual indicator (green check or red X)

**Dependencies**: Task 7.1

**Complexity**: Low
**Estimated Time**: 30 minutes

---

### Task 7.3: Add Filename Pattern Preview

**File**: `ui/pages/obsidian_config_page.py` (extend Task 7.1)

**Description**: Show preview of generated filename

**Acceptance Criteria**:
- [ ] Live preview as user types pattern
- [ ] Uses sample book data for preview
- [ ] Shows sanitized result
- [ ] Shows warning if pattern is invalid

**Dependencies**: Task 7.1, Task 4.3

**Complexity**: Medium
**Estimated Time**: 1 hour

**Sample Data**:
- Title: "Clean Code: A Handbook of Agile Software Craftsmanship"
- Author: "Robert C. Martin"
- Format: "pdf"
- ISBN: "9780132350884"

---

### Task 7.4: Add Template Preview

**File**: `ui/pages/obsidian_config_page.py` (extend Task 7.1)

**Description**: Show preview of rendered template

**Acceptance Criteria**:
- [ ] Expandable section "Preview Template"
- [ ] Renders template with sample data
- [ ] Shows first 500 characters
- [ ] Updates when custom template uploaded

**Dependencies**: Task 7.1, Task 3.1

**Complexity**: Medium
**Estimated Time**: 1 hour

---

## Phase 8: UI Export Component (Export Interface)

### Task 8.1: Create Obsidian Export Component

**File**: `ui/components/obsidian_export_component.py`

**Description**: UI component for triggering export and showing progress

**Acceptance Criteria**:
- [ ] Function `render_obsidian_export_button(csv_path: str, app_state)`
- [ ] "Export to Obsidian" button
- [ ] Validates configuration before export
- [ ] Shows validation errors if config incomplete
- [ ] Disables button during export
- [ ] Shows progress bar during export
- [ ] Shows progress percentage
- [ ] Shows current book being processed
- [ ] Shows summary on completion

**Dependencies**: Task 1.2, Task 6.1

**Complexity**: High
**Estimated Time**: 2.5 hours

---

### Task 8.2: Add Progress Tracking to UI

**File**: `ui/components/obsidian_export_component.py` (extend Task 8.1)

**Description**: Real-time progress updates during export

**Acceptance Criteria**:
- [ ] Streamlit progress bar
- [ ] Progress percentage (e.g., "Processing 45/150...")
- [ ] Current book title being processed
- [ ] Estimated time remaining (optional)

**Dependencies**: Task 8.1, Task 6.2

**Complexity**: Medium
**Estimated Time**: 1.5 hours

**Technical Details**:
- Use `st.progress()` for bar
- Use `st.empty()` for updating text
- Update via progress callback

---

### Task 8.3: Add Export Summary Display

**File**: `ui/components/obsidian_export_component.py` (extend Task 8.1)

**Description**: Display export results summary

**Acceptance Criteria**:
- [ ] Shows total records processed
- [ ] Shows successful count (green)
- [ ] Shows skipped count (yellow)
- [ ] Shows error count (red)
- [ ] Expandable error list
- [ ] Each error shows book title and error message
- [ ] Success message if all succeeded
- [ ] Warning message if some failed

**Dependencies**: Task 8.1

**Complexity**: Medium
**Estimated Time**: 1 hour

**Layout**:
```
✅ Export completed!

📊 Summary:
- Total: 150
- Successful: 145 ✓
- Skipped: 3 (already exist)
- Errors: 2 ✗

[View Errors ▼]
  1. "Book Title 1" - Failed to create note: Permission denied
  2. "Book Title 2" - Template rendering error: Invalid placeholder
```

---

### Task 8.4: Integrate Export Component in Main UI

**File**: `ui/pages/library_page.py` or `app.py` (modify existing)

**Description**: Add Obsidian export button to library view

**Acceptance Criteria**:
- [ ] "Export to Obsidian" button next to "Export to Notion"
- [ ] Only shown when CSV loaded
- [ ] Opens export component when clicked
- [ ] Uses current loaded CSV path

**Dependencies**: Task 8.1

**Complexity**: Low
**Estimated Time**: 30 minutes

---

## Phase 9: Integration and Testing

### Task 9.1: Create End-to-End Integration Test

**File**: `tests/integration/test_obsidian_export_e2e.py`

**Description**: Full integration test of export workflow

**Test Scenario**:
1. Create temporary vault directory
2. Create sample CSV with enriched data
3. Create ObsidianExportService with real implementations
4. Run export
5. Verify notes created in vault
6. Verify note content matches expected
7. Verify YAML frontmatter is valid
8. Clean up

**Acceptance Criteria**:
- [ ] Test with 10 sample books
- [ ] Uses real FilesystemFileManager
- [ ] Uses real MarkdownTemplateEngine
- [ ] Uses real GoogleBooksObsidianRecordMapper
- [ ] Verifies all 10 notes created
- [ ] Verifies note content structure
- [ ] Verifies frontmatter parsing
- [ ] Tests with custom template
- [ ] Tests with default template
- [ ] Tests overwrite behavior

**Dependencies**: All implementation tasks

**Complexity**: High
**Estimated Time**: 3 hours

---

### Task 9.2: Test with Real Obsidian Vault

**Description**: Manual test with actual Obsidian installation

**Test Steps**:
1. Set up test Obsidian vault
2. Configure export with vault path
3. Export sample library (50+ books)
4. Open vault in Obsidian
5. Verify notes display correctly
6. Verify frontmatter is recognized
7. Verify images load (if URLs valid)
8. Verify links work

**Acceptance Criteria**:
- [ ] All notes created successfully
- [ ] Notes open in Obsidian without errors
- [ ] Frontmatter displays in properties panel
- [ ] Cover images display (when URLs valid)
- [ ] Preview links work
- [ ] Tags are recognized

**Dependencies**: All implementation tasks

**Complexity**: Medium
**Estimated Time**: 1 hour

---

### Task 9.3: Test Error Scenarios

**File**: `tests/integration/test_obsidian_export_errors.py`

**Description**: Test various error scenarios

**Test Cases**:
- [ ] Vault path doesn't exist (should fail with clear error)
- [ ] No write permissions (should fail with clear error)
- [ ] CSV file not found (should fail immediately)
- [ ] CSV file empty (should complete with 0 exports)
- [ ] CSV missing required columns (should use defaults)
- [ ] Custom template has syntax error (should fall back to default)
- [ ] Custom template file not found (should fall back to default)
- [ ] Disk full (should fail gracefully)
- [ ] Very long filename (should truncate)
- [ ] Special characters in path (should handle)

**Dependencies**: All implementation tasks

**Complexity**: Medium
**Estimated Time**: 2 hours

---

### Task 9.4: Test Performance with Large Dataset

**File**: `tests/integration/test_obsidian_export_performance.py`

**Description**: Test with large number of books

**Test Scenario**:
- Generate CSV with 1000+ books
- Run export
- Measure time
- Verify memory usage
- Verify all books exported

**Acceptance Criteria**:
- [ ] Completes export of 1000 books
- [ ] Completes in reasonable time (< 5 minutes)
- [ ] Memory usage stays reasonable (< 500MB)
- [ ] Progress updates work smoothly
- [ ] No crashes or hangs

**Dependencies**: All implementation tasks

**Complexity**: Medium
**Estimated Time**: 1.5 hours

---

### Task 9.5: Test MCP Tools Integration

**Description**: Manual test with MCP tools if available

**Test Steps**:
1. Set up MCP tools in environment
2. Configure to use MCP tools
3. Run export
4. Verify MCP tools are called
5. Verify notes created correctly
6. Test MCP fallback (disable MCP, verify uses filesystem)

**Acceptance Criteria**:
- [ ] MCP tools detected when available
- [ ] Export uses MCP tools successfully
- [ ] Falls back to filesystem when MCP unavailable
- [ ] Logs indicate which method used

**Dependencies**: Task 5.2

**Complexity**: Medium
**Estimated Time**: 1 hour

**Note**: May be skipped if MCP tools not available in environment

---

## Phase 10: Documentation and Polish

### Task 10.1: Add Logging Throughout

**Files**: All implementation files

**Description**: Ensure comprehensive logging

**Acceptance Criteria**:
- [ ] All services log start/end of operations
- [ ] All errors logged with ERROR level
- [ ] All warnings logged with WARNING level
- [ ] Debug logging for detailed operations
- [ ] Logger names follow module structure
- [ ] No sensitive data in logs

**Dependencies**: All implementation tasks

**Complexity**: Medium
**Estimated Time**: 2 hours

**Logging Levels**:
- DEBUG: Template rendering, field mapping decisions
- INFO: Export started, export completed, progress updates
- WARNING: Fallback to default template, MCP unavailable
- ERROR: File operation failures, validation errors

---

### Task 10.2: Refine Error Messages

**Files**: All implementation files

**Description**: Ensure error messages are user-friendly

**Acceptance Criteria**:
- [ ] All user-facing errors are clear and actionable
- [ ] No technical jargon in UI error messages
- [ ] Errors suggest solutions when possible
- [ ] Errors include relevant context (filename, book title)

**Dependencies**: All implementation tasks

**Complexity**: Low
**Estimated Time**: 1 hour

**Examples**:
- ❌ "FileNotFoundError: [Errno 2] No such file or directory"
- ✅ "Vault path not found: /path/to/vault. Please check the path in settings."

- ❌ "Jinja2TemplateError: unexpected char '(' at line 5"
- ✅ "Template syntax error at line 5. Using default template instead."

---

### Task 10.3: Add Inline Code Documentation

**Files**: All implementation files

**Description**: Ensure all code is well-documented

**Acceptance Criteria**:
- [ ] All public functions have docstrings (Google style)
- [ ] All classes have docstrings
- [ ] All interfaces have comprehensive docstrings
- [ ] Complex logic has explanatory comments
- [ ] Type hints on all function signatures

**Dependencies**: All implementation tasks

**Complexity**: Medium
**Estimated Time**: 2 hours

---

### Task 10.4: Create Example Template File

**File**: `examples/obsidian_book_template.md`

**Description**: Provide example custom template

**Acceptance Criteria**:
- [ ] Valid Markdown with YAML frontmatter
- [ ] Uses variety of placeholders
- [ ] Well-commented to explain usage
- [ ] Different from default template (shows customization)

**Complexity**: Low
**Estimated Time**: 30 minutes

---

### Task 10.5: Update README

**File**: `README.md`

**Description**: Document Obsidian export feature

**Sections to Add**:
- [ ] "Obsidian Export" section
- [ ] Configuration steps
- [ ] Available template placeholders
- [ ] Custom template instructions
- [ ] Filename pattern examples
- [ ] Troubleshooting common issues
- [ ] Screenshots (optional)

**Dependencies**: All implementation tasks

**Complexity**: Low
**Estimated Time**: 1 hour

---

### Task 10.6: Create Architecture Documentation

**File**: `.claude/ARCHITECTURE.md` (update existing or create new section)

**Description**: Document Obsidian export architecture

**Sections to Add**:
- [ ] Component diagram
- [ ] Data flow diagram
- [ ] Interface descriptions
- [ ] Design decisions
- [ ] SOLID principles application

**Dependencies**: All implementation tasks

**Complexity**: Medium
**Estimated Time**: 1.5 hours

---

## Summary

### Total Tasks: 62

### Estimated Time by Phase:
- **Phase 1**: 2 hours
- **Phase 2**: 1.5 hours
- **Phase 3**: 3.5 hours
- **Phase 4**: 5.5 hours
- **Phase 5**: 8 hours
- **Phase 6**: 7.5 hours
- **Phase 7**: 6.5 hours
- **Phase 8**: 5.5 hours
- **Phase 9**: 9.5 hours
- **Phase 10**: 8 hours

### Total Estimated Time: ~57.5 hours (~7-8 working days)

### Complexity Breakdown:
- **Low**: 17 tasks (~13 hours)
- **Medium**: 27 tasks (~29 hours)
- **High**: 8 tasks (~15.5 hours)

### Critical Path:
1. Phase 1-2: Foundation (required for all)
2. Phase 3-4-5: Core implementations (can be parallelized)
3. Phase 6: Service (depends on 3, 4, 5)
4. Phase 7-8: UI (depends on 6)
5. Phase 9: Testing (depends on all)
6. Phase 10: Polish (can overlap with 9)

### Dependencies Graph:
```
Phase 1 (Foundation)
  ↓
Phase 2 (Interfaces)
  ↓
Phase 3 (Template) ──┐
Phase 4 (Mapper) ────┤
Phase 5 (File Mgr) ──┤
  ↓                   ↓
Phase 6 (Service) ←───┘
  ↓
Phase 7 (Config UI)
Phase 8 (Export UI)
  ↓
Phase 9 (Testing)
  ↓
Phase 10 (Polish)
```

### Next Steps:
1. Review and approve this task breakdown
2. Begin with Phase 1 tasks
3. Create feature branch: `feature/obsidian-export`
4. Implement in order, testing as you go
5. Create PR when ready for review
