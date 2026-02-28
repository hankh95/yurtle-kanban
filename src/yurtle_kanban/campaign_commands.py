"""
Initiative CLI commands for yurtle-kanban.

Provides theme-aware command groups for managing multi-item initiatives:
- ``voyage`` group for nautical theme (creates VOY- items)
- ``epic`` group for software theme (creates EPIC- items)

Both groups share identical subcommands (create, show, add) and auto-detect
the appropriate item type from the current theme configuration.
"""

from __future__ import annotations

import re
import sys
from datetime import date

import click
import yaml
from rich.console import Console
from rich.table import Table

from .models import WorkItemStatus, WorkItemType
from .template_engine import TemplateEngine

console = Console()

# Map theme names to their initiative item type
_INITIATIVE_TYPES: dict[str, WorkItemType] = {
    "nautical": WorkItemType.VOYAGE,
    "software": WorkItemType.EPIC,
}

_INITIATIVE_TEMPLATES: dict[str, tuple[str, str]] = {
    # theme_name -> (template_theme, template_item_type)
    "nautical": ("nautical", "voyage"),
    "software": ("software", "epic"),
}

_TYPE_LABELS: dict[WorkItemType, str] = {
    WorkItemType.VOYAGE: "Voyage",
    WorkItemType.EPIC: "Epic",
}


def _get_service():
    """Get the kanban service for the current directory."""
    from .cli import get_service

    return get_service()


def _get_engine() -> TemplateEngine:
    """Get the template engine."""
    from .cli import _get_templates_dir

    return TemplateEngine(_get_templates_dir())


def _detect_initiative_type(service) -> tuple[WorkItemType, str]:
    """Detect the initiative item type from the current theme.

    Returns:
        (WorkItemType, theme_name) tuple.

    Raises:
        click.ClickException if no initiative type for the current theme.
    """
    config = service.config

    # Check multi-board: look for a board with an initiative-supporting theme
    if config.is_multi_board:
        for board in config.boards:
            preset = getattr(board, "preset", None)
            if preset in _INITIATIVE_TYPES:
                return _INITIATIVE_TYPES[preset], preset
        # Fall back to first board's preset
        first_preset = getattr(config.boards[0], "preset", None) if config.boards else None
        if first_preset in _INITIATIVE_TYPES:
            return _INITIATIVE_TYPES[first_preset], first_preset

    # Single-board: check theme
    theme_name = getattr(config, "theme", None)
    if theme_name in _INITIATIVE_TYPES:
        return _INITIATIVE_TYPES[theme_name], theme_name

    # Try loading theme config to get the name
    theme = config.get_theme()
    if theme:
        name = theme.get("theme", {}).get("name", "")
        if name in _INITIATIVE_TYPES:
            return _INITIATIVE_TYPES[name], name

    raise click.ClickException(
        "No initiative type found for the current theme. "
        "Voyages are supported in 'nautical' theme, epics in 'software' theme."
    )


def _update_item_related(service, item_id: str, initiative_id: str) -> bool:
    """Add initiative_id to an item's related list in its frontmatter.

    Returns True if the file was updated, False if initiative_id was already present.
    """
    if not service._items:
        service.scan()
    item = service._items.get(item_id)
    if item is None:
        console.print(f"[yellow]Warning: Item {item_id} not found[/yellow]")
        return False

    content = item.file_path.read_text()
    frontmatter_match = re.match(r"^---\n(.*?\n)---", content, re.DOTALL)
    if not frontmatter_match:
        console.print(f"[yellow]Warning: No frontmatter in {item_id}[/yellow]")
        return False

    fm_text = frontmatter_match.group(1)
    fm = yaml.safe_load(fm_text) or {}

    related = fm.get("related", [])
    if isinstance(related, str):
        related = [r.strip() for r in related.split(",")]

    if initiative_id in related:
        return False  # Already linked

    related.append(initiative_id)

    # Update the frontmatter in the file
    if re.search(r"^related:", fm_text, re.MULTILINE):
        # Replace existing related line
        new_content = re.sub(
            r"^(related:\s*).*$",
            f"\\g<1>[{', '.join(related)}]",
            content,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        # Insert related before the closing ---
        new_content = content.replace(
            "\n---",
            f"\nrelated: [{', '.join(related)}]\n---",
            1,
        )

    item.file_path.write_text(new_content)
    item.related = related
    return True


# ---------------------------------------------------------------------------
# Shared implementation functions
# ---------------------------------------------------------------------------


def _do_create(title: str, priority: str, items: str | None, push: bool):
    """Create a new voyage or epic based on the current theme."""
    service = _get_service()
    item_type, theme_name = _detect_initiative_type(service)

    engine = _get_engine()
    template_theme, template_type = _INITIATIVE_TEMPLATES[theme_name]

    # Allocate ID
    prefix = service._get_type_prefix(item_type)
    next_num = service._get_next_id_number(prefix)
    item_id = f"{prefix}-{next_num:03d}"

    # Render template
    variables = {"id": item_id, "title": title, "date": date.today().isoformat()}
    try:
        content = engine.render(template_theme, template_type, variables)
    except FileNotFoundError:
        content = None

    if content:
        content = content.replace("{{NUMBER}}", str(next_num))
        content = content.replace("{{DATE}}", date.today().isoformat())
        content = content.replace("{{TITLE}}", title)

    type_label = _TYPE_LABELS.get(item_type, "Initiative")

    if push:
        item = service.create_item_and_push(
            item_type=item_type,
            title=title,
            priority=priority,
            content=content,
            item_id=item_id,
        )
    else:
        item = service.create_item(
            item_type=item_type,
            title=title,
            priority=priority,
            content=content,
            item_id=item_id,
        )

    console.print(f"Created {type_label} [bold green]{item.id}[/bold green]: {title}")
    console.print(f"  File: {item.file_path}")

    # Link items if provided
    if items:
        item_ids = [i.strip() for i in items.split(",") if i.strip()]
        for linked_id in item_ids:
            if _update_item_related(service, linked_id, item.id):
                console.print(f"  Linked {linked_id} → {item.id}")
            else:
                console.print(f"  {linked_id} already linked or not found")


def _do_show(initiative_id: str):
    """Show an initiative with its linked items and progress."""
    service = _get_service()
    if not service._items:
        service.scan()

    initiative = service._items.get(initiative_id)
    if initiative is None:
        console.print(f"[red]{initiative_id} not found[/red]")
        sys.exit(1)

    # Find all items with this initiative in their related list
    linked_items = [
        item
        for item in service._items.values()
        if initiative_id in item.related and item.id != initiative_id
    ]
    linked_items.sort(key=lambda i: (-i.priority_score, i.id))

    # Also check if the initiative itself lists items in its related field
    # (bidirectional linking)
    linked_ids = {i.id for i in linked_items}
    for rel_id in initiative.related:
        if rel_id not in linked_ids:
            rel_item = service._items.get(rel_id)
            if rel_item:
                linked_items.append(rel_item)

    status_colors = {
        WorkItemStatus.DONE: "green",
        WorkItemStatus.IN_PROGRESS: "cyan",
        WorkItemStatus.REVIEW: "yellow",
        WorkItemStatus.BLOCKED: "red",
        WorkItemStatus.BACKLOG: "dim",
        WorkItemStatus.READY: "blue",
    }

    type_label = _TYPE_LABELS.get(initiative.item_type, "Initiative")
    color = status_colors.get(initiative.status, "white")
    console.print(
        f"\n[bold]{type_label} {initiative.id}[/bold]: {initiative.title} "
        f"[{color}]({initiative.status.value})[/{color}]"
    )

    if not linked_items:
        cmd = "voyage" if initiative.item_type == WorkItemType.VOYAGE else "epic"
        console.print("  No linked items found.")
        console.print(
            f"  [dim]Link items with: yurtle-kanban {cmd} add {initiative_id} ITEM-ID[/dim]"
        )
        return

    # Progress summary
    done_count = sum(1 for i in linked_items if i.status == WorkItemStatus.DONE)
    total = len(linked_items)
    console.print(f"  Progress: {done_count}/{total} items complete\n")

    # Items table
    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", width=14)
    table.add_column("Title", min_width=30)
    table.add_column("Status", width=12)
    table.add_column("Assignee", width=10)
    table.add_column("Priority", width=8)

    for item in linked_items:
        color = status_colors.get(item.status, "white")
        status_str = f"[{color}]{item.status.value}[/{color}]"
        table.add_row(
            item.id,
            item.title[:40],
            status_str,
            item.assignee or "-",
            item.priority or "medium",
        )

    console.print(table)


def _do_add(initiative_id: str, item_id: str):
    """Link an item to a voyage/epic by adding it to the item's related field."""
    service = _get_service()
    if not service._items:
        service.scan()

    # Verify initiative exists
    if initiative_id not in service._items:
        console.print(f"[red]{initiative_id} not found[/red]")
        sys.exit(1)

    if _update_item_related(service, item_id, initiative_id):
        console.print(f"Linked [bold]{item_id}[/bold] → [bold]{initiative_id}[/bold]")
    else:
        item = service._items.get(item_id)
        if item is None:
            console.print(f"[red]Item {item_id} not found[/red]")
            sys.exit(1)
        else:
            console.print(f"{item_id} is already linked to {initiative_id}")


# ---------------------------------------------------------------------------
# ``voyage`` command group (nautical theme)
# ---------------------------------------------------------------------------


@click.group()
def voyage():
    """Manage voyages — multi-item initiatives grouping related expeditions."""
    pass


@voyage.command("create")
@click.argument("title")
@click.option("--priority", "-p", default="high", help="Priority level")
@click.option("--items", help="Comma-separated item IDs to link")
@click.option("--push", is_flag=True, help="Commit and push (atomic)")
def voyage_create(title: str, priority: str, items: str | None, push: bool):
    """Create a new voyage (or epic, based on theme)."""
    _do_create(title, priority, items, push)


@voyage.command("show")
@click.argument("initiative_id")
def voyage_show(initiative_id: str):
    """Show a voyage/epic with linked items and progress."""
    _do_show(initiative_id)


@voyage.command("add")
@click.argument("initiative_id")
@click.argument("item_id")
def voyage_add(initiative_id: str, item_id: str):
    """Link an item to a voyage/epic."""
    _do_add(initiative_id, item_id)


# ---------------------------------------------------------------------------
# ``epic`` command group (software theme)
# ---------------------------------------------------------------------------


@click.group()
def epic():
    """Manage epics — multi-item initiatives grouping related features."""
    pass


@epic.command("create")
@click.argument("title")
@click.option("--priority", "-p", default="high", help="Priority level")
@click.option("--items", help="Comma-separated item IDs to link")
@click.option("--push", is_flag=True, help="Commit and push (atomic)")
def epic_create(title: str, priority: str, items: str | None, push: bool):
    """Create a new epic (or voyage, based on theme)."""
    _do_create(title, priority, items, push)


@epic.command("show")
@click.argument("initiative_id")
def epic_show(initiative_id: str):
    """Show an epic/voyage with linked items and progress."""
    _do_show(initiative_id)


@epic.command("add")
@click.argument("initiative_id")
@click.argument("item_id")
def epic_add(initiative_id: str, item_id: str):
    """Link an item to an epic/voyage."""
    _do_add(initiative_id, item_id)
