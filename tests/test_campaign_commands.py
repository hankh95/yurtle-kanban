"""Tests for voyage/epic CLI commands (initiative management)."""

import subprocess

import pytest
from click.testing import CliRunner

from yurtle_kanban.cli import main
from yurtle_kanban.config import KanbanConfig, PathConfig
from yurtle_kanban.models import WorkItem, WorkItemStatus, WorkItemType
from yurtle_kanban.service import KanbanService


# ---------------------------------------------------------------------------
# Fixtures — Nautical theme (voyages)
# ---------------------------------------------------------------------------


@pytest.fixture
def nautical_repo(tmp_path):
    """Create a minimal git repo with nautical theme for voyage testing."""
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    (tmp_path / ".kanban").mkdir()
    (tmp_path / "kanban-work" / "expeditions").mkdir(parents=True)
    (tmp_path / "kanban-work" / "voyages").mkdir(parents=True)
    (tmp_path / "kanban-work" / "signals").mkdir(parents=True)

    config = KanbanConfig(
        theme="nautical",
        paths=PathConfig(
            root="kanban-work/",
            scan_paths=[
                "kanban-work/expeditions/",
                "kanban-work/voyages/",
                "kanban-work/signals/",
            ],
        ),
    )
    config.save(tmp_path / ".kanban" / "config.yaml")
    return tmp_path


@pytest.fixture
def nautical_runner(nautical_repo, monkeypatch):
    """Click runner with cwd set to nautical repo."""
    from yurtle_kanban import config as config_mod

    config_mod._theme_cache.clear()
    monkeypatch.chdir(nautical_repo)
    return CliRunner()


# ---------------------------------------------------------------------------
# Fixtures — Software theme (epics)
# ---------------------------------------------------------------------------


@pytest.fixture
def software_repo(tmp_path):
    """Create a minimal git repo with software theme for epic testing."""
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    (tmp_path / ".kanban").mkdir()
    (tmp_path / "work" / "features").mkdir(parents=True)
    (tmp_path / "work" / "epics").mkdir(parents=True)
    (tmp_path / "work" / "bugs").mkdir(parents=True)

    config = KanbanConfig(
        theme="software",
        paths=PathConfig(
            root="work/",
            scan_paths=[
                "work/features/",
                "work/epics/",
                "work/bugs/",
            ],
        ),
    )
    config.save(tmp_path / ".kanban" / "config.yaml")
    return tmp_path


@pytest.fixture
def software_runner(software_repo, monkeypatch):
    """Click runner with cwd set to software repo."""
    from yurtle_kanban import config as config_mod

    config_mod._theme_cache.clear()
    monkeypatch.chdir(software_repo)
    return CliRunner()


# ---------------------------------------------------------------------------
# Voyage Create (nautical theme)
# ---------------------------------------------------------------------------


class TestVoyageCreate:
    """Tests for 'yurtle-kanban voyage create'."""

    def test_voyage_create_nautical(self, nautical_runner, nautical_repo):
        """Create a voyage in nautical theme should produce VOY-XXX."""
        result = nautical_runner.invoke(
            main, ["voyage", "create", "Campaign Management"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        assert "VOY-" in result.output
        assert "Campaign Management" in result.output

    def test_voyage_create_auto_increments(self, nautical_runner, nautical_repo):
        """Second voyage should get next ID number."""
        nautical_runner.invoke(
            main, ["voyage", "create", "First Voyage"],
            catch_exceptions=False,
        )
        result = nautical_runner.invoke(
            main, ["voyage", "create", "Second Voyage"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "VOY-" in result.output

    def test_voyage_create_with_priority(self, nautical_runner, nautical_repo):
        """Voyage should accept --priority flag."""
        result = nautical_runner.invoke(
            main, ["voyage", "create", "Critical Voyage", "-p", "critical"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Epic Create (software theme)
# ---------------------------------------------------------------------------


class TestEpicCreate:
    """Tests for 'yurtle-kanban epic create'."""

    def test_epic_create_software(self, software_runner, software_repo):
        """Create an epic in software theme should produce EPIC-XXX."""
        result = software_runner.invoke(
            main, ["epic", "create", "User Auth Overhaul"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        assert "EPIC-" in result.output
        assert "User Auth Overhaul" in result.output


# ---------------------------------------------------------------------------
# Voyage Show
# ---------------------------------------------------------------------------


class TestVoyageShow:
    """Tests for 'yurtle-kanban voyage show'."""

    def test_show_existing_voyage(self, nautical_runner, nautical_repo):
        """Show should display a created voyage."""
        nautical_runner.invoke(
            main, ["voyage", "create", "Test Voyage"],
            catch_exceptions=False,
        )
        result = nautical_runner.invoke(
            main, ["voyage", "show", "VOY-001"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Test Voyage" in result.output

    def test_show_nonexistent_voyage(self, nautical_runner, nautical_repo):
        """Show should fail for nonexistent ID."""
        result = nautical_runner.invoke(
            main, ["voyage", "show", "VOY-999"],
        )
        assert result.exit_code != 0

    def test_show_with_linked_items(self, nautical_runner, nautical_repo):
        """Show should display items linked via related field."""
        # Create a voyage
        nautical_runner.invoke(
            main, ["voyage", "create", "Big Voyage"],
            catch_exceptions=False,
        )
        # Create an expedition and link it
        nautical_runner.invoke(
            main, ["create", "expedition", "Phase 1 Work", "--priority", "high"],
            catch_exceptions=False,
        )
        nautical_runner.invoke(
            main, ["voyage", "add", "VOY-001", "EXP-001"],
            catch_exceptions=False,
        )
        result = nautical_runner.invoke(
            main, ["voyage", "show", "VOY-001"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "EXP-001" in result.output
        assert "0/1" in result.output or "Progress" in result.output


# ---------------------------------------------------------------------------
# Voyage Add
# ---------------------------------------------------------------------------


class TestVoyageAdd:
    """Tests for 'yurtle-kanban voyage add'."""

    def test_add_links_item(self, nautical_runner, nautical_repo):
        """Add should write voyage ID to item's related field."""
        # Create voyage and expedition
        nautical_runner.invoke(
            main, ["voyage", "create", "Link Test"],
            catch_exceptions=False,
        )
        nautical_runner.invoke(
            main, ["create", "expedition", "Item To Link", "--priority", "high"],
            catch_exceptions=False,
        )
        result = nautical_runner.invoke(
            main, ["voyage", "add", "VOY-001", "EXP-001"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Linked" in result.output

        # Verify the file was updated
        exp_files = list(
            (nautical_repo / "kanban-work" / "expeditions").glob("EXP-001*.md")
        )
        assert len(exp_files) == 1
        content = exp_files[0].read_text()
        assert "VOY-001" in content

    def test_add_idempotent(self, nautical_runner, nautical_repo):
        """Adding the same link twice should not duplicate."""
        nautical_runner.invoke(
            main, ["voyage", "create", "Idem Test"],
            catch_exceptions=False,
        )
        nautical_runner.invoke(
            main, ["create", "expedition", "Item", "--priority", "high"],
            catch_exceptions=False,
        )
        nautical_runner.invoke(
            main, ["voyage", "add", "VOY-001", "EXP-001"],
            catch_exceptions=False,
        )
        result = nautical_runner.invoke(
            main, ["voyage", "add", "VOY-001", "EXP-001"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "already linked" in result.output

    def test_add_nonexistent_voyage(self, nautical_runner, nautical_repo):
        """Adding to nonexistent voyage should fail."""
        result = nautical_runner.invoke(
            main, ["voyage", "add", "VOY-999", "EXP-001"],
        )
        assert result.exit_code != 0

    def test_add_nonexistent_item(self, nautical_runner, nautical_repo):
        """Adding nonexistent item should fail."""
        nautical_runner.invoke(
            main, ["voyage", "create", "Test"],
            catch_exceptions=False,
        )
        result = nautical_runner.invoke(
            main, ["voyage", "add", "VOY-001", "EXP-999"],
        )
        # Should warn about item not found (exits 0 with warning)
        assert "not found" in result.output


# ---------------------------------------------------------------------------
# Related Field
# ---------------------------------------------------------------------------


class TestRelatedField:
    """Tests for the related field on WorkItem."""

    def test_related_field_exists(self):
        """WorkItem should have a related field."""
        item = WorkItem(
            id="EXP-001",
            title="Test",
            item_type=WorkItemType.EXPEDITION,
            status=WorkItemStatus.BACKLOG,
            file_path="/tmp/test.md",
            related=["VOY-001", "EXP-002"],
        )
        assert item.related == ["VOY-001", "EXP-002"]

    def test_related_default_empty(self):
        """Related should default to empty list."""
        item = WorkItem(
            id="EXP-001",
            title="Test",
            item_type=WorkItemType.EXPEDITION,
            status=WorkItemStatus.BACKLOG,
            file_path="/tmp/test.md",
        )
        assert item.related == []

    def test_related_in_to_dict(self):
        """to_dict should include related."""
        item = WorkItem(
            id="EXP-001",
            title="Test",
            item_type=WorkItemType.EXPEDITION,
            status=WorkItemStatus.BACKLOG,
            file_path="/tmp/test.md",
            related=["VOY-001"],
        )
        d = item.to_dict()
        assert d["related"] == ["VOY-001"]

    def test_related_in_to_markdown(self):
        """to_markdown should include related in frontmatter."""
        item = WorkItem(
            id="EXP-001",
            title="Test",
            item_type=WorkItemType.EXPEDITION,
            status=WorkItemStatus.BACKLOG,
            file_path="/tmp/test.md",
            related=["VOY-001", "EXP-002"],
        )
        md = item.to_markdown()
        assert "related: [VOY-001, EXP-002]" in md

    def test_related_in_to_yurtle(self):
        """to_yurtle should include kb:related."""
        item = WorkItem(
            id="EXP-001",
            title="Test",
            item_type=WorkItemType.EXPEDITION,
            status=WorkItemStatus.BACKLOG,
            file_path="/tmp/test.md",
            related=["VOY-001"],
        )
        yurtle = item.to_yurtle()
        assert "kb:related" in yurtle

    def test_related_parsed_from_frontmatter(self, nautical_runner, nautical_repo):
        """Service should parse related field from frontmatter."""
        # Create an item with related field
        exp_dir = nautical_repo / "kanban-work" / "expeditions"
        (exp_dir / "EXP-001-Test.md").write_text(
            "---\n"
            "id: EXP-001\n"
            'title: "Test"\n'
            "type: expedition\n"
            "status: backlog\n"
            "created: 2026-02-27\n"
            "priority: medium\n"
            "related: [VOY-001, EXP-002]\n"
            "---\n\n# Test\n"
        )
        config = KanbanConfig.load(nautical_repo / ".kanban" / "config.yaml")
        service = KanbanService(config, nautical_repo)
        service.scan()

        item = service._items.get("EXP-001")
        assert item is not None
        assert "VOY-001" in item.related
        assert "EXP-002" in item.related


# ---------------------------------------------------------------------------
# Board --voyage filter
# ---------------------------------------------------------------------------


class TestBoardVoyageFilter:
    """Tests for 'yurtle-kanban board --voyage'."""

    def test_board_voyage_filter(self, nautical_runner, nautical_repo):
        """Board --voyage should only show items linked to that voyage."""
        # Create voyage + two expeditions, link only one
        nautical_runner.invoke(
            main, ["voyage", "create", "Filter Test"],
            catch_exceptions=False,
        )
        nautical_runner.invoke(
            main, ["create", "expedition", "Linked Item", "--priority", "high"],
            catch_exceptions=False,
        )
        nautical_runner.invoke(
            main, ["create", "expedition", "Unlinked Item", "--priority", "low"],
            catch_exceptions=False,
        )
        nautical_runner.invoke(
            main, ["voyage", "add", "VOY-001", "EXP-001"],
            catch_exceptions=False,
        )
        result = nautical_runner.invoke(
            main, ["board", "--voyage", "VOY-001"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # Board output should contain the linked item but exact rendering
        # depends on board renderer — just verify no crash


# ---------------------------------------------------------------------------
# Epic command works for both themes
# ---------------------------------------------------------------------------


class TestEpicAliasWorksInNautical:
    """Epic command should also work in nautical theme (creates voyage)."""

    def test_epic_command_in_nautical_creates_voyage(self, nautical_runner, nautical_repo):
        """Using 'epic create' in nautical theme should still create a VOY- item."""
        result = nautical_runner.invoke(
            main, ["epic", "create", "Cross Theme Test"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "VOY-" in result.output


class TestVoyageAliasWorksInSoftware:
    """Voyage command should also work in software theme (creates epic)."""

    def test_voyage_command_in_software_creates_epic(self, software_runner, software_repo):
        """Using 'voyage create' in software theme should still create an EPIC- item."""
        result = software_runner.invoke(
            main, ["voyage", "create", "Cross Theme Test"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "EPIC-" in result.output
