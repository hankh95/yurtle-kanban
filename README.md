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
# Initialize in your project (scaffolds directories + templates)
cd my-project
yurtle-kanban init --theme software
# Creates: kanban-work/features/, kanban-work/bugs/, kanban-work/epics/,
#          kanban-work/issues/, kanban-work/tasks/, kanban-work/ideas/
# Each with a _TEMPLATE.md showing the correct frontmatter format

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

# Prioritized roadmap (excludes done items)
yurtle-kanban roadmap
yurtle-kanban roadmap --by-type
yurtle-kanban roadmap --export md

# Completed work history
yurtle-kanban history
yurtle-kanban history --week
yurtle-kanban history --by-assignee

# Export board
yurtle-kanban export --format html --output board.html
yurtle-kanban export --format markdown --output BOARD.md
yurtle-kanban export --format json
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize with theme, scaffold directories + templates |
| `list` | List work items with optional filters |
| `create` | Create a new work item (`--push` for atomic multi-agent safety) |
| `move` | Move item to new status (with `--assign`, `--force`) |
| `show` | Show item details |
| `board` | Display kanban board in terminal |
| `stats` | Show board statistics |
| `roadmap` | Prioritized view of all non-done items |
| `history` | Completed work log with time filters |
| `metrics` | Flow metrics (cycle time, lead time) |
| `next` | Suggest next item to work on |
| `next-id` | **Allocate next ID atomically (prevents duplicates!)** |
| `blocked` | List blocked items |
| `comment` | Add comment to item |
| `export` | Export board to HTML/Markdown/JSON |
| `validate` | Check for ID mismatches and duplicates |

### Preventing Duplicate IDs (Multi-Agent Safe)

**Recommended:** Use `create --push` for a single atomic operation:

```bash
# Atomic: fetch → allocate → create file → commit → push (retries on conflict)
yurtle-kanban create expedition "Research vectors" --push
yurtle-kanban create feature "Add dark mode" --push --assignee Mini
```

This is the safest approach — one command, no race window between ID allocation and file creation.

**Advanced:** Use `next-id` when you need the ID before creating the file manually:

```bash
yurtle-kanban next-id EXP --json
# {"success": true, "id": "EXP-609", "prefix": "EXP", "number": 609}
```

Both commands:
1. Fetch latest from remote
2. Scan files (frontmatter + filenames + `_ID_ALLOCATIONS.json`) for highest ID
3. Commit and push to claim the ID
4. Retry with rebase if another agent pushed first

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

Running `yurtle-kanban init --theme software` auto-generates this config:

```yaml
# .kanban/config.yaml
kanban:
  theme: software   # or: nautical, custom

  paths:
    root: kanban-work/
    scan_paths:
      - "kanban-work/features/"
      - "kanban-work/bugs/"
      - "kanban-work/epics/"
      - "kanban-work/issues/"
      - "kanban-work/tasks/"
      - "kanban-work/ideas/"

  ignore:
    - "**/archive/**"
    - "**/templates/**"
    - "**/_TEMPLATE*"
```

Each directory gets a `_TEMPLATE.md` with the correct frontmatter and type-specific sections (e.g., bugs get "Steps to Reproduce", features get "Acceptance Criteria").

## Themes

**Software (default):**
```
Feature (FEAT-), Bug (BUG-), Epic (EPIC-), Issue (ISSUE-), Task (TASK-), Idea (IDEA-)
Columns: Backlog → Ready → In Progress → Review → Done
```

**Nautical:**
```
Expedition (EXP-), Voyage (VOY-), Chore (CHORE-), Hazard (HAZ-), Signal (SIG-)
Columns: Harbor → Provisioning → Underway → Approaching Port → Arrived (+ Stranded)
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

yurtle-kanban includes **theme-specific** Claude Code skills for multi-agent workflows. Skills are automatically installed by `yurtle-kanban init` based on your theme.

### Skills by Theme

**Theme-neutral** (installed for all themes):

| Skill | Command | Purpose |
|-------|---------|---------|
| `/sync` | Start of session | Pull latest, check handoffs, reviews, blocked items |
| `/status` | Show kanban board | See what's in progress, ready, blocked |
| `/release [patch\|minor\|major]` | Create release | Bump version, update CHANGELOG, create git tag |

**Nautical theme** (`--theme nautical`):

| Skill | Command | Purpose |
|-------|---------|---------|
| `/expedition <title>` | Create expedition | Atomic `create --push` with EXP- prefix |
| `/work [EXP-XXX]` | Pick up work | Start work, create branch, update kanban |
| `/done [EXP-XXX]` | Complete work | Run tests, commit, push, create PR, update kanban |
| `/review EXP-XXX` | Review expedition | Verify tests, docs, merge readiness |
| `/handoff EXP-XXX agent` | Hand off work | Pass work to another agent with context |
| `/blocked EXP-XXX reason` | Mark blocked | Track why work is blocked and who can unblock |

**Software theme** (`--theme software`):

| Skill | Command | Purpose |
|-------|---------|---------|
| `/feature <title>` | Create feature | Atomic `create --push` with FEAT- prefix |
| `/work [FEAT-XXX]` | Pick up work | Start work, create branch, update kanban |
| `/done [FEAT-XXX]` | Complete work | Run tests, commit, push, create PR, update kanban |
| `/review FEAT-XXX` | Review feature | Verify tests, docs, merge readiness |
| `/handoff FEAT-XXX agent` | Hand off work | Pass work to another agent with context |
| `/blocked FEAT-XXX reason` | Mark blocked | Track why work is blocked and who can unblock |

### Multi-Agent Coordination

With multiple agents working concurrently, use these patterns:

**Agent assignment tags** (in work item frontmatter):
```yaml
tags: [agent-a, gpu-required]     # Assigned to Agent A, needs GPU
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

Skills are automatically installed to `.claude/skills/` when you run `yurtle-kanban init`:

```bash
yurtle-kanban init --theme nautical   # Installs nautical skills (/expedition, etc.)
yurtle-kanban init --theme software   # Installs software skills (/feature, etc.)
```

To install manually:
```bash
# Theme-neutral skills (always needed)
cp -r skills/sync skills/status skills/release .claude/skills/

# Theme-specific skills (pick one)
cp -r skills/nautical/* .claude/skills/   # Nautical theme
cp -r skills/software/* .claude/skills/   # Software theme
```

## Agent Instructions (CLAUDE.md Snippet)

Add this to your project's `CLAUDE.md` (or equivalent copilot instructions) so AI agents use yurtle-kanban correctly:

````markdown
## Work Tracking (yurtle-kanban)

This project uses yurtle-kanban for work tracking. Git is the database.

**Creating work items (IMPORTANT — prevents ID conflicts):**
```bash
# ALWAYS use --push when creating items. This is atomic and multi-agent safe.
yurtle-kanban create <type> "<title>" --push [--priority <p>] [--assignee <name>]

# Examples:
yurtle-kanban create expedition "Research vectors" --push --priority high
yurtle-kanban create feature "Add dark mode" --push --assignee Mini
```

The `--push` flag atomically: fetches latest → allocates ID → creates file → commits → pushes.
If another agent pushed first, it retries with a new ID. Never create items without `--push`.

**Viewing work:**
```bash
yurtle-kanban board                        # Kanban board
yurtle-kanban roadmap                      # Prioritized backlog
yurtle-kanban list --status in_progress    # Filter by status
yurtle-kanban history --week               # Recent completions
```

**Moving items:**
```bash
yurtle-kanban move EXP-001 in_progress
yurtle-kanban move EXP-001 done
```
````

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

## Changelog

### v1.9.0
- **Theme-specific skills** — Skills are now organized by theme (`skills/nautical/`, `skills/software/`). Software theme gets `/feature`, `/work`, `/done`, `/review`, `/handoff`, `/blocked` with FEAT-prefixed terminology. Theme-neutral skills (`/sync`, `/status`, `/release`) stay shared.
- **Auto-install skills on init** — `yurtle-kanban init` now copies theme-matched skills to `.claude/skills/` automatically
- **`create --push` no-remote fix** — Gracefully degrades to local commit when no git remote is configured (v1.8.1)

### v1.8.0
- **`create --push`** — Atomic create: fetch → allocate → create file → commit → push, with retry on conflict. Eliminates ID race conditions in multi-agent workflows.
- **Agent Instructions** — README now includes a copyable CLAUDE.md snippet for AI agent projects

### v1.7.0
- **`init` scaffolding** — Creates type-specific directories with `_TEMPLATE.md` files, auto-populates `scan_paths` in config (#7)
- **`roadmap` command** — Prioritized view of non-done items with `--by-type`, `--type`, `--export md`, `--json` (#1)
- **`history` command** — Completed work log with `--week`, `--month`, `--since`, `--by-assignee`, `--by-type` (#2)

### v1.6.0
- **`next-id` fix** — Now reads `_ID_ALLOCATIONS.json` as source of truth (was only scanning filesystem) (#8)
- **`create` file placement** — Items go into theme-defined type directories (e.g., `kanban-work/expeditions/`) with slugified filenames (#9)
- **Theme `path:` field** — Both nautical and software themes define explicit paths per item type (#10)
- 17 new tests for ID allocation, file placement, slug generation, and directory resolution

### v1.5.0
- Flow metrics with TTL status history tracking (`metrics` command)
- `--force` flag on `move` to skip WIP limit checks
- Increased WIP limits in nautical theme

### v1.4.0
- `--assign` and `--export-board` options on `move` command
- Expedition-index export format with Work Trail and Dependency Tree

### v1.3.0
- Expedition-index export format

### v1.2.0
- `/release` skill for semantic versioning
- Modern Python 3.10+ type hints

### v1.1.0
- Claude Code skills for multi-agent workflows (`/sync`, `/work`, `/done`, `/expedition`, etc.)

### v1.0.0
- Initial release: CLI, board, list, create, move, show, stats, next-id, export, validate, MCP server

## Related Projects

- [Yurtle Specification](https://github.com/hankh95/yurtle) - Turtle RDF in Markdown
- [yurtle-rdflib](https://github.com/hankh95/yurtle-rdflib) - RDFlib parser plugin
- [nusy-nano](https://github.com/hankh95/nusy-nano) - Neurosymbolic reasoning

## License

MIT License - see [LICENSE](LICENSE) for details.
