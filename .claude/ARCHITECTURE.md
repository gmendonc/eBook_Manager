# eBook Manager - Architecture Guidelines

## Overview
This project follows **Clean Architecture**, **Black Box Design**, and **SOLID principles** with emphasis on **high cohesion** and **low coupling**. The architecture ensures maintainability, testability, and flexibility for future enhancements.

**Core Philosophy**: _"It's faster to write five lines of code today than to write one line today and then have to edit it in the future."_ - Eskil Steenberg

Our goal is to create software that:
- Maintains constant developer velocity regardless of project size
- Can be understood and maintained by any developer
- Has modules that can be completely replaced without breaking the system
- Optimizes for human cognitive load, not code cleverness
- Strictly adheres to SOLID principles at all architectural levels
- Achieves high cohesion within modules and low coupling between modules

## Foundational Principles

This architecture is built on three complementary foundations:

1. **SOLID Principles** - Object-oriented design principles ensuring maintainability
   - Single Responsibility Principle (SRP)
   - Open/Closed Principle (OCP)
   - Liskov Substitution Principle (LSP)
   - Interface Segregation Principle (ISP)
   - Dependency Inversion Principle (DIP)

   _See [claude.md](.claude/claude.md) for detailed SOLID guidelines with examples._

2. **High Cohesion, Low Coupling** - Module organization principles
   - **High Cohesion**: All elements within a module are strongly related
   - **Low Coupling**: Minimal dependencies between modules
   - Changes in one module don't cascade to others

   _See [claude.md](.claude/claude.md) for practical examples._

3. **Black Box Design** - Component isolation principles
   - Hide all implementation details
   - Expose only well-defined interfaces
   - Enable complete replaceability of components

   _Detailed below._

These principles work together:
- **SOLID** provides the OOP foundation
- **Cohesion/Coupling** guides module organization
- **Black Box** ensures component isolation
- **Clean Architecture** structures the layers

## Black Box Design Principles

### 1. Black Box Interfaces
Every module is a **black box** with a clean, documented API:
- **Hide implementation details completely** - Never expose "how", only "what"
- **Communicate through well-defined interfaces** - Use `core/interfaces/` protocols
- **Think API-first** - "What does this module DO, not HOW it does it"
- **Document contracts clearly** - The interface is the single source of truth

**Example**: A scanner's interface defines `scan_source(source: Source) -> pd.DataFrame`, but the caller never knows whether it reads from iCloud, filesystem, or anywhere else.

### 2. Replaceable Components
Any module should be **completely rewritable** using only its interface:
- **No leaked implementation details** - If you must know how a module works internally to use it, the API is broken
- **Complete independence** - A developer should be able to replace any module without touching other code
- **Interface stability** - Design interfaces that survive implementation changes
- **Test replaceability** - Could you hand this interface to another developer and they could build it?

**Question to ask**: _"If I deleted this entire module, could someone rebuild it using only the interface definition and tests?"_

### 3. Primitive-First Design
Identify and standardize the **core primitive data types** that flow through the system:
- **DataFrame as the universal ebook container** - `pd.DataFrame` with standardized columns
- **Source** - Represents where ebooks come from
- **Config objects** - `NotionExportConfig`, `NotionPropertyMap`
- **Simple primitives** - Prefer simple, consistent data structures
- **Build complexity through composition** - Not through complicated primitives

**Think like Unix**: Just as Unix uses files as the universal primitive, we use DataFrames as our universal ebook collection primitive.

### 4. Single Responsibility Modules
**One module = one person** should be able to build and maintain it:
- **Clear, singular purpose** - Each module does ONE thing well
- **Human-sized complexity** - If one developer can't hold it in their head, split it
- **Cognitive load optimization** - Make it easy to understand, not clever
- **Obvious responsibilities** - Anyone should know what a module does from its name

**Red flag**: If you need a diagram to explain what a single module does, it's too complex.

## Architecture Principles

### 1. Dependency Rule
- **Dependencies point inward**: Outer layers depend on inner layers, never the reverse
- **Core domain is independent**: The `core` layer has no dependencies on outer layers
- **Interfaces define contracts**: Use interfaces/protocols in `core/interfaces` to define boundaries

### 2. Layer Structure

```
┌─────────────────────────────────────────────────┐
│               UI Layer (ui/)                    │
│         Streamlit Components & Pages            │
├─────────────────────────────────────────────────┤
│          Application Layer (core/)              │
│     Services, Use Cases, Business Logic         │
├─────────────────────────────────────────────────┤
│          Domain Layer (core/domain/)            │
│     Entities, Value Objects, Domain Logic       │
├─────────────────────────────────────────────────┤
│         Interface Layer (core/interfaces/)      │
│        Protocols & Abstract Base Classes        │
├─────────────────────────────────────────────────┤
│          Adapter Layer (adapters/)              │
│  External Services, APIs, Data Sources          │
└─────────────────────────────────────────────────┘
```

## Directory Structure

### `/core` - Business Logic & Domain
- **`/core/domain/`**: Domain entities and value objects
  - Pure Python classes representing business concepts
  - No external dependencies
  - Example: `Source`, `NotionExportConfig`, `NotionPropertyMap`

- **`/core/interfaces/`**: Interface definitions (Protocols/ABCs)
  - Define contracts for adapters
  - Enable dependency inversion
  - Example: `Scanner`, `Enricher`, `Exporter`, `NotionApiClient`

- **`/core/services/`**: Application services and use cases
  - Orchestrate business logic
  - Coordinate between domain and adapters
  - Example: `ScanService`, `EnrichService`, `NotionExportService`

- **`/core/repositories/`**: Data access interfaces and implementations
  - Abstract data persistence
  - Example: `ConfigRepository`, `NotionConfigRepository`

### `/adapters` - External Integrations
- **`/adapters/scanners/`**: Scanner implementations
  - `icloud_scanner.py`, `filesystem_scanner.py`, etc.
  - Implement `Scanner` interface from `core/interfaces`

- **`/adapters/enrichers/`**: Metadata enrichment implementations
  - `google_books_enricher.py`, `basic_enricher.py`, etc.
  - Implement `Enricher` interface
  - Use Factory pattern (`factory.py`) for creation

- **`/adapters/notion/`**: Notion integration components
  - `api_client.py`: API communication
  - `record_mapper.py`: Data transformation
  - `database_creator.py`: Database setup
  - `exporter.py`: Export orchestration
  - All implement interfaces from `core/interfaces/notion_*`

### `/ui` - User Interface Layer
- **`/ui/components/`**: Reusable UI components
  - Stateless presentation components
  - Example: `source_form.py`, `notion_export_component.py`

- **`/ui/pages/`**: Full page implementations
  - Page-level logic and layout
  - Example: `home_page.py`, `scan_page.py`, `view_page.py`

- **`/ui/state.py`**: Application state management
  - Streamlit session state management

- **`/ui/router.py`**: Page routing logic

### `/utils` - Shared Utilities
- Cross-cutting concerns
- Helper functions
- Example: `notion_utils.py`

### `/tests` - Test Suite
- Mirror the source structure
- Unit tests for core logic
- Integration tests for adapters

## Coding Standards

### 1. Naming Conventions
- **Classes**: PascalCase (e.g., `NotionExportService`)
- **Functions/Methods**: snake_case (e.g., `export_to_notion`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRY_ATTEMPTS`)
- **Private members**: Prefix with underscore (e.g., `_validate_config`)

### 2. File Organization
- One primary class per file
- File name matches the primary class name in snake_case
- `__init__.py` should only contain exports, no logic

### 3. Import Organization
```python
# Standard library imports
import os
from typing import List, Optional

# Third-party imports
import pandas as pd
from notion_client import Client

# Local application imports
from core.interfaces.scanner import Scanner
from core.domain.source import Source
```

### 4. Type Hints
- **Always use type hints** for function signatures
- Use `typing` module for complex types
- Example:
```python
def scan_source(self, source: Source) -> pd.DataFrame:
    """Scan a source and return ebook data."""
    pass
```

### 5. Documentation
- **Docstrings required** for all public classes and methods
- Use Google-style docstrings
- Example:
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

## Black Box Analysis Framework

When analyzing or refactoring code, **always ask these questions**:

### 1. What are the primitives?
**Question**: What core data flows through this system?
- In our system: `DataFrame` (ebook collections), `Source` (origin), config objects
- Keep primitives **simple and consistent**
- Don't create new primitives without strong justification

### 2. Where are the black box boundaries?
**Question**: What should be hidden vs. exposed?
- **Good boundary**: `Scanner` interface - callers don't know if it's iCloud or filesystem
- **Good boundary**: `Enricher` interface - callers don't know if it's Google Books API or local extraction
- **Bad boundary**: Exposing Notion API client details to services (wrap it!)

### 3. Is this replaceable?
**Question**: Could someone rewrite this module using only the interface?
- **Test**: Give another developer just the interface - can they implement it?
- **Test**: Could you swap out Notion for Airtable by changing one adapter?
- If not replaceable, the interface is leaking implementation details

### 4. Does this optimize for human understanding?
**Question**: Will this be maintainable in 5 years by a different developer?
- **Explicit over clever**: Prefer clear code over "smart" code
- **Self-documenting**: Names and structure should make intentions obvious
- **Future-proof**: Design for the developer who knows nothing about the current implementation

### 5. Are responsibilities clear?
**Question**: Does each module have one obvious job?
- **One-sentence test**: Can you describe what a module does in one clear sentence?
- **Single axis of change**: A module should have only ONE reason to change
- **No god objects**: If a class does everything, it should do nothing

## Refactoring Strategy

When refactoring existing code, follow this process:

### Step 1: Identify Primitives
- What data types flow through the system?
- Which ones are fundamental? Which are derivative?
- Can we reduce complexity by standardizing on fewer primitives?

### Step 2: Draw Black Box Boundaries
- Map current module dependencies
- Identify where implementation details leak across boundaries
- Design clean interfaces that hide "how" and expose only "what"

### Step 3: Design Clean Interfaces
- Write the interface FIRST, before implementation
- Ask: "Can someone implement this without seeing my code?"
- Make interfaces as simple as possible, but no simpler
- Document pre-conditions, post-conditions, and invariants

### Step 4: Implement Incrementally
- Replace modules one at a time
- Use interfaces to decouple during transition
- Keep the system working at each step
- Never break existing functionality

### Step 5: Test Interfaces
- Write tests against interfaces, not implementations
- Verify modules can be swapped without breaking tests
- Use mock implementations to test consumers

### Step 6: Validate Replaceability
- Give the interface to someone else - can they implement it?
- Can you delete the implementation and rebuild it from the interface?
- Does changing implementation require changing consumers?

## Design Patterns

### 1. Factory Pattern (Black Box Creator)
- **Purpose**: Hide construction complexity behind simple creation interface
- **Location**: `adapters/*/factory.py`
- **Example**: `EnricherFactory.create(type)` - caller doesn't know how it's built
- **Black box principle**: Creation details are hidden, consumer gets interface

### 2. Strategy Pattern (Interchangeable Black Boxes)
- **Purpose**: Make algorithm implementations completely replaceable
- **Used in**: Scanners, enrichers - swap implementations without changing consumers
- **Black box principle**: Each strategy is a black box implementing the same interface

### 3. Repository Pattern (Data Access Black Box)
- **Purpose**: Hide data storage details completely
- **Location**: `core/repositories/`
- **Black box principle**: Consumers don't know if data is in JSON, database, or API

### 4. Dependency Injection (Black Box Wiring)
- **Purpose**: Wire black boxes together without tight coupling
- **Implementation**: Services receive dependencies via constructor
- **Black box principle**: Components know dependencies only through interfaces

### 5. Adapter Pattern (External Wrapper Black Box)
- **Purpose**: Wrap external dependencies so they can be replaced
- **Critical rule**: **NEVER depend directly on external libraries you don't control**
- **Example**: Wrap `notion_client` in our own `NotionApiClient` interface
- **Black box principle**: If Notion changes their API, only the adapter changes

## Implementation Guidelines

### Adding a New Scanner
1. Create implementation in `/adapters/scanners/`
2. Implement `Scanner` interface from `core/interfaces/scanner.py`
3. Register in scanner factory (if applicable)
4. Add configuration support in domain model
5. Update UI to support new scanner type

### Adding a New Enricher
1. Create implementation in `/adapters/enrichers/`
2. Implement `Enricher` interface from `core/interfaces/enricher.py`
3. Register in `EnricherFactory`
4. Add tests in `/tests/adapters/enrichers/`

### Adding a New Service
1. Create in `/core/services/`
2. Define required interfaces in `/core/interfaces/` if needed
3. Inject dependencies via constructor
4. Add comprehensive docstrings
5. Write unit tests

### Adding a New UI Page
1. Create page file in `/ui/pages/`
2. Follow existing page structure
3. Use components from `/ui/components/` where possible
4. Register in router if needed
5. Keep business logic in services, not UI

## Code Quality Guidelines

### Write for the Future Developer
Every line of code should be written assuming:
- **You won't remember it in 6 months**
- **Someone else will maintain it**
- **The context will be lost**
- **The clever solution will be mysterious**

### Explicit Over Implicit
**Good**:
```python
def scan_icloud_source(source: Source) -> pd.DataFrame:
    """Scan iCloud Drive for ebooks."""
    ebooks = []
    for file_path in self._list_icloud_files(source.path):
        if self._is_ebook_file(file_path):
            ebooks.append(self._extract_metadata(file_path))
    return pd.DataFrame(ebooks)
```

**Bad** (too clever):
```python
def scan(s):
    return pd.DataFrame([self._extract(f) for f in self._list(s.path) if self._is_ebook(f)])
```

### Design APIs Forward
Think about what you'll need in 2 years:
- **Today**: You might only need to scan one source type
- **Tomorrow**: You'll need multiple source types
- **Design the interface today** for tomorrow's needs
- **But implement only** what you need today

### Wrap External Dependencies
**Critical Rule**: Never depend directly on code you don't control

**Good** (wrapped):
```python
# core/interfaces/notion_api_client.py
class NotionApiClient(Protocol):
    def create_page(self, database_id: str, properties: dict) -> dict:
        """Create a page in Notion database."""
        ...

# adapters/notion/api_client.py
class NotionApiClientImpl:
    def __init__(self, client: Client):
        self._client = client  # Notion SDK client wrapped

    def create_page(self, database_id: str, properties: dict) -> dict:
        return self._client.pages.create(...)
```

**Bad** (direct dependency):
```python
# core/services/export_service.py
from notion_client import Client  # DON'T DO THIS IN CORE!

class ExportService:
    def __init__(self):
        self.notion = Client(auth=token)  # Tightly coupled
```

**Why?** If Notion changes their SDK, you only change one adapter file, not your entire codebase.

## Red Flags to Avoid

### 1. Leaking Implementation Details
**Red flag**: API method names that reveal internal implementation
- Bad: `get_data_from_json_file()` - reveals storage mechanism
- Good: `get_config()` - hides how config is stored

### 2. Over-Complex Modules
**Red flag**: One person can't understand the module in 30 minutes
- **Solution**: Split into smaller, focused modules
- **Test**: Can you describe what it does in one sentence?

### 3. Hard-Coded Dependencies
**Red flag**: Using concrete classes instead of interfaces
```python
# Bad
class ExportService:
    def __init__(self):
        self.notion_client = NotionApiClientImpl()  # Hard-coded

# Good
class ExportService:
    def __init__(self, notion_client: NotionApiClient):
        self._notion_client = notion_client  # Injected interface
```

### 4. God Objects/Classes
**Red flag**: A class that does everything
- `DatabaseManager` that also handles HTTP requests, logging, caching, validation...
- **Solution**: Single Responsibility - split it up

### 5. Fragile Interfaces
**Red flag**: Changes in implementation force changes in consumers
- If you rename an internal method and consumers break, your interface leaked
- **Solution**: Stable public API, private implementation

### 6. Tight Coupling
**Red flag**: Changing one module requires changing many others
- **Test**: Can you replace module A without touching modules B, C, D?
- **Solution**: Depend on interfaces, not implementations

### 7. Implicit Contracts
**Red flag**: Code that "just works" if you know the secret
- Undocumented parameter requirements
- Hidden state dependencies
- Magic values
- **Solution**: Make contracts explicit in interfaces and documentation

## Error Handling

### Principles
- **Fail fast**: Validate inputs early at API boundaries
- **Specific exceptions**: Create custom exceptions in domain layer
- **Graceful degradation**: Handle failures without crashing the app
- **User-friendly messages**: Translate technical errors for UI
- **Black box errors**: Don't leak implementation details in error messages

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

## Testing Strategy

### Unit Tests
- Test core business logic in isolation
- Mock all external dependencies
- Location: `tests/core/`

### Integration Tests
- Test adapter implementations with real/mock services
- Location: `tests/adapters/`

### Test Coverage
- Aim for >80% coverage in core layer
- Critical paths must be tested
- Use pytest as test framework

## Configuration Management

### Application Config
- Store in `ebook_manager_config.json`
- Managed via `ConfigRepository`
- Never commit sensitive data

### Notion Config
- Store in `notion_config.json`
- Managed via `NotionConfigRepository`
- Use environment variables for secrets in production

## Logging

### Standards
- Use Python's `logging` module
- Log levels:
  - **DEBUG**: Detailed diagnostic info
  - **INFO**: General informational messages
  - **WARNING**: Warning messages for unexpected situations
  - **ERROR**: Error messages for failures
  - **CRITICAL**: Critical errors that may crash the app

### Example
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

## Data Management

### DataFrames
- Primary data structure: `pandas.DataFrame`
- Standard columns for ebook data:
  - `title`, `author`, `file_path`, `format`, `size`, `source`
  - Additional metadata as needed

### CSV Files
- Use for data persistence and export
- Include timestamp in filename (e.g., `ebooks_icloud_20250413_112404.csv`)
- Store in project root (configurable)

## Security Considerations

### Credentials
- **Never hardcode credentials**
- Use keyring for sensitive data (e.g., iCloud passwords)
- Environment variables for API keys
- Exclude credential files from version control

### API Rate Limiting
- Implement rate limiting for external APIs (Google Books, Notion)
- Use exponential backoff for retries
- Respect API quotas

## Performance Guidelines

### Pandas Operations
- Use vectorized operations instead of loops
- Avoid `iterrows()`, prefer `apply()` or vectorized methods
- Use `read_csv()` with appropriate dtypes

### Caching
- Cache API responses when appropriate
- Use `/cache` directory for temporary data
- Implement cache invalidation strategy

### Async Operations
- Consider async/await for I/O-bound operations
- Use Streamlit's caching mechanisms (`@st.cache_data`)

## Git Workflow

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### Commit Messages
- Use conventional commits format
- Examples:
  - `feat: add Dropbox scanner support`
  - `fix: resolve Notion export timeout issue`
  - `refactor: extract enricher factory pattern`
  - `docs: update architecture guidelines`

### Pull Requests
- Must pass all tests
- Require code review
- Update documentation as needed

## Future Considerations

### Scalability
- Consider database storage for large libraries (SQLite/PostgreSQL)
- Implement pagination for large datasets in UI
- Background task processing for long-running operations

### Extensibility
- Plugin system for custom scanners/enrichers
- Configurable enrichment pipelines
- Support for additional export targets beyond Notion

### Maintainability
- Keep dependencies up to date
- Regular refactoring to reduce technical debt
- Maintain comprehensive documentation

## Build Tooling for Black Boxes

Good architecture requires good tools to validate and debug:

### 1. Interface Validators
Create tools to verify implementations match interfaces:
```python
# tests/utils/interface_validator.py
def validate_scanner(scanner_class: Type) -> bool:
    """Verify a scanner properly implements the Scanner interface."""
    required_methods = ['scan_source', 'validate_credentials']
    for method in required_methods:
        if not hasattr(scanner_class, method):
            raise InterfaceViolation(f"Missing required method: {method}")
```

### 2. Mock Implementations
Provide mock implementations for testing consumers:
```python
# tests/mocks/mock_scanner.py
class MockScanner(Scanner):
    """Mock scanner for testing - returns predictable data."""
    def scan_source(self, source: Source) -> pd.DataFrame:
        return pd.DataFrame({
            'title': ['Test Book'],
            'author': ['Test Author'],
            'format': ['epub']
        })
```

### 3. Diagnostic Tools
Build utilities to inspect black boxes without breaking them:
```python
# utils/diagnostics.py
def trace_scanner_calls(scanner: Scanner) -> Scanner:
    """Wrap scanner with logging to debug issues."""
    # Returns same interface with diagnostic logging
```

### 4. Interface Documentation Generator
Auto-generate documentation from interfaces:
- Extract method signatures from `core/interfaces/`
- Generate API documentation
- Keep docs and code in sync

## Validating Your Architecture

Use this checklist when reviewing code or designs:

### Black Box Checklist
- [ ] Can I describe what this module does in ONE sentence?
- [ ] Could someone rebuild this module using only its interface?
- [ ] Does the interface hide ALL implementation details?
- [ ] Can I swap this implementation without touching consumers?
- [ ] Is this module small enough for one person to maintain?
- [ ] Does the interface expose "what" without revealing "how"?
- [ ] Are dependencies injected through interfaces, not hard-coded?
- [ ] Could I replace any external library this uses without major refactoring?

### Interface Design Checklist
- [ ] Is the interface documented with clear contracts?
- [ ] Are all parameters and return types clearly specified?
- [ ] Are error cases and exceptions documented?
- [ ] Could another developer implement this without seeing my code?
- [ ] Does the interface name describe purpose, not implementation?
- [ ] Are there integration tests that verify the interface contract?

### Module Responsibility Checklist
- [ ] Does this module have exactly ONE reason to change?
- [ ] Are related functions grouped together?
- [ ] Are unrelated functions in separate modules?
- [ ] Is the module's purpose obvious from its name?
- [ ] Does the module operate on a clear set of primitives?

## Architectural Decision Records (ADRs)

Document significant architectural decisions:

### When to Create an ADR
- Adding a new major dependency
- Choosing between architectural patterns
- Defining new black box boundaries
- Establishing new primitives
- Making trade-offs that affect maintainability

### ADR Template
```markdown
# ADR-NNN: Title

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
What is the issue we're facing? What forces are at play?

## Decision
What are we going to do? What black box boundaries are we establishing?

## Consequences
What becomes easier? What becomes harder?
How does this affect replaceability and maintainability?

## Alternatives Considered
What other options did we evaluate and why did we reject them?
```

## System Primitives Reference

### Current Primitives
Document the core primitives used throughout the system:

1. **DataFrame (Ebook Collection)**
   - Standard columns: `title`, `author`, `file_path`, `format`, `size`, `source`, `isbn`, `publisher`, `year`
   - Universal container for ebook metadata
   - Flows between: Scanners → Services → Enrichers → Exporters

2. **Source (Origin Configuration)**
   - Represents where ebooks come from
   - Fields: `name`, `type`, `path`, `credentials`
   - Used by: Scanners, UI, Configuration

3. **NotionExportConfig (Export Settings)**
   - Configuration for Notion exports
   - Fields: `token`, `database_id`, `parent_page_id`
   - Used by: Export services, UI, Repositories

4. **NotionPropertyMap (Schema Mapping)**
   - Maps DataFrame columns to Notion properties
   - Enables flexible schema adaptation
   - Used by: Record mappers, Exporters

### Adding New Primitives
**Think carefully before adding new primitives!**

Questions to ask:
- Is this truly fundamental to the system?
- Can we express this using existing primitives?
- Will this simplify or complicate the system?
- Can ALL relevant modules work with this primitive?

## Claude Code Instructions

When working with Claude Code on this project:

### 1. Always Check Architecture First
Before implementing features, review:
- [ ] Which layer does this belong in?
- [ ] What interfaces need to be defined?
- [ ] What primitives will flow through this code?
- [ ] How will this be testable and replaceable?

### 2. Respect Black Box Boundaries
- Never expose implementation details in interfaces
- Keep core/ independent of adapters/
- Wrap all external dependencies
- Design for replaceability

### 3. Follow the Checklist
Use the validation checklists above before:
- Adding new modules
- Modifying interfaces
- Refactoring code
- Reviewing pull requests

### 4. Document Architectural Decisions
Create an ADR for significant changes:
- New dependencies
- New primitives
- Interface changes
- Boundary modifications

### 5. Optimize for Humans
- Write explicit, clear code
- Name things for their purpose
- Document contracts and invariants
- Make intentions obvious

---

## Summary: The North Star

**Goal**: Create a system where any module can be completely replaced without breaking anything else.

**How**:
1. Define clear **primitives** that flow through the system
2. Establish **black box boundaries** with clean interfaces
3. Hide **implementation details** completely
4. Design for **replaceability** and **human understanding**
5. Keep modules **small and focused**
6. **Wrap external dependencies** to maintain control
7. **Test interfaces**, not implementations

**Remember**:
- It's faster to write explicit code today than to maintain clever code tomorrow
- If one person can't understand a module, it's too complex
- The best architecture makes complex systems feel simple
- Good interfaces survive implementation changes

**When in doubt, ask**:
_"Could I delete this entire module and rebuild it using only its interface and tests?"_

If the answer is no, the interface is broken.
