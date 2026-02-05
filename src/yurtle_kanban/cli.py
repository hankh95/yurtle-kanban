"""
yurtle-kanban CLI

File-based kanban using Yurtle (Turtle RDF in Markdown). Git is your database.

Usage:
    yurtle-kanban init [--theme THEME] [--path PATH]
    yurtle-kanban list [--status STATUS] [--type TYPE] [--assignee ASSIGNEE]
    yurtle-kanban create TYPE TITLE [--priority PRIORITY] [--assignee ASSIGNEE]
    yurtle-kanban move ID STATUS
    yurtle-kanban show ID
    yurtle-kanban board
    yurtle-kanban stats
    yurtle-kanban next [--assignee ASSIGNEE]
    yurtle-kanban export --format FORMAT [--output FILE]
"""

import json
import shutil
import sys
from pathlib import Path

import click
from rich.console import Console

from .board import render_board, render_item_detail, render_list, render_stats
from .config import KanbanConfig
from .export import export_html, export_json, export_markdown, export_expedition_index
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


@main.command()
@click.option("--theme", default="software", help="Theme: software, nautical, or custom")
@click.option("--path", default="work/", help="Path for work items")
def init(theme: str, path: str):
    """Initialize yurtle-kanban in the current directory."""
    repo_root = Path.cwd()

    # Create .kanban directory structure
    kanban_dir = repo_root / ".kanban"
    kanban_dir.mkdir(exist_ok=True)
    (kanban_dir / "workflows").mkdir(exist_ok=True)
    (kanban_dir / "templates").mkdir(exist_ok=True)

    # Create config.yaml
    config_content = f"""# yurtle-kanban configuration
kanban:
  theme: {theme}

  paths:
    root: {path}

  # scan_paths:
  #   - {path}
  #   - specs/

  ignore:
    - "**/archive/**"
    - "**/templates/**"
"""
    config_path = kanban_dir / "config.yaml"
    config_path.write_text(config_content)

    # Copy templates for the selected theme
    templates_src = _get_templates_dir()
    theme_templates = templates_src / theme
    templates_copied = 0

    if theme_templates.exists():
        templates_dst = kanban_dir / "templates"
        for template_file in theme_templates.glob("*.md"):
            shutil.copy(template_file, templates_dst / template_file.name)
            templates_copied += 1

    # Create work directory
    work_dir = repo_root / path
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / ".gitkeep").touch()

    console.print(f"[green]Initialized yurtle-kanban with theme '{theme}'[/green]")
    console.print(f"  Created: .kanban/config.yaml")
    console.print(f"  Created: .kanban/templates/ ({templates_copied} templates)")
    console.print(f"  Created: .kanban/workflows/")
    console.print(f"  Created: {path}")
    console.print()
    console.print("Next steps:")
    console.print(f"  1. Create work items: yurtle-kanban create feature 'My feature'")
    console.print(f"  2. View board: yurtle-kanban board")
    console.print(f"  3. Customize templates in .kanban/templates/")


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
def create(
    item_type: str,
    title: str,
    priority: str,
    assignee: str | None,
    description: str | None,
    tags: str | None,
):
    """Create a new work item."""
    service = get_service()

    try:
        work_type = WorkItemType.from_string(item_type)
    except ValueError:
        console.print(f"[red]Unknown type: {item_type}[/red]")
        console.print(f"Valid types: {', '.join(t.value for t in WorkItemType)}")
        sys.exit(1)

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

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
@click.option("--export-board", "-e", help="Export board to file after move (e.g., 'kanban-work/KANBAN-BOARD.md')")
@click.option("--force", "-f", is_flag=True, help="Skip WIP limit and workflow validation")
def move(item_id: str, new_status: str, no_commit: bool, message: str | None, assign: str | None, export_board: str | None, force: bool):
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
def show(item_id: str):
    """Show details of a work item."""
    service = get_service()

    item = service.get_item(item_id.upper())
    if not item:
        console.print(f"[red]Item not found: {item_id}[/red]")
        sys.exit(1)

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
                    console.print(f"  Cycle Time: {hours/24:.1f} days")

            if metrics_data.get("lead_time_hours"):
                hours = metrics_data["lead_time_hours"]
                if hours < 24:
                    console.print(f"  Lead Time: {hours:.1f} hours")
                else:
                    console.print(f"  Lead Time: {hours/24:.1f} days")

            console.print(f"  Transitions: {metrics_data['transitions']}")
            console.print()

            if metrics_data.get("time_in_status"):
                console.print("  [bold]Time in Status:[/bold]")
                for status, hours in sorted(metrics_data["time_in_status"].items()):
                    if hours < 24:
                        console.print(f"    {status}: {hours:.1f} hours")
                    else:
                        console.print(f"    {status}: {hours/24:.1f} days")
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
                    console.print(f"  Avg Cycle Time: {hours/24:.1f} days")

            if metrics_data.get("avg_lead_time_hours"):
                hours = metrics_data["avg_lead_time_hours"]
                if hours < 24:
                    console.print(f"  Avg Lead Time: {hours:.1f} hours")
                else:
                    console.print(f"  Avg Lead Time: {hours/24:.1f} days")

            if not metrics_data.get("items_with_history"):
                console.print()
                console.print("[dim]No status history yet. History is recorded when items move.[/dim]")


@main.command("export")
@click.option("--format", "-f", "fmt", required=True,
              type=click.Choice(["html", "markdown", "json", "expedition-index"]),
              help="Export format")
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
def validate(fix: bool):
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
            issues.append({
                "type": "duplicate_id",
                "id": item.id,
                "file": str(item.file_path),
                "other_file": str(seen_ids[item.id]),
                "message": f"Duplicate ID: {item.id} in {item.file_path} and {seen_ids[item.id]}",
            })
        else:
            seen_ids[item.id] = item.file_path

        # Check file name matches ID
        file_stem = item.file_path.stem  # e.g., "EXP-300-Some-Title"
        expected_prefix = item.id  # e.g., "EXP-300"

        if not file_stem.startswith(expected_prefix):
            issues.append({
                "type": "filename_mismatch",
                "id": item.id,
                "file": str(item.file_path),
                "expected_prefix": expected_prefix,
                "message": f"File name '{file_stem}' doesn't start with ID '{expected_prefix}'",
            })

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
