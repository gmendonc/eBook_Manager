# Claude Code Instructions for eBook Manager

## Project Philosophy

This project follows **Clean Architecture**, **Black Box Design**, and **SOLID principles** with emphasis on **high cohesion** and **low coupling**.

**Core Principle**: _"It's faster to write five lines of code today than to write one line today and then have to edit it in the future."_ - Eskil Steenberg

## Your Mission

Create software that:
- Maintains constant developer velocity regardless of project size
- Can be understood and maintained by any developer
- Has modules that can be **completely replaced** without breaking the system
- Optimizes for **human cognitive load**, not code cleverness
- Adheres to **SOLID principles** at all levels
- Achieves **high cohesion** within modules and **low coupling** between modules

## Architecture Overview

### Layer Structure
```
UI Layer (ui/) → Application Layer (core/services/) → Domain Layer (core/domain/)
                          ↓
            Interface Layer (core/interfaces/) ← Adapter Layer (adapters/)
```

### System Primitives
1. **DataFrame** - Universal ebook collection container with standardized columns
2. **Source** - Origin configuration for scanners
3. **NotionExportConfig** - Export settings
4. **NotionPropertyMap** - Schema mapping

## SOLID Principles - The Foundation

### S - Single Responsibility Principle (SRP)
**Rule**: A class should have ONE and only ONE reason to change.

✅ **Good**:
```python
# One responsibility: map DataFrame records to Notion format
class NotionRecordMapper:
    def map_to_notion_properties(self, record: dict) -> dict:
        """Convert ebook record to Notion properties."""
        pass

# Separate responsibility: communicate with Notion API
class NotionApiClient:
    def create_page(self, database_id: str, properties: dict) -> dict:
        """Create page in Notion."""
        pass
```

❌ **Bad**:
```python
# Too many responsibilities: mapping, API calls, validation, error handling
class NotionManager:
    def export_ebook(self, record: dict):
        # Maps data
        # Calls API
        # Validates
        # Handles errors
        pass
```

**In practice**:
- Each service should orchestrate ONE use case
- Each adapter should handle ONE external integration
- Each mapper should transform ONE type of data
- If a class name has "And" or "Manager", it's probably doing too much

### O - Open/Closed Principle (OCP)
**Rule**: Open for extension, closed for modification.

✅ **Good** (extensible via new implementations):
```python
# core/interfaces/enricher.py
class Enricher(Protocol):
    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich ebook metadata."""
        pass

# Add new enricher WITHOUT modifying existing code
class GoogleBooksEnricher:
    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        # New implementation
        pass

class OpenLibraryEnricher:  # Add new source easily
    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        # Another implementation
        pass
```

❌ **Bad** (requires modification to extend):
```python
class EnrichService:
    def enrich(self, df: pd.DataFrame, source: str):
        if source == "google_books":
            # Google Books logic
        elif source == "open_library":  # Must modify this class!
            # Open Library logic
```

**In practice**:
- Use interfaces and polymorphism
- Factory pattern for creating implementations
- Strategy pattern for swappable algorithms
- Add new features by adding new classes, not modifying existing ones

### L - Liskov Substitution Principle (LSP)
**Rule**: Subtypes must be substitutable for their base types without breaking the program.

✅ **Good**:
```python
class Scanner(Protocol):
    def scan_source(self, source: Source) -> pd.DataFrame:
        """Scan and return DataFrame with standard columns."""
        pass

class ICloudScanner:
    def scan_source(self, source: Source) -> pd.DataFrame:
        # Returns DataFrame with required columns
        return pd.DataFrame(columns=['title', 'author', 'file_path', ...])

class FilesystemScanner:
    def scan_source(self, source: Source) -> pd.DataFrame:
        # Returns same structure - substitutable!
        return pd.DataFrame(columns=['title', 'author', 'file_path', ...])
```

❌ **Bad** (violates contract):
```python
class ICloudScanner:
    def scan_source(self, source: Source) -> pd.DataFrame:
        return pd.DataFrame(columns=['title', 'author', 'file_path'])

class SpecialScanner:
    def scan_source(self, source: Source) -> dict:  # Different return type!
        return {'books': [...]}  # Breaks substitutability
```

**In practice**:
- All implementations of an interface must honor the same contract
- Same input/output types
- Same pre-conditions and post-conditions
- No surprising behavior changes
- Standardize DataFrame columns across all scanners

### I - Interface Segregation Principle (ISP)
**Rule**: Clients should not be forced to depend on interfaces they don't use.

✅ **Good** (focused interfaces):
```python
# Separate focused interfaces
class NotionPageCreator(Protocol):
    def create_page(self, database_id: str, properties: dict) -> dict:
        pass

class NotionDatabaseCreator(Protocol):
    def create_database(self, parent_page_id: str, schema: dict) -> str:
        pass

class NotionDatabaseVerifier(Protocol):
    def verify_database_schema(self, database_id: str) -> bool:
        pass

# Services only depend on what they need
class ExportService:
    def __init__(self, page_creator: NotionPageCreator):  # Only needs page creation
        self._page_creator = page_creator
```

❌ **Bad** (fat interface):
```python
# One big interface with everything
class NotionClient(Protocol):
    def create_page(self, database_id: str, properties: dict) -> dict:
        pass
    def create_database(self, parent_page_id: str, schema: dict) -> str:
        pass
    def verify_database_schema(self, database_id: str) -> bool:
        pass
    def update_page(self, page_id: str, properties: dict) -> dict:
        pass
    def delete_page(self, page_id: str) -> None:
        pass
    # ... 10 more methods

# Service forced to depend on methods it doesn't use
class ExportService:
    def __init__(self, client: NotionClient):  # Depends on everything!
        self._client = client
```

**In practice**:
- Create small, focused interfaces (like we have: `NotionApiClient`, `NotionDatabaseCreator`, etc.)
- Services only inject the interfaces they actually use
- Better testability - only mock what's needed
- Current project structure is good: separate interfaces in `core/interfaces/notion_*`

### D - Dependency Inversion Principle (DIP)
**Rule**: Depend on abstractions, not concretions. High-level modules should not depend on low-level modules.

✅ **Good** (depends on abstractions):
```python
# core/services/export_service.py
from core.interfaces.notion_api_client import NotionApiClient
from core.interfaces.notion_record_mapper import NotionRecordMapper

class NotionExportService:
    def __init__(
        self,
        api_client: NotionApiClient,  # Interface, not concrete class
        mapper: NotionRecordMapper     # Interface, not concrete class
    ):
        self._api_client = api_client
        self._mapper = mapper
```

❌ **Bad** (depends on concrete implementations):
```python
# core/services/export_service.py
from adapters.notion.api_client import NotionApiClientImpl  # Concrete class!
from adapters.notion.record_mapper import NotionRecordMapperImpl  # Concrete!

class NotionExportService:
    def __init__(self):
        self._api_client = NotionApiClientImpl()  # Hard-coded dependency
        self._mapper = NotionRecordMapperImpl()   # Hard-coded dependency
```

**In practice**:
- Core layer defines interfaces (`core/interfaces/`)
- Adapters implement those interfaces (`adapters/`)
- Services depend on interfaces, not implementations
- Dependency injection via constructor
- This enables testing and replaceability

## High Cohesion, Low Coupling

### High Cohesion
**Rule**: Elements within a module should be strongly related and focused on a single purpose.

✅ **High Cohesion** (all methods relate to scanning):
```python
class ICloudScanner:
    def scan_source(self, source: Source) -> pd.DataFrame:
        """Main scanning entry point."""
        pass

    def _list_icloud_files(self, path: str) -> List[str]:
        """List files in iCloud path."""
        pass

    def _is_ebook_file(self, file_path: str) -> bool:
        """Check if file is an ebook."""
        pass

    def _extract_metadata(self, file_path: str) -> dict:
        """Extract ebook metadata."""
        pass
```

❌ **Low Cohesion** (unrelated responsibilities):
```python
class ICloudScanner:
    def scan_source(self, source: Source) -> pd.DataFrame:
        pass

    def send_email_notification(self, email: str):  # Unrelated!
        pass

    def log_to_database(self, message: str):  # Unrelated!
        pass

    def validate_notion_config(self, config: dict):  # Unrelated!
        pass
```

**Indicators of High Cohesion**:
- All methods work with the same data
- All methods serve the same high-level purpose
- Methods call each other to accomplish shared goals
- Can describe module purpose in one sentence

### Low Coupling
**Rule**: Minimize dependencies between modules. Changes in one module shouldn't ripple through others.

✅ **Low Coupling** (communication through interfaces):
```python
# Service knows nothing about HOW scanning works
class LibraryService:
    def __init__(self, scanner: Scanner):  # Only knows the interface
        self._scanner = scanner

    def scan_library(self, source: Source) -> pd.DataFrame:
        return self._scanner.scan_source(source)  # No knowledge of implementation

# Can swap scanner implementation without touching LibraryService
scanner = ICloudScanner()  # or FilesystemScanner(), or DropboxScanner()
service = LibraryService(scanner)
```

❌ **High Coupling** (knows too much about other modules):
```python
class LibraryService:
    def scan_library(self, source: Source) -> pd.DataFrame:
        # Knows about iCloud internals!
        if source.type == "icloud":
            client = ICloudClient(source.username, source.password)
            client.authenticate()
            files = client.list_directory(source.path)
            # ... iCloud-specific logic
        elif source.type == "filesystem":
            # ... filesystem-specific logic
```

**Indicators of Low Coupling**:
- Modules communicate through interfaces
- Changes in one module don't require changes in others
- Can test modules in isolation
- Can replace implementations easily
- Minimal knowledge of other modules' internals

## Critical Rules - ALWAYS Follow

### 1. Black Box Boundaries (Supports: DIP, ISP, OCP)
- **NEVER expose implementation details** in interfaces
- **Hide "how", expose only "what"**
- Every module must be replaceable using only its interface
- Ask: _"Could someone rebuild this module using only the interface and tests?"_

### 2. Dependency Rule (Supports: DIP, High Cohesion)
- **Dependencies point inward**: Outer layers depend on inner layers, never reverse
- **Core is independent**: `core/` has NO dependencies on `adapters/` or `ui/`
- **Use interfaces**: All cross-layer communication through `core/interfaces/`

### 3. Wrap External Dependencies (Supports: DIP, OCP, Low Coupling)
- **NEVER import external libraries directly in core/**
- **ALWAYS wrap** third-party code in adapters with our own interfaces
- Example: Wrap `notion_client` in `NotionApiClient` interface
- **Why**: If external library changes, only one adapter file changes

### 4. Single Responsibility (Supports: SRP, High Cohesion)
- **One module = one person** should be able to understand and maintain it
- If you can't describe a module's purpose in ONE sentence, split it
- **Human-sized complexity**: If it takes >30 minutes to understand, it's too complex
- **One reason to change**: Each module should have exactly one responsibility

### 5. Explicit Over Clever (Supports: All SOLID principles)
- Write code for the developer who knows nothing about the implementation
- Clear, verbose code > clever, compact code
- You won't remember why you did it in 6 months
- Make intentions obvious

## Before Writing Any Code

Check these questions:

### Architectural Questions
- [ ] Which layer does this belong in? (core, adapters, ui, utils)
- [ ] What interfaces need to be defined or modified?
- [ ] What primitives will flow through this code?
- [ ] Is this module small enough for one person to maintain?
- [ ] Can this be replaced without touching other modules?

### SOLID Compliance Questions
- [ ] **SRP**: Does this class/module have exactly ONE reason to change?
- [ ] **OCP**: Can I extend this without modifying existing code?
- [ ] **LSP**: Are all implementations truly substitutable for their interface?
- [ ] **ISP**: Am I creating focused interfaces, not fat ones?
- [ ] **DIP**: Am I depending on abstractions (interfaces), not concretions?

### Cohesion & Coupling Questions
- [ ] **High Cohesion**: Do all methods in this class serve one clear purpose?
- [ ] **Low Coupling**: Can I change this module without affecting others?
- [ ] Does this module know too much about other modules' internals?
- [ ] Are dependencies injected through interfaces?
- [ ] Can I test this module in isolation?

### Black Box Questions
- [ ] Does the interface hide ALL implementation details?
- [ ] Could someone implement this without seeing my code?
- [ ] Am I wrapping external dependencies?
- [ ] Are dependencies injected through interfaces?
- [ ] Does the interface expose "what" without revealing "how"?

## Implementation Guidelines

### Adding a New Scanner
1. Create implementation in `/adapters/scanners/[name]_scanner.py`
2. Implement `Scanner` interface from `core/interfaces/scanner.py`
3. Register in factory if applicable
4. Add domain support in `core/domain/source.py`
5. Update UI to support new type
6. **Verify**: Can you swap scanners without changing calling code?

### Adding a New Enricher
1. Create implementation in `/adapters/enrichers/[name]_enricher.py`
2. Implement `Enricher` interface from `core/interfaces/enricher.py`
3. Register in `EnricherFactory`
4. Add tests in `/tests/adapters/enrichers/`
5. **Verify**: Can you replace this enricher without touching services?

### Adding a New Service
1. Create in `/core/services/[name]_service.py`
2. Define required interfaces in `/core/interfaces/` if needed
3. Inject dependencies via constructor (never hard-code)
4. Add comprehensive Google-style docstrings
5. Write unit tests that mock dependencies
6. **Verify**: Can you test this service with all dependencies mocked?

### Adding a New UI Page
1. Create in `/ui/pages/[name]_page.py`
2. Follow existing page structure
3. Use components from `/ui/components/` for reusability
4. **NEVER put business logic in UI** - call services instead
5. Keep UI stateless where possible

## Code Quality Standards

### Type Hints (Required)
```python
def scan_source(self, source: Source) -> pd.DataFrame:
    """Scan a source and return ebook metadata."""
    pass
```

### Docstrings (Required for Public APIs)
```python
def create_database(self, parent_page_id: str, database_name: str) -> str:
    """
    Create a new Notion database.

    Args:
        parent_page_id: The ID of the parent page
        database_name: Name for the new database

    Returns:
        The ID of the created database

    Raises:
        NotionApiError: If database creation fails
    """
    pass
```

### Import Organization
```python
# Standard library imports
import os
from typing import List, Optional

# Third-party imports
import pandas as pd
from notion_client import Client  # Only in adapters, NEVER in core!

# Local application imports
from core.interfaces.scanner import Scanner
from core.domain.source import Source
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `NotionExportService`)
- **Functions/Methods**: `snake_case` (e.g., `export_to_notion`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_ATTEMPTS`)
- **Private members**: `_underscore_prefix` (e.g., `_validate_config`)

## Red Flags - STOP and Refactor

### 1. Leaking Implementation Details
❌ **Bad**: `get_data_from_json_file()` - reveals storage
✅ **Good**: `get_config()` - hides storage mechanism

### 2. Direct External Dependencies in Core
❌ **Bad**:
```python
# core/services/export_service.py
from notion_client import Client  # DON'T DO THIS!
```

✅ **Good**:
```python
# core/services/export_service.py
from core.interfaces.notion_api_client import NotionApiClient

# adapters/notion/api_client.py
from notion_client import Client  # Only in adapters!
```

### 3. Hard-Coded Dependencies
❌ **Bad**:
```python
class ExportService:
    def __init__(self):
        self.notion_client = NotionApiClientImpl()  # Hard-coded!
```

✅ **Good**:
```python
class ExportService:
    def __init__(self, notion_client: NotionApiClient):  # Injected interface
        self._notion_client = notion_client
```

### 4. God Objects
If a class does everything, split it:
- ❌ `DatabaseManager` that handles HTTP, logging, caching, validation
- ✅ Separate classes: `HttpClient`, `Logger`, `Cache`, `Validator`

### 5. Clever Code
❌ **Bad** (too clever):
```python
def scan(s):
    return pd.DataFrame([self._extract(f) for f in self._list(s.path) if self._is_ebook(f)])
```

✅ **Good** (explicit):
```python
def scan_icloud_source(source: Source) -> pd.DataFrame:
    """Scan iCloud Drive for ebooks."""
    ebooks = []
    for file_path in self._list_icloud_files(source.path):
        if self._is_ebook_file(file_path):
            ebooks.append(self._extract_metadata(file_path))
    return pd.DataFrame(ebooks)
```

## Design Patterns to Use

### 1. Factory Pattern
- **Where**: `adapters/*/factory.py`
- **Purpose**: Hide construction complexity
- **Example**: `EnricherFactory.create(type)` returns interface, not concrete class

### 2. Strategy Pattern
- **Where**: Scanners, Enrichers
- **Purpose**: Make implementations interchangeable
- **Key**: All strategies implement the same interface

### 3. Repository Pattern
- **Where**: `core/repositories/`
- **Purpose**: Hide data storage details
- **Key**: Consumers don't know if data is in JSON, DB, or API

### 4. Dependency Injection
- **Where**: All services
- **Purpose**: Decouple components
- **Key**: Inject interfaces via constructor, never hard-code

### 5. Adapter Pattern
- **Where**: `adapters/`
- **Purpose**: Wrap external dependencies
- **Critical**: ALWAYS wrap external libraries you don't control

## Testing Strategy

### Unit Tests
- Test core business logic in isolation
- Mock ALL external dependencies
- Test against interfaces, not implementations
- Location: `tests/core/`

### Integration Tests
- Test adapter implementations
- Use real or realistic mocks
- Verify interface contracts
- Location: `tests/adapters/`

### Replaceability Test
**The ultimate test**: Could you delete a module and rebuild it using only:
- The interface definition
- The test suite
- No knowledge of the original implementation

If NO → the interface is broken or tests are insufficient

## Error Handling

### Principles
- **Fail fast** at API boundaries - validate inputs early
- **Specific exceptions** - create custom exceptions in `core/exceptions.py`
- **Black box errors** - don't leak implementation details in messages
- **User-friendly** - translate technical errors for UI

### Exception Hierarchy
```python
# core/exceptions.py
class EbookManagerError(Exception):
    """Base exception for all application errors"""
    pass

class ScannerError(EbookManagerError):
    """Errors during scanning operations"""
    pass

class EnricherError(EbookManagerError):
    """Errors during enrichment operations"""
    pass

class NotionError(EbookManagerError):
    """Errors related to Notion integration"""
    pass
```

## Performance Guidelines

### Pandas Operations
- Use vectorized operations, not loops
- Avoid `iterrows()`, prefer `apply()` or vectorized methods
- Specify dtypes in `read_csv()` for performance

### Caching
- Cache expensive API calls when appropriate
- Use `cache/` directory for temporary data
- Implement cache invalidation strategy
- Use Streamlit's `@st.cache_data` for UI performance

## Logging Standards

```python
import logging

logger = logging.getLogger(__name__)

def scan_source(self, source: Source) -> pd.DataFrame:
    logger.info(f"Starting scan of source: {source.name}")
    try:
        # scanning logic
        logger.debug(f"Found {len(results)} ebooks")
        return results
    except Exception as e:
        logger.error(f"Failed to scan source {source.name}: {str(e)}")
        raise ScannerError(f"Scan failed: {str(e)}") from e
```

**Levels**:
- **DEBUG**: Detailed diagnostic info
- **INFO**: General informational messages
- **WARNING**: Unexpected situations
- **ERROR**: Failures
- **CRITICAL**: Critical errors that may crash

## Git Workflow

### Branches
- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation

### Commits
Use conventional commits:
- `feat: add Dropbox scanner support`
- `fix: resolve Notion export timeout`
- `refactor: extract enricher factory pattern`
- `docs: update architecture guidelines`

## Architectural Decision Records (ADRs)

Create an ADR when:
- Adding new major dependency
- Choosing between patterns
- Defining new black box boundaries
- Establishing new primitives
- Making maintainability trade-offs

Store in: `.claude/adrs/ADR-NNN-title.md`

## When Reviewing Code or PRs

Use these checklists:

### SOLID Principles Checklist
- [ ] **SRP**: Does each class have exactly ONE responsibility?
- [ ] **OCP**: Can this be extended without modification?
- [ ] **LSP**: Are implementations truly substitutable?
- [ ] **ISP**: Are interfaces focused, not bloated?
- [ ] **DIP**: Do we depend on abstractions, not concretions?

### Cohesion & Coupling Checklist
- [ ] **High Cohesion**: Are all methods/functions in a module closely related?
- [ ] **Low Coupling**: Can modules be changed independently?
- [ ] Are there minimal dependencies between modules?
- [ ] Do modules communicate only through interfaces?
- [ ] Can each module be tested in isolation?

### Black Box Checklist
- [ ] Can I describe what this module does in ONE sentence?
- [ ] Could someone rebuild this using only its interface?
- [ ] Does the interface hide ALL implementation details?
- [ ] Can I swap this without touching consumers?
- [ ] Is this small enough for one person to maintain?
- [ ] Are dependencies injected, not hard-coded?

### Interface Design Checklist
- [ ] Is the interface documented with clear contracts?
- [ ] Are parameters and return types clearly specified?
- [ ] Are error cases documented?
- [ ] Does the name describe purpose, not implementation?
- [ ] Are there tests that verify the contract?

### Code Quality Checklist
- [ ] Is the code explicit and easy to understand?
- [ ] Are type hints used for all function signatures?
- [ ] Are docstrings present for public APIs?
- [ ] Is error handling appropriate and informative?
- [ ] Are external dependencies properly wrapped?
- [ ] Does the code follow naming conventions?

## The North Star

**Goal**: Create a system where **any module can be completely replaced** without breaking anything else.

**Guiding Principles**:
1. **SOLID** - Foundation for maintainable OOP design
2. **High Cohesion, Low Coupling** - Modules that work together, change independently
3. **Black Box Design** - Hide implementation, expose only interfaces
4. **Clean Architecture** - Dependencies point inward, core is independent
5. **Human-Optimized** - Write for understanding, not cleverness

**When in doubt, ask**:
- _"Could I delete this entire module and rebuild it using only its interface and tests?"_
- _"Does this class have exactly ONE reason to change?"_
- _"Can I replace this implementation without touching other code?"_
- _"Will a developer understand this in 5 years?"_

**If any answer is NO**, refactor before proceeding.

---

## Quick Reference

**Before adding code**:
- Check layer, define interfaces, verify replaceability
- Ensure SOLID compliance and high cohesion
- Verify low coupling through dependency injection

**Before committing**:
- Run tests, verify black box boundaries
- Check for leaked implementation details
- Confirm each class has one responsibility

**Before pushing**:
- Ensure `core/` is independent
- All external dependencies wrapped in adapters
- Interfaces are focused and well-documented

**Before merging**:
- Review against all checklists above
- Verify SOLID principles throughout
- Confirm high cohesion, low coupling

**Remember**:
- Write for the developer who will maintain this in 5 years
- Make it obvious, not clever
- SOLID principles are non-negotiable
- Every module must be replaceable

For detailed architecture documentation, see [ARCHITECTURE.md](.claude/ARCHITECTURE.md).
