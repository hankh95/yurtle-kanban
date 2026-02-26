"""
Tests for multi-board configuration support.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from yurtle_kanban.config import (
    KanbanConfig,
    BoardConfig,
    PathConfig,
    CONFIG_VERSION_SINGLE,
    CONFIG_VERSION_MULTI,
)
from yurtle_kanban.service import KanbanService


class TestBoardConfig:
    """Tests for BoardConfig dataclass."""

    def test_board_config_defaults(self):
        """Test BoardConfig with default values."""
        board = BoardConfig(name="test")
        assert board.name == "test"
        assert board.preset == "software"
        assert board.path == "work/"
        assert board.wip_limits == {}

    def test_board_config_custom(self):
        """Test BoardConfig with custom values."""
        board = BoardConfig(
            name="research",
            preset="hdd",
            path="research/",
            wip_limits={"active": 2, "draft": 5},
        )
        assert board.name == "research"
        assert board.preset == "hdd"
        assert board.path == "research/"
        assert board.wip_limits == {"active": 2, "draft": 5}

    def test_board_config_from_dict(self):
        """Test BoardConfig.from_dict."""
        data = {
            "name": "development",
            "preset": "nautical",
            "path": "kanban-work/",
            "wip_limits": {"underway": 3},
        }
        board = BoardConfig.from_dict(data)
        assert board.name == "development"
        assert board.preset == "nautical"
        assert board.path == "kanban-work/"
        assert board.wip_limits == {"underway": 3}

    def test_board_config_to_dict(self):
        """Test BoardConfig.to_dict."""
        board = BoardConfig(
            name="research",
            preset="hdd",
            path="research/",
            wip_limits={"active": 2},
        )
        data = board.to_dict()
        assert data == {
            "name": "research",
            "preset": "hdd",
            "path": "research/",
            "wip_limits": {"active": 2},
        }

    def test_board_config_get_path(self):
        """Test BoardConfig.get_path."""
        board = BoardConfig(name="test", path="my/path/")
        assert board.get_path() == Path("my/path/")


class TestKanbanConfigMultiBoard:
    """Tests for multi-board KanbanConfig."""

    def test_single_board_default(self):
        """Test default single-board configuration."""
        config = KanbanConfig()
        assert config.version == CONFIG_VERSION_SINGLE
        assert not config.is_multi_board
        assert len(config.boards) == 0

    def test_multi_board_detection(self):
        """Test multi-board mode detection."""
        config = KanbanConfig(
            version=CONFIG_VERSION_MULTI,
            boards=[
                BoardConfig(name="dev", preset="software", path="work/"),
                BoardConfig(name="research", preset="hdd", path="research/"),
            ],
        )
        assert config.is_multi_board
        assert len(config.boards) == 2

    def test_get_board_by_name(self):
        """Test getting a board by name."""
        config = KanbanConfig(
            version=CONFIG_VERSION_MULTI,
            boards=[
                BoardConfig(name="dev", preset="software", path="work/"),
                BoardConfig(name="research", preset="hdd", path="research/"),
            ],
        )
        board = config.get_board("research")
        assert board is not None
        assert board.name == "research"
        assert board.preset == "hdd"

    def test_get_board_not_found(self):
        """Test getting a non-existent board."""
        config = KanbanConfig(
            version=CONFIG_VERSION_MULTI,
            boards=[BoardConfig(name="dev")],
        )
        board = config.get_board("nonexistent")
        assert board is None

    def test_get_default_board(self):
        """Test getting the default board."""
        config = KanbanConfig(
            version=CONFIG_VERSION_MULTI,
            boards=[
                BoardConfig(name="dev"),
                BoardConfig(name="research"),
            ],
            default_board="research",
        )
        board = config.get_default_board()
        assert board is not None
        assert board.name == "research"

    def test_get_default_board_fallback(self):
        """Test default board falls back to first board."""
        config = KanbanConfig(
            version=CONFIG_VERSION_MULTI,
            boards=[
                BoardConfig(name="first"),
                BoardConfig(name="second"),
            ],
        )
        board = config.get_default_board()
        assert board is not None
        assert board.name == "first"

    def test_add_board_single_to_multi(self):
        """Test adding a board upgrades from single to multi."""
        config = KanbanConfig(
            theme="software",
            paths=PathConfig(root="work/"),
        )
        assert not config.is_multi_board

        config.add_board(BoardConfig(name="research", preset="hdd", path="research/"))

        assert config.is_multi_board
        assert len(config.boards) == 2  # Original + new
        assert config.boards[0].name == "default"  # Original converted
        assert config.boards[1].name == "research"

    def test_add_board_multi(self):
        """Test adding a board in multi-board mode."""
        config = KanbanConfig(
            version=CONFIG_VERSION_MULTI,
            boards=[BoardConfig(name="dev")],
        )
        config.add_board(BoardConfig(name="research"))

        assert len(config.boards) == 2
        assert config.boards[1].name == "research"


class TestKanbanConfigLoadSave:
    """Tests for loading and saving multi-board configs."""

    def test_load_v2_config(self, tmp_path):
        """Test loading a v2 multi-board config."""
        config_path = tmp_path / ".kanban" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("""
version: "2.0"
boards:
  - name: development
    preset: nautical
    path: kanban-work/
    wip_limits:
      underway: 3
  - name: research
    preset: hdd
    path: research/
default_board: development
namespace: "https://example.com/"
""")

        config = KanbanConfig.load(config_path)

        assert config.is_multi_board
        assert len(config.boards) == 2
        assert config.boards[0].name == "development"
        assert config.boards[0].preset == "nautical"
        assert config.boards[0].wip_limits == {"underway": 3}
        assert config.boards[1].name == "research"
        assert config.boards[1].preset == "hdd"
        assert config.default_board == "development"
        assert config.namespace == "https://example.com/"

    def test_load_v1_config_backward_compat(self, tmp_path):
        """Test loading a v1 config (backward compatibility)."""
        config_path = tmp_path / ".kanban" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("""
kanban:
  theme: nautical
  paths:
    root: kanban-work/
""")

        config = KanbanConfig.load(config_path)

        assert not config.is_multi_board
        assert config.theme == "nautical"
        assert config.paths.root == "kanban-work/"

    def test_save_v2_config(self, tmp_path):
        """Test saving a v2 multi-board config."""
        config = KanbanConfig(
            version=CONFIG_VERSION_MULTI,
            boards=[
                BoardConfig(name="dev", preset="software", path="work/"),
                BoardConfig(name="research", preset="hdd", path="research/"),
            ],
            default_board="dev",
            namespace="https://test.dev/",
        )

        config_path = tmp_path / ".kanban" / "config.yaml"
        config.save(config_path)

        # Reload and verify
        loaded = KanbanConfig.load(config_path)
        assert loaded.is_multi_board
        assert len(loaded.boards) == 2
        assert loaded.default_board == "dev"
        assert loaded.namespace == "https://test.dev/"

    def test_get_work_paths_multi(self):
        """Test get_work_paths in multi-board mode."""
        config = KanbanConfig(
            version=CONFIG_VERSION_MULTI,
            boards=[
                BoardConfig(name="dev", path="work/"),
                BoardConfig(name="research", path="research/"),
            ],
        )
        paths = config.get_work_paths()
        assert len(paths) == 2
        assert Path("work/") in paths
        assert Path("research/") in paths


class TestKanbanServiceMultiBoard:
    """Tests for KanbanService with multi-board support."""

    @pytest.fixture
    def multi_board_setup(self, tmp_path):
        """Create a multi-board test environment."""
        # Create config
        config_path = tmp_path / ".kanban" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("""
version: "2.0"
boards:
  - name: development
    preset: nautical
    path: kanban-work/
  - name: research
    preset: software
    path: research/
default_board: development
""")

        # Create work item directories
        (tmp_path / "kanban-work" / "expeditions").mkdir(parents=True)
        (tmp_path / "research" / "experiments").mkdir(parents=True)

        # Create some work items
        dev_item = tmp_path / "kanban-work" / "expeditions" / "EXP-001-Test.md"
        dev_item.write_text("""---
id: EXP-001
title: "Test Expedition"
type: expedition
status: backlog
---
# Test Expedition
""")

        research_item = tmp_path / "research" / "experiments" / "EXPR-101.md"
        research_item.write_text("""---
id: EXPR-101
title: "Test Experiment"
type: feature
status: in_progress
---
# Test Experiment
""")

        config = KanbanConfig.load(config_path)
        service = KanbanService(config, tmp_path)

        return {
            "tmp_path": tmp_path,
            "config": config,
            "service": service,
        }

    def test_get_board_default(self, multi_board_setup):
        """Test getting the default board."""
        service = multi_board_setup["service"]
        board = service.get_board()

        assert board.id == "development"
        assert board.name == "Development Board"

    def test_get_board_by_name(self, multi_board_setup):
        """Test getting a specific board by name."""
        service = multi_board_setup["service"]
        board = service.get_board(board_name="research")

        assert board.id == "research"
        assert board.name == "Research Board"

    def test_board_items_filtered(self, multi_board_setup):
        """Test that each board only shows its own items."""
        service = multi_board_setup["service"]

        dev_board = service.get_board(board_name="development")
        research_board = service.get_board(board_name="research")

        # Development board should have EXP-001
        dev_ids = [item.id for item in dev_board.items]
        assert "EXP-001" in dev_ids
        assert "EXPR-101" not in dev_ids

        # Research board should have EXPR-101
        research_ids = [item.id for item in research_board.items]
        assert "EXPR-101" in research_ids
        assert "EXP-001" not in research_ids


class TestBoardForPath:
    """Tests for detecting board from path."""

    def test_get_board_for_path(self, tmp_path):
        """Test detecting board from file path."""
        config = KanbanConfig(
            version=CONFIG_VERSION_MULTI,
            boards=[
                BoardConfig(name="dev", path="kanban-work/"),
                BoardConfig(name="research", path="research/"),
            ],
        )

        # Test path matching
        board = config.get_board_for_path(
            tmp_path / "kanban-work" / "expeditions" / "EXP-001.md",
            repo_root=tmp_path,
        )
        assert board is not None
        assert board.name == "dev"

        board = config.get_board_for_path(
            tmp_path / "research" / "experiments" / "EXPR-101.md",
            repo_root=tmp_path,
        )
        assert board is not None
        assert board.name == "research"

    def test_get_board_for_path_no_match(self, tmp_path):
        """Test path that doesn't match any board."""
        config = KanbanConfig(
            version=CONFIG_VERSION_MULTI,
            boards=[
                BoardConfig(name="dev", path="kanban-work/"),
            ],
        )

        board = config.get_board_for_path(
            tmp_path / "other" / "file.md",
            repo_root=tmp_path,
        )
        assert board is None
