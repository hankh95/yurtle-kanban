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

## Installation

```bash
pip install yurtle-kanban

# With MCP server support
pip install yurtle-kanban[mcp]
```

## Quick Start

```bash
# Initialize in your project
cd my-project
yurtle-kanban init --theme software

# Create work items
yurtle-kanban create feature "Add dark mode" --priority high
yurtle-kanban create bug "Fix login error" --assignee dev-1

# View the board
yurtle-kanban board

# List work items
yurtle-kanban list
yurtle-kanban list --status in_progress
yurtle-kanban list --assignee dev-1

# Move items
yurtle-kanban move FEAT-001 in_progress
yurtle-kanban move FEAT-001 done

# Show item details
yurtle-kanban show FEAT-001

# Export board
yurtle-kanban export --format html --output board.html
yurtle-kanban export --format markdown --output BOARD.md
yurtle-kanban export --format json
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize yurtle-kanban in current directory |
| `list` | List work items with optional filters |
| `create` | Create a new work item |
| `move` | Move item to new status |
| `show` | Show item details |
| `board` | Display kanban board in terminal |
| `stats` | Show board statistics |
| `next` | Suggest next item to work on |
| `next-id` | **Allocate next ID atomically (prevents duplicates!)** |
| `blocked` | List blocked items |
| `comment` | Add comment to item |
| `export` | Export board to HTML/Markdown/JSON |
| `validate` | Check for ID mismatches and duplicates |

### Preventing Duplicate IDs (Multi-Agent Safe)

When multiple agents or developers create work items concurrently, use `next-id` to prevent duplicate IDs:

```bash
# Allocate next ID with git sync (recommended)
yurtle-kanban next-id EXP
# Output: Allocated: EXP-609

# Get JSON output
yurtle-kanban next-id EXP --json
# {"success": true, "id": "EXP-609", "prefix": "EXP", "number": 609}

# Local only (no git fetch/push)
yurtle-kanban next-id EXP --no-sync
```

The command:
1. Fetches latest from remote
2. Scans files (frontmatter + filenames) for highest ID
3. Commits allocation to `.kanban/_ID_ALLOCATIONS.json`
4. Pushes to remote to claim the ID
5. Retries with rebase if push fails (another agent got there first)

## Work Items as Files

Each work item is a markdown file with Yurtle blocks:

```markdown
---
id: FEAT-042
title: "Add dark mode support"
type: feature
status: in_progress
priority: high
assignee: dev-1
created: 2026-01-12
tags: [ui, accessibility]
---

# Add Dark Mode Support

Implement dark mode toggle in the settings panel.

## Acceptance Criteria
- [ ] Toggle in settings
- [ ] Persists across sessions
- [ ] Respects system preference

```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a kb:Feature ;
   kb:id "FEAT-042" ;
   kb:status kb:in_progress ;
   kb:priority kb:high ;
   kb:assignee <../team/dev-1.md> ;
   kb:created "2026-01-12"^^xsd:date ;
   kb:tag "ui", "accessibility" .
```
```

The file IS the work item. `<>` refers to the file itself as an RDF subject.

## Configuration

```yaml
# .kanban/config.yaml
kanban:
  theme: software   # or: nautical, custom

  paths:
    root: work/     # All items in one directory
    # OR organize by type:
    # features: specs/features/
    # bugs: specs/bugs/

  # Scan multiple directories
  scan_paths:
    - work/
    - specs/
    - docs/roadmap/

  ignore:
    - "**/archive/**"
    - "**/templates/**"
```

## Themes

**Software (default):**
```
Feature (FEAT-), Bug (BUG-), Epic (EPIC-), Issue (ISSUE-), Task (TASK-), Idea (IDEA-)
Columns: Backlog → Ready → In Progress → Review → Done
```

**Nautical:**
```
Expedition (EXP-), Voyage (VOY-), Directive (DIR-), Hazard (HAZ-), Signal (SIG-)
Columns: Harbor → Provisioning → Underway → Approaching → Arrived
```

**Custom:** Define your own in `themes/my-theme.yaml`

## MCP Server for AI Agents

yurtle-kanban includes an MCP (Model Context Protocol) server for Claude Code and other AI agents:

```bash
# Start the MCP server
yurtle-kanban-mcp
```

### Available Tools

| Tool | Description |
|------|-------------|
| `kanban_list_items` | List items with optional filters |
| `kanban_get_item` | Get item by ID |
| `kanban_create_item` | Create new item |
| `kanban_move_item` | Move item to new status |
| `kanban_get_board` | Get full board state |
| `kanban_get_my_items` | Get items for assignee |
| `kanban_get_blocked` | Get blocked items |
| `kanban_suggest_next` | Suggest next item to work on |
| `kanban_add_comment` | Add comment to item |
| `kanban_update_item` | Update item properties |
| **`kanban_next_id`** | **Allocate next ID (prevents duplicates!)** |

### Critical: Using `kanban_next_id` for Multi-Agent Safety

When creating new work items, ALWAYS call `kanban_next_id` first:

```json
// Step 1: Allocate ID
{
  "name": "kanban_next_id",
  "arguments": {
    "prefix": "EXP",
    "sync_remote": true
  }
}
// Returns: {"success": true, "id": "EXP-609", "number": 609}

// Step 2: Create file using that ID
// File: work/EXP-609-My-Feature.md with id: EXP-609 in frontmatter
```

This prevents duplicate IDs when multiple agents work concurrently.

### Claude Code Integration

Add to your MCP config:

```json
{
  "mcpServers": {
    "kanban": {
      "command": "yurtle-kanban-mcp",
      "args": []
    }
  }
}
```

Then Claude can manage your kanban:

```
Agent: I'll check what I should work on next.
[Calls: kanban_suggest_next()]

Response: {
  "suggestion": {"id": "FEAT-042", "title": "Add dark mode", "priority": "high"},
  "message": "Suggested: FEAT-042 - Add dark mode"
}

Agent: Let me move that to in progress.
[Calls: kanban_move_item(item_id="FEAT-042", new_status="in_progress")]

Response: {
  "success": true,
  "message": "Moved FEAT-042 to in_progress"
}
```

## Claude Code Skills

yurtle-kanban v1.1+ includes Claude Code skills for multi-agent workflows. Skills are markdown files that define reusable agent workflows.

### Available Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| `/sync` | Start of session | Pull latest, check handoffs, reviews, blocked items |
| `/status` | Show kanban board | See what's in progress, ready, blocked |
| `/work [ID]` | Pick up work | Start work, create branch, update kanban |
| `/expedition <title>` | Create expedition | Allocate ID, create file, push immediately |
| `/done [ID]` | Complete work | Run tests, commit, push, create PR, update kanban |
| `/review ID` | Review expedition | Verify tests, docs, merge readiness |
| `/handoff ID agent-X` | Hand off work | Pass work to another agent with context |
| `/blocked ID reason` | Mark blocked | Track why work is blocked and who can unblock |

### Multi-Agent Coordination

With multiple agents working concurrently, use these patterns:

**Agent assignment tags** (in expedition frontmatter):
```yaml
tags: [agent-a, dgx-required]     # Assigned to Agent A, needs GPU
tags: [agent-b, mac-compatible]   # Assigned to Agent B, runs on Mac
tags: [needs-coordination]        # Requires multiple agents
tags: [any-agent]                 # Anyone can pick up
```

**Handoff notes** are created in `kanban-work/handoffs/` when passing work between agents.

**Session start ritual** (`/sync`):
1. Pull latest from main
2. Check for handoffs addressed to you
3. Check items in review
4. Check blocked items
5. Recommend next action

### Installing Skills

Skills are included in the package. To use them with Claude Code:

1. Copy the `skills/` directory to your project's `.claude/skills/`
2. Or install from the package data:
   ```bash
   cp -r $(python -c "import yurtle_kanban; print(yurtle_kanban.__path__[0])")/../share/yurtle-kanban/skills .claude/
   ```

## Python API

```python
from pathlib import Path
from yurtle_kanban import KanbanConfig, KanbanService, WorkItemType

# Load config
config = KanbanConfig.load(Path(".kanban/config.yaml"))
service = KanbanService(config, Path.cwd())

# List items
items = service.get_items(status=WorkItemStatus.READY)

# Create item
item = service.create_item(
    item_type=WorkItemType.FEATURE,
    title="New feature",
    priority="high",
    assignee="dev-1",
)

# Move item
service.move_item("FEAT-001", WorkItemStatus.DONE)

# Get board
board = service.get_board()
for col in board.columns:
    print(f"{col.name}: {len(board.get_items_by_status(col.id))} items")
```

## Export Formats

### HTML (GitHub Pages compatible)
```bash
yurtle-kanban export --format html --output docs/board.html
```
Self-contained HTML with embedded CSS. Perfect for GitHub Pages.

### Markdown
```bash
yurtle-kanban export --format markdown --output BOARD.md
```
Table format for embedding in README.

### JSON
```bash
yurtle-kanban export --format json > board.json
```
For integrations and CI/CD.

## GitHub Actions

Auto-update board on push:

```yaml
# .github/workflows/kanban-board.yml
name: Update Kanban Board
on:
  push:
    paths:
      - 'work/**/*.md'

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install yurtle-kanban
      - run: yurtle-kanban export --format html --output docs/board.html
      - run: |
          git config user.name "github-actions[bot]"
          git add docs/board.html
          git commit -m "chore: update kanban board" || exit 0
          git push
```

## Why Keep Work Items in Your Project?

| Benefit | Description |
|---------|-------------|
| Single source of truth | Work items live with the code they describe |
| Git history together | Feature branch includes both code AND its work item |
| No external dependency | No Jira outage blocks your workflow |
| Offline-first | Works without internet |
| AI agent access | Agents read/write work items like any file |
| PR integration | Work item changes visible in pull requests |

## Related Projects

- [Yurtle Specification](https://github.com/hankh95/yurtle) - Turtle RDF in Markdown
- [yurtle-rdflib](https://github.com/hankh95/yurtle-rdflib) - RDFlib parser plugin
- [nusy-nano](https://github.com/hankh95/nusy-nano) - Neurosymbolic reasoning

## License

MIT License - see [LICENSE](LICENSE) for details.
