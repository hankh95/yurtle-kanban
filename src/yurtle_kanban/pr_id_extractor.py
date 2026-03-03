"""Extract kanban item IDs from PR bodies and branch names.

Used by the kanban-auto-close GitHub Actions workflow to identify
which items to move when a PR merges. Also usable as a standalone
CLI helper.

Supports all yurtle-kanban item prefixes (EXP, CHORE, FEAT, etc.).
"""

from __future__ import annotations

import re

# All known item ID prefixes, longest first to avoid partial matches
# (e.g., "PAPER" before "P", "EXPR" before "EXP").
PREFIXES = (
    "EXPEDITION", "EXPERIMENT", "LITERATURE", "HYPOTHESIS",
    "DIRECTIVE", "FEATURE", "MEASURE", "VOYAGE", "SIGNAL",
    "HAZARD", "PAPER", "ISSUE", "CHORE", "EPIC", "EXPR",
    "FEAT", "IDEA", "TASK", "BUG", "DIR", "EXP", "HAZ",
    "LIT", "SIG", "VOY", "M", "H",
)

# Pattern for PR body keywords: Closes EXP-1023, Fixes CHORE-055, etc.
_PREFIX_GROUP = "|".join(PREFIXES)
_KEYWORD_PATTERN = re.compile(
    rf"(?:closes|fixes|resolves)\s+({_PREFIX_GROUP})-(\d+)",
    re.IGNORECASE,
)

# Pattern for branch names: exp-1023-title, chore-055-cleanup, etc.
_BRANCH_PREFIXES = "|".join(p.lower() for p in PREFIXES)
_BRANCH_PATTERN = re.compile(
    rf"^({_BRANCH_PREFIXES})-(\d+)",
    re.IGNORECASE,
)


def extract_ids_from_text(text: str) -> list[str]:
    """Extract item IDs from PR body text using keyword patterns.

    Scans for ``Closes EXP-1023``, ``Fixes CHORE-055``,
    ``Resolves FEAT-042`` (case-insensitive). Returns deduplicated
    list preserving first-seen order.

    >>> extract_ids_from_text("Closes EXP-1023 and Fixes CHORE-055")
    ['EXP-1023', 'CHORE-055']
    """
    seen: set[str] = set()
    result: list[str] = []
    for match in _KEYWORD_PATTERN.finditer(text):
        prefix = match.group(1).upper()
        number = match.group(2)
        item_id = f"{prefix}-{number}"
        if item_id not in seen:
            seen.add(item_id)
            result.append(item_id)
    return result


def extract_id_from_branch(branch: str) -> str | None:
    """Extract a single item ID from a branch name.

    >>> extract_id_from_branch("exp-1023-hdd-knowledge-blocks")
    'EXP-1023'
    >>> extract_id_from_branch("main")
    """
    match = _BRANCH_PATTERN.match(branch)
    if not match:
        return None
    prefix = match.group(1).upper()
    number = match.group(2)
    return f"{prefix}-{number}"


def extract_all(pr_body: str, branch: str) -> list[str]:
    """Extract all item IDs from PR body and branch name.

    PR body keywords take priority. Branch name is a fallback
    that only adds if not already found. Returns deduplicated list.

    >>> extract_all("Closes EXP-1023", "exp-1023-title")
    ['EXP-1023']
    >>> extract_all("", "chore-055-cleanup")
    ['CHORE-055']
    """
    ids = extract_ids_from_text(pr_body)
    seen = set(ids)
    branch_id = extract_id_from_branch(branch)
    if branch_id and branch_id not in seen:
        ids.append(branch_id)
    return ids
