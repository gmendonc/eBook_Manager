# Obsidian Export Feature - Implementation Plan

## Executive Summary

This document outlines the strategy for implementing Obsidian export functionality in the eBook Manager application. The implementation will follow the existing architecture patterns established by the Notion export feature, adhering to SOLID principles, Clean Architecture, and Black Box Design.

## Goals

1. **Export library to Obsidian**: Enable users to export their enriched ebook library as Markdown notes in their Obsidian vault
2. **Customizable templates**: Support both default and custom Markdown templates with YAML frontmatter
3. **Flexible configuration**: Allow users to configure export behavior, file naming, and default values
4. **Robust error handling**: Gracefully handle errors while continuing to process remaining books
5. **MCP integration**: Use Obsidian MCP tools when available, with filesystem fallback

## Architecture Strategy

### Following Existing Patterns

The Obsidian export will mirror the Notion export architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                         UI Layer                            │
│  - obsidian_config_page.py (configuration interface)       │
│  - obsidian_export_component.py (export button/progress)   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Application Layer                         │
│  - obsidian_export_service.py (orchestrates export)        │
│  - Uses interfaces, not concrete implementations           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Interface Layer                           │
│  - ObsidianFileManager (create/update notes)               │
│  - ObsidianTemplateEngine (process templates)              │
│  - ObsidianRecordMapper (CSV → template data)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Adapter Layer                            │
│  - McpFileManager (uses MCP tools)                         │
│  - FilesystemFileManager (direct file operations)          │
│  - MarkdownTemplateEngine (Jinja2-based)                   │
│  - GoogleBooksRecordMapper (maps enriched CSV data)        │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

#### 1. **Dependency Inversion (DIP)**
- Service depends on interfaces, not implementations
- Adapters implement interfaces defined in core layer
- Concrete implementations injected via constructor

#### 2. **Single Responsibility (SRP)**
- `ObsidianExportService`: Orchestrate export workflow
- `ObsidianFileManager`: Handle file creation/updates
- `ObsidianTemplateEngine`: Process template placeholders
- `ObsidianRecordMapper`: Map CSV data to template variables
- `ObsidianConfigRepository`: Persist/load configuration

#### 3. **Open/Closed (OCP)**
- New file managers can be added without modifying service
- Template engines are swappable via interface
- Record mappers can be extended for different data sources

#### 4. **Interface Segregation (ISP)**
- Small, focused interfaces
- Each interface serves one specific purpose
- Services only depend on interfaces they actually use

#### 5. **Liskov Substitution (LSP)**
- All FileManager implementations are substitutable
- MCP and filesystem managers honor the same contract
- Template engines follow identical behavior

## System Primitives

### 1. **CSV Record (Dict[str, Any])**
- Input data structure from enriched CSV
- Contains basic fields + Google Books enriched fields

### 2. **Template Data (Dict[str, str])**
- Placeholder → value mapping
- Used by template engine to generate Markdown

### 3. **Note Metadata**
- File path, creation status, error messages
- Used for progress tracking and error reporting

### 4. **ObsidianExportConfig**
- Centralized configuration for export behavior
- Vault path, folder, template, naming pattern, defaults

## Implementation Phases

### Phase 1: Domain and Infrastructure (Foundation)
**Purpose**: Create data structures and configuration management

1. Create `ObsidianExportConfig` dataclass
2. Create `ObsidianConfigRepository` for persistence
3. Define default template as embedded string
4. Create custom exceptions

**Deliverable**: Configuration can be saved/loaded

### Phase 2: Core Interfaces (Contracts)
**Purpose**: Define black box boundaries

1. Create `ObsidianFileManager` interface
2. Create `ObsidianTemplateEngine` interface
3. Create `ObsidianRecordMapper` interface

**Deliverable**: Clear contracts for all components

### Phase 3: Template Engine (Markdown Generation)
**Purpose**: Process templates with placeholders

1. Implement `MarkdownTemplateEngine`
2. Support Jinja2-style placeholders: `{{placeholder}}`
3. Support date formatting: `{{DATE:format}}`
4. Handle missing placeholders gracefully
5. Validate template syntax

**Deliverable**: Can generate Markdown from template + data

### Phase 4: Record Mapper (Data Transformation)
**Purpose**: Transform CSV records into template data

1. Implement `GoogleBooksRecordMapper`
2. Map all CSV fields to template placeholders
3. Implement priority fallback (GB_* > extracted > default)
4. Format dates, URLs, multi-value fields
5. Sanitize data for Markdown

**Deliverable**: CSV record → template data dictionary

### Phase 5: File Managers (File Operations)
**Purpose**: Write Markdown files to Obsidian vault

1. Implement `FilesystemFileManager` (always available)
   - Create directories if needed
   - Write/update Markdown files
   - Check if file exists
   - Generate sanitized filenames
2. Implement `McpFileManager` (when MCP available)
   - Use `obsidian-mcp-tools:create_vault_file`
   - Use `obsidian-mcp-tools:get_vault_file`
   - Fallback to filesystem on error

**Deliverable**: Can write notes to Obsidian vault

### Phase 6: Export Service (Orchestration)
**Purpose**: Coordinate the entire export workflow

1. Implement `ObsidianExportService`
2. Read CSV file
3. For each record:
   - Map to template data
   - Render template
   - Generate filename
   - Check if exists (skip if needed)
   - Write to vault
   - Track progress and errors
4. Return summary (success/skip/error counts)

**Deliverable**: End-to-end export working programmatically

### Phase 7: UI Configuration (User Settings)
**Purpose**: Allow users to configure export

1. Create `obsidian_config_page.py`
2. Form fields:
   - Vault path (with validation)
   - Notes folder
   - Template option (default/custom + file upload)
   - Filename pattern (with preview)
   - Default values (status, priority, device, purpose)
   - Advanced options (overwrite, use MCP)
3. Save to repository
4. Load existing configuration

**Deliverable**: Users can configure Obsidian export

### Phase 8: UI Export Component (Export Interface)
**Purpose**: Trigger export and show progress

1. Create `obsidian_export_component.py`
2. "Export to Obsidian" button
3. Validate configuration before export
4. Progress bar during export
5. Summary display:
   - Total processed
   - Successful
   - Skipped (already exist)
   - Errors (with messages)
6. Error list (expandable)

**Deliverable**: Users can export via UI

### Phase 9: Integration and Testing
**Purpose**: Ensure everything works together

1. Test with sample CSV data
2. Test with and without MCP tools
3. Test custom templates
4. Test error scenarios
5. Test with different configurations
6. Verify SOLID principles compliance

**Deliverable**: Fully functional, tested feature

### Phase 10: Documentation and Polish
**Purpose**: Make feature discoverable and usable

1. Update README with Obsidian export instructions
2. Add inline code documentation
3. Create example template file
4. Add logging throughout
5. Refine error messages for clarity

**Deliverable**: Production-ready feature

## Data Flow

### Export Process Flow

```
1. User clicks "Export to Obsidian"
   ↓
2. UI validates configuration
   ↓
3. Creates ObsidianExportService with dependencies
   ↓
4. Service reads CSV file
   ↓
5. For each book record:
   ├─ RecordMapper.map_record(record) → template_data
   ├─ TemplateEngine.render(template, template_data) → markdown
   ├─ Generate filename from pattern
   ├─ FileManager.exists(filename)? → skip if exists & !overwrite
   ├─ FileManager.create_note(filename, markdown)
   ├─ Track result (success/skip/error)
   └─ Update progress in UI
   ↓
6. Return summary to UI
   ↓
7. Display results to user
```

### CSV Field → Template Placeholder Mapping

**High-Level Mapping Strategy:**
```python
{
    "title": GB_Titulo > Titulo_Extraido > Nome (without extension),
    "author": GB_Autores > Autor_Extraido > "Unknown Author",
    "publisher": GB_Editora > "",
    "publishDate": GB_Data_Publicacao > "",
    "totalPage": GB_Paginas > "",
    "isbn10": GB_ISBN10 > "",
    "isbn13": GB_ISBN13 > "",
    "coverUrl": GB_Capa_Link > "",
    "description": GB_Descricao > "",
    "categories": GB_Categorias > "",
    "language": GB_Idioma > "",
    "preview_link": GB_Preview_Link > "",
    "format": Formato (lowercase),
    "file_size": Tamanho(MB),
    "file_path": Caminho,
    "modified_date": Data Modificação,
    "created": current_date,
    "updated": current_date,
    "status": config.default_status,
    "priority": config.default_priority,
    "device": config.default_device,
    "purpose": config.default_purpose
}
```

## Default Template

The system will include this default template:

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

## Template Placeholder Processing

### Built-in Placeholders

1. **Book metadata**: `{{title}}`, `{{author}}`, `{{publisher}}`, etc.
2. **Dates**: `{{DATE:YYYY-MM-DD}}`, `{{created}}`, `{{updated}}`
3. **Config defaults**: `{{status}}`, `{{priority}}`, `{{device}}`, `{{purpose}}`
4. **File info**: `{{format}}`, `{{file_size}}`, `{{file_path}}`

### Date Formatting

Support date format codes:
- `{{DATE:YYYY-MM-DD}}` → 2025-10-19
- `{{DATE:YYYY-MM-DD HH:mm:ss}}` → 2025-10-19 14:30:45
- `{{created}}`, `{{updated}}` use ISO format by default

### Missing Data Handling

- Empty string for missing optional fields
- Default values for configured fields (status, priority, etc.)
- Graceful degradation (don't break on missing fields)

## Filename Generation

### Pattern Processing

Pattern: `{title} - {author}.md`

1. Replace `{title}` with book title
2. Replace `{author}` with book author
3. Sanitize for filesystem:
   - Remove: `:`, `/`, `\`, `*`, `?`, `"`, `<`, `>`, `|`
   - Replace with: `-` or remove entirely
4. Collapse multiple spaces to single space
5. Truncate to `max_filename_length`
6. Add `.md` extension

### Examples

| Pattern | Title | Author | Result |
|---------|-------|--------|--------|
| `{title} - {author}` | "Clean Code" | "Robert C. Martin" | `Clean Code - Robert C. Martin.md` |
| `{author} - {title}` | "Infonomics" | "Douglas B. Laney" | `Douglas B. Laney - Infonomics.md` |
| `[{format}] {title}` | "SOLID Principles" | "N/A" | `[pdf] SOLID Principles.md` |

## Error Handling Strategy

### Principles

1. **Fail gracefully**: One book's error doesn't stop the export
2. **Collect errors**: Track all errors for user review
3. **Limit error details**: Store max 50 errors to prevent memory issues
4. **Clear messages**: User-friendly error descriptions

### Error Categories

| Category | Handling | User Message |
|----------|----------|--------------|
| Configuration invalid | Prevent export | "Configuration incomplete: {details}" |
| Vault path not found | Prevent export | "Vault path does not exist: {path}" |
| Template not found | Use default | "Custom template not found, using default" |
| Template syntax error | Use default | "Template syntax error, using default: {error}" |
| CSV read error | Stop export | "Failed to read CSV file: {error}" |
| Record mapping error | Skip record | "Error processing book: {title}" |
| File write error | Skip record | "Failed to create note: {filename}" |
| MCP tools unavailable | Switch to filesystem | "MCP tools unavailable, using direct filesystem" |

### Progress Tracking

```python
{
    "total": 150,
    "processed": 75,
    "successful": 70,
    "skipped": 3,  # Already exist, overwrite=False
    "errors": 2,
    "error_messages": ["...", "..."]
}
```

## Validation Rules

### Configuration Validation

- ✓ Vault path is not empty
- ✓ Vault path exists (if filesystem, check; if MCP, trust user)
- ✓ Notes folder is not empty
- ✓ Filename pattern contains at least one placeholder
- ✓ Custom template file exists (if specified)
- ✓ Template is valid Markdown with frontmatter

### Runtime Validation

- ✓ CSV file exists and readable
- ✓ CSV has required columns (at minimum: Nome or Titulo_Extraido or GB_Titulo)
- ✓ Generated filename is valid (not empty, not too long, no invalid chars)
- ✓ Markdown content is valid (not empty)

## Testing Strategy

### Unit Tests (Per Component)

1. **ObsidianConfigRepository**: Save/load/update
2. **MarkdownTemplateEngine**: Render various templates
3. **GoogleBooksRecordMapper**: Map with different data combinations
4. **FilesystemFileManager**: File operations
5. **McpFileManager**: MCP tool interactions (mocked)
6. **ObsidianExportService**: Orchestration logic (with mocked dependencies)

### Integration Tests

1. **End-to-end export**: Real CSV → Real vault (temp directory)
2. **Template variations**: Default, custom, minimal
3. **Error scenarios**: Missing vault, bad CSV, template errors
4. **Large datasets**: Performance with 1000+ books

### Manual Tests

1. Export to real Obsidian vault
2. Verify notes open correctly in Obsidian
3. Test MCP tools integration (if available)
4. Test UI workflow
5. Verify error messages are helpful

## Success Criteria

### Functional Requirements ✓

- [ ] Users can configure Obsidian export via UI
- [ ] Users can export library to Obsidian with one click
- [ ] Notes are created with proper Markdown and YAML frontmatter
- [ ] Custom templates are supported
- [ ] Filename patterns are customizable
- [ ] Google Books data is properly mapped to templates
- [ ] Progress is shown during export
- [ ] Results summary is displayed
- [ ] Errors are collected and shown to user
- [ ] MCP tools are used when available
- [ ] Filesystem fallback works

### Non-Functional Requirements ✓

- [ ] Code follows SOLID principles
- [ ] Architecture mirrors Notion export patterns
- [ ] All components are replaceable (black box)
- [ ] Comprehensive error handling
- [ ] Clear logging throughout
- [ ] Type hints on all functions
- [ ] Docstrings on all public APIs
- [ ] Configuration persists between sessions

### Quality Checks ✓

- [ ] No hard-coded dependencies
- [ ] All dependencies injected via constructors
- [ ] Interfaces hide implementation details
- [ ] Each class has single responsibility
- [ ] Core layer has no adapter dependencies
- [ ] Unit tests for all components
- [ ] Integration test for end-to-end flow

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| MCP tools not available | Medium | Implement filesystem fallback |
| Custom templates break | Low | Validate and fallback to default |
| Large CSV files (10k+ books) | Medium | Process in chunks, show progress |
| Obsidian vault on network drive | Low | Add timeout handling |
| Unicode in filenames | Medium | Sanitize all filenames |
| Duplicate filenames | Low | Add counter suffix: `Book (1).md` |

## Future Enhancements (Not in Scope)

- Bi-directional sync (Obsidian → CSV)
- Update existing notes with new enriched data
- Batch operations (select specific books to export)
- Export filters (by format, author, category)
- Template library (pre-made templates)
- Image caching (download covers to vault)

## Conclusion

This implementation plan provides a comprehensive roadmap for adding Obsidian export functionality while maintaining the high-quality architecture of the eBook Manager application. By following the established patterns and SOLID principles, we ensure the feature is maintainable, testable, and extensible.

The phased approach allows for incremental development and testing, reducing risk and enabling early feedback. Each phase builds on the previous one, creating a solid foundation for the next.
