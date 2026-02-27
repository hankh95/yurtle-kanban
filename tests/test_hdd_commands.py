"""Tests for HDD (Hypothesis-Driven Development) CLI commands and TemplateEngine."""

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from yurtle_kanban.cli import main
from yurtle_kanban.config import KanbanConfig, PathConfig
from yurtle_kanban.models import WorkItemStatus, WorkItemType
from yurtle_kanban.service import KanbanService
from yurtle_kanban.template_engine import TemplateEngine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_repo(tmp_path):
    """Create a minimal git repo for HDD testing."""
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    # HDD directory structure
    (tmp_path / ".kanban").mkdir()
    (tmp_path / "research" / "ideas").mkdir(parents=True)
    (tmp_path / "research" / "literature").mkdir(parents=True)
    (tmp_path / "research" / "papers").mkdir(parents=True)
    (tmp_path / "research" / "hypotheses").mkdir(parents=True)
    (tmp_path / "research" / "experiments").mkdir(parents=True)
    (tmp_path / "research" / "measures").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def hdd_config(temp_repo):
    """Config with HDD theme."""
    config = KanbanConfig(
        theme="hdd",
        paths=PathConfig(
            root="research/",
            scan_paths=[
                "research/ideas/",
                "research/literature/",
                "research/papers/",
                "research/hypotheses/",
                "research/experiments/",
                "research/measures/",
            ],
        ),
    )
    config.save(temp_repo / ".kanban" / "config.yaml")
    return config


@pytest.fixture
def hdd_service(temp_repo, hdd_config):
    """KanbanService with HDD config."""
    return KanbanService(hdd_config, temp_repo)


@pytest.fixture
def templates_dir():
    """Get the real templates directory from the package."""
    pkg_dir = Path(__file__).parent.parent / "templates"
    if pkg_dir.exists():
        return pkg_dir
    pytest.skip("Templates directory not found")


@pytest.fixture
def engine(templates_dir):
    """TemplateEngine pointing to real templates."""
    return TemplateEngine(templates_dir)


@pytest.fixture
def runner(temp_repo, hdd_config, monkeypatch):
    """Click CLI test runner with cwd set to temp_repo.

    Clears the theme cache to avoid cross-test contamination.
    """
    from yurtle_kanban import config as config_mod

    config_mod._theme_cache.clear()
    monkeypatch.chdir(temp_repo)
    return CliRunner()


# ---------------------------------------------------------------------------
# TestTemplateEngine
# ---------------------------------------------------------------------------


class TestTemplateEngine:
    """Tests for TemplateEngine variable substitution."""

    def test_render_idea_template(self, engine):
        """Idea template should substitute id, title, and date."""
        content = engine.render("hdd", "idea", {
            "id": "IDEA-R-001",
            "title": "Test Idea",
            "date": "2026-02-27",
        })
        assert "id: IDEA-R-001" in content
        assert 'title: "Test Idea"' in content
        assert "created: 2026-02-27" in content
        assert "# Test Idea" in content

    def test_render_literature_with_source_idea(self, engine):
        """Literature template should link to source idea."""
        content = engine.render("hdd", "literature", {
            "id": "LIT-001",
            "title": "Survey of Methods",
            "source_idea": "IDEA-R-003",
        })
        assert "id: LIT-001" in content
        assert "source_idea: IDEA-R-003" in content

    def test_render_hypothesis_with_paper(self, engine):
        """Hypothesis template should substitute paper and n."""
        content = engine.render("hdd", "hypothesis", {
            "id": "H130.1",
            "title": "V12 improves accuracy",
            "paper": "130",
            "n": "1",
        })
        assert "id: H130.1" in content
        assert "paper: PAPER-130" in content
        # Body references should be substituted
        assert "EXPR-130" in content  # Experiment Design table

    def test_render_paper_template(self, engine):
        """Paper template should substitute number."""
        content = engine.render("hdd", "paper", {
            "id": "PAPER-130",
            "title": "NuSy Brain Architecture",
            "paper_num": "130",
        })
        assert "id: PAPER-130" in content
        assert 'title: "NuSy Brain Architecture"' in content

    def test_render_measure_template(self, engine):
        """Measure template should substitute unit and category."""
        content = engine.render("hdd", "measure", {
            "id": "M-042",
            "title": "Reasoning Accuracy",
            "unit": "percent",
            "category": "accuracy",
        })
        assert "id: M-042" in content
        assert 'title: "Reasoning Accuracy"' in content

    def test_render_experiment_template(self, engine):
        """Experiment template should substitute paper, hypothesis, and title."""
        content = engine.render("hdd", "experiment", {
            "id": "EXPR-130",
            "title": "V12 accuracy test",
            "paper": "130",
            "n": "1",
            "hypothesis_id": "H130.1",
        })
        assert "id: EXPR-130" in content
        assert "hypothesis: H130.1" in content

    def test_missing_template_raises(self, engine):
        """Non-existent template should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            engine.render("nonexistent", "foo", {"id": "X-1"})

    def test_date_auto_filled(self, engine):
        """Date should be auto-filled with today if not provided."""
        content = engine.render("hdd", "idea", {
            "id": "IDEA-R-001",
            "title": "Test",
        })
        assert "YYYY-MM-DD" not in content
        assert "created:" in content


# ---------------------------------------------------------------------------
# TestWorkItemTypeEnum
# ---------------------------------------------------------------------------


class TestHDDEnumTypes:
    """Verify HDD types exist in WorkItemType enum."""

    @pytest.mark.parametrize("type_str", [
        "literature", "paper", "hypothesis", "experiment", "measure",
    ])
    def test_hdd_type_from_string(self, type_str):
        """HDD types should parse from string."""
        result = WorkItemType.from_string(type_str)
        assert result.value == type_str

    def test_existing_types_unchanged(self):
        """Existing software/nautical types should still work."""
        assert WorkItemType.from_string("feature") == WorkItemType.FEATURE
        assert WorkItemType.from_string("expedition") == WorkItemType.EXPEDITION


# ---------------------------------------------------------------------------
# TestHDDIdeaCreate
# ---------------------------------------------------------------------------


class TestHDDIdeaCreate:
    """Tests for 'yurtle-kanban idea create'."""

    def test_idea_create_research(self, runner, temp_repo, hdd_config):
        """Create a research idea with auto-allocated IDEA-R ID."""
        result = runner.invoke(main, ["idea", "create", "Test Idea"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "IDEA-R-001" in result.output

    def test_idea_create_feature(self, runner, temp_repo, hdd_config):
        """Create a feature idea with IDEA-F prefix."""
        result = runner.invoke(
            main, ["idea", "create", "Dashboard Widget", "--type", "feature"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        assert "IDEA-F-001" in result.output

    def test_idea_create_auto_increments(self, runner, temp_repo, hdd_config):
        """Second idea should get IDEA-R-002."""
        runner.invoke(main, ["idea", "create", "First Idea"], catch_exceptions=False)
        result = runner.invoke(main, ["idea", "create", "Second Idea"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "IDEA-R-002" in result.output

    def test_idea_file_uses_template(self, runner, temp_repo, hdd_config):
        """Created file should contain HDD template sections."""
        runner.invoke(main, ["idea", "create", "Template Test"], catch_exceptions=False)
        # Find the created file
        ideas_dir = temp_repo / "research" / "ideas"
        files = list(ideas_dir.glob("IDEA-R-001*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "## Observation" in content
        assert "## Prior Art Check" in content


# ---------------------------------------------------------------------------
# TestHDDLiteratureCreate
# ---------------------------------------------------------------------------


class TestHDDLiteratureCreate:
    """Tests for 'yurtle-kanban literature create'."""

    def test_literature_create(self, runner, temp_repo, hdd_config):
        """Create a literature review."""
        result = runner.invoke(
            main, ["literature", "create", "Transfer Learning Survey"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "LIT-001" in result.output

    def test_literature_with_idea_link(self, runner, temp_repo, hdd_config):
        """Literature should link to source idea."""
        runner.invoke(main, ["idea", "create", "Base Idea"], catch_exceptions=False)
        result = runner.invoke(
            main,
            ["literature", "create", "Related Survey", "--idea", "IDEA-R-001"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "LIT-001" in result.output
        # Check file content
        lit_dir = temp_repo / "research" / "literature"
        files = list(lit_dir.glob("LIT-001*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "source_idea: IDEA-R-001" in content


# ---------------------------------------------------------------------------
# TestHDDPaperCreate
# ---------------------------------------------------------------------------


class TestHDDPaperCreate:
    """Tests for 'yurtle-kanban paper create'."""

    def test_paper_create(self, runner, temp_repo, hdd_config):
        """Create a paper with user-provided number."""
        result = runner.invoke(
            main, ["paper", "create", "130", "NuSy Brain Architecture"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "PAPER-130" in result.output

    def test_paper_duplicate_rejected(self, runner, temp_repo, hdd_config):
        """Duplicate paper number should be rejected."""
        runner.invoke(
            main, ["paper", "create", "130", "First Paper"],
            catch_exceptions=False,
        )
        result = runner.invoke(
            main, ["paper", "create", "130", "Duplicate Paper"],
            catch_exceptions=False,
        )
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_paper_file_has_template_sections(self, runner, temp_repo, hdd_config):
        """Paper file should have standard paper sections."""
        runner.invoke(
            main, ["paper", "create", "131", "Test Paper"],
            catch_exceptions=False,
        )
        papers_dir = temp_repo / "research" / "papers"
        files = list(papers_dir.glob("PAPER-131*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "## Abstract" in content
        assert "## Methodology" in content


# ---------------------------------------------------------------------------
# TestHDDHypothesisCreate
# ---------------------------------------------------------------------------


class TestHDDHypothesisCreate:
    """Tests for 'yurtle-kanban hypothesis create'."""

    def test_hypothesis_create_with_auto_id(self, runner, temp_repo, hdd_config):
        """Hypothesis without --id should auto-allocate H{paper}.1."""
        result = runner.invoke(
            main,
            ["hypothesis", "create", "V12 improves accuracy", "--paper", "130"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "H130.1" in result.output

    def test_hypothesis_create_with_explicit_id(self, runner, temp_repo, hdd_config):
        """Hypothesis with --id should use the provided ID."""
        result = runner.invoke(
            main,
            ["hypothesis", "create", "Better recall", "--paper", "130", "--id", "H130.5"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "H130.5" in result.output

    def test_hypothesis_auto_increments(self, runner, temp_repo, hdd_config):
        """Second hypothesis for same paper should be H130.2."""
        runner.invoke(
            main,
            ["hypothesis", "create", "First hyp", "--paper", "130"],
            catch_exceptions=False,
        )
        result = runner.invoke(
            main,
            ["hypothesis", "create", "Second hyp", "--paper", "130"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "H130.2" in result.output

    def test_hypothesis_requires_paper(self, runner, temp_repo, hdd_config):
        """Hypothesis without --paper should fail."""
        result = runner.invoke(
            main,
            ["hypothesis", "create", "No paper given"],
        )
        assert result.exit_code != 0

    def test_hypothesis_duplicate_rejected(self, runner, temp_repo, hdd_config):
        """Duplicate hypothesis ID should be rejected."""
        runner.invoke(
            main,
            ["hypothesis", "create", "First", "--paper", "130", "--id", "H130.1"],
            catch_exceptions=False,
        )
        result = runner.invoke(
            main,
            ["hypothesis", "create", "Duplicate", "--paper", "130", "--id", "H130.1"],
            catch_exceptions=False,
        )
        assert result.exit_code != 0
        assert "already exists" in result.output


# ---------------------------------------------------------------------------
# TestHDDExperimentCreate
# ---------------------------------------------------------------------------


class TestHDDExperimentCreate:
    """Tests for 'yurtle-kanban experiment create'."""

    def test_experiment_create(self, runner, temp_repo, hdd_config):
        """Create an experiment."""
        result = runner.invoke(
            main,
            [
                "experiment", "create", "EXPR-130",
                "--hypothesis", "H130.1",
                "--title", "V12 accuracy test",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "EXPR-130" in result.output

    def test_experiment_auto_prefixes(self, runner, temp_repo, hdd_config):
        """Experiment ID without EXPR- prefix should be normalized."""
        result = runner.invoke(
            main,
            [
                "experiment", "create", "130",
                "--hypothesis", "H130.1",
                "--title", "Test experiment",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "EXPR-130" in result.output

    def test_experiment_requires_hypothesis(self, runner, temp_repo, hdd_config):
        """Experiment without --hypothesis should fail."""
        result = runner.invoke(
            main,
            ["experiment", "create", "EXPR-130", "--title", "No hyp"],
        )
        assert result.exit_code != 0

    def test_experiment_requires_title(self, runner, temp_repo, hdd_config):
        """Experiment without --title should fail."""
        result = runner.invoke(
            main,
            ["experiment", "create", "EXPR-130", "--hypothesis", "H130.1"],
        )
        assert result.exit_code != 0

    def test_experiment_file_links_hypothesis(self, runner, temp_repo, hdd_config):
        """Experiment file should reference the hypothesis."""
        runner.invoke(
            main,
            [
                "experiment", "create", "EXPR-130",
                "--hypothesis", "H130.1",
                "--title", "Linking test",
            ],
            catch_exceptions=False,
        )
        exp_dir = temp_repo / "research" / "experiments"
        files = list(exp_dir.glob("EXPR-130*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "hypothesis: H130.1" in content


# ---------------------------------------------------------------------------
# TestHDDMeasureCreate
# ---------------------------------------------------------------------------


class TestHDDMeasureCreate:
    """Tests for 'yurtle-kanban measure create'."""

    def test_measure_create_auto_id(self, runner, temp_repo, hdd_config):
        """Measure without --id should auto-allocate M-001."""
        result = runner.invoke(
            main,
            ["measure", "create", "Reasoning Accuracy", "--unit", "percent", "--category", "accuracy"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "M-001" in result.output

    def test_measure_create_explicit_id(self, runner, temp_repo, hdd_config):
        """Measure with --id should use provided ID."""
        result = runner.invoke(
            main,
            [
                "measure", "create", "Latency",
                "--unit", "ms", "--category", "performance",
                "--id", "M-042",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "M-042" in result.output

    def test_measure_auto_increments(self, runner, temp_repo, hdd_config):
        """Second measure should get M-002."""
        runner.invoke(
            main,
            ["measure", "create", "First", "--unit", "count", "--category", "test"],
            catch_exceptions=False,
        )
        result = runner.invoke(
            main,
            ["measure", "create", "Second", "--unit", "count", "--category", "test"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "M-002" in result.output

    def test_measure_requires_unit(self, runner, temp_repo, hdd_config):
        """Measure without --unit should fail."""
        result = runner.invoke(
            main,
            ["measure", "create", "No Unit", "--category", "test"],
        )
        assert result.exit_code != 0

    def test_measure_requires_category(self, runner, temp_repo, hdd_config):
        """Measure without --category should fail."""
        result = runner.invoke(
            main,
            ["measure", "create", "No Category", "--unit", "count"],
        )
        assert result.exit_code != 0

    def test_measure_duplicate_rejected(self, runner, temp_repo, hdd_config):
        """Duplicate measure ID should be rejected."""
        runner.invoke(
            main,
            [
                "measure", "create", "First",
                "--unit", "count", "--category", "test",
                "--id", "M-042",
            ],
            catch_exceptions=False,
        )
        result = runner.invoke(
            main,
            [
                "measure", "create", "Duplicate",
                "--unit", "count", "--category", "test",
                "--id", "M-042",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code != 0
        assert "already exists" in result.output


# ---------------------------------------------------------------------------
# TestMultiSegmentPrefix
# ---------------------------------------------------------------------------


class TestMultiSegmentPrefix:
    """Regression test: IDEA-R-003 → next should be IDEA-R-004."""

    def test_idea_r_prefix_increment(self, temp_repo, hdd_config):
        """_get_next_id_number should handle IDEA-R multi-segment prefix."""
        service = KanbanService(hdd_config, temp_repo)

        # Create a fake IDEA-R-003 file
        ideas_dir = temp_repo / "research" / "ideas"
        fake_file = ideas_dir / "IDEA-R-003-Some-Idea.md"
        fake_file.write_text(
            "---\nid: IDEA-R-003\ntitle: \"Test\"\ntype: idea\nstatus: draft\n"
            "created: 2026-01-01\npriority: medium\ntags: []\n---\n# Test\n"
        )

        # Re-scan
        service.scan()
        next_num = service._get_next_id_number("IDEA-R")
        assert next_num == 4, f"Expected 4, got {next_num}"

    def test_idea_f_prefix_independent(self, temp_repo, hdd_config):
        """IDEA-F numbering should be independent of IDEA-R."""
        service = KanbanService(hdd_config, temp_repo)

        # Create an IDEA-R file
        ideas_dir = temp_repo / "research" / "ideas"
        (ideas_dir / "IDEA-R-005-Research.md").write_text(
            "---\nid: IDEA-R-005\ntitle: \"R\"\ntype: idea\nstatus: draft\n"
            "created: 2026-01-01\npriority: medium\ntags: []\n---\n# R\n"
        )
        # Create an IDEA-F file
        (ideas_dir / "IDEA-F-002-Feature.md").write_text(
            "---\nid: IDEA-F-002\ntitle: \"F\"\ntype: idea\nstatus: draft\n"
            "created: 2026-01-01\npriority: medium\ntags: []\n---\n# F\n"
        )

        service.scan()
        assert service._get_next_id_number("IDEA-R") == 6
        assert service._get_next_id_number("IDEA-F") == 3


# ---------------------------------------------------------------------------
# TestHypothesisNumbering
# ---------------------------------------------------------------------------


class TestHypothesisNumbering:
    """Tests for get_next_hypothesis_number()."""

    def test_first_hypothesis_for_paper(self, temp_repo, hdd_config):
        """First hypothesis for a paper should be 1."""
        service = KanbanService(hdd_config, temp_repo)
        assert service.get_next_hypothesis_number("130") == 1

    def test_auto_increment_hypothesis(self, temp_repo, hdd_config):
        """Hypothesis numbering should increment based on existing items."""
        service = KanbanService(hdd_config, temp_repo)

        # Create H130.1 and H130.2
        hyp_dir = temp_repo / "research" / "hypotheses"
        for n in (1, 2):
            (hyp_dir / f"H130.{n}-test.md").write_text(
                f"---\nid: H130.{n}\ntitle: \"Test\"\ntype: hypothesis\nstatus: draft\n"
                f"created: 2026-01-01\npaper: PAPER-130\ntags: []\n---\n# Test\n"
            )

        service.scan()
        assert service.get_next_hypothesis_number("130") == 3

    def test_different_papers_independent(self, temp_repo, hdd_config):
        """Hypothesis numbering should be per-paper."""
        service = KanbanService(hdd_config, temp_repo)

        hyp_dir = temp_repo / "research" / "hypotheses"
        (hyp_dir / "H130.1-test.md").write_text(
            "---\nid: H130.1\ntitle: \"Test\"\ntype: hypothesis\nstatus: draft\n"
            "created: 2026-01-01\npaper: PAPER-130\ntags: []\n---\n# Test\n"
        )
        (hyp_dir / "H131.1-test.md").write_text(
            "---\nid: H131.1\ntitle: \"Test\"\ntype: hypothesis\nstatus: draft\n"
            "created: 2026-01-01\npaper: PAPER-131\ntags: []\n---\n# Test\n"
        )

        service.scan()
        assert service.get_next_hypothesis_number("130") == 2
        assert service.get_next_hypothesis_number("131") == 2
        assert service.get_next_hypothesis_number("132") == 1
