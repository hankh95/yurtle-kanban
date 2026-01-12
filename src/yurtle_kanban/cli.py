"""
yurtle-kanban CLI

Usage:
    yurtle-kanban init [--theme THEME] [--path PATH]
    yurtle-kanban list [--status STATUS] [--type TYPE]
    yurtle-kanban create TYPE TITLE [--path PATH]
    yurtle-kanban move ID STATUS
    yurtle-kanban board
    yurtle-kanban query SPARQL
"""

import click


@click.group()
@click.version_option()
def main():
    """File-based kanban using Yurtle. Git is your database."""
    pass


@main.command()
@click.option("--theme", default="software", help="Theme: software, nautical, or custom")
@click.option("--path", default="work/", help="Path for work items")
def init(theme: str, path: str):
    """Initialize yurtle-kanban in the current directory."""
    click.echo(f"Initializing yurtle-kanban with theme '{theme}' at '{path}'")
    # TODO: Implement initialization
    click.echo("Created .kanban/config.yaml")
    click.echo(f"Created {path}")


@main.command("list")
@click.option("--status", help="Filter by status")
@click.option("--type", "item_type", help="Filter by type")
def list_items(status: str | None, item_type: str | None):
    """List work items."""
    click.echo("Listing work items...")
    # TODO: Implement listing


@main.command()
@click.argument("item_type")
@click.argument("title")
@click.option("--path", help="Path for the new work item")
def create(item_type: str, title: str, path: str | None):
    """Create a new work item."""
    click.echo(f"Creating {item_type}: {title}")
    # TODO: Implement creation


@main.command()
@click.argument("item_id")
@click.argument("status")
def move(item_id: str, status: str):
    """Move a work item to a new status."""
    click.echo(f"Moving {item_id} to {status}")
    # TODO: Implement move


@main.command()
def board():
    """Show the kanban board view."""
    click.echo("Kanban Board")
    click.echo("=" * 60)
    # TODO: Implement board view


@main.command()
@click.argument("sparql")
def query(sparql: str):
    """Run a SPARQL query on work items."""
    click.echo(f"Running query: {sparql}")
    # TODO: Implement SPARQL query


if __name__ == "__main__":
    main()
