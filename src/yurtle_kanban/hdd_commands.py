"""
HDD (Hypothesis-Driven Development) CLI commands for yurtle-kanban.

Provides Click subgroups for creating HDD research items:
- idea: Research or feature ideas
- literature: Literature reviews
- paper: Research papers
- hypothesis: Testable hypotheses
- experiment: Experiment protocols
- measure: Metric definitions
"""

from __future__ import annotations

import click
from rich.console import Console

from .models import WorkItemType
from .template_engine import TemplateEngine

console = Console()


def _get_service():
    """Get the kanban service for the current directory."""
    from .cli import get_service

    return get_service()


def _get_engine() -> TemplateEngine:
    """Get the template engine."""
    # Import from cli.py to avoid duplication (lazy import to avoid circular import)
    from .cli import _get_templates_dir

    return TemplateEngine(_get_templates_dir())


def _update_parent(
    service,
    parent_id: str,
    child_type: str,
    child_id: str,
    push: bool,
) -> None:
    """Best-effort update of parent's turtle block with inverse reference.

    Silent on failure — the child creation is the primary operation.
    """
    try:
        updated = service.update_parent_turtle_block(
            parent_id, child_type, child_id, push=push,
        )
        if updated:
            console.print(f"  [dim]Updated {parent_id} with inverse reference[/dim]")
    except Exception as e:
        console.print(f"  [yellow]Warning: could not update {parent_id}: {e}[/yellow]")


# ---------------------------------------------------------------------------
# hdd (top-level group for cross-type operations)
# ---------------------------------------------------------------------------


@click.group()
def hdd():
    """Hypothesis-Driven Development — cross-type operations."""
    pass


@hdd.command("backfill")
@click.option("--dry-run", is_flag=True, help="Preview changes without modifying files")
def hdd_backfill(dry_run):
    """Add missing turtle knowledge blocks to HDD files.

    Scans all HDD items, builds expected RDF triples from frontmatter,
    diffs against the file's existing graph, and inserts a fenced turtle
    block with only the missing triples.
    """
    from rich.table import Table

    service = _get_service()
    results = service.backfill_turtle_blocks(dry_run=dry_run)

    backfilled = [r for r in results if r["action"] in ("backfill", "would_backfill")]
    up_to_date = [r for r in results if r["action"] == "up_to_date"]

    if not backfilled and not up_to_date:
        console.print("[dim]No HDD items found.[/dim]")
        return

    if backfilled:
        table = Table(title="Backfill Results" + (" (dry run)" if dry_run else ""))
        table.add_column("ID", width=16)
        table.add_column("Type", width=12)
        table.add_column("Triples", width=8, justify="right")
        table.add_column("Action")
        for r in backfilled:
            action_text = "would add" if dry_run else "added"
            table.add_row(r["id"], r["type"], str(r["triples_added"]), action_text)
        console.print(table)

    summary_parts = []
    if backfilled:
        verb = "Would backfill" if dry_run else "Backfilled"
        summary_parts.append(f"[bold]{verb}[/bold] {len(backfilled)} files")
    if up_to_date:
        summary_parts.append(f"{len(up_to_date)} already up to date")
    console.print("  ".join(summary_parts))


# ---------------------------------------------------------------------------
# idea
# ---------------------------------------------------------------------------


@click.group()
def idea():
    """Manage research/feature ideas (HDD)."""
    pass


@idea.command("create")
@click.argument("title")
@click.option(
    "--type",
    "idea_type",
    default="research",
    type=click.Choice(["research", "feature"]),
    help="Idea type: research (IDEA-R) or feature (IDEA-F)",
)
@click.option("--priority", "-p", default="medium", help="Priority: critical, high, medium, low")
@click.option("--push", is_flag=True, help="Atomic: create, commit, and push")
def idea_create(title: str, idea_type: str, priority: str, push: bool):
    """Create a new research or feature idea.

    Examples:
        yurtle-kanban idea create "Explore transfer learning"
        yurtle-kanban idea create "Dashboard widget" --type feature
        yurtle-kanban idea create "New metric" --push
    """
    service = _get_service()
    engine = _get_engine()

    # Determine prefix based on idea type
    prefix = "IDEA-R" if idea_type == "research" else "IDEA-F"
    next_num = service._get_next_id_number(prefix)
    item_id = f"{prefix}-{next_num:03d}"

    # Render template
    variables = {"id": item_id, "title": title}
    try:
        content = engine.render("hdd", "idea", variables)
    except FileNotFoundError:
        raise click.ClickException("HDD idea template not found")

    if push:
        result = service.create_item_and_push(
            item_type=WorkItemType.IDEA,
            title=title,
            priority=priority,
            content=content,
            item_id=item_id,
        )
        if result["success"]:
            pushed = " and pushed" if result.get("pushed") else ""
            console.print(f"[green]Created{pushed} {result['id']}: {title}[/green]")
            console.print(f"  File: {result['item'].file_path}")
        else:
            raise click.ClickException(f"Failed: {result['message']}")
    else:
        item = service.create_item(
            item_type=WorkItemType.IDEA,
            title=title,
            priority=priority,
            content=content,
            item_id=item_id,
        )
        console.print(f"[green]Created {item.id}: {title}[/green]")
        console.print(f"  File: {item.file_path}")


# ---------------------------------------------------------------------------
# literature
# ---------------------------------------------------------------------------


@click.group()
def literature():
    """Manage literature reviews (HDD)."""
    pass


@literature.command("create")
@click.argument("title")
@click.option("--idea", "source_idea", default=None, help="Source idea ID (e.g., IDEA-R-001)")
@click.option("--priority", "-p", default="medium", help="Priority")
@click.option("--push", is_flag=True, help="Atomic: create, commit, and push")
def literature_create(title: str, source_idea: str | None, priority: str, push: bool):
    """Create a new literature review.

    Examples:
        yurtle-kanban literature create "Transfer learning survey"
        yurtle-kanban literature create "Metric frameworks" --idea IDEA-R-001
    """
    service = _get_service()
    engine = _get_engine()

    prefix = "LIT"
    next_num = service._get_next_id_number(prefix)
    item_id = f"{prefix}-{next_num:03d}"

    variables: dict[str, str] = {"id": item_id, "title": title}
    if source_idea:
        variables["source_idea"] = source_idea

    try:
        content = engine.render("hdd", "literature", variables)
    except FileNotFoundError:
        raise click.ClickException("HDD literature template not found")

    if push:
        result = service.create_item_and_push(
            item_type=WorkItemType.LITERATURE,
            title=title,
            priority=priority,
            content=content,
            item_id=item_id,
        )
        if result["success"]:
            pushed = " and pushed" if result.get("pushed") else ""
            console.print(f"[green]Created{pushed} {result['id']}: {title}[/green]")
            console.print(f"  File: {result['item'].file_path}")
            if source_idea:
                _update_parent(service, source_idea, "literature", result["id"], push=True)
        else:
            raise click.ClickException(f"Failed: {result['message']}")
    else:
        item = service.create_item(
            item_type=WorkItemType.LITERATURE,
            title=title,
            priority=priority,
            content=content,
            item_id=item_id,
        )
        console.print(f"[green]Created {item.id}: {title}[/green]")
        console.print(f"  File: {item.file_path}")
        if source_idea:
            _update_parent(service, source_idea, "literature", item.id, push=False)


# ---------------------------------------------------------------------------
# paper
# ---------------------------------------------------------------------------


@click.group()
def paper():
    """Manage research papers (HDD)."""
    pass


@paper.command("create")
@click.argument("number", type=int)
@click.argument("title")
@click.option("--authors", default=None, help="Comma-separated author list")
@click.option("--priority", "-p", default="medium", help="Priority")
@click.option("--push", is_flag=True, help="Atomic: create, commit, and push")
def paper_create(number: int, title: str, authors: str | None, priority: str, push: bool):
    """Create a new research paper.

    NUMBER is the paper number (e.g., 130 for PAPER-130).

    Examples:
        yurtle-kanban paper create 130 "NuSy Brain Architecture"
        yurtle-kanban paper create 131 "Training Methodology" --authors "Alice, Bob"
    """
    service = _get_service()
    engine = _get_engine()

    item_id = f"PAPER-{number}"

    # Check for duplicate
    existing = service.get_item(item_id)
    if existing:
        raise click.ClickException(f"{item_id} already exists: {existing.title}")

    variables: dict[str, str] = {
        "id": item_id,
        "title": title,
        "paper_num": str(number),
    }
    if authors:
        variables["authors"] = authors

    try:
        content = engine.render("hdd", "paper", variables)
    except FileNotFoundError:
        raise click.ClickException("HDD paper template not found")

    if push:
        result = service.create_item_and_push(
            item_type=WorkItemType.PAPER,
            title=title,
            priority=priority,
            content=content,
            item_id=item_id,
        )
        if result["success"]:
            pushed = " and pushed" if result.get("pushed") else ""
            console.print(f"[green]Created{pushed} {result['id']}: {title}[/green]")
            console.print(f"  File: {result['item'].file_path}")
        else:
            raise click.ClickException(f"Failed: {result['message']}")
    else:
        item = service.create_item(
            item_type=WorkItemType.PAPER,
            title=title,
            priority=priority,
            content=content,
            item_id=item_id,
        )
        console.print(f"[green]Created {item.id}: {title}[/green]")
        console.print(f"  File: {item.file_path}")


# ---------------------------------------------------------------------------
# hypothesis
# ---------------------------------------------------------------------------


@click.group()
def hypothesis():
    """Manage hypotheses (HDD)."""
    pass


@hypothesis.command("create")
@click.argument("statement")
@click.option("--paper", "paper_num", required=True, type=int, help="Paper number (e.g., 130)")
@click.option(
    "--id", "hyp_id", default=None,
    help="Explicit ID (e.g., H130.1). Auto-allocates if omitted.",
)
@click.option("--target", default=None, help="Target metric value (e.g., '>=50%')")
@click.option("--source-idea", default=None, help="Source idea ID (e.g., IDEA-R-001)")
@click.option(
    "--measures", default=None,
    help="Comma-separated measure IDs (e.g., 'M-007,M-025')",
)
@click.option(
    "--literature", default=None,
    help="Comma-separated literature IDs (e.g., 'LIT-001,LIT-003')",
)
@click.option("--priority", "-p", default="medium", help="Priority")
@click.option("--push", is_flag=True, help="Atomic: create, commit, and push")
def hypothesis_create(
    statement: str,
    paper_num: int,
    hyp_id: str | None,
    target: str | None,
    source_idea: str | None,
    measures: str | None,
    literature: str | None,
    priority: str,
    push: bool,
):
    """Create a new hypothesis.

    STATEMENT is the hypothesis text.

    Examples:
        yurtle-kanban hypothesis create "V12 improves accuracy by 15%" --paper 130
        yurtle-kanban hypothesis create "Faster convergence" --paper 130 --id H130.1
        yurtle-kanban hypothesis create "Better recall" --paper 130 --target ">=85%"
    """
    service = _get_service()
    engine = _get_engine()

    # Auto-allocate hypothesis number if no explicit ID
    if hyp_id is None:
        next_n = service.get_next_hypothesis_number(str(paper_num))
        hyp_id = f"H{paper_num}.{next_n}"
        hyp_n = str(next_n)
    else:
        # Extract n from user-provided ID (e.g., H130.1 → "1")
        if "." in hyp_id:
            hyp_n = hyp_id.split(".")[-1]
        else:
            hyp_n = "1"

    # Check for duplicate
    existing = service.get_item(hyp_id)
    if existing:
        raise click.ClickException(f"{hyp_id} already exists: {existing.title}")

    variables: dict[str, str | list[str]] = {
        "id": hyp_id,
        "title": statement,
        "paper": str(paper_num),
        "n": hyp_n,
    }
    if target:
        variables["target"] = target
    if source_idea:
        variables["source_idea"] = source_idea
    if measures:
        variables["measures"] = [m.strip() for m in measures.split(",")]
    if literature:
        variables["literature"] = [lit.strip() for lit in literature.split(",")]

    try:
        content = engine.render("hdd", "hypothesis", variables)
    except FileNotFoundError:
        raise click.ClickException("HDD hypothesis template not found")

    if push:
        result = service.create_item_and_push(
            item_type=WorkItemType.HYPOTHESIS,
            title=statement,
            priority=priority,
            content=content,
            item_id=hyp_id,
        )
        if result["success"]:
            pushed = " and pushed" if result.get("pushed") else ""
            console.print(f"[green]Created{pushed} {result['id']}: {statement}[/green]")
            console.print(f"  File: {result['item'].file_path}")
            _update_parent(service, f"PAPER-{paper_num}", "hypothesis", result["id"], push=True)
        else:
            raise click.ClickException(f"Failed: {result['message']}")
    else:
        item = service.create_item(
            item_type=WorkItemType.HYPOTHESIS,
            title=statement,
            priority=priority,
            content=content,
            item_id=hyp_id,
        )
        console.print(f"[green]Created {item.id}: {statement}[/green]")
        console.print(f"  File: {item.file_path}")
        _update_parent(service, f"PAPER-{paper_num}", "hypothesis", item.id, push=False)


# ---------------------------------------------------------------------------
# experiment
# ---------------------------------------------------------------------------


@click.group()
def experiment():
    """Manage experiments (HDD)."""
    pass


@experiment.command("create")
@click.argument("expr_id")
@click.option("--hypothesis", "hyp_id", required=True, help="Hypothesis ID (e.g., H130.1)")
@click.option("--title", required=True, help="Experiment title")
@click.option("--measures", default=None, help="Comma-separated measure IDs (e.g., 'M-007,M-025')")
@click.option("--priority", "-p", default="medium", help="Priority")
@click.option("--push", is_flag=True, help="Atomic: create, commit, and push")
def experiment_create(
    expr_id: str, hyp_id: str, title: str,
    measures: str | None, priority: str, push: bool,
):
    """Create a new experiment.

    EXPR_ID is the experiment ID (e.g., EXPR-130).

    Examples:
        yurtle-kanban experiment create EXPR-130 --hypothesis H130.1 --title "V12 accuracy test"
    """
    service = _get_service()
    engine = _get_engine()

    # Normalize ID
    if not expr_id.startswith("EXPR-"):
        expr_id = f"EXPR-{expr_id}"

    # Check for duplicate
    existing = service.get_item(expr_id)
    if existing:
        raise click.ClickException(f"{expr_id} already exists: {existing.title}")

    # Extract paper number from hypothesis or EXPR ID
    paper_num = expr_id.replace("EXPR-", "")
    hyp_n = hyp_id.split(".")[-1] if "." in hyp_id else "1"

    variables: dict[str, str | list[str]] = {
        "id": expr_id,
        "title": title,
        "paper": paper_num,
        "n": hyp_n,
        "hypothesis_id": hyp_id,
    }
    if measures:
        variables["measures"] = [m.strip() for m in measures.split(",")]

    try:
        content = engine.render("hdd", "experiment", variables)
    except FileNotFoundError:
        raise click.ClickException("HDD experiment template not found")

    if push:
        result = service.create_item_and_push(
            item_type=WorkItemType.EXPERIMENT,
            title=title,
            priority=priority,
            content=content,
            item_id=expr_id,
        )
        if result["success"]:
            pushed = " and pushed" if result.get("pushed") else ""
            console.print(f"[green]Created{pushed} {result['id']}: {title}[/green]")
            console.print(f"  File: {result['item'].file_path}")
            _update_parent(service, hyp_id, "experiment", result["id"], push=True)
        else:
            raise click.ClickException(f"Failed: {result['message']}")
    else:
        item = service.create_item(
            item_type=WorkItemType.EXPERIMENT,
            title=title,
            priority=priority,
            content=content,
            item_id=expr_id,
        )
        console.print(f"[green]Created {item.id}: {title}[/green]")
        console.print(f"  File: {item.file_path}")
        _update_parent(service, hyp_id, "experiment", item.id, push=False)


# ---------------------------------------------------------------------------
# measure
# ---------------------------------------------------------------------------


@click.group()
def measure():
    """Manage metric definitions (HDD)."""
    pass


@measure.command("create")
@click.argument("title")
@click.option("--unit", required=True, help="Unit of measurement (e.g., 'percent', 'count', 'ms')")
@click.option(
    "--category", required=True,
    help="Category (e.g., 'accuracy', 'performance', 'coverage')",
)
@click.option(
    "--id", "measure_id", default=None,
    help="Explicit ID (e.g., M-042). Auto-allocates if omitted.",
)
@click.option("--priority", "-p", default="medium", help="Priority")
@click.option("--push", is_flag=True, help="Atomic: create, commit, and push")
def measure_create(
    title: str,
    unit: str,
    category: str,
    measure_id: str | None,
    priority: str,
    push: bool,
):
    """Create a new measure definition.

    Examples:
        yurtle-kanban measure create "Reasoning Accuracy" --unit percent --category accuracy
        yurtle-kanban measure create "Response Latency" --unit ms --category performance --id M-042
    """
    service = _get_service()
    engine = _get_engine()

    # Auto-allocate or use provided
    if measure_id is None:
        prefix = "M"
        next_num = service._get_next_id_number(prefix)
        measure_id = f"M-{next_num:03d}"

    # Check for duplicate
    existing = service.get_item(measure_id)
    if existing:
        raise click.ClickException(f"{measure_id} already exists: {existing.title}")

    variables: dict[str, str] = {
        "id": measure_id,
        "title": title,
        "unit": unit,
        "category": category,
    }

    try:
        content = engine.render("hdd", "measure", variables)
    except FileNotFoundError:
        raise click.ClickException("HDD measure template not found")

    if push:
        result = service.create_item_and_push(
            item_type=WorkItemType.MEASURE,
            title=title,
            priority=priority,
            content=content,
            item_id=measure_id,
        )
        if result["success"]:
            pushed = " and pushed" if result.get("pushed") else ""
            console.print(f"[green]Created{pushed} {result['id']}: {title}[/green]")
            console.print(f"  File: {result['item'].file_path}")
        else:
            raise click.ClickException(f"Failed: {result['message']}")
    else:
        item = service.create_item(
            item_type=WorkItemType.MEASURE,
            title=title,
            priority=priority,
            content=content,
            item_id=measure_id,
        )
        console.print(f"[green]Created {item.id}: {title}[/green]")
        console.print(f"  File: {item.file_path}")
