"""Tests for KanbanService — ID allocation and item creation."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from yurtle_kanban.config import KanbanConfig, PathConfig
from yurtle_kanban.models import WorkItemType
from yurtle_kanban.service import KanbanService


@pytest.fixture
def temp_repo(tmp_path):
    """Create a minimal git repo with kanban config."""
    # Init git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    # Create kanban dirs
    (tmp_path / ".kanban").mkdir()
    (tmp_path / "kanban-work" / "expeditions").mkdir(parents=True)
    (tmp_path / "kanban-work" / "voyages").mkdir(parents=True)
    (tmp_path / "kanban-work" / "signals").mkdir(parents=True)
    (tmp_path / "kanban-work" / "features").mkdir(parents=True)
    (tmp_path / "kanban-work" / "bugs").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def nautical_config(temp_repo):
    """Config with nautical theme and scan_paths."""
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
    config.save(temp_repo / ".kanban" / "config.yaml")
    return config


@pytest.fixture
def software_config(temp_repo):
    """Config with software theme."""
    config = KanbanConfig(
        theme="software",
        paths=PathConfig(
            root="kanban-work/",
            scan_paths=[
                "kanban-work/features/",
                "kanban-work/bugs/",
            ],
        ),
    )
    config.save(temp_repo / ".kanban" / "config.yaml")
    return config


class TestNextIdIncrement:
    """Bug #8: next-id must increment for new prefixes."""

    def test_next_id_increments_without_files(self, temp_repo, nautical_config):
        """Repeated next-id calls should return incrementing numbers."""
        svc = KanbanService(nautical_config, temp_repo)

        result1 = svc.allocate_next_id("EXP", sync_remote=False, commit_allocation=True)
        assert result1["number"] == 1
        assert result1["id"] == "EXP-001"

        result2 = svc.allocate_next_id("EXP", sync_remote=False, commit_allocation=True)
        assert result2["number"] == 2
        assert result2["id"] == "EXP-002"

        result3 = svc.allocate_next_id("EXP", sync_remote=False, commit_allocation=True)
        assert result3["number"] == 3
        assert result3["id"] == "EXP-003"

    def test_next_id_increments_new_prefix(self, temp_repo, nautical_config):
        """A brand-new prefix with no files should still increment."""
        svc = KanbanService(nautical_config, temp_repo)

        r1 = svc.allocate_next_id("SIG", sync_remote=False, commit_allocation=True)
        r2 = svc.allocate_next_id("SIG", sync_remote=False, commit_allocation=True)

        assert r1["id"] == "SIG-001"
        assert r2["id"] == "SIG-002"

    def test_next_id_respects_existing_files(self, temp_repo, nautical_config):
        """If EXP-005 already exists on disk, next should be EXP-006."""
        # Create a file on disk
        exp_dir = temp_repo / "kanban-work" / "expeditions"
        (exp_dir / "EXP-005-Some-Title.md").write_text(
            "---\nid: EXP-005\ntitle: Existing\nstatus: backlog\n---\n"
        )

        svc = KanbanService(nautical_config, temp_repo)
        result = svc.allocate_next_id("EXP", sync_remote=False, commit_allocation=True)

        assert result["number"] == 6
        assert result["id"] == "EXP-006"

    def test_next_id_reads_allocations_file(self, temp_repo, nautical_config):
        """_get_next_id_number should read from _ID_ALLOCATIONS.json."""
        # Pre-populate allocations file
        lock_file = temp_repo / ".kanban" / "_ID_ALLOCATIONS.json"
        lock_file.write_text(json.dumps([
            {"id": "FEAT-001", "prefix": "FEAT", "number": 1},
            {"id": "FEAT-002", "prefix": "FEAT", "number": 2},
            {"id": "FEAT-003", "prefix": "FEAT", "number": 3},
        ]))

        svc = KanbanService(nautical_config, temp_repo)
        next_num = svc._get_next_id_number("FEAT")

        assert next_num == 4

    def test_next_id_uses_max_across_sources(self, temp_repo, nautical_config):
        """Should use max of allocations file AND filesystem."""
        # Allocations file says EXP-003
        lock_file = temp_repo / ".kanban" / "_ID_ALLOCATIONS.json"
        lock_file.write_text(json.dumps([
            {"id": "EXP-003", "prefix": "EXP", "number": 3},
        ]))

        # But filesystem has EXP-010
        exp_dir = temp_repo / "kanban-work" / "expeditions"
        (exp_dir / "EXP-010-Big-One.md").write_text(
            "---\nid: EXP-010\ntitle: Big\nstatus: backlog\n---\n"
        )

        svc = KanbanService(nautical_config, temp_repo)
        next_num = svc._get_next_id_number("EXP")

        assert next_num == 11  # max(3, 10) + 1


class TestCreateItemPlacement:
    """Bug #9: create should place files in type-specific directories."""

    def test_create_expedition_goes_to_expeditions_dir(self, temp_repo, nautical_config):
        """Expedition files should land in kanban-work/expeditions/."""
        svc = KanbanService(nautical_config, temp_repo)
        item = svc.create_item(WorkItemType.EXPEDITION, "Test Expedition")

        assert "kanban-work/expeditions/" in str(item.file_path)
        assert item.file_path.exists()
        assert item.id == "EXP-001"

    def test_create_signal_goes_to_signals_dir(self, temp_repo, nautical_config):
        """Signal files should land in kanban-work/signals/."""
        svc = KanbanService(nautical_config, temp_repo)
        item = svc.create_item(WorkItemType.SIGNAL, "New Idea")

        assert "kanban-work/signals/" in str(item.file_path)
        assert item.file_path.exists()

    def test_create_feature_goes_to_features_dir(self, temp_repo, software_config):
        """Feature files should land in kanban-work/features/."""
        svc = KanbanService(software_config, temp_repo)
        item = svc.create_item(WorkItemType.FEATURE, "Dark Mode")

        assert "kanban-work/features/" in str(item.file_path)
        assert item.file_path.exists()

    def test_create_includes_title_slug_in_filename(self, temp_repo, nautical_config):
        """Filename should include a title slug."""
        svc = KanbanService(nautical_config, temp_repo)
        item = svc.create_item(WorkItemType.EXPEDITION, "Fix The Bug")

        assert "Fix-The-Bug" in item.file_path.name

    def test_create_multiple_items_get_unique_ids(self, temp_repo, nautical_config):
        """Creating multiple items should yield unique IDs."""
        svc = KanbanService(nautical_config, temp_repo)

        item1 = svc.create_item(WorkItemType.SIGNAL, "First")
        item2 = svc.create_item(WorkItemType.SIGNAL, "Second")
        item3 = svc.create_item(WorkItemType.SIGNAL, "Third")

        assert item1.id == "SIG-001"
        assert item2.id == "SIG-002"
        assert item3.id == "SIG-003"
        assert item1.file_path != item2.file_path
        assert item2.file_path != item3.file_path


class TestCreateItemAndPush:
    """Test atomic create + push flow."""

    @pytest.fixture
    def repo_with_remote(self, tmp_path):
        """Create a git repo with a local 'remote' for push tests."""
        import subprocess

        # Create a bare repo to act as remote
        remote_path = tmp_path / "remote.git"
        remote_path.mkdir()
        subprocess.run(["git", "init", "--bare"], cwd=remote_path, capture_output=True, check=True)

        # Create working repo
        work_path = tmp_path / "work"
        work_path.mkdir()
        subprocess.run(["git", "init"], cwd=work_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=work_path, capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=work_path, capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote_path)],
            cwd=work_path, capture_output=True, check=True,
        )

        # Create kanban dirs and initial commit
        (work_path / ".kanban").mkdir()
        (work_path / "kanban-work" / "expeditions").mkdir(parents=True)
        (work_path / "kanban-work" / "signals").mkdir(parents=True)
        (work_path / ".gitkeep").write_text("")
        subprocess.run(["git", "add", "."], cwd=work_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=work_path, capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=work_path, capture_output=True, check=True,
        )

        return work_path

    def test_atomic_create_returns_success(self, repo_with_remote, nautical_config):
        """Atomic create should return success with item details."""
        nautical_config.save(repo_with_remote / ".kanban" / "config.yaml")
        svc = KanbanService(nautical_config, repo_with_remote)

        result = svc.create_item_and_push(
            item_type=WorkItemType.EXPEDITION,
            title="Test Atomic",
        )

        assert result["success"] is True
        assert result["id"] == "EXP-001"
        assert result["item"] is not None
        assert result["item"].file_path.exists()

    def test_atomic_create_writes_allocation(self, repo_with_remote, nautical_config):
        """Atomic create should update _ID_ALLOCATIONS.json."""
        nautical_config.save(repo_with_remote / ".kanban" / "config.yaml")
        svc = KanbanService(nautical_config, repo_with_remote)

        svc.create_item_and_push(
            item_type=WorkItemType.EXPEDITION,
            title="Test Alloc",
        )

        alloc_file = repo_with_remote / ".kanban" / "_ID_ALLOCATIONS.json"
        assert alloc_file.exists()
        allocations = json.loads(alloc_file.read_text())
        assert len(allocations) == 1
        assert allocations[0]["id"] == "EXP-001"

    def test_atomic_create_pushes_to_remote(self, repo_with_remote, nautical_config):
        """Atomic create should push to the remote."""
        import subprocess

        nautical_config.save(repo_with_remote / ".kanban" / "config.yaml")
        svc = KanbanService(nautical_config, repo_with_remote)

        svc.create_item_and_push(
            item_type=WorkItemType.SIGNAL,
            title="Pushed Signal",
        )

        # Check remote has the commit
        log = subprocess.run(
            ["git", "log", "--oneline", "origin/main"],
            cwd=repo_with_remote,
            capture_output=True,
            text=True,
        )
        assert "SIG-001" in log.stdout

    def test_atomic_create_sequential_ids(self, repo_with_remote, nautical_config):
        """Multiple atomic creates should get sequential IDs."""
        nautical_config.save(repo_with_remote / ".kanban" / "config.yaml")
        svc = KanbanService(nautical_config, repo_with_remote)

        r1 = svc.create_item_and_push(WorkItemType.EXPEDITION, "First")
        r2 = svc.create_item_and_push(WorkItemType.EXPEDITION, "Second")

        assert r1["id"] == "EXP-001"
        assert r2["id"] == "EXP-002"

    def test_atomic_create_places_file_correctly(self, repo_with_remote, nautical_config):
        """File should go in the theme-defined directory with slug."""
        nautical_config.save(repo_with_remote / ".kanban" / "config.yaml")
        svc = KanbanService(nautical_config, repo_with_remote)

        result = svc.create_item_and_push(
            WorkItemType.EXPEDITION,
            "Fix The Bug",
            priority="high",
        )

        item = result["item"]
        assert "kanban-work/expeditions/" in str(item.file_path)
        assert "Fix-The-Bug" in item.file_path.name


class TestSlugify:
    """Test the title slugification."""

    def test_basic_slug(self):
        assert KanbanService._slugify("Fix The Bug") == "Fix-The-Bug"

    def test_special_chars_removed(self):
        assert KanbanService._slugify("Add feature: auth!") == "Add-feature-auth"

    def test_long_title_truncated(self):
        slug = KanbanService._slugify("A" * 100)
        assert len(slug) <= 50

    def test_empty_title(self):
        assert KanbanService._slugify("") == ""


class TestGetTypeDirectory:
    """Test type-to-directory resolution."""

    def test_theme_path_takes_priority(self, temp_repo, nautical_config):
        """Theme-defined path should be used first."""
        svc = KanbanService(nautical_config, temp_repo)
        path = svc._get_type_directory(WorkItemType.EXPEDITION)

        assert path == temp_repo / "kanban-work/expeditions/"

    def test_scan_path_fallback(self, temp_repo):
        """If no theme path, scan_paths keyword match is used."""
        config = KanbanConfig(
            theme="nautical",
            paths=PathConfig(
                root="kanban-work/",
                scan_paths=["kanban-work/voyages/"],
            ),
        )
        # Clear the theme path for voyages to test scan_path fallback
        svc = KanbanService(config, temp_repo)
        # Even without explicit path in theme, scan_paths should match "voyages"
        path = svc._get_type_directory(WorkItemType.VOYAGE)
        assert "voyages" in str(path)

    def test_root_fallback(self, temp_repo):
        """If nothing matches, fall back to root."""
        config = KanbanConfig(
            theme="nonexistent",  # No theme loaded → no theme paths
            paths=PathConfig(root="work/", scan_paths=[]),
        )
        svc = KanbanService(config, temp_repo)
        path = svc._get_type_directory(WorkItemType.FEATURE)

        assert path == temp_repo / "work/"
