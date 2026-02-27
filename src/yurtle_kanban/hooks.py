"""
Hook engine for event-driven kanban automation.

Fires configurable actions when kanban events occur (item creation,
status changes, blocking, etc.). Config is loaded from a Yurtle file
(.kanban/hooks/kanban-hooks.yurtle.md) with YAML frontmatter.

Actions are best-effort: failures are logged but never fail the
kanban operation.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger("yurtle-kanban.hooks")


# ─── Events ────────────────────────────────────────────────────────────────


class HookEvent(Enum):
    """Events that can trigger hooks."""

    ITEM_CREATED = "on_create"
    STATUS_CHANGE = "on_status_change"
    ASSIGNED = "on_assign"
    BLOCKED = "on_blocked"
    STALE_DETECTED = "on_stale"
    WIP_EXCEEDED = "on_wip_exceeded"


# ─── Context ───────────────────────────────────────────────────────────────


@dataclass
class HookContext:
    """Context passed to hook actions.

    Contains all information about the kanban event that triggered
    the hook. Used for template variable substitution and as the
    payload for NATS/log/shell actions.
    """

    event: HookEvent
    item_id: str
    item_type: str  # expedition, chore, idea, hypothesis, etc.
    title: str = ""
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    assignee: Optional[str] = None
    forced: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "event": self.event.value,
            "item_id": self.item_id,
            "item_type": self.item_type,
            "title": self.title,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "assignee": self.assignee,
            "forced": self.forced,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **self.metadata,
        }

    def render_template(self, template: str) -> str:
        """Replace {var} placeholders with context values."""
        replacements = {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "title": self.title,
            "event": self.event.value,
            "old_status": self.old_status or "",
            "new_status": self.new_status or "",
            "assignee": self.assignee or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": json.dumps(self.to_dict()),
        }
        result = template
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result


# ─── Engine ────────────────────────────────────────────────────────────────


class HookEngine:
    """Loads hook config from a Yurtle file and executes matching actions.

    Config is read from YAML frontmatter (the ``hooks:`` key).
    TTL blocks in the Yurtle file are ignored — they exist for
    graph queries by santiago-bosun.
    """

    def __init__(self, config_path: Path | None = None):
        self._hooks_config: dict[str, list[dict]] = {}
        if config_path and config_path.exists():
            self._load_config(config_path)

    @property
    def is_configured(self) -> bool:
        """Whether any hooks are loaded."""
        return bool(self._hooks_config)

    def _load_config(self, path: Path) -> None:
        """Load hook definitions from Yurtle file YAML frontmatter."""
        try:
            content = path.read_text(encoding="utf-8")
            frontmatter = _extract_frontmatter(content)
            self._hooks_config = frontmatter.get("hooks", {})
            if self._hooks_config:
                hook_count = sum(len(v) for v in self._hooks_config.values())
                logger.info(f"Loaded {hook_count} hook(s) from {path}")
        except Exception as e:
            logger.warning(f"Failed to load hooks config from {path}: {e}")

    def trigger(self, event: HookEvent, context: HookContext) -> None:
        """Execute all hooks matching this event and context."""
        if not self._hooks_config:
            return

        matched = self._matching_hooks(event, context)
        for hook_def in matched:
            actions = hook_def.get("actions", [])
            for action in actions:
                try:
                    _execute_action(action, context)
                except Exception as e:
                    logger.warning(
                        f"Hook action {action.get('type', '?')} failed "
                        f"for {context.item_id}: {e}"
                    )

    def _matching_hooks(
        self, event: HookEvent, context: HookContext
    ) -> list[dict]:
        """Return hook definitions that match the event and context."""
        hook_list = self._hooks_config.get(event.value, [])
        matched = []

        for hook_def in hook_list:
            # Filter by item_types (if specified)
            item_types = hook_def.get("item_types")
            if item_types and context.item_type not in item_types:
                continue

            # Filter by from/to status (for on_status_change)
            from_status = hook_def.get("from")
            if from_status and context.old_status != from_status:
                continue

            to_status = hook_def.get("to")
            if to_status and context.new_status != to_status:
                continue

            matched.append(hook_def)

        return matched


# ─── Actions ───────────────────────────────────────────────────────────────


def _execute_action(action: dict, context: HookContext) -> None:
    """Dispatch to the appropriate action handler."""
    action_type = action.get("type", "")

    if action_type == "nats_publish":
        _action_nats_publish(action, context)
    elif action_type == "log":
        _action_log(action, context)
    elif action_type == "shell":
        _action_shell(action, context)
    else:
        logger.warning(f"Unknown action type: {action_type}")


def _action_nats_publish(action: dict, context: HookContext) -> None:
    """Publish event to a NATS subject via the ``nats`` CLI."""
    subject = action.get("subject", f"ship.kanban.{context.event.value}")
    subject = context.render_template(subject)
    payload = json.dumps(context.to_dict())

    try:
        subprocess.run(
            ["nats", "pub", subject, payload],
            capture_output=True,
            text=True,
            timeout=10,
        )
        logger.debug(f"Published to {subject}: {context.item_id}")
    except FileNotFoundError:
        logger.debug("nats CLI not found — skipping nats_publish")
    except subprocess.TimeoutExpired:
        logger.warning(f"nats pub timed out for {subject}")
    except Exception as e:
        logger.warning(f"nats_publish failed: {e}")


def _action_log(action: dict, context: HookContext) -> None:
    """Append a JSON line to a log file."""
    log_path = action.get("path", ".kanban/hooks.log")
    log_path = Path(context.render_template(log_path))

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = context.to_dict()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.debug(f"Logged event to {log_path}: {context.item_id}")
    except Exception as e:
        logger.warning(f"log action failed: {e}")


def _action_shell(action: dict, context: HookContext) -> None:
    """Run a shell command with template variable substitution."""
    command = action.get("command", "")
    if not command:
        return

    command = context.render_template(command)
    timeout = action.get("timeout", 30)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            logger.warning(
                f"shell action exited {result.returncode}: "
                f"{result.stderr.strip()[:200]}"
            )
        else:
            logger.debug(f"shell action succeeded: {command[:80]}")
    except subprocess.TimeoutExpired:
        logger.warning(f"shell action timed out after {timeout}s: {command[:80]}")
    except Exception as e:
        logger.warning(f"shell action failed: {e}")


# ─── Helpers ───────────────────────────────────────────────────────────────


def _extract_frontmatter(content: str) -> dict[str, Any]:
    """Extract YAML frontmatter from a Yurtle markdown file."""
    if not content.startswith("---"):
        return {}

    end = content.find("---", 3)
    if end == -1:
        return {}

    try:
        return yaml.safe_load(content[3:end]) or {}
    except Exception as e:
        logger.warning(f"Failed to parse hook frontmatter: {e}")
        return {}
