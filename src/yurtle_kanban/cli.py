"""
yurtle-kanban CLI

File-based kanban using Yurtle (Turtle RDF in Markdown). Git is your database.

Usage:
    yurtle-kanban init [--theme THEME] [--path PATH]
    yurtle-kanban list [--status STATUS] [--type TYPE] [--assignee ASSIGNEE]
    yurtle-kanban create TYPE TITLE [--priority PRIORITY] [--assignee ASSIGNEE] [--push]
    yurtle-kanban move ID STATUS
    yurtle-kanban show ID
    yurtle-kanban board
    yurtle-kanban stats
    yurtle-kanban roadmap [--by-type] [--type TYPE] [--export md]
    yurtle-kanban history [--week] [--month] [--since DATE] [--by-assignee]
    yurtle-kanban next [--assignee ASSIGNEE]
    yurtle-kanban export --format FORMAT [--output FILE]
"""

import json
import shutil
import sys
from pathlib import Path

import click
from rich.console import Console

from .board import (
    render_board,
    render_history,
    render_item_detail,
    render_list,
    render_roadmap,
    render_stats,
)
from .config import KanbanConfig
from .export import export_expedition_index, export_html, export_json, export_markdown
from .models import WorkItemStatus, WorkItemType
from .service import KanbanService


def _get_templates_dir() -> Path:
    """Get the path to the templates directory in the package."""
    # Templates are at the package root level (not in src/)
    try:
        import yurtle_kanban

        package_dir = Path(yurtle_kanban.__file__).parent.parent.parent
        templates_dir = package_dir / "templates"
        if templates_dir.exists():
            return templates_dir
    except Exception:
        pass

    # Fallback: try relative to this file
    templates_dir = Path(__file__).parent.parent.parent / "templates"
    return templates_dir


def _get_skills_dir() -> Path:
    """Get the path to the skills directory in the package."""
    try:
        import yurtle_kanban

        package_dir = Path(yurtle_kanban.__file__).parent.parent.parent
        skills_dir = package_dir / "skills"
        if skills_dir.exists():
            return skills_dir
    except Exception:
        pass

    # Fallback: try relative to this file
    skills_dir = Path(__file__).parent.parent.parent / "skills"
    return skills_dir


console = Console()


def get_service() -> KanbanService:
    """Get the kanban service for the current directory."""
    repo_root = Path.cwd()

    # Find .kanban/config.yaml
    config_path = repo_root / ".kanban" / "config.yaml"

    if config_path.exists():
        config = KanbanConfig.load(config_path)
    else:
        config = KanbanConfig()  # Use defaults

    return KanbanService(config, repo_root)


@click.group()
@click.version_option(package_name="yurtle-kanban")
def main():
    """File-based kanban using Yurtle. Git is your database."""
    pass


def _generate_template(prefix: str, type_name: str, sections: list[str]) -> str:
    """Generate a _TEMPLATE.md file for an item type."""
    section_text = "\n\n".join(f"## {s}\n" for s in sections)
    return f"""---
id: {prefix}-XXX
title: ""
status: backlog
created: YYYY-MM-DD
priority: medium
assignee:
tags: []
related: []
---

# {prefix}-XXX: Title

{section_text}"""


# Template sections per item type
_TEMPLATE_SECTIONS: dict[str, list[str]] = {
    # Software theme
    "feature": ["Goal", "Acceptance Criteria"],
    "bug": ["Description", "Steps to Reproduce", "Expected Behavior", "Actual Behavior"],
    "epic": ["Goal", "Scope", "Milestones"],
    "issue": ["Description", "Context"],
    "task": ["Goal", "Steps", "Acceptance Criteria"],
    "idea": ["Description", "Motivation"],
    # Nautical theme
    "expedition": ["Context", "Plan", "Definition of Done"],
    "voyage": ["Vision", "Expeditions", "Success Criteria"],
    "chore": ["Description"],
    "hazard": ["Description", "Impact", "Mitigation"],
    "signal": ["Observation", "Potential Value"],
}


@main.command()
@click.option("--theme", default="software", help="Theme: software, nautical, or custom")
@click.option("--path", default="work/", help="Path for work items")
def init(theme: str, path: str):
    """Initialize yurtle-kanban in the current directory."""
    from .config import _load_builtin_theme

    repo_root = Path.cwd()

    # Create .kanban directory structure
    kanban_dir = repo_root / ".kanban"
    kanban_dir.mkdir(exist_ok=True)
    (kanban_dir / "workflows").mkdir(exist_ok=True)
    (kanban_dir / "templates").mkdir(exist_ok=True)

    # Load theme to discover item types and paths
    theme_data = _load_builtin_theme(theme, repo_root)
    item_types = theme_data.get("item_types", {}) if theme_data else {}

    # Scaffold type-specific directories with templates
    scan_paths = []
    dirs_created = []
    for type_id, type_def in item_types.items():
        type_path = type_def.get("path")
        if type_path:
            type_dir = repo_root / type_path
            type_dir.mkdir(parents=True, exist_ok=True)
            scan_paths.append(type_path)
            dirs_created.append(type_path)

            # Create _TEMPLATE.md in each directory
            prefix = type_def.get("id_prefix", type_id[:4].upper())
            sections = _TEMPLATE_SECTIONS.get(type_id, ["Description"])
            template_path = type_dir / "_TEMPLATE.md"
            if not template_path.exists():
                template_path.write_text(_generate_template(prefix, type_id, sections))

    # Create config.yaml with auto-populated scan_paths
    scan_paths_yaml = "\n".join(f'    - "{p}"' for p in scan_paths)
    config_content = f"""# yurtle-kanban configuration
kanban:
  theme: {theme}

  paths:
    root: {path}
    scan_paths:
{scan_paths_yaml}

  ignore:
    - "**/archive/**"
    - "**/templates/**"
    - "**/_TEMPLATE*"
"""
    config_path = kanban_dir / "config.yaml"
    config_path.write_text(config_content)

    # Copy any additional theme templates
    templates_src = _get_templates_dir()
    theme_templates = templates_src / theme
    templates_copied = 0
    if theme_templates.exists():
        templates_dst = kanban_dir / "templates"
        for template_file in theme_templates.glob("*.md"):
            shutil.copy(template_file, templates_dst / template_file.name)
            templates_copied += 1

    # Create root work directory (fallback)
    work_dir = repo_root / path
    work_dir.mkdir(parents=True, exist_ok=True)

    # Install theme-matched Claude Code skills
    skills_src = _get_skills_dir()
    skills_installed = 0
    if skills_src.exists():
        skills_dst = repo_root / ".claude" / "skills"
        skills_dst.mkdir(parents=True, exist_ok=True)

        # Copy theme-neutral skills (sync, status, release)
        for skill_dir in skills_src.iterdir():
            if skill_dir.is_dir() and skill_dir.name not in ("nautical", "software"):
                dst = skills_dst / skill_dir.name
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(skill_dir, dst)
                skills_installed += 1

        # Copy theme-specific skills
        theme_skills = skills_src / theme
        if theme_skills.exists():
            for skill_dir in theme_skills.iterdir():
                if skill_dir.is_dir():
                    dst = skills_dst / skill_dir.name
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(skill_dir, dst)
                    skills_installed += 1

    console.print(f"[green]Initialized yurtle-kanban with theme '{theme}'[/green]")
    console.print("  Config:  .kanban/config.yaml")
    if dirs_created:
        for d in dirs_created:
            console.print(f"  Created: {d} (with _TEMPLATE.md)")
    else:
        console.print(f"  Created: {path}")
    if templates_copied:
        console.print(f"  Copied:  {templates_copied} templates to .kanban/templates/")
    if skills_installed:
        console.print(
            f"  Skills:  {skills_installed} Claude Code skills installed to .claude/skills/"
        )
    console.print()
    console.print("Next steps:")
    example_type = list(item_types.keys())[0] if item_types else "feature"
    console.print(f"  1. Create work items: yurtle-kanban create {example_type} 'My item'")
    console.print("  2. View board: yurtle-kanban board")


@main.command("list")
@click.option("--status", "-s", help="Filter by status (backlog, ready, in_progress, review, done)")
@click.option("--type", "-t", "item_type", help="Filter by type (feature, bug, epic, task)")
@click.option("--assignee", "-a", help="Filter by assignee")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_items(
    status: str | None,
    item_type: str | None,
    assignee: str | None,
    as_json: bool,
):
    """List work items."""
    service = get_service()

    # Parse filters
    status_filter = None
    if status:
        try:
            status_filter = WorkItemStatus.from_string(status)
        except ValueError:
            console.print(f"[red]Unknown status: {status}[/red]")
            sys.exit(1)

    type_filter = None
    if item_type:
        try:
            type_filter = WorkItemType.from_string(item_type)
        except ValueError:
            console.print(f"[red]Unknown type: {item_type}[/red]")
            sys.exit(1)

    items = service.get_items(
        status=status_filter,
        item_type=type_filter,
        assignee=assignee,
    )

    if not items:
        console.print("[dim]No work items found.[/dim]")
        return

    if as_json:
        data = [item.to_dict() for item in items]
        click.echo(json.dumps(data, indent=2))
    else:
        render_list(items, console)


@main.command()
@click.argument("item_type")
@click.argument("title")
@click.option("--priority", "-p", default="medium", help="Priority: critical, high, medium, low")
@click.option("--assignee", "-a", help="Assignee")
@click.option("--description", "-d", help="Description")
@click.option("--tags", help="Comma-separated tags")
@click.option(
    "--push",
    is_flag=True,
    help="Atomic: allocate ID, create file, commit, and push (multi-agent safe)",
)
def create(
    item_type: str,
    title: str,
    priority: str,
    assignee: str | None,
    description: str | None,
    tags: str | None,
    push: bool,
):
    """Create a new work item.

    Use --push for multi-agent safety: fetches latest, allocates ID,
    creates the file, commits, and pushes in one atomic operation.
    If another agent pushed first, it retries with a new ID.

    Examples:
        yurtle-kanban create feature "Add dark mode"
        yurtle-kanban create expedition "Research vectors" --push
        yurtle-kanban create bug "Login crash" --push --assignee Mini
    """
    service = get_service()

    try:
        work_type = WorkItemType.from_string(item_type)
    except ValueError:
        console.print(f"[red]Unknown type: {item_type}[/red]")
        console.print(f"Valid types: {', '.join(t.value for t in WorkItemType)}")
        sys.exit(1)

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    if push:
        result = service.create_item_and_push(
            item_type=work_type,
            title=title,
            priority=priority,
            assignee=assignee,
            description=description,
            tags=tag_list,
        )
        if result["success"]:
            item = result["item"]
            if result.get("pushed"):
                console.print(f"[green]Created and pushed {result['id']}: {title}[/green]")
                console.print(f"  File: {item.file_path}")
                console.print("[dim]  (committed and pushed to remote)[/dim]")
            else:
                console.print(f"[green]Created {result['id']}: {title}[/green]")
                console.print(f"  File: {item.file_path}")
                console.print("[dim]  (committed locally — no remote configured)[/dim]")
        else:
            console.print(f"[red]Failed: {result['message']}[/red]")
            sys.exit(1)
    else:
        item = service.create_item(
            item_type=work_type,
            title=title,
            priority=priority,
            assignee=assignee,
            description=description,
            tags=tag_list,
        )
        console.print(f"[green]Created {item.id}: {item.title}[/green]")
        console.print(f"  File: {item.file_path}")


@main.command()
@click.argument("item_id")
@click.argument("new_status")
@click.option("--no-commit", is_flag=True, help="Don't create git commit")
@click.option("--message", "-m", help="Custom commit message")
@click.option("--assign", "-a", help="Set assignee (e.g., 'Claude-M5', 'Claude-DGX')")
@click.option(
    "--export-board",
    "-e",
    help="Export board to file after move (e.g., 'kanban-work/KANBAN-BOARD.md')",
)
@click.option("--force", "-f", is_flag=True, help="Skip WIP limit and workflow validation")
def move(
    item_id: str,
    new_status: str,
    no_commit: bool,
    message: str | None,
    assign: str | None,
    export_board: str | None,
    force: bool,
):
    """Move a work item to a new status.

    Examples:
        yurtle-kanban move EXP-123 in_progress
        yurtle-kanban move EXP-123 in_progress --assign "Claude-M5"
        yurtle-kanban move EXP-123 done --export-board kanban-work/KANBAN-BOARD.md
        yurtle-kanban move EXP-123 ready --force  # Skip WIP limit check
    """
    service = get_service()

    try:
        status = WorkItemStatus.from_string(new_status)
    except ValueError:
        console.print(f"[red]Unknown status: {new_status}[/red]")
        console.print(f"Valid statuses: {', '.join(s.value for s in WorkItemStatus)}")
        sys.exit(1)

    try:
        item = service.move_item(
            item_id.upper(),
            status,
            commit=not no_commit,
            message=message,
            assignee=assign,
            skip_wip_check=force,
            validate_workflow=not force,
        )
        console.print(f"[green]Moved {item.id} to {status.value}[/green]")
        if assign:
            console.print(f"  Assigned to: {assign}")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    # Export board if requested
    if export_board:
        board = service.get_board()
        content = export_expedition_index(board, min_id=600)
        Path(export_board).write_text(content)
        console.print(f"[green]Exported board to {export_board}[/green]")


@main.command()
@click.argument("item_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show(item_id: str, as_json: bool):
    """Show details of a work item."""
    service = get_service()

    item = service.get_item(item_id.upper())
    if not item:
        if as_json:
            click.echo(json.dumps({"error": f"Item not found: {item_id}"}))
        else:
            console.print(f"[red]Item not found: {item_id}[/red]")
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(item.to_dict(), indent=2))
    else:
        render_item_detail(item, console)


@main.command()
def board():
    """Show the kanban board view."""
    service = get_service()
    board = service.get_board()
    render_board(board, console)


@main.command()
def stats():
    """Show board statistics."""
    service = get_service()
    board = service.get_board()
    render_stats(board, console)


@main.command()
@click.option("--by-type", is_flag=True, help="Group by item type")
@click.option("--type", "-t", "item_type", help="Filter to a single item type")
@click.option("--export", "-e", "export_fmt", type=click.Choice(["md"]), help="Export as markdown")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def roadmap(by_type: bool, item_type: str | None, export_fmt: str | None, as_json: bool):
    """Show a prioritized roadmap of all work items.

    Displays all non-done items sorted by priority (critical first).
    Use --by-type to group by item type.

    Examples:
        yurtle-kanban roadmap
        yurtle-kanban roadmap --by-type
        yurtle-kanban roadmap --type expedition
        yurtle-kanban roadmap --export md
    """
    service = get_service()

    # Get all non-done items
    items = service.get_items()
    items = [i for i in items if i.status != WorkItemStatus.DONE]

    # Optional type filter
    if item_type:
        try:
            type_filter = WorkItemType.from_string(item_type)
            items = [i for i in items if i.item_type == type_filter]
        except ValueError:
            console.print(f"[red]Unknown type: {item_type}[/red]")
            sys.exit(1)

    # Items are already sorted by priority from get_items()
    if as_json:
        data = [item.to_dict() for item in items]
        click.echo(json.dumps(data, indent=2))
    elif export_fmt == "md":
        lines = ["# Roadmap\n"]
        for i, item in enumerate(items, 1):
            priority = item.priority or "medium"
            assignee = item.assignee or "unassigned"
            lines.append(
                f"{i}. **{item.id}**: {item.title} [{priority}] ({item.status.value}) @{assignee}"
            )
        click.echo("\n".join(lines))
    else:
        render_roadmap(items, console, by_type=by_type)


@main.command()
@click.option("--since", help="Show items completed since date (YYYY-MM-DD)")
@click.option("--week", is_flag=True, help="Show items completed in the last 7 days")
@click.option("--month", is_flag=True, help="Show items completed in the last 30 days")
@click.option("--by-assignee", is_flag=True, help="Group by assignee")
@click.option("--by-type", is_flag=True, help="Group by item type")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def history(
    since: str | None,
    week: bool,
    month: bool,
    by_assignee: bool,
    by_type: bool,
    as_json: bool,
):
    """Show completed work history.

    Displays done items in reverse chronological order.
    Use time filters to narrow the range.

    Examples:
        yurtle-kanban history
        yurtle-kanban history --week
        yurtle-kanban history --since 2026-01-01
        yurtle-kanban history --by-assignee
    """
    from datetime import datetime, timedelta

    service = get_service()

    # Get done items
    items = service.get_items(status=WorkItemStatus.DONE)

    # Apply time filters
    cutoff = None
    if week:
        cutoff = datetime.now() - timedelta(days=7)
    elif month:
        cutoff = datetime.now() - timedelta(days=30)
    elif since:
        try:
            cutoff = datetime.fromisoformat(since)
        except ValueError:
            console.print(f"[red]Invalid date format: {since} (use YYYY-MM-DD)[/red]")
            sys.exit(1)

    if cutoff:
        filtered = []
        for item in items:
            if item.updated and item.updated >= cutoff:
                filtered.append(item)
            elif item.created and datetime.combine(item.created, datetime.min.time()) >= cutoff:
                filtered.append(item)
        items = filtered

    # Sort by updated date (most recent first)
    items.sort(key=lambda i: i.updated or datetime.min, reverse=True)

    if as_json:
        data = [item.to_dict() for item in items]
        click.echo(json.dumps(data, indent=2))
    else:
        render_history(items, console, by_assignee=by_assignee, by_type=by_type)


@main.command("next")
@click.option("--assignee", "-a", help="Filter by assignee")
def next_item(assignee: str | None):
    """Suggest the next item to work on."""
    service = get_service()

    item = service.suggest_next_item(assignee=assignee)

    if not item:
        console.print("[dim]No ready items to work on.[/dim]")
        return

    console.print("[bold]Suggested next item:[/bold]")
    render_item_detail(item, console)


@main.command()
@click.argument("item_id")
@click.argument("comment")
@click.option("--author", "-a", default="cli", help="Comment author")
def comment(item_id: str, comment: str, author: str):
    """Add a comment to a work item."""
    service = get_service()

    try:
        item = service.add_comment(item_id.upper(), comment, author)
        console.print(f"[green]Added comment to {item.id}[/green]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
def blocked():
    """List blocked items."""
    service = get_service()
    items = service.get_blocked_items()

    if not items:
        console.print("[green]No blocked items.[/green]")
        return

    console.print(f"[bold red]Blocked Items ({len(items)})[/bold red]")
    render_list(items, console)


@main.command()
@click.argument("item_id", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def metrics(item_id: str | None, as_json: bool):
    """Show flow metrics for an item or the board.

    Flow metrics track time spent in each status to help identify bottlenecks.
    Status history is automatically recorded when items move between statuses.

    Examples:
        yurtle-kanban metrics           # Board-wide metrics
        yurtle-kanban metrics EXP-123   # Metrics for a specific item
    """
    service = get_service()

    if item_id:
        # Single item metrics
        metrics_data = service.get_flow_metrics(item_id.upper())

        if "error" in metrics_data:
            console.print(f"[yellow]{metrics_data['error']}[/yellow]")
            console.print("[dim]Status history is recorded when items move between statuses.[/dim]")
            return

        if as_json:
            click.echo(json.dumps(metrics_data, indent=2, default=str))
        else:
            console.print(f"[bold]Flow Metrics: {item_id.upper()}[/bold]")
            console.print()

            if metrics_data.get("cycle_time_hours"):
                hours = metrics_data["cycle_time_hours"]
                if hours < 24:
                    console.print(f"  Cycle Time: {hours:.1f} hours")
                else:
                    console.print(f"  Cycle Time: {hours / 24:.1f} days")

            if metrics_data.get("lead_time_hours"):
                hours = metrics_data["lead_time_hours"]
                if hours < 24:
                    console.print(f"  Lead Time: {hours:.1f} hours")
                else:
                    console.print(f"  Lead Time: {hours / 24:.1f} days")

            console.print(f"  Transitions: {metrics_data['transitions']}")
            console.print()

            if metrics_data.get("time_in_status"):
                console.print("  [bold]Time in Status:[/bold]")
                for status, hours in sorted(metrics_data["time_in_status"].items()):
                    if hours < 24:
                        console.print(f"    {status}: {hours:.1f} hours")
                    else:
                        console.print(f"    {status}: {hours / 24:.1f} days")
    else:
        # Board-wide metrics
        metrics_data = service.get_board_metrics()

        if as_json:
            click.echo(json.dumps(metrics_data, indent=2, default=str))
        else:
            console.print("[bold]Board Flow Metrics[/bold]")
            console.print()
            console.print(f"  Total Items: {metrics_data['total_items']}")
            console.print(f"  Items with History: {metrics_data['items_with_history']}")

            if metrics_data.get("avg_cycle_time_hours"):
                hours = metrics_data["avg_cycle_time_hours"]
                if hours < 24:
                    console.print(f"  Avg Cycle Time: {hours:.1f} hours")
                else:
                    console.print(f"  Avg Cycle Time: {hours / 24:.1f} days")

            if metrics_data.get("avg_lead_time_hours"):
                hours = metrics_data["avg_lead_time_hours"]
                if hours < 24:
                    console.print(f"  Avg Lead Time: {hours:.1f} hours")
                else:
                    console.print(f"  Avg Lead Time: {hours / 24:.1f} days")

            if not metrics_data.get("items_with_history"):
                console.print()
                console.print(
                    "[dim]No status history yet. History is recorded when items move.[/dim]"
                )


@main.command("export")
@click.option(
    "--format",
    "-f",
    "fmt",
    required=True,
    type=click.Choice(["html", "markdown", "json", "expedition-index"]),
    help="Export format",
)
@click.option("--output", "-o", help="Output file (default: stdout)")
@click.option("--min-id", default=600, help="Minimum ID for Work Trail (expedition-index only)")
def export_cmd(fmt: str, output: str | None, min_id: int):
    """Export the board to various formats.

    Formats:
    - html: Standalone HTML board view
    - markdown: Simple markdown table
    - json: JSON for integrations
    - expedition-index: Enhanced index with Work Trail and Dependency Tree
    """
    service = get_service()
    board = service.get_board()

    if fmt == "html":
        content = export_html(board)
    elif fmt == "markdown":
        content = export_markdown(board)
    elif fmt == "json":
        content = export_json(board)
    elif fmt == "expedition-index":
        content = export_expedition_index(board, min_id=min_id)
    else:
        console.print(f"[red]Unknown format: {fmt}[/red]")
        sys.exit(1)

    if output:
        Path(output).write_text(content)
        console.print(f"[green]Exported to {output}[/green]")
    else:
        click.echo(content)


@main.command("next-id")
@click.argument("prefix")
@click.option("--no-sync", is_flag=True, help="Skip git fetch/push (local only)")
@click.option("--no-commit", is_flag=True, help="Don't commit the allocation")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def next_id(prefix: str, no_sync: bool, no_commit: bool, as_json: bool):
    """Allocate the next available ID for a prefix.

    This command prevents duplicate IDs when multiple agents create work items
    concurrently by:
    1. Fetching latest changes from remote
    2. Scanning all files to find the highest ID
    3. Committing and pushing an allocation lock file

    Examples:
        yurtle-kanban next-id EXP       # Allocate next expedition ID
        yurtle-kanban next-id FEAT      # Allocate next feature ID
        yurtle-kanban next-id EXP --no-sync  # Local only (no git operations)
    """
    service = get_service()

    result = service.allocate_next_id(
        prefix=prefix,
        sync_remote=not no_sync,
        commit_allocation=not no_commit,
    )

    if as_json:
        click.echo(json.dumps(result, indent=2))
    else:
        if result["success"]:
            console.print(f"[green]Allocated: {result['id']}[/green]")
            console.print(f"  Prefix: {result['prefix']}")
            console.print(f"  Number: {result['number']}")
            if not no_sync:
                console.print("[dim]  (committed and pushed to remote)[/dim]")
        else:
            console.print(f"[red]Failed to allocate ID: {result['message']}[/red]")
            sys.exit(1)


@main.command()
@click.option("--fix", is_flag=True, help="Attempt to fix issues (rename files)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def validate(fix: bool, as_json: bool):
    """Validate work items for consistency issues.

    Checks:
    - File name matches ID in frontmatter
    - No duplicate IDs
    - Required fields present (id, title, status, type)
    """
    service = get_service()
    items = service.get_items()

    issues = []
    seen_ids = {}

    for item in items:
        # Check for duplicate IDs
        if item.id in seen_ids:
            issues.append(
                {
                    "type": "duplicate_id",
                    "id": item.id,
                    "file": str(item.file_path),
                    "other_file": str(seen_ids[item.id]),
                    "message": (
                        f"Duplicate ID: {item.id} in "
                        f"{item.file_path} and {seen_ids[item.id]}"
                    ),
                }
            )
        else:
            seen_ids[item.id] = item.file_path

        # Check file name matches ID
        file_stem = item.file_path.stem  # e.g., "EXP-300-Some-Title"
        expected_prefix = item.id  # e.g., "EXP-300"

        if not file_stem.startswith(expected_prefix):
            issues.append(
                {
                    "type": "filename_mismatch",
                    "id": item.id,
                    "file": str(item.file_path),
                    "expected_prefix": expected_prefix,
                    "message": f"File name '{file_stem}' doesn't start with ID '{expected_prefix}'",
                }
            )

    if as_json:
        result = {
            "valid": len(issues) == 0,
            "items_checked": len(items),
            "issues": issues,
        }
        click.echo(json.dumps(result, indent=2))
        if issues:
            sys.exit(1)
        return

    if not issues:
        console.print("[green]All work items valid.[/green]")
        console.print(f"  Checked {len(items)} items")
        return

    # Report issues
    console.print(f"[bold red]Found {len(issues)} issue(s):[/bold red]")
    console.print()

    for issue in issues:
        if issue["type"] == "duplicate_id":
            console.print(f"[red]DUPLICATE ID:[/red] {issue['id']}")
            console.print(f"  File 1: {issue['file']}")
            console.print(f"  File 2: {issue['other_file']}")
        elif issue["type"] == "filename_mismatch":
            console.print(f"[yellow]FILENAME MISMATCH:[/yellow] {issue['id']}")
            console.print(f"  File: {issue['file']}")
            console.print(f"  Expected prefix: {issue['expected_prefix']}")

        console.print()

    if fix:
        fixed = 0
        for issue in issues:
            if issue["type"] == "filename_mismatch":
                old_path = Path(issue["file"])
                # Build new filename: ID + rest of old name after any existing ID
                old_stem = old_path.stem
                new_stem = issue["expected_prefix"]

                # Try to preserve the descriptive part after the ID
                # e.g., "EXP-303-Automated-Domain-Research" -> keep "-Automated-Domain-Research"
                import re

                match = re.match(r"^[A-Z]+-\d+(-.*)?$", old_stem)
                if match and match.group(1):
                    new_stem = issue["expected_prefix"] + match.group(1)

                new_path = old_path.parent / f"{new_stem}{old_path.suffix}"

                if new_path != old_path and not new_path.exists():
                    old_path.rename(new_path)
                    console.print(f"[green]Fixed:[/green] {old_path.name} -> {new_path.name}")
                    fixed += 1

        if fixed:
            console.print(f"\n[green]Fixed {fixed} issue(s)[/green]")
    else:
        console.print("[dim]Run with --fix to attempt automatic fixes[/dim]")

    sys.exit(1)


if __name__ == "__main__":
    main()
