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


class TestHDDTypeRoutingMultiBoard:
    """Issue #20: HDD item types must route to the research board in multi-board mode.

    When a multi-board config has development (nautical) + research (hdd) boards,
    HDD item types (hypothesis, experiment, literature, measure, paper, idea)
    should be created in the research board's directories, not the development board's.
    """

    @pytest.fixture
    def multiboard_hdd_setup(self, tmp_path):
        """Create a multi-board environment with development + research boards."""
        import subprocess

        # Init git repo (needed for create_item_and_push)
        subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path, capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path, capture_output=True, check=True,
        )

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
    preset: hdd
    path: research/
default_board: development
""")

        # Create directory structure
        for subdir in ["expeditions", "chores", "voyages"]:
            (tmp_path / "kanban-work" / subdir).mkdir(parents=True)
        for subdir in ["ideas", "literature", "papers", "hypotheses", "experiments", "measures"]:
            (tmp_path / "research" / subdir).mkdir(parents=True)

        config = KanbanConfig.load(config_path)
        service = KanbanService(config, tmp_path)

        return {"tmp_path": tmp_path, "config": config, "service": service}

    def test_hypothesis_routes_to_research(self, multiboard_hdd_setup):
        """Hypothesis should be created in research/hypotheses/, not kanban-work/."""
        from yurtle_kanban.models import WorkItemType

        service = multiboard_hdd_setup["service"]
        tmp_path = multiboard_hdd_setup["tmp_path"]

        item = service.create_item(
            item_type=WorkItemType.HYPOTHESIS,
            title="V12 improves accuracy",
            item_id="H130.1",
        )

        assert "research/hypotheses/" in str(item.file_path)
        assert "kanban-work" not in str(item.file_path)
        assert item.file_path.exists()

    def test_experiment_routes_to_research(self, multiboard_hdd_setup):
        """Experiment should be created in research/experiments/."""
        from yurtle_kanban.models import WorkItemType

        service = multiboard_hdd_setup["service"]

        item = service.create_item(
            item_type=WorkItemType.EXPERIMENT,
            title="V12 accuracy test",
            item_id="EXPR-130",
        )

        assert "research/experiments/" in str(item.file_path)
        assert "kanban-work" not in str(item.file_path)

    def test_paper_routes_to_research(self, multiboard_hdd_setup):
        """Paper should be created in research/papers/."""
        from yurtle_kanban.models import WorkItemType

        service = multiboard_hdd_setup["service"]

        item = service.create_item(
            item_type=WorkItemType.PAPER,
            title="NuSy Brain Architecture",
            item_id="PAPER-130",
        )

        assert "research/papers/" in str(item.file_path)

    def test_literature_routes_to_research(self, multiboard_hdd_setup):
        """Literature should be created in research/literature/."""
        from yurtle_kanban.models import WorkItemType

        service = multiboard_hdd_setup["service"]

        item = service.create_item(
            item_type=WorkItemType.LITERATURE,
            title="Transfer learning survey",
            item_id="LIT-001",
        )

        assert "research/literature/" in str(item.file_path)

    def test_measure_routes_to_research(self, multiboard_hdd_setup):
        """Measure should be created in research/measures/."""
        from yurtle_kanban.models import WorkItemType

        service = multiboard_hdd_setup["service"]

        item = service.create_item(
            item_type=WorkItemType.MEASURE,
            title="Reasoning Accuracy",
            item_id="M-001",
        )

        assert "research/measures/" in str(item.file_path)

    def test_idea_routes_to_research(self, multiboard_hdd_setup):
        """Idea should be created in research/ideas/."""
        from yurtle_kanban.models import WorkItemType

        service = multiboard_hdd_setup["service"]

        item = service.create_item(
            item_type=WorkItemType.IDEA,
            title="Explore transfer learning",
            item_id="IDEA-R-001",
        )

        assert "research/ideas/" in str(item.file_path)

    def test_expedition_still_routes_to_kanban_work(self, multiboard_hdd_setup):
        """Nautical types should still route to kanban-work/, not research/."""
        from yurtle_kanban.models import WorkItemType

        service = multiboard_hdd_setup["service"]

        item = service.create_item(
            item_type=WorkItemType.EXPEDITION,
            title="Test expedition",
            item_id="EXP-999",
        )

        assert "kanban-work" in str(item.file_path)
        assert "research" not in str(item.file_path)


class TestBoardConfigScanPaths:
    """Tests for BoardConfig scan_paths parsing (fix for dropped scan_paths)."""

    def test_from_dict_parses_scan_paths(self):
        """scan_paths should be preserved when loading from dict."""
        data = {
            "name": "research",
            "preset": "hdd",
            "path": "research/",
            "scan_paths": [
                "research/hypotheses/",
                "research/experiments/",
            ],
        }
        board = BoardConfig.from_dict(data)
        assert board.scan_paths == [
            "research/hypotheses/",
            "research/experiments/",
        ]

    def test_from_dict_defaults_empty_scan_paths(self):
        """Missing scan_paths should default to empty list."""
        board = BoardConfig.from_dict({"name": "dev"})
        assert board.scan_paths == []

    def test_to_dict_includes_scan_paths(self):
        """scan_paths should be serialized when present."""
        board = BoardConfig(
            name="research",
            preset="hdd",
            path="research/",
            scan_paths=["research/hypotheses/", "research/experiments/"],
        )
        data = board.to_dict()
        assert data["scan_paths"] == [
            "research/hypotheses/",
            "research/experiments/",
        ]

    def test_to_dict_omits_empty_scan_paths(self):
        """Empty scan_paths should not appear in serialized form."""
        board = BoardConfig(name="dev", path="work/")
        data = board.to_dict()
        assert "scan_paths" not in data

    def test_v2_load_aggregates_scan_paths(self, tmp_path):
        """_load_v2 should populate PathConfig.scan_paths from all boards."""
        config_path = tmp_path / ".kanban" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("""
version: "2.0"
boards:
  - name: development
    preset: nautical
    path: kanban-work/
    scan_paths:
      - "kanban-work/expeditions/"
      - "kanban-work/chores/"
  - name: research
    preset: hdd
    path: research/
    scan_paths:
      - "research/hypotheses/"
      - "research/experiments/"
default_board: development
""")
        config = KanbanConfig.load(config_path)
        assert len(config.paths.scan_paths) == 4
        assert "kanban-work/expeditions/" in config.paths.scan_paths
        assert "research/hypotheses/" in config.paths.scan_paths

    def test_v2_save_load_roundtrip_with_scan_paths(self, tmp_path):
        """scan_paths should survive a save+load roundtrip."""
        config = KanbanConfig(
            version=CONFIG_VERSION_MULTI,
            boards=[
                BoardConfig(
                    name="dev",
                    preset="nautical",
                    path="work/",
                    scan_paths=["work/features/", "work/bugs/"],
                ),
            ],
        )
        config_path = tmp_path / ".kanban" / "config.yaml"
        config.save(config_path)

        loaded = KanbanConfig.load(config_path)
        assert loaded.boards[0].scan_paths == ["work/features/", "work/bugs/"]


class TestIrregularPluralRouting:
    """Tests for scan_path keyword matching with irregular plurals."""

    def test_hypothesis_matches_hypotheses_scan_path(self, tmp_path):
        """hypothesis type should match 'hypotheses' in scan_paths."""
        from yurtle_kanban.models import WorkItemType

        config = KanbanConfig(
            theme="nonexistent",
            paths=PathConfig(
                root="work/",
                scan_paths=["research/hypotheses/"],
            ),
        )
        (tmp_path / "research" / "hypotheses").mkdir(parents=True)
        svc = KanbanService(config, tmp_path)
        path = svc._get_type_directory(WorkItemType.HYPOTHESIS)
        assert "hypotheses" in str(path)

    def test_literature_matches_literature_scan_path(self, tmp_path):
        """literature type should match 'literature' in scan_paths."""
        from yurtle_kanban.models import WorkItemType

        config = KanbanConfig(
            theme="nonexistent",
            paths=PathConfig(
                root="work/",
                scan_paths=["research/literature/"],
            ),
        )
        (tmp_path / "research" / "literature").mkdir(parents=True)
        svc = KanbanService(config, tmp_path)
        path = svc._get_type_directory(WorkItemType.LITERATURE)
        assert "literature" in str(path)

    def test_experiment_still_matches_with_regular_plural(self, tmp_path):
        """Regular plurals (experiment→experiments) should still work."""
        from yurtle_kanban.models import WorkItemType

        config = KanbanConfig(
            theme="nonexistent",
            paths=PathConfig(
                root="work/",
                scan_paths=["research/experiments/"],
            ),
        )
        (tmp_path / "research" / "experiments").mkdir(parents=True)
        svc = KanbanService(config, tmp_path)
        path = svc._get_type_directory(WorkItemType.EXPERIMENT)
        assert "experiments" in str(path)
