"""
Work item models for yurtle-kanban.

These models represent the core data structures for file-based kanban.
Each WorkItem corresponds to a Yurtle markdown file.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class WorkItemStatus(Enum):
    """Standard work item statuses."""
    BACKLOG = "backlog"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"

    @classmethod
    def from_string(cls, value: str) -> "WorkItemStatus":
        """Parse status from string, handling various formats."""
        normalized = value.lower().replace("-", "_").replace(" ", "_")
        for status in cls:
            if status.value == normalized:
                return status
        raise ValueError(f"Unknown status: {value}")


class WorkItemType(Enum):
    """Standard work item types (supports both software and nautical themes)."""
    # Software theme
    FEATURE = "feature"
    BUG = "bug"
    EPIC = "epic"
    ISSUE = "issue"
    TASK = "task"
    IDEA = "idea"
    # Nautical theme
    EXPEDITION = "expedition"
    VOYAGE = "voyage"
    DIRECTIVE = "directive"
    HAZARD = "hazard"
    SIGNAL = "signal"
    CHORE = "chore"

    @classmethod
    def from_string(cls, value: str) -> "WorkItemType":
        """Parse type from string."""
        normalized = value.lower()
        for item_type in cls:
            if item_type.value == normalized:
                return item_type
        raise ValueError(f"Unknown item type: {value}")


@dataclass
class Comment:
    """A comment on a work item."""
    content: str
    author: str
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Column:
    """A kanban column definition."""
    id: str
    name: str
    order: int
    wip_limit: int | None = None
    description: str | None = None

    def is_over_wip(self, count: int) -> bool:
        """Check if column is over WIP limit."""
        if self.wip_limit is None:
            return False
        return count > self.wip_limit


@dataclass
class WorkItem:
    """A work item represented by a Yurtle markdown file."""

    id: str
    title: str
    item_type: WorkItemType
    status: WorkItemStatus
    file_path: Path

    # Optional fields
    priority: str | None = None
    assignee: str | None = None
    created: date | None = None
    updated: datetime | None = None
    tags: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    blocks: list[str] = field(default_factory=list)
    description: str | None = None
    comments: list[Comment] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.updated is None:
            self.updated = datetime.now()

    @property
    def uri(self) -> str:
        """Return the file URI for this work item."""
        return f"file://{self.file_path.absolute()}"

    @property
    def is_blocked(self) -> bool:
        """Check if item is blocked."""
        return self.status == WorkItemStatus.BLOCKED

    @property
    def priority_score(self) -> int:
        """Get numeric priority score for sorting."""
        priority_map = {
            "critical": 100,
            "high": 75,
            "medium": 50,
            "low": 25,
            "backlog": 10,
        }
        return priority_map.get(self.priority or "medium", 50)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "item_type": self.item_type.value,
            "status": self.status.value,
            "file_path": str(self.file_path),
            "priority": self.priority,
            "assignee": self.assignee,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "tags": self.tags,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "description": self.description,
        }

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

        if self.depends_on:
            deps_str = ', '.join(f'<{dep}>' for dep in self.depends_on)
            lines.append(f'   kb:dependsOn {deps_str} ;')

        # Remove trailing semicolon from last line and add period
        lines[-1] = lines[-1].rstrip(' ;') + ' .'

        return '\n'.join(lines)

    def to_markdown(self) -> str:
        """Generate full markdown file content.

        Format: Frontmatter (single source of truth) + Title + Content.
        No duplicate formatted sections. No yurtle blocks.
        """
        lines = [
            "---",
            f'id: {self.id}',
            f'title: "{self.title}"',
            f'type: {self.item_type.value}',
            f'status: {self.status.value}',
        ]

        if self.priority:
            lines.append(f'priority: {self.priority}')
        if self.assignee:
            lines.append(f'assignee: {self.assignee}')
        if self.created:
            lines.append(f'created: {self.created.isoformat()}')
        if self.tags:
            lines.append(f'tags: [{", ".join(self.tags)}]')

        # Always include depends_on (even if empty)
        if self.depends_on:
            lines.append(f'depends_on: [{", ".join(self.depends_on)}]')
        else:
            lines.append('depends_on: []')

        lines.extend([
            "---",
            "",
            f"# {self.title}",
            "",
        ])

        if self.description:
            lines.append(self.description)

        return '\n'.join(lines)


@dataclass
class Board:
    """A kanban board containing work items organized by columns."""
    id: str
    name: str
    columns: list[Column]
    items: list[WorkItem] = field(default_factory=list)
    # Optional mapping from column ID to WorkItemStatus (for themed columns)
    column_status_map: dict[str, WorkItemStatus] = field(default_factory=dict)

    def get_items_by_status(self, status: WorkItemStatus) -> list[WorkItem]:
        """Get all items with a specific status."""
        return [item for item in self.items if item.status == status]

    def get_column_counts(self) -> dict[str, int]:
        """Get count of items in each column."""
        counts = {}
        for col in self.columns:
            # Use column_status_map if available, otherwise try standard parsing
            if col.id in self.column_status_map:
                status = self.column_status_map[col.id]
            else:
                try:
                    status = WorkItemStatus.from_string(col.id)
                except ValueError:
                    # Unknown column, count as 0
                    counts[col.id] = 0
                    continue
            counts[col.id] = len(self.get_items_by_status(status))
        return counts

    def get_wip_violations(self) -> list[tuple[Column, int]]:
        """Get columns that are over WIP limit."""
        violations = []
        counts = self.get_column_counts()
        for col in self.columns:
            count = counts.get(col.id, 0)
            if col.is_over_wip(count):
                violations.append((col, count))
        return violations
