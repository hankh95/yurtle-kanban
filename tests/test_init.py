"""Tests for the init command scaffolding (Issue #7)."""

import yaml
from pathlib import Path
from click.testing import CliRunner

from yurtle_kanban.cli import main


class TestInitScaffolding:
    """Init should scaffold directories and templates from the theme."""

    def test_software_theme_creates_all_directories(self, tmp_path, monkeypatch):
        """Software theme should create 6 type directories."""
        monkeypatch.chdir(tmp_path)
        # Init a git repo so the CLI doesn't complain
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        runner = CliRunner()
        result = runner.invoke(main, ["init", "--theme", "software"])

        assert result.exit_code == 0, result.output

        expected_dirs = [
            "kanban-work/features",
            "kanban-work/bugs",
            "kanban-work/epics",
            "kanban-work/issues",
            "kanban-work/tasks",
            "kanban-work/ideas",
        ]
        for d in expected_dirs:
            assert (tmp_path / d).is_dir(), f"Missing directory: {d}"

    def test_nautical_theme_creates_all_directories(self, tmp_path, monkeypatch):
        """Nautical theme should create 5 type directories."""
        monkeypatch.chdir(tmp_path)
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        runner = CliRunner()
        result = runner.invoke(main, ["init", "--theme", "nautical"])

        assert result.exit_code == 0, result.output

        expected_dirs = [
            "kanban-work/expeditions",
            "kanban-work/voyages",
            "kanban-work/chores",
            "kanban-work/hazards",
            "kanban-work/signals",
        ]
        for d in expected_dirs:
            assert (tmp_path / d).is_dir(), f"Missing directory: {d}"

    def test_templates_created_in_each_directory(self, tmp_path, monkeypatch):
        """Each directory should get a _TEMPLATE.md file."""
        monkeypatch.chdir(tmp_path)
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        runner = CliRunner()
        runner.invoke(main, ["init", "--theme", "software"])

        for d in ["features", "bugs", "epics", "issues", "tasks", "ideas"]:
            template = tmp_path / "kanban-work" / d / "_TEMPLATE.md"
            assert template.exists(), f"Missing template: {template}"

    def test_template_has_correct_prefix(self, tmp_path, monkeypatch):
        """Template frontmatter should use the correct ID prefix."""
        monkeypatch.chdir(tmp_path)
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        runner = CliRunner()
        runner.invoke(main, ["init", "--theme", "software"])

        template = (tmp_path / "kanban-work" / "features" / "_TEMPLATE.md").read_text()
        assert "FEAT-XXX" in template

        template = (tmp_path / "kanban-work" / "bugs" / "_TEMPLATE.md").read_text()
        assert "BUG-XXX" in template

    def test_nautical_template_has_correct_prefix(self, tmp_path, monkeypatch):
        """Nautical template should use EXP, VOY, etc."""
        monkeypatch.chdir(tmp_path)
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        runner = CliRunner()
        runner.invoke(main, ["init", "--theme", "nautical"])

        template = (tmp_path / "kanban-work" / "expeditions" / "_TEMPLATE.md").read_text()
        assert "EXP-XXX" in template

        template = (tmp_path / "kanban-work" / "signals" / "_TEMPLATE.md").read_text()
        assert "SIG-XXX" in template

    def test_config_yaml_has_scan_paths(self, tmp_path, monkeypatch):
        """Generated config should include scan_paths for all type dirs."""
        monkeypatch.chdir(tmp_path)
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        runner = CliRunner()
        runner.invoke(main, ["init", "--theme", "software"])

        config_text = (tmp_path / ".kanban" / "config.yaml").read_text()
        assert "kanban-work/features/" in config_text
        assert "kanban-work/bugs/" in config_text

    def test_config_yaml_has_ignore_templates(self, tmp_path, monkeypatch):
        """Config should ignore _TEMPLATE* files."""
        monkeypatch.chdir(tmp_path)
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        runner = CliRunner()
        runner.invoke(main, ["init", "--theme", "software"])

        config_text = (tmp_path / ".kanban" / "config.yaml").read_text()
        assert "_TEMPLATE" in config_text

    def test_flat_directory_structure(self, tmp_path, monkeypatch):
        """All directories should be flat (no nesting like idea-intake/ideas-queue)."""
        monkeypatch.chdir(tmp_path)
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        runner = CliRunner()
        runner.invoke(main, ["init", "--theme", "software"])

        # Check that ideas/ is a flat directory, not nested
        ideas_dir = tmp_path / "kanban-work" / "ideas"
        assert ideas_dir.is_dir()
        # Should NOT have any nested subdirectories (only _TEMPLATE.md)
        subdirs = [p for p in ideas_dir.iterdir() if p.is_dir()]
        assert len(subdirs) == 0, f"Unexpected nested dirs in ideas/: {subdirs}"

    def test_template_sections_match_type(self, tmp_path, monkeypatch):
        """Bug templates should have 'Steps to Reproduce', expeditions 'Plan', etc."""
        monkeypatch.chdir(tmp_path)
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

        runner = CliRunner()
        runner.invoke(main, ["init", "--theme", "software"])

        bug_template = (tmp_path / "kanban-work" / "bugs" / "_TEMPLATE.md").read_text()
        assert "## Steps to Reproduce" in bug_template
        assert "## Expected Behavior" in bug_template

        feat_template = (tmp_path / "kanban-work" / "features" / "_TEMPLATE.md").read_text()
        assert "## Goal" in feat_template
        assert "## Acceptance Criteria" in feat_template
