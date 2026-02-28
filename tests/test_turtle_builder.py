"""Tests for TurtleBlockBuilder — generates Turtle knowledge blocks for HDD items."""

import pytest

from yurtle_kanban.turtle_builder import TurtleBlockBuilder, _format_uri_list


@pytest.fixture
def builder():
    return TurtleBlockBuilder()


# ---------------------------------------------------------------------------
# _format_uri_list
# ---------------------------------------------------------------------------


class TestFormatUriList:
    def test_single_string(self):
        assert _format_uri_list("measure", "M-007") == "measure:M-007"

    def test_list_of_values(self):
        result = _format_uri_list("measure", ["M-007", "M-025"])
        assert result == "measure:M-007, measure:M-025"

    def test_single_element_list(self):
        assert _format_uri_list("lit", ["LIT-001"]) == "lit:LIT-001"


# ---------------------------------------------------------------------------
# Idea
# ---------------------------------------------------------------------------


class TestBuildIdea:
    def test_basic(self, builder):
        block = builder.build("idea", {"id": "IDEA-R-010", "title": "Test idea"})
        assert "```turtle" in block
        assert "```" in block
        assert '<#IDEA-R-010> a idea:Idea' in block
        assert 'rdfs:label "Test idea"' in block
        assert "@prefix idea:" in block
        assert "@prefix rdfs:" in block


# ---------------------------------------------------------------------------
# Literature
# ---------------------------------------------------------------------------


class TestBuildLiterature:
    def test_basic(self, builder):
        block = builder.build("literature", {"id": "LIT-001", "title": "Survey"})
        assert '<#LIT-001> a lit:Literature' in block
        assert 'rdfs:label "Survey"' in block
        assert "lit:explores" not in block

    def test_with_source_idea(self, builder):
        block = builder.build("literature", {
            "id": "LIT-001",
            "title": "Survey",
            "source_idea": "IDEA-R-010",
        })
        assert "lit:explores idea:IDEA-R-010" in block
        assert "@prefix idea:" in block


# ---------------------------------------------------------------------------
# Paper
# ---------------------------------------------------------------------------


class TestBuildPaper:
    def test_basic(self, builder):
        block = builder.build("paper", {"id": "PAPER-130", "title": "Brain Arch"})
        assert '<#PAPER-130> a paper:Paper' in block
        assert 'rdfs:label "Brain Arch"' in block


# ---------------------------------------------------------------------------
# Hypothesis
# ---------------------------------------------------------------------------


class TestBuildHypothesis:
    def test_basic_with_paper(self, builder):
        block = builder.build("hypothesis", {
            "id": "H130.1",
            "title": "Accuracy improves",
            "paper": "130",
        })
        assert '<#H130.1> a hyp:Hypothesis' in block
        assert 'hyp:paper paper:PAPER-130' in block
        assert "@prefix paper:" in block

    def test_with_target(self, builder):
        block = builder.build("hypothesis", {
            "id": "H130.1",
            "title": "Accuracy improves",
            "paper": "130",
            "target": ">=85%",
        })
        assert 'hyp:target ">=85%"' in block

    def test_with_source_idea(self, builder):
        block = builder.build("hypothesis", {
            "id": "H130.1",
            "title": "Test",
            "paper": "130",
            "source_idea": "IDEA-R-010",
        })
        assert "hyp:sourceIdea idea:IDEA-R-010" in block
        assert "@prefix idea:" in block

    def test_with_measures(self, builder):
        block = builder.build("hypothesis", {
            "id": "H130.1",
            "title": "Test",
            "paper": "130",
            "measures": ["M-007", "M-025"],
        })
        assert "hyp:measuredBy measure:M-007, measure:M-025" in block
        assert "@prefix measure:" in block

    def test_with_literature(self, builder):
        block = builder.build("hypothesis", {
            "id": "H130.1",
            "title": "Test",
            "paper": "130",
            "literature": ["LIT-001", "LIT-003"],
        })
        assert "hyp:informedBy lit:LIT-001, lit:LIT-003" in block
        assert "@prefix lit:" in block

    def test_all_optional_fields(self, builder):
        block = builder.build("hypothesis", {
            "id": "H130.1",
            "title": "Full hypothesis",
            "paper": "130",
            "target": ">=85%",
            "source_idea": "IDEA-R-010",
            "measures": ["M-007"],
            "literature": ["LIT-001"],
        })
        assert "hyp:paper" in block
        assert "hyp:target" in block
        assert "hyp:sourceIdea" in block
        assert "hyp:measuredBy" in block
        assert "hyp:informedBy" in block


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------


class TestBuildExperiment:
    def test_basic(self, builder):
        block = builder.build("experiment", {
            "id": "EXPR-130",
            "title": "V12 accuracy test",
            "paper": "130",
            "hypothesis_id": "H130.1",
        })
        assert '<#EXPR-130> a expr:Experiment' in block
        assert 'expr:paper paper:PAPER-130' in block
        assert 'expr:hypothesis hyp:H130.1' in block

    def test_with_measures(self, builder):
        block = builder.build("experiment", {
            "id": "EXPR-130",
            "title": "Test",
            "paper": "130",
            "hypothesis_id": "H130.1",
            "measures": ["M-007", "M-025"],
        })
        assert "expr:measure measure:M-007, measure:M-025" in block


# ---------------------------------------------------------------------------
# Measure
# ---------------------------------------------------------------------------


class TestBuildMeasure:
    def test_basic(self, builder):
        block = builder.build("measure", {
            "id": "M-042",
            "title": "Response Latency",
            "unit": "ms",
            "category": "performance",
        })
        assert '<#M-042> a measure:Measure' in block
        assert 'measure:unit "ms"' in block
        assert 'measure:category "performance"' in block


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_unknown_type_returns_empty(self, builder):
        assert builder.build("unknown_type", {"id": "X"}) == ""

    def test_title_with_quotes_escaped(self, builder):
        """Titles containing double quotes should be escaped in rdfs:label."""
        block = builder.build("idea", {
            "id": "IDEA-R-001",
            "title": 'Evaluating "Yurtle" Format',
        })
        assert r'rdfs:label "Evaluating \"Yurtle\" Format"' in block

    def test_title_with_backslash_escaped(self, builder):
        """Backslashes in titles should be escaped."""
        block = builder.build("idea", {
            "id": "IDEA-R-001",
            "title": r"Path C:\data\test",
        })
        assert r'rdfs:label "Path C:\\data\\test"' in block

    def test_only_needed_prefixes_included(self, builder):
        block = builder.build("idea", {"id": "IDEA-R-001", "title": "Test"})
        assert "@prefix idea:" in block
        assert "@prefix rdfs:" in block
        # Should NOT include unused prefixes
        assert "@prefix hyp:" not in block
        assert "@prefix expr:" not in block
        assert "@prefix measure:" not in block

    def test_block_starts_and_ends_with_fence(self, builder):
        block = builder.build("idea", {"id": "IDEA-R-001", "title": "Test"})
        lines = block.strip().split("\n")
        assert lines[0] == "```turtle"
        assert lines[-1] == "```"
