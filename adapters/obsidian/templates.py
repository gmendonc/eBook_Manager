# adapters/obsidian/templates.py
"""
Default Markdown template for Obsidian book notes.

This module contains the default template used when no custom template is specified.
The template uses Jinja2 syntax with {{ placeholder }} for variable substitution.
"""

DEFAULT_TEMPLATE = """---
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
topics: {{topics}}
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

{% if preview_link %}
[📖 Preview on Google Books]({{preview_link}})
{% endif %}
"""

# Template placeholder documentation
TEMPLATE_PLACEHOLDERS = {
    # Book metadata from Google Books
    "title": "Book title (GB_Titulo > Titulo_Extraido > Nome)",
    "author": "Book author (GB_Autores > Autor_Extraido > 'Unknown Author')",
    "publisher": "Publisher name (GB_Editora)",
    "publishDate": "Publication date (GB_Data_Publicacao)",
    "totalPage": "Number of pages (GB_Paginas)",
    "isbn10": "ISBN-10 identifier (GB_ISBN10)",
    "isbn13": "ISBN-13 identifier (GB_ISBN13)",
    "coverUrl": "Cover image URL (GB_Capa_Link)",
    "description": "Book description/synopsis (GB_Descricao)",
    "categories": "Book categories/genres (GB_Categorias)",
    "topics": "Topic tags as list (Temas_Sugeridos > GB_Categorias, split by comma/semicolon)",
    "language": "Book language code (GB_Idioma)",
    "preview_link": "Google Books preview URL (GB_Preview_Link)",

    # File metadata
    "format": "File format (Formato)",
    "file_size": "File size in MB (Tamanho(MB))",
    "file_path": "Full file path (Caminho)",
    "modified_date": "File modification date (Data Modificação)",

    # Date fields
    "created": "Note creation timestamp (current date/time)",
    "updated": "Note update timestamp (current date/time)",

    # User-configurable defaults
    "status": "Reading status (from config.default_status)",
    "priority": "Priority level (from config.default_priority)",
    "device": "Reading device (from config.default_device)",
    "purpose": "Purpose tags (from config.default_purpose)",
}
