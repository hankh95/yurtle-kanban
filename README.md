# yurtle-kanban

**File-based kanban using Yurtle (Turtle RDF in Markdown). Git is your database.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## What is yurtle-kanban?

A workflow management system where:
- **Files ARE work items** - Each task is a markdown file with Yurtle (Turtle RDF) blocks
- **Git IS the database** - No external database, your repo is the source of truth
- **SPARQL enables queries** - Query your work items like a knowledge graph
- **Themes customize naming** - Use software terms (feature, bug) or nautical (expedition, voyage) or your own

## Part of the Yurtle Ecosystem

```
yurtle           ->  Turtle RDF in Markdown specification
yurtle-rdflib    ->  RDFlib parser/serializer plugin
yurtle-kanban    ->  This project: file-based workflow management
nusy-nano        ->  Optional: neurosymbolic reasoning
```

## Quick Start

```bash
pip install yurtle-kanban

# Initialize in your project
cd my-project
yurtle-kanban init --theme software

# Create a work item
yurtle-kanban create feature "Add dark mode"

# List work items
yurtle-kanban list

# Move to done
yurtle-kanban move FEAT-001 done
```

## Work Items as Files

Each work item is a markdown file with Yurtle blocks:

```markdown
---
title: "Add dark mode support"
---

# Add Dark Mode Support

Description goes here...

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .

<> a kb:Feature ;
   kb:id "FEAT-042" ;
   kb:status kb:in_progress ;
   kb:priority kb:high ;
   kb:assignee <../team/developer-1.md> .
```

The file IS the work item. `<>` refers to the file itself as an RDF subject.

## Configurable Paths

Work items can live anywhere in your repo:

```yaml
# .kanban/config.yaml
kanban:
  theme: software
  paths:
    root: work/           # Simple: all in one directory
    # OR
    features: specs/features/
    bugs: specs/bugs/     # By type: separate directories
```

## Themes

**Software (default):**
- Feature, Bug, Epic, Issue, Task

**Nautical:**
- Expedition, Voyage, Directive, Hazard, Signal

**Custom:**
- Define your own item types and workflows

## Why Keep Work Items in Your Project?

| Benefit | Description |
|---------|-------------|
| Single source of truth | Work items live with the code they describe |
| Git history together | Feature branch includes both code AND its work item |
| No external dependency | No Jira outage blocks your workflow |
| Offline-first | Works without internet |
| AI agent access | Agents read/write work items like any file |

## MCP Integration

yurtle-kanban provides an MCP server for AI agents:

```python
# Agents can use structured tools
list_items(status="in_progress")
move_item(id="FEAT-042", new_status="done")
create_item(type="feature", title="New feature")
```

## Documentation

- [Yurtle Specification](https://github.com/hankh95/yurtle)
- [yurtle-rdflib](https://github.com/hankh95/yurtle-rdflib)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Status

**In Development** - Phase 1: Core Library
