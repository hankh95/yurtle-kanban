"""
Terminal board rendering using the rich library.

Provides beautiful terminal-based kanban board visualization.
"""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import Board, WorkItem, WorkItemStatus


# Priority colors
PRIORITY_COLORS = {
    "critical": "bold red",
    "high": "red",
    "medium": "yellow",
    "low": "blue",
    "backlog": "dim",
}

# Status colors for column headers
STATUS_COLORS = {
    "backlog": "dim white",
    "ready": "cyan",
    "in_progress": "green",
    "review": "yellow",
    "done": "bright_green",
    "blocked": "red",
    # Nautical theme
    "harbor": "dim white",
    "provisioning": "cyan",
    "underway": "green",
    "approaching": "yellow",
    "arrived": "bright_green",
}

# Type icons
TYPE_ICONS = {
    "feature": "+",
    "bug": "!",
    "epic": "E",
    "issue": "#",
    "task": "T",
    "idea": "?",
    # Nautical theme
    "expedition": "X",
    "voyage": "V",
    "directive": "D",
    "hazard": "!",
    "signal": "S",
}


def render_board(board: Board, console: Console | None = None) -> None:
    """Render a kanban board to the terminal."""
    if console is None:
        console = Console()

    # Title
    console.print()
    console.print(f"[bold]{board.name}[/bold]", justify="center")
    console.print()

    # Get column counts
    column_counts = board.get_column_counts()

    # Create table
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold",
        expand=True,
    )

    # Add columns
    for col in board.columns:
        count = column_counts.get(col.id, 0)
        wip_str = ""
        if col.wip_limit:
            if count > col.wip_limit:
                wip_str = f" [red]({count}/{col.wip_limit})[/red]"
            else:
                wip_str = f" ({count}/{col.wip_limit})"
        else:
            wip_str = f" ({count})"

        color = STATUS_COLORS.get(col.id, "white")
        table.add_column(f"[{color}]{col.name}{wip_str}[/{color}]", width=25)

    # Group items by status
    items_by_status: dict[str, list[WorkItem]] = {}
    for col in board.columns:
        try:
            status = WorkItemStatus.from_string(col.id)
            items_by_status[col.id] = board.get_items_by_status(status)
        except ValueError:
            items_by_status[col.id] = []

    # Find max items in any column
    max_items = max(len(items) for items in items_by_status.values()) if items_by_status else 0

    # Add rows
    for i in range(max(max_items, 1)):
        row = []
        for col in board.columns:
            items = items_by_status.get(col.id, [])
            if i < len(items):
                row.append(render_card(items[i]))
            else:
                row.append("")
        table.add_row(*row)

    console.print(table)

    # Show WIP violations
    violations = board.get_wip_violations()
    if violations:
        console.print()
        console.print("[bold red]WIP Limit Violations:[/bold red]")
        for col, count in violations:
            console.print(f"  - {col.name}: {count}/{col.wip_limit}")

    console.print()


def render_card(item: WorkItem) -> Panel:
    """Render a single work item card."""
    # Build card content
    lines = []

    # ID and type icon
    icon = TYPE_ICONS.get(item.item_type.value, "•")
    lines.append(f"[dim]{icon}[/dim] [bold]{item.id}[/bold]")

    # Title (truncate if too long)
    title = item.title
    if len(title) > 20:
        title = title[:17] + "..."
    lines.append(title)

    # Priority badge
    if item.priority:
        color = PRIORITY_COLORS.get(item.priority, "white")
        lines.append(f"[{color}]●[/{color}] {item.priority}")

    # Assignee
    if item.assignee:
        lines.append(f"[dim]@{item.assignee}[/dim]")

    # Tags
    if item.tags:
        tag_str = " ".join(f"[cyan]#{t}[/cyan]" for t in item.tags[:2])
        lines.append(tag_str)

    content = "\n".join(lines)

    # Determine border color based on priority
    border_color = "white"
    if item.priority == "critical":
        border_color = "red"
    elif item.priority == "high":
        border_color = "yellow"
    elif item.is_blocked:
        border_color = "red"

    return Panel(
        content,
        border_style=border_color,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def render_item_detail(item: WorkItem, console: Console | None = None) -> None:
    """Render detailed view of a single work item."""
    if console is None:
        console = Console()

    icon = TYPE_ICONS.get(item.item_type.value, "•")

    console.print()
    console.print(Panel(
        f"[bold]{icon} {item.id}: {item.title}[/bold]",
        border_style="cyan",
    ))

    # Details table
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Field", style="dim")
    table.add_column("Value")

    table.add_row("Type", item.item_type.value)
    table.add_row("Status", item.status.value)
    table.add_row("Priority", item.priority or "medium")
    table.add_row("Assignee", item.assignee or "unassigned")

    if item.created:
        table.add_row("Created", item.created.isoformat())

    if item.tags:
        table.add_row("Tags", ", ".join(item.tags))

    if item.depends_on:
        table.add_row("Depends On", ", ".join(item.depends_on))

    table.add_row("File", str(item.file_path))

    console.print(table)

    # Description
    if item.description:
        console.print()
        console.print("[bold]Description[/bold]")
        console.print(Panel(item.description, border_style="dim"))

    # Comments
    if item.comments:
        console.print()
        console.print("[bold]Comments[/bold]")
        for comment in item.comments:
            timestamp = comment.created_at.strftime("%Y-%m-%d %H:%M")
            console.print(f"  [dim]{timestamp}[/dim] [bold]{comment.author}[/bold]")
            console.print(f"    {comment.content}")

    console.print()


def render_list(items: list[WorkItem], console: Console | None = None) -> None:
    """Render a list of work items."""
    if console is None:
        console = Console()

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold",
    )

    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Priority")
    table.add_column("Assignee", style="dim")

    for item in items:
        icon = TYPE_ICONS.get(item.item_type.value, "•")
        priority_color = PRIORITY_COLORS.get(item.priority or "medium", "white")
        status_color = STATUS_COLORS.get(item.status.value, "white")

        title = item.title
        if len(title) > 40:
            title = title[:37] + "..."

        # Handle assignee as string or list
        assignee = item.assignee
        if isinstance(assignee, list):
            assignee = ", ".join(str(a) for a in assignee if a)
        assignee = assignee or "-"

        table.add_row(
            f"{icon} {item.id}",
            title,
            f"[{status_color}]{item.status.value}[/{status_color}]",
            f"[{priority_color}]{item.priority or 'medium'}[/{priority_color}]",
            assignee,
        )

    console.print(table)


def render_stats(board: Board, console: Console | None = None) -> None:
    """Render board statistics."""
    if console is None:
        console = Console()

    counts = board.get_column_counts()
    total = sum(counts.values())

    console.print()
    console.print("[bold]Board Statistics[/bold]")
    console.print()

    # Status breakdown
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Status")
    table.add_column("Count", justify="right")
    table.add_column("Bar")

    max_count = max(counts.values()) if counts else 1

    for col in board.columns:
        count = counts.get(col.id, 0)
        bar_width = int((count / max_count) * 20) if max_count > 0 else 0
        bar = "█" * bar_width
        color = STATUS_COLORS.get(col.id, "white")

        table.add_row(
            f"[{color}]{col.name}[/{color}]",
            str(count),
            f"[{color}]{bar}[/{color}]",
        )

    table.add_row("", "", "")
    table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]", "")

    console.print(table)
    console.print()
