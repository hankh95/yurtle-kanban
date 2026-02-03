"""
yurtle-kanban: File-based kanban using Yurtle (Turtle RDF in Markdown).

Git is your database.

Usage:
    # CLI
    yurtle-kanban init
    yurtle-kanban board
    yurtle-kanban list
    yurtle-kanban create feature "My feature"
    yurtle-kanban move FEAT-001 done

    # Python API
    from yurtle_kanban import KanbanService, KanbanConfig
    config = KanbanConfig.load(Path(".kanban/config.yaml"))
    service = KanbanService(config, Path.cwd())
    items = service.get_items()

    # MCP Server
    yurtle-kanban-mcp
"""

__version__ = "0.1.0"

# Register yurtle_rdflib plugin with rdflib (enables format="yurtle" parsing)
# This must be imported before any rdflib Graph.parse() calls with format="yurtle"
try:
    import yurtle_rdflib  # noqa: F401
except ImportError:
    pass  # yurtle_rdflib is optional; YAML frontmatter still works without it

from yurtle_kanban.config import KanbanConfig
from yurtle_kanban.models import (
    Board,
    Column,
    Comment,
    WorkItem,
    WorkItemStatus,
    WorkItemType,
)
from yurtle_kanban.service import KanbanService
from yurtle_kanban.workflow import (
    StateConfig,
    TransitionRule,
    WorkflowConfig,
    WorkflowParser,
    get_default_workflow,
)

__all__ = [
    # Config
    "KanbanConfig",
    # Models
    "Board",
    "Column",
    "Comment",
    "WorkItem",
    "WorkItemStatus",
    "WorkItemType",
    # Service
    "KanbanService",
    # Workflow
    "StateConfig",
    "TransitionRule",
    "WorkflowConfig",
    "WorkflowParser",
    "get_default_workflow",
]
