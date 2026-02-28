"""
Research interlink display for campaign/voyage show.

Parses fenced ```turtle blocks from HDD item files and queries the RDF
graph for research relationships: hypothesis→paper, experiment→hypothesis,
measure metadata.

Only renders when linked items include HDD types with Turtle knowledge blocks.

Note: yurtle-rdflib v0.1.0 only parses YAML frontmatter into WorkItem.graph.
Fenced Turtle blocks require direct parsing with rdflib until yurtle-rdflib
supports them. This module does that parsing on demand.
"""

from __future__ import annotations

import logging
import re

from rdflib import Graph, Namespace, RDFS
from rich.console import Console
from rich.table import Table

from .models import WorkItem, WorkItemStatus, WorkItemType
from .turtle_builder import PREFIXES

logger = logging.getLogger(__name__)

# Derive namespaces from turtle_builder.PREFIXES (single source of truth)
HYP = Namespace(PREFIXES["hyp"])
PAPER = Namespace(PREFIXES["paper"])
EXPR = Namespace(PREFIXES["expr"])
MEASURE = Namespace(PREFIXES["measure"])
LIT = Namespace(PREFIXES["lit"])
IDEA = Namespace(PREFIXES["idea"])

# HDD item types that carry research metadata
HDD_TYPES = frozenset({
    WorkItemType.PAPER,
    WorkItemType.HYPOTHESIS,
    WorkItemType.EXPERIMENT,
    WorkItemType.MEASURE,
    WorkItemType.LITERATURE,
    WorkItemType.IDEA,
})

_STATUS_COLORS = {
    WorkItemStatus.DONE: "green",
    WorkItemStatus.IN_PROGRESS: "cyan",
    WorkItemStatus.REVIEW: "yellow",
    WorkItemStatus.BLOCKED: "red",
    WorkItemStatus.BACKLOG: "dim",
    WorkItemStatus.READY: "blue",
}

# Regex to extract fenced turtle/yurtle blocks from markdown
_TURTLE_BLOCK_RE = re.compile(r"```(?:turtle|yurtle)\s*\n(.*?)```", re.DOTALL)


def _parse_turtle_blocks(item: WorkItem) -> Graph:
    """Parse fenced ```turtle blocks from an item's file into an RDF graph.

    Returns an rdflib Graph with triples from all fenced Turtle blocks.
    Returns an empty graph if no blocks found or parsing fails.
    """
    g = Graph()
    try:
        content = item.file_path.read_text()
    except OSError:
        return g

    for match in _TURTLE_BLOCK_RE.finditer(content):
        block = match.group(1)
        try:
            g.parse(data=block, format="turtle")
        except Exception as e:
            logger.debug(f"Failed to parse turtle block in {item.file_path}: {e}")
    return g


def _obj_id(uri_str: str) -> str:
    """Extract display ID from an RDF URI.

    Turtle blocks use ``<#H130.1>`` (fragment) or ``paper:PAPER-130``
    (prefixed name resolved to full URI). Extract the meaningful part.
    """
    s = str(uri_str)
    if "#" in s:
        return s.rsplit("#", 1)[-1]
    # For full URIs like https://nusy.dev/paper/PAPER-130
    for prefix_uri in PREFIXES.values():
        if s.startswith(prefix_uri):
            return s[len(prefix_uri):]
    return s.rsplit("/", 1)[-1] if "/" in s else s


def _first_value(graph: Graph, predicate) -> str | None:
    """Get the first object value for a predicate from a graph."""
    for _, _, obj in graph.triples((None, predicate, None)):
        return str(obj)
    return None


def has_research_items(items: list[WorkItem]) -> bool:
    """Check if any items are HDD types."""
    return any(item.item_type in HDD_TYPES for item in items)


def render_research_interlinks(items: list[WorkItem], console: Console) -> None:
    """Render research interlinks section for HDD items.

    Parses fenced Turtle blocks from each HDD item's file and displays
    tables grouped by type. No output if no HDD items exist.
    """
    # Separate HDD items by type, parse their Turtle blocks
    hypotheses: list[tuple[WorkItem, Graph]] = []
    experiments: list[tuple[WorkItem, Graph]] = []
    papers: list[tuple[WorkItem, Graph]] = []
    measures: list[tuple[WorkItem, Graph]] = []
    literature: list[tuple[WorkItem, Graph]] = []

    for item in items:
        if item.item_type not in HDD_TYPES:
            continue
        g = _parse_turtle_blocks(item)
        if len(g) == 0:
            continue
        match item.item_type:
            case WorkItemType.HYPOTHESIS:
                hypotheses.append((item, g))
            case WorkItemType.EXPERIMENT:
                experiments.append((item, g))
            case WorkItemType.PAPER:
                papers.append((item, g))
            case WorkItemType.MEASURE:
                measures.append((item, g))
            case WorkItemType.LITERATURE:
                literature.append((item, g))

    if not any([hypotheses, experiments, papers, measures, literature]):
        return

    console.print("\n  [bold]Research Interlinks[/bold]")
    console.print("  " + "\u2501" * 40)

    # Papers
    if papers:
        console.print("\n  [bold dim]Papers:[/bold dim]")
        for p, g in papers:
            color = _STATUS_COLORS.get(p.status, "white")
            label = _first_value(g, RDFS.label) or p.title
            console.print(
                f"    [bold]{p.id}[/bold]  {label[:50]}  "
                f"[{color}]({p.status.value})[/{color}]"
            )

    # Hypotheses
    if hypotheses:
        console.print("\n  [bold dim]Hypotheses:[/bold dim]")
        table = Table(show_header=True, header_style="bold dim", padding=(0, 1))
        table.add_column("ID", width=12)
        table.add_column("Label", min_width=25)
        table.add_column("Paper", width=14)
        table.add_column("Target", width=14)
        table.add_column("Status", width=12)

        for h, g in hypotheses:
            paper_uri = _first_value(g, HYP.paper)
            paper_display = _obj_id(paper_uri) if paper_uri else "-"
            target = _first_value(g, HYP.target) or "-"
            label = _first_value(g, RDFS.label) or h.title
            color = _STATUS_COLORS.get(h.status, "white")
            table.add_row(
                h.id,
                label[:35],
                paper_display,
                target[:14],
                f"[{color}]{h.status.value}[/{color}]",
            )
        console.print(table)

    # Experiments
    if experiments:
        console.print("\n  [bold dim]Experiments:[/bold dim]")
        table = Table(show_header=True, header_style="bold dim", padding=(0, 1))
        table.add_column("ID", width=14)
        table.add_column("Label", min_width=25)
        table.add_column("Hypothesis", width=12)
        table.add_column("Paper", width=14)
        table.add_column("Status", width=12)

        for e, g in experiments:
            hyp_uri = _first_value(g, EXPR.hypothesis)
            hyp_display = _obj_id(hyp_uri) if hyp_uri else "-"
            paper_uri = _first_value(g, EXPR.paper)
            paper_display = _obj_id(paper_uri) if paper_uri else "-"
            label = _first_value(g, RDFS.label) or e.title
            color = _STATUS_COLORS.get(e.status, "white")
            table.add_row(
                e.id,
                label[:35],
                hyp_display,
                paper_display,
                f"[{color}]{e.status.value}[/{color}]",
            )
        console.print(table)

    # Measures
    if measures:
        console.print("\n  [bold dim]Measures:[/bold dim]")
        table = Table(show_header=True, header_style="bold dim", padding=(0, 1))
        table.add_column("ID", width=8)
        table.add_column("Label", min_width=25)
        table.add_column("Unit", width=12)
        table.add_column("Category", width=14)

        for m, g in measures:
            label = _first_value(g, RDFS.label) or m.title
            unit = _first_value(g, MEASURE.unit) or "-"
            category = _first_value(g, MEASURE.category) or "-"
            table.add_row(m.id, label[:30], unit, category)
        console.print(table)

    # Literature
    if literature:
        console.print("\n  [bold dim]Literature:[/bold dim]")
        for lit, g in literature:
            color = _STATUS_COLORS.get(lit.status, "white")
            label = _first_value(g, RDFS.label) or lit.title
            explores_uri = _first_value(g, LIT.explores)
            explores = f" \u2192 {_obj_id(explores_uri)}" if explores_uri else ""
            console.print(
                f"    [bold]{lit.id}[/bold]  {label[:40]}{explores}  "
                f"[{color}]({lit.status.value})[/{color}]"
            )
