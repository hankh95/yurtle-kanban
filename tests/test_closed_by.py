"""Tests for --closed-by graph provenance on move — Issue #28."""

from __future__ import annotations

import pytest

from yurtle_kanban.config import KanbanConfig
from yurtle_kanban.models import WorkItemStatus
from yurtle_kanban.service import KanbanService


@pytest.fixture
def kanban_setup(tmp_path):
    """Minimal kanban setup with one expedition for move testing."""
    config_path = tmp_path / ".kanban" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("""
version: "2.0"
boards:
  - name: development
    preset: nautical
    path: work/
default_board: development
""")

    (tmp_path / "work" / "expeditions").mkdir(parents=True)

    item_file = tmp_path / "work" / "expeditions" / "EXP-100.md"
    item_file.write_text("""---
id: EXP-100
title: "Test Expedition"
type: expedition
status: in_progress
---
# Test Expedition
""")

    config = KanbanConfig.load(config_path)
    service = KanbanService(config, tmp_path)
    return {"service": service, "item_file": item_file}


class TestClosedByProvenance:
    def test_move_with_closed_by_writes_triple(self, kanban_setup):
        """Moving with closed_by should write kb:closedBy triple."""
        service = kanban_setup["service"]
        item_file = kanban_setup["item_file"]
        pr_url = "https://github.com/hankh95/nusy-product-team/pull/228"

        service.move_item(
            "EXP-100",
            WorkItemStatus.DONE,
            commit=False,
            validate_workflow=False,
            closed_by=pr_url,
        )

        content = item_file.read_text()
        assert "kb:closedBy" in content
        assert pr_url in content
        assert f"<{pr_url}>" in content

    def test_move_without_closed_by_has_no_triple(self, kanban_setup):
        """Moving without closed_by should NOT write kb:closedBy."""
        service = kanban_setup["service"]
        item_file = kanban_setup["item_file"]

        service.move_item(
            "EXP-100",
            WorkItemStatus.DONE,
            commit=False,
            validate_workflow=False,
        )

        content = item_file.read_text()
        assert "kb:closedBy" not in content

    def test_closed_by_with_forced_move(self, kanban_setup):
        """Both kb:closedBy and kb:forcedMove should coexist."""
        service = kanban_setup["service"]
        item_file = kanban_setup["item_file"]
        pr_url = "https://github.com/test/pull/1"

        service.move_item(
            "EXP-100",
            WorkItemStatus.DONE,
            commit=False,
            validate_workflow=False,  # forced=True derived from this
            closed_by=pr_url,
        )

        content = item_file.read_text()
        assert "kb:closedBy" in content
        assert "kb:forcedMove" in content
        assert pr_url in content

    def test_closed_by_appears_in_turtle_block(self, kanban_setup):
        """The kb:closedBy triple should be inside the yurtle block."""
        service = kanban_setup["service"]
        item_file = kanban_setup["item_file"]
        pr_url = "https://github.com/example/pull/99"

        service.move_item(
            "EXP-100",
            WorkItemStatus.DONE,
            commit=False,
            validate_workflow=False,
            closed_by=pr_url,
        )

        content = item_file.read_text()
        # Find the yurtle block
        start = content.index("```yurtle")
        end = content.index("```", start + 3)
        turtle_block = content[start:end]

        assert "kb:closedBy" in turtle_block
        assert f"<{pr_url}>" in turtle_block
        assert "kb:status kb:done" in turtle_block
