"""Tests for work item models."""

from datetime import date
from pathlib import Path

import pytest

from yurtle_kanban.models import WorkItem, WorkItemStatus, WorkItemType


class TestWorkItem:
    """Tests for the WorkItem model."""

    def test_create_work_item(self):
        """Test creating a basic work item."""
        item = WorkItem(
            id="FEAT-001",
            title="Add dark mode",
            item_type=WorkItemType.FEATURE,
            status=WorkItemStatus.IN_PROGRESS,
            file_path=Path("work/FEAT-001.md"),
        )

        assert item.id == "FEAT-001"
        assert item.title == "Add dark mode"
        assert item.item_type == WorkItemType.FEATURE
        assert item.status == WorkItemStatus.IN_PROGRESS

    def test_work_item_with_optional_fields(self):
        """Test work item with all optional fields."""
        item = WorkItem(
            id="BUG-042",
            title="Fix login issue",
            item_type=WorkItemType.BUG,
            status=WorkItemStatus.READY,
            file_path=Path("work/bugs/BUG-042.md"),
            priority="high",
            assignee="../team/dev-1.md",
            created=date(2026, 1, 12),
            tags=["auth", "critical"],
            depends_on=["FEAT-001"],
        )

        assert item.priority == "high"
        assert item.assignee == "../team/dev-1.md"
        assert item.created == date(2026, 1, 12)
        assert "auth" in item.tags
        assert "FEAT-001" in item.depends_on

    def test_to_yurtle(self):
        """Test generating Yurtle block content."""
        item = WorkItem(
            id="FEAT-001",
            title="Test feature",
            item_type=WorkItemType.FEATURE,
            status=WorkItemStatus.IN_PROGRESS,
            file_path=Path("work/FEAT-001.md"),
            priority="high",
            tags=["ui", "ux"],
        )

        yurtle = item.to_yurtle()

        assert "@prefix kb:" in yurtle
        assert 'kb:id "FEAT-001"' in yurtle
        assert "kb:status kb:in_progress" in yurtle
        assert "kb:priority kb:high" in yurtle
        assert '"ui"' in yurtle
        assert '"ux"' in yurtle


class TestWorkItemStatus:
    """Tests for work item statuses."""

    def test_all_statuses_exist(self):
        """Test that all expected statuses are defined."""
        statuses = [s.value for s in WorkItemStatus]
        assert "backlog" in statuses
        assert "in_progress" in statuses
        assert "done" in statuses


class TestWorkItemType:
    """Tests for work item types."""

    def test_all_types_exist(self):
        """Test that all expected types are defined."""
        types = [t.value for t in WorkItemType]
        assert "feature" in types
        assert "bug" in types
        assert "epic" in types
