"""
Work item models for yurtle-kanban.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Optional


class WorkItemStatus(Enum):
    """Standard work item statuses."""
    BACKLOG = "backlog"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


class WorkItemType(Enum):
    """Standard work item types (software theme)."""
    FEATURE = "feature"
    BUG = "bug"
    EPIC = "epic"
    ISSUE = "issue"
    TASK = "task"
    IDEA = "idea"


@dataclass
class WorkItem:
    """A work item represented by a Yurtle markdown file."""

    id: str
    title: str
    item_type: WorkItemType
    status: WorkItemStatus
    file_path: Path

    # Optional fields
    priority: Optional[str] = None
    assignee: Optional[str] = None
    created: Optional[date] = None
    tags: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    description: Optional[str] = None

    @property
    def uri(self) -> str:
        """Return the file URI for this work item."""
        return f"file://{self.file_path.absolute()}"

    def to_yurtle(self) -> str:
        """Generate Yurtle block content for this work item."""
        lines = [
            '@prefix kb: <https://yurtle.dev/kanban/> .',
            '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .',
            '',
            f'<> a kb:{self.item_type.value.title()} ;',
            f'   kb:id "{self.id}" ;',
            f'   kb:status kb:{self.status.value} ;',
        ]

        if self.priority:
            lines.append(f'   kb:priority kb:{self.priority} ;')

        if self.assignee:
            lines.append(f'   kb:assignee <{self.assignee}> ;')

        if self.created:
            lines.append(f'   kb:created "{self.created.isoformat()}"^^xsd:date ;')

        if self.tags:
            tag_str = ', '.join(f'"{tag}"' for tag in self.tags)
            lines.append(f'   kb:tag {tag_str} ;')

        # Remove trailing semicolon from last line and add period
        lines[-1] = lines[-1].rstrip(' ;') + ' .'

        return '\n'.join(lines)
