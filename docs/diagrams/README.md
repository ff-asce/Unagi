# UNAGI Architecture Diagrams

This directory contains visual diagrams of the UNAGI system architecture using Mermaid syntax. GitHub automatically renders these as interactive diagrams.

## Available Diagrams

### [ARCHITECTURE.md](ARCHITECTURE.md)

Complete set of architecture diagrams including:

1. **Overall System Architecture** - High-level view of all components
2. **Intelligence System Architecture** - Detailed view of the intelligence layer
3. **Data Flow - Food Logging** - Sequence diagram for logging meals
4. **Data Flow - Intelligence & Suggestions** - Sequence diagram for generating suggestions
5. **Database Schema** - Entity-relationship diagram of all tables
6. **Component Dependencies** - Dependency graph showing relationships
7. **Deployment Architecture** - How UNAGI is deployed on user's machine

## How to View

### On GitHub
Simply open any `.md` file in this directory on GitHub, and the Mermaid diagrams will render automatically.

### Locally
Use a Markdown viewer that supports Mermaid:
- **VS Code**: Install "Markdown Preview Mermaid Support" extension
- **Obsidian**: Mermaid is supported natively
- **Online**: Copy diagram code to https://mermaid.live/

### Export as Images
To export diagrams as PNG/SVG:
1. Visit https://mermaid.live/
2. Paste the Mermaid code
3. Click "Actions" → "Export PNG" or "Export SVG"

## Diagram Types

### Graph Diagrams
- Show component relationships
- Use boxes and arrows
- Color-coded by layer (blue=intelligence, green=storage, red=core)

### Sequence Diagrams
- Show data flow over time
- Illustrate request/response patterns
- Useful for understanding interactions

### Entity-Relationship Diagrams
- Show database schema
- Illustrate table relationships
- Include field types and constraints

## Color Coding

- **Blue** (#e1f5ff): Intelligence system components
- **Green** (#e1ffe1): Storage components (database, vector store)
- **Red** (#ffe1e1): Core application components
- **Dotted lines**: Optional connections
- **Solid lines**: Required connections

## Contributing

When adding new diagrams:
1. Use Mermaid syntax for consistency
2. Follow the color coding scheme
3. Add clear titles and descriptions
4. Update this README with new diagram descriptions

## Resources

- [Mermaid Documentation](https://mermaid.js.org/)
- [Mermaid Live Editor](https://mermaid.live/)
- [GitHub Mermaid Support](https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/)

---

**Note**: These diagrams are automatically rendered on GitHub. No image files needed!