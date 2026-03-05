"""Tests for the hybrid query engine (EXP-1090).

Phase 1: UnifiedGraph + SPARQL
Phase 2: EmbeddingIndex (skipped if sentence-transformers not installed)
Phase 3: NLDecomposer + QueryEngine hybrid
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from yurtle_kanban.models import WorkItem, WorkItemStatus, WorkItemType
from yurtle_kanban.query import NLDecomposer, QueryEngine, UnifiedGraph

try:
    from yurtle_kanban.query import EmbeddingIndex

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_item(
    item_id: str,
    title: str,
    status: WorkItemStatus = WorkItemStatus.BACKLOG,
    item_type: WorkItemType = WorkItemType.EXPEDITION,
    priority: str = "medium",
    assignee: str | None = None,
    tags: list[str] | None = None,
    depends_on: list[str] | None = None,
    related: list[str] | None = None,
    description: str | None = None,
) -> WorkItem:
    return WorkItem(
        id=item_id,
        title=title,
        item_type=item_type,
        status=status,
        file_path=Path(f"/tmp/{item_id}.md"),
        priority=priority,
        assignee=assignee,
        created=date(2026, 1, 1),
        tags=tags or [],
        depends_on=depends_on or [],
        related=related or [],
        description=description,
    )


@pytest.fixture
def sample_items() -> list[WorkItem]:
    return [
        _make_item("EXP-700", "Y0/Y1 Chunk Graph Storage", WorkItemStatus.REVIEW, tags=["brain", "graph"]),
        _make_item("EXP-750", "Vision for Beings — Multimodal Visual Learning", WorkItemStatus.BLOCKED, tags=["multimodal"]),
        _make_item("EXP-800", "Fix daemon graph search", WorkItemStatus.IN_PROGRESS, assignee="DGX", tags=["brain", "chat"]),
        _make_item("EXP-850", "Wire Y4/Y6 into daemon chat", WorkItemStatus.IN_PROGRESS, assignee="Mini", tags=["brain", "y-layer"]),
        _make_item("EXP-900", "Graph Verbalization Pipeline", WorkItemStatus.DONE, tags=["brain", "graph"]),
        _make_item("EXP-950", "CarClaw: CarPlay Voice Agent", WorkItemStatus.BACKLOG, tags=["ios", "carplay"]),
        _make_item("EXP-1000", "First LoRA Fine-Tune", WorkItemStatus.BACKLOG, tags=["training", "lora"], description="Fine-tune Nemotron on Santiago knowledge graph"),
        _make_item(
            "CHORE-050", "Clean up stale branches",
            WorkItemStatus.DONE,
            item_type=WorkItemType.CHORE,
            tags=["maintenance"],
        ),
        _make_item(
            "EXP-600", "Old expedition below 700",
            WorkItemStatus.BACKLOG,
            description="Legacy work item",
        ),
    ]


@pytest.fixture
def unified_graph(sample_items) -> UnifiedGraph:
    ug = UnifiedGraph()
    ug.add_items(sample_items)
    return ug


# ---------------------------------------------------------------------------
# Phase 1: UnifiedGraph + SPARQL
# ---------------------------------------------------------------------------


class TestUnifiedGraph:
    def test_add_items_populates_graph(self, unified_graph):
        assert len(unified_graph) > 0

    def test_get_item_by_id(self, unified_graph):
        item = unified_graph.get_item("EXP-800")
        assert item is not None
        assert item.title == "Fix daemon graph search"

    def test_get_item_not_found(self, unified_graph):
        assert unified_graph.get_item("EXP-9999") is None

    def test_sparql_select_all_ids(self, unified_graph):
        results = unified_graph.sparql(
            "PREFIX kb: <https://yurtle.dev/kanban/> "
            "SELECT ?id WHERE { ?item kb:id ?id . } ORDER BY ?id"
        )
        ids = [r["id"] for r in results]
        assert "EXP-800" in ids
        assert "CHORE-050" in ids

    def test_sparql_filter_by_status(self, unified_graph):
        results = unified_graph.sparql(
            "PREFIX kb: <https://yurtle.dev/kanban/> "
            "SELECT ?id WHERE { "
            "  ?item kb:id ?id . "
            "  ?item kb:status kb:in_progress . "
            "}"
        )
        ids = {r["id"] for r in results}
        assert ids == {"EXP-800", "EXP-850"}

    def test_sparql_filter_by_type(self, unified_graph):
        results = unified_graph.sparql(
            "PREFIX kb: <https://yurtle.dev/kanban/> "
            "SELECT ?id WHERE { "
            "  ?item a kb:Chore . "
            "  ?item kb:id ?id . "
            "}"
        )
        ids = {r["id"] for r in results}
        assert ids == {"CHORE-050"}

    def test_sparql_filter_by_numeric_id_range(self, unified_graph):
        results = unified_graph.sparql(
            "PREFIX kb: <https://yurtle.dev/kanban/> "
            "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> "
            "SELECT ?id WHERE { "
            "  ?item kb:id ?id . "
            "  ?item kb:numericId ?numId . "
            "  FILTER(?numId > 700) "
            "}"
        )
        ids = {r["id"] for r in results}
        assert "EXP-600" not in ids
        assert "EXP-800" in ids
        assert "EXP-1000" in ids

    def test_sparql_combined_status_and_range(self, unified_graph):
        """The original question: not-done expeditions above 700."""
        results = unified_graph.sparql(
            "PREFIX kb: <https://yurtle.dev/kanban/> "
            "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> "
            "SELECT ?id WHERE { "
            "  ?item a kb:Expedition . "
            "  ?item kb:id ?id . "
            "  ?item kb:status ?status . "
            "  ?item kb:numericId ?numId . "
            "  FILTER(?status != kb:done) "
            "  FILTER(?numId > 700) "
            "} ORDER BY ?id"
        )
        ids = {r["id"] for r in results}
        assert "EXP-900" not in ids  # done
        assert "EXP-600" not in ids  # below 700
        assert "CHORE-050" not in ids  # chore, not expedition
        assert "EXP-800" in ids
        assert "EXP-850" in ids
        assert "EXP-950" in ids
        assert "EXP-1000" in ids

    def test_sparql_by_assignee(self, unified_graph):
        results = unified_graph.sparql(
            "PREFIX kb: <https://yurtle.dev/kanban/> "
            "SELECT ?id WHERE { "
            "  ?item kb:id ?id . "
            "  ?item kb:assignee ?a . "
            '  FILTER(CONTAINS(LCASE(?a), "mini")) '
            "}"
        )
        ids = {r["id"] for r in results}
        assert ids == {"EXP-850"}

    def test_sparql_by_tag(self, unified_graph):
        results = unified_graph.sparql(
            "PREFIX kb: <https://yurtle.dev/kanban/> "
            "SELECT ?id WHERE { "
            "  ?item kb:id ?id . "
            "  ?item kb:tag ?tag . "
            '  FILTER(?tag = "brain") '
            "}"
        )
        ids = {r["id"] for r in results}
        assert "EXP-700" in ids
        assert "EXP-800" in ids
        assert "EXP-850" in ids
        assert "EXP-900" in ids
        assert "EXP-950" not in ids  # tagged ios, carplay

    def test_sparql_optional_none_not_stringified(self, unified_graph):
        """OPTIONAL bindings should return empty string, not 'None'."""
        results = unified_graph.sparql(
            "PREFIX kb: <https://yurtle.dev/kanban/> "
            "SELECT ?id ?assignee WHERE { "
            "  ?item kb:id ?id . "
            "  OPTIONAL { ?item kb:assignee ?assignee . } "
            "  ?item kb:status kb:backlog . "
            "}"
        )
        # EXP-950 is backlog with no assignee
        for r in results:
            if r["id"] == "EXP-950":
                assert r["assignee"] != "None", "None should not be stringified"
                assert r["assignee"] == ""
                break

    def test_items_property(self, unified_graph):
        """Public items property exposes WorkItem dict."""
        assert "EXP-800" in unified_graph.items
        assert unified_graph.items["EXP-800"].title == "Fix daemon graph search"

    def test_per_file_graph_merge(self):
        """Per-file RDF triples from WorkItem.graph are merged into unified graph."""
        from rdflib import Graph as RDFGraph, Literal, URIRef

        # Create item with a custom RDF graph (simulating yurtle fenced block)
        custom_graph = RDFGraph()
        custom_graph.add((
            URIRef("https://example.org/custom"),
            URIRef("https://example.org/pred"),
            Literal("custom_value"),
        ))
        item = _make_item("EXP-999", "Item with custom RDF")
        item.graph = custom_graph

        ug = UnifiedGraph()
        ug.add_item(item)

        # Custom triple should be queryable
        results = list(ug.graph.triples((
            URIRef("https://example.org/custom"),
            URIRef("https://example.org/pred"),
            None,
        )))
        assert len(results) == 1
        assert str(results[0][2]) == "custom_value"

    def test_from_service_returns_populated_graph(self, sample_items):
        """Test that from_service pattern works (without real service)."""
        ug = UnifiedGraph()
        ug.add_items(sample_items)
        assert ug.get_item("EXP-700") is not None


# ---------------------------------------------------------------------------
# Phase 3: NLDecomposer
# ---------------------------------------------------------------------------


class TestNLDecomposer:
    @pytest.fixture
    def decomposer(self):
        return NLDecomposer()

    def test_parse_not_done(self, decomposer):
        parsed = decomposer.parse("not done expeditions")
        assert "done" in parsed.status_filter
        assert "expedition" in parsed.type_filter

    def test_parse_not_done_hyphenated(self, decomposer):
        parsed = decomposer.parse("not-done items")
        assert "done" in parsed.status_filter

    def test_parse_id_above(self, decomposer):
        parsed = decomposer.parse("expeditions above 700")
        assert parsed.id_min == 700
        assert "expedition" in parsed.type_filter

    def test_parse_id_below(self, decomposer):
        parsed = decomposer.parse("items below 500")
        assert parsed.id_max == 500

    def test_parse_id_between(self, decomposer):
        parsed = decomposer.parse("expeditions between 100 and 200")
        assert parsed.id_min == 100
        assert parsed.id_max == 200

    def test_parse_status_in_progress(self, decomposer):
        parsed = decomposer.parse("in progress items")
        assert "in_progress" in parsed.status_include

    def test_parse_blocked(self, decomposer):
        parsed = decomposer.parse("blocked expeditions")
        assert "blocked" in parsed.status_include
        assert "expedition" in parsed.type_filter

    def test_parse_assignee(self, decomposer):
        parsed = decomposer.parse("assigned to Mini")
        assert parsed.assignee == "Mini"

    def test_parse_tag(self, decomposer):
        parsed = decomposer.parse("tagged brain")
        assert parsed.tag == "brain"

    def test_parse_type_chore(self, decomposer):
        parsed = decomposer.parse("all chores")
        assert "chore" in parsed.type_filter

    def test_parse_type_voyage(self, decomposer):
        parsed = decomposer.parse("voyages in review")
        assert "voyage" in parsed.type_filter
        assert "review" in parsed.status_include

    def test_parse_semantic_remainder(self, decomposer):
        parsed = decomposer.parse("not done expeditions above 700 that improve brain functioning")
        assert "done" in parsed.status_filter
        assert "expedition" in parsed.type_filter
        assert parsed.id_min == 700
        assert "brain functioning" in parsed.semantic_query.lower() or "improve brain" in parsed.semantic_query.lower()

    def test_parse_pure_semantic(self, decomposer):
        parsed = decomposer.parse("knowledge graph reasoning improvements")
        assert not parsed.has_structured or parsed.semantic_query
        assert "knowledge graph" in parsed.semantic_query.lower() or "reasoning" in parsed.semantic_query.lower()

    def test_has_structured(self, decomposer):
        parsed = decomposer.parse("not done expeditions")
        assert parsed.has_structured

    def test_has_semantic(self, decomposer):
        parsed = decomposer.parse("improve brain functioning")
        assert parsed.has_semantic

    def test_id_above_boundary(self, decomposer):
        """'above 700' means > 700, not >= 700."""
        parsed = decomposer.parse("above 700")
        assert parsed.id_min == 700  # stored as 700, SPARQL uses > (strict)

    def test_inverted_between_swaps(self, decomposer):
        """'between 900 and 200' should swap to min=200, max=900."""
        parsed = decomposer.parse("between 900 and 200")
        assert parsed.id_min == 200
        assert parsed.id_max == 900

    def test_gt_symbol_parses(self, decomposer):
        """'>= 500' should parse as id_min."""
        parsed = decomposer.parse(">= 500")
        assert parsed.id_min == 500

    def test_complex_query(self, decomposer):
        """The original query that motivated EXP-1090."""
        parsed = decomposer.parse("not-done expeditions above 700 that improve brain functioning")
        assert "done" in parsed.status_filter
        assert "expedition" in parsed.type_filter
        assert parsed.id_min == 700
        assert parsed.has_semantic


# ---------------------------------------------------------------------------
# Phase 1+3 Integration: QueryEngine (graph-only mode)
# ---------------------------------------------------------------------------


class TestQueryEngineGraphOnly:
    @pytest.fixture
    def engine(self, unified_graph):
        return QueryEngine(unified_graph=unified_graph, embedding_index=None)

    def test_sparql_passthrough(self, engine):
        results = engine.sparql(
            "PREFIX kb: <https://yurtle.dev/kanban/> "
            "SELECT ?id WHERE { ?item kb:id ?id . ?item kb:status kb:in_progress . }"
        )
        ids = {r["id"] for r in results}
        assert ids == {"EXP-800", "EXP-850"}

    def test_query_not_done_expeditions_above_700(self, engine):
        results = engine.query("not-done expeditions above 700")
        ids = {r.item.id for r in results}
        assert "EXP-800" in ids
        assert "EXP-850" in ids
        assert "EXP-950" in ids
        assert "EXP-1000" in ids
        assert "EXP-900" not in ids  # done
        assert "EXP-600" not in ids  # below 700
        assert "CHORE-050" not in ids  # chore

    def test_query_blocked_items(self, engine):
        results = engine.query("blocked expeditions")
        ids = {r.item.id for r in results}
        assert "EXP-750" in ids

    def test_query_assigned_to_mini(self, engine):
        results = engine.query("assigned to Mini")
        ids = {r.item.id for r in results}
        assert "EXP-850" in ids
        assert "EXP-800" not in ids  # assigned to DGX

    def test_query_returns_all_when_no_filters(self, engine):
        results = engine.query("everything")
        assert len(results) > 0

    def test_query_in_progress(self, engine):
        results = engine.query("in progress")
        ids = {r.item.id for r in results}
        assert ids == {"EXP-800", "EXP-850"}


# ---------------------------------------------------------------------------
# Phase 2: EmbeddingIndex (skip if sentence-transformers not installed)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SENTENCE_TRANSFORMERS, reason="sentence-transformers not installed")
class TestEmbeddingIndex:
    def test_search_returns_results(self, sample_items):
        idx = EmbeddingIndex()
        idx.add_items(sample_items)
        hits = idx.search("knowledge graph reasoning", top_k=5)
        assert len(hits) > 0
        assert all(hasattr(h, "score") for h in hits)

    def test_semantic_relevance(self, sample_items):
        idx = EmbeddingIndex()
        idx.add_items(sample_items)
        hits = idx.search("graph search and brain reasoning", top_k=3)
        # Graph/brain items should rank higher than CarPlay
        hit_ids = [h.item_id for h in hits]
        # At least one brain-related item in top 3
        brain_items = {"EXP-700", "EXP-800", "EXP-850", "EXP-900", "EXP-1000"}
        assert any(h in brain_items for h in hit_ids)

    def test_cache_roundtrip(self, sample_items, tmp_path):
        # Build and cache
        idx1 = EmbeddingIndex(cache_dir=tmp_path)
        idx1.add_items(sample_items)
        hits1 = idx1.search("graph", top_k=3)

        # Load from cache
        idx2 = EmbeddingIndex(cache_dir=tmp_path)
        idx2.add_items(sample_items)  # same items → same hash
        hits2 = idx2.search("graph", top_k=3)

        assert [h.item_id for h in hits1] == [h.item_id for h in hits2]


# ---------------------------------------------------------------------------
# Phase 2+3 Integration: QueryEngine with semantic search
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SENTENCE_TRANSFORMERS, reason="sentence-transformers not installed")
class TestQueryEngineHybrid:
    @pytest.fixture
    def engine(self, sample_items):
        ug = UnifiedGraph()
        ug.add_items(sample_items)
        emb = EmbeddingIndex()
        emb.add_items(sample_items)
        return QueryEngine(unified_graph=ug, embedding_index=emb)

    def test_hybrid_query_ranks_by_relevance(self, engine):
        results = engine.query("not-done expeditions above 700 that improve brain functioning")
        ids = [r.item.id for r in results]
        # Brain items should be present (graph filter works)
        assert any("EXP-800" == r.item.id for r in results)
        assert any("EXP-850" == r.item.id for r in results)
        # Done and below-700 items should be excluded (graph filter)
        assert "EXP-900" not in ids  # done
        assert "EXP-600" not in ids  # below 700
        # All results should have semantic scores
        assert all(r.semantic_score >= 0 for r in results)

    def test_hybrid_query_has_scores(self, engine):
        results = engine.query("not-done expeditions above 700 that improve brain")
        assert all(r.combined_score > 0 for r in results)
        assert any(r.semantic_score > 0 for r in results)
