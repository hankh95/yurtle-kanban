"""Tests for workflow configuration parsing and validation."""

from pathlib import Path

import pytest

from yurtle_kanban.models import WorkItem, WorkItemStatus, WorkItemType
from yurtle_kanban.workflow import (
    StateConfig,
    TransitionRule,
    WorkflowConfig,
    WorkflowParser,
    get_default_workflow,
)


class TestStateConfig:
    """Tests for StateConfig."""

    def test_can_transition_to(self):
        """Test transition checking."""
        state = StateConfig(
            id="ready",
            name="Ready",
            allowed_transitions=["in_progress", "blocked"]
        )

        assert state.can_transition_to("in_progress") is True
        assert state.can_transition_to("blocked") is True
        assert state.can_transition_to("done") is False

    def test_initial_and_terminal(self):
        """Test initial and terminal flags."""
        initial = StateConfig(id="backlog", name="Backlog", is_initial=True)
        terminal = StateConfig(id="done", name="Done", is_terminal=True)

        assert initial.is_initial is True
        assert initial.is_terminal is False
        assert terminal.is_initial is False
        assert terminal.is_terminal is True


class TestWorkflowConfig:
    """Tests for WorkflowConfig."""

    def test_get_state(self):
        """Test getting state by ID."""
        workflow = WorkflowConfig(
            id="test",
            states=[
                StateConfig(id="ready", name="Ready"),
                StateConfig(id="in_progress", name="In Progress"),
            ]
        )

        assert workflow.get_state("ready") is not None
        assert workflow.get_state("ready").name == "Ready"
        assert workflow.get_state("in_progress") is not None
        assert workflow.get_state("unknown") is None

    def test_get_state_normalized(self):
        """Test state lookup with different formats."""
        workflow = WorkflowConfig(
            id="test",
            states=[StateConfig(id="in_progress", name="In Progress")]
        )

        assert workflow.get_state("in_progress") is not None
        assert workflow.get_state("in-progress") is not None
        assert workflow.get_state("IN_PROGRESS") is not None

    def test_get_initial_states(self):
        """Test getting initial states."""
        workflow = WorkflowConfig(
            id="test",
            states=[
                StateConfig(id="backlog", name="Backlog", is_initial=True),
                StateConfig(id="ready", name="Ready"),
                StateConfig(id="done", name="Done", is_terminal=True),
            ]
        )

        initial = workflow.get_initial_states()
        assert len(initial) == 1
        assert initial[0].id == "backlog"

    def test_get_terminal_states(self):
        """Test getting terminal states."""
        workflow = WorkflowConfig(
            id="test",
            states=[
                StateConfig(id="backlog", name="Backlog", is_initial=True),
                StateConfig(id="done", name="Done", is_terminal=True),
            ]
        )

        terminal = workflow.get_terminal_states()
        assert len(terminal) == 1
        assert terminal[0].id == "done"

    def test_get_allowed_transitions(self):
        """Test getting allowed transitions."""
        workflow = WorkflowConfig(
            id="test",
            states=[
                StateConfig(id="ready", name="Ready",
                           allowed_transitions=["in_progress", "blocked"]),
            ]
        )

        transitions = workflow.get_allowed_transitions("ready")
        assert "in_progress" in transitions
        assert "blocked" in transitions

    def test_to_mermaid(self):
        """Test Mermaid diagram generation."""
        workflow = WorkflowConfig(
            id="test",
            name="Test Workflow",
            states=[
                StateConfig(id="ready", name="Ready", is_initial=True,
                           allowed_transitions=["in_progress"]),
                StateConfig(id="in_progress", name="In Progress",
                           allowed_transitions=["done"]),
                StateConfig(id="done", name="Done", is_terminal=True),
            ]
        )

        mermaid = workflow.to_mermaid()
        assert "stateDiagram-v2" in mermaid
        assert "[*] --> ready" in mermaid
        assert "ready --> in_progress" in mermaid
        assert "done --> [*]" in mermaid

    def test_to_ascii(self):
        """Test ASCII diagram generation."""
        workflow = WorkflowConfig(
            id="test",
            name="Test Workflow",
            applies_to="feature",
            states=[
                StateConfig(id="ready", name="Ready",
                           allowed_transitions=["in_progress"]),
            ]
        )

        ascii_diagram = workflow.to_ascii()
        assert "Test Workflow" in ascii_diagram
        assert "feature" in ascii_diagram
        assert "[ready]" in ascii_diagram


class TestWorkflowParser:
    """Tests for WorkflowParser."""

    def test_get_default_workflow(self):
        """Test getting default workflow."""
        workflow = get_default_workflow()

        assert workflow.id == "default"
        assert len(workflow.states) > 0

        # Check we have expected states
        state_ids = [s.id for s in workflow.states]
        assert "backlog" in state_ids
        assert "ready" in state_ids
        assert "in_progress" in state_ids
        assert "done" in state_ids

    def test_validate_transition_valid(self):
        """Test validating a valid transition."""
        parser = WorkflowParser()
        workflow = get_default_workflow()

        item = WorkItem(
            id="FEAT-001",
            title="Test Feature",
            item_type=WorkItemType.FEATURE,
            status=WorkItemStatus.READY,
            file_path=Path("test.md"),
        )

        valid, error = parser.validate_transition(
            item, WorkItemStatus.IN_PROGRESS, workflow
        )

        assert valid is True
        assert error == ""

    def test_validate_transition_invalid(self):
        """Test validating an invalid transition."""
        parser = WorkflowParser()
        workflow = get_default_workflow()

        item = WorkItem(
            id="FEAT-001",
            title="Test Feature",
            item_type=WorkItemType.FEATURE,
            status=WorkItemStatus.BACKLOG,
            file_path=Path("test.md"),
        )

        # Backlog can only go to ready, not directly to done
        valid, error = parser.validate_transition(
            item, WorkItemStatus.DONE, workflow
        )

        assert valid is False
        assert "Cannot transition" in error

    def test_validate_transition_no_workflow(self):
        """Test transition validation without workflow (allows all)."""
        parser = WorkflowParser()

        item = WorkItem(
            id="FEAT-001",
            title="Test Feature",
            item_type=WorkItemType.FEATURE,
            status=WorkItemStatus.BACKLOG,
            file_path=Path("test.md"),
        )

        # Without a workflow, all transitions are allowed
        valid, error = parser.validate_transition(item, WorkItemStatus.DONE)

        assert valid is True


class TestTransitionRule:
    """Tests for transition rules."""

    def test_rule_structure(self):
        """Test rule dataclass structure."""
        rule = TransitionRule(
            id="require_assignee",
            applies_to="in_progress",
            condition="item.assignee is not None",
            message="Must have an assignee"
        )

        assert rule.id == "require_assignee"
        assert rule.applies_to == "in_progress"
        assert "assignee" in rule.condition
