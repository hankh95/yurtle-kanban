"""Tests for --priority filter on the list command."""

import json
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from yurtle_kanban.cli import main
from yurtle_kanban.config import KanbanConfig, PathConfig
from yurtle_kanban.models import WorkItemStatus
from yurtle_kanban.service import KanbanService


@pytest.fixture
def temp_repo(tmp_path):
    """Create a minimal git repo with kanban config and items at various priorities."""
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True, check=True)

    (tmp_path / ".kanban").mkdir()
    (tmp_path / "kanban-work" / "expeditions").mkdir(parents=True)

    config = KanbanConfig(
        theme="nautical",
        paths=PathConfig(
            root="kanban-work/",
            scan_paths=["kanban-work/expeditions/"],
        ),
    )
    config.save(tmp_path / ".kanban" / "config.yaml")

    # Create items with different priorities
    exp_dir = tmp_path / "kanban-work" / "expeditions"
    (exp_dir / "EXP-001-Critical-Item.md").write_text(
        "---\nid: EXP-001\ntitle: Critical Item\nstatus: backlog\npriority: critical\n---\n"
    )
    (exp_dir / "EXP-002-High-Item.md").write_text(
        "---\nid: EXP-002\ntitle: High Item\nstatus: backlog\npriority: high\n---\n"
    )
    (exp_dir / "EXP-003-Medium-Item.md").write_text(
        "---\nid: EXP-003\ntitle: Medium Item\nstatus: backlog\npriority: medium\n---\n"
    )
    (exp_dir / "EXP-004-Low-Item.md").write_text(
        "---\nid: EXP-004\ntitle: Low Item\nstatus: in_progress\npriority: low\n---\n"
    )
    (exp_dir / "EXP-005-No-Priority.md").write_text(
        "---\nid: EXP-005\ntitle: No Priority\nstatus: backlog\n---\n"
    )

    return tmp_path


class TestPriorityFilterService:
    """Test priority filtering at the service layer."""

    def test_filter_single_priority(self, temp_repo):
        config = KanbanConfig.load(temp_repo / ".kanban" / "config.yaml")
        svc = KanbanService(config, temp_repo)

        items = svc.get_items(priority=["critical"])
        assert len(items) == 1
        assert items[0].id == "EXP-001"

    def test_filter_multiple_priorities(self, temp_repo):
        config = KanbanConfig.load(temp_repo / ".kanban" / "config.yaml")
        svc = KanbanService(config, temp_repo)

        items = svc.get_items(priority=["critical", "high"])
        assert len(items) == 2
        ids = {i.id for i in items}
        assert ids == {"EXP-001", "EXP-002"}

    def test_filter_no_priority_defaults_to_medium(self, temp_repo):
        """Items without explicit priority default to 'medium'."""
        config = KanbanConfig.load(temp_repo / ".kanban" / "config.yaml")
        svc = KanbanService(config, temp_repo)

        items = svc.get_items(priority=["medium"])
        ids = {i.id for i in items}
        # EXP-003 (explicit medium) and EXP-005 (no priority → medium)
        assert "EXP-003" in ids
        assert "EXP-005" in ids

    def test_filter_priority_with_status(self, temp_repo):
        """Priority filter combines with status filter."""
        config = KanbanConfig.load(temp_repo / ".kanban" / "config.yaml")
        svc = KanbanService(config, temp_repo)

        items = svc.get_items(
            priority=["low"],
            status=WorkItemStatus.IN_PROGRESS,
        )
        assert len(items) == 1
        assert items[0].id == "EXP-004"

    def test_no_priority_filter_returns_all(self, temp_repo):
        config = KanbanConfig.load(temp_repo / ".kanban" / "config.yaml")
        svc = KanbanService(config, temp_repo)

        items = svc.get_items(priority=None)
        assert len(items) == 5


class TestPriorityFilterCLI:
    """Test --priority flag via CLI runner."""

    def test_cli_priority_filter(self, temp_repo, monkeypatch):
        monkeypatch.chdir(temp_repo)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "--priority", "critical", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["id"] == "EXP-001"

    def test_cli_priority_comma_separated(self, temp_repo, monkeypatch):
        monkeypatch.chdir(temp_repo)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "--priority", "critical,high", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2
        ids = {d["id"] for d in data}
        assert ids == {"EXP-001", "EXP-002"}

    def test_cli_priority_invalid_value(self, temp_repo, monkeypatch):
        monkeypatch.chdir(temp_repo)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "--priority", "urgent"])
        assert result.exit_code != 0

    def test_cli_priority_short_flag(self, temp_repo, monkeypatch):
        monkeypatch.chdir(temp_repo)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "-p", "high", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["id"] == "EXP-002"
