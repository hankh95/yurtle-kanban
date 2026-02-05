"""
Kanban Service - Core operations for managing work items.

This service provides the business logic for:
- Loading/saving work items from Yurtle files
- State transitions with validation
- WIP limit enforcement
- Item creation and updates
"""

import logging
import re
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from .config import KanbanConfig
from .models import Board, Column, Comment, WorkItem, WorkItemStatus, WorkItemType
from .workflow import WorkflowParser, WorkflowConfig


logger = logging.getLogger("yurtle-kanban")


class KanbanService:
    """Service for managing kanban work items."""

    def __init__(self, config: KanbanConfig, repo_root: Path):
        self.config = config
        self.repo_root = repo_root
        self._items: dict[str, WorkItem] = {}
        self._board: Board | None = None
        self._workflow_parser = WorkflowParser(repo_root / ".kanban")
        self._workflows: dict[str, WorkflowConfig] = {}

    def scan(self) -> list[WorkItem]:
        """Scan configured paths for work items."""
        self._items.clear()

        for scan_path in self.config.get_work_paths():
            full_path = self.repo_root / scan_path
            if full_path.exists():
                for item in self._scan_directory(full_path):
                    self._items[item.id] = item

        return list(self._items.values())

    def _scan_directory(self, directory: Path) -> list[WorkItem]:
        """Scan a directory for Yurtle work items."""
        items = []

        for md_file in directory.rglob("*.md"):
            # Check ignore patterns
            if self._should_ignore(md_file):
                continue

            item = self._parse_file(md_file)
            if item:
                items.append(item)

        return items

    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        path_str = str(path.relative_to(self.repo_root))
        for pattern in self.config.paths.ignore:
            # Simple glob-style matching
            if "**" in pattern:
                pattern_part = pattern.replace("**", "").strip("/")
                if pattern_part in path_str:
                    return True
            elif pattern.startswith("*"):
                if path_str.endswith(pattern[1:]):
                    return True
        return False

    def _parse_file(self, file_path: Path) -> WorkItem | None:
        """Parse a markdown file for work item data."""
        try:
            content = file_path.read_text()

            # Parse frontmatter
            frontmatter = self._parse_frontmatter(content)
            if not frontmatter:
                return None

            # Get required fields
            item_id = frontmatter.get("id")
            if not item_id:
                # Generate from filename
                item_id = file_path.stem.upper().replace("-", "_")

            item_type_str = frontmatter.get("type", "task")
            try:
                item_type = WorkItemType.from_string(item_type_str)
            except ValueError:
                # Try theme mapping
                item_type = self._map_theme_type(item_type_str)
                if not item_type:
                    return None

            status_str = frontmatter.get("status", "backlog")
            try:
                status = WorkItemStatus.from_string(status_str)
            except ValueError:
                # Try theme mapping
                status = self._map_theme_status(status_str)
                if not status:
                    status = WorkItemStatus.BACKLOG

            # Get title
            title = frontmatter.get("title", file_path.stem.replace("-", " ").title())

            # Parse optional fields
            priority = frontmatter.get("priority")
            assignee = frontmatter.get("assignee")
            tags = frontmatter.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]

            depends_on = frontmatter.get("depends_on", [])
            if isinstance(depends_on, str):
                depends_on = [d.strip() for d in depends_on.split(",")]

            created = None
            if "created" in frontmatter:
                created_val = frontmatter["created"]
                if isinstance(created_val, date):
                    created = created_val
                elif isinstance(created_val, str):
                    try:
                        created = date.fromisoformat(created_val)
                    except ValueError:
                        pass

            # Extract description (content after frontmatter, before yurtle block)
            description = self._extract_description(content)

            return WorkItem(
                id=item_id,
                title=title,
                item_type=item_type,
                status=status,
                file_path=file_path,
                priority=priority,
                assignee=assignee,
                created=created,
                tags=tags,
                depends_on=depends_on,
                description=description,
            )

        except Exception as e:
            logger.debug(f"Failed to parse {file_path}: {e}")
            return None

    def _parse_frontmatter(self, content: str) -> dict[str, Any] | None:
        """Parse YAML frontmatter from markdown content."""
        if not content.startswith("---"):
            return None

        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        try:
            return yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return None

    def _extract_description(self, content: str) -> str | None:
        """Extract description from markdown content."""
        # Remove frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]

        # Remove yurtle blocks
        content = re.sub(r"```yurtle.*?```", "", content, flags=re.DOTALL)

        # Remove heading (title)
        lines = content.strip().split("\n")
        description_lines = []
        skip_heading = True
        for line in lines:
            if skip_heading and line.startswith("#"):
                skip_heading = False
                continue
            description_lines.append(line)

        description = "\n".join(description_lines).strip()
        return description if description else None

    def _map_theme_type(self, type_str: str) -> WorkItemType | None:
        """Map theme-specific type to standard type."""
        theme = self.config.get_theme()
        if theme and "item_types" in theme:
            for type_id, type_def in theme["item_types"].items():
                if type_id == type_str.lower():
                    # Map common nautical types
                    mapping = {
                        "expedition": WorkItemType.FEATURE,
                        "voyage": WorkItemType.EPIC,
                        "directive": WorkItemType.TASK,
                        "hazard": WorkItemType.BUG,
                        "signal": WorkItemType.IDEA,
                    }
                    return mapping.get(type_id, WorkItemType.TASK)
        return None

    def _map_theme_status(self, status_str: str) -> WorkItemStatus | None:
        """Map theme-specific status to standard status."""
        # Common status mappings across themes
        mapping = {
            # Nautical theme
            "harbor": WorkItemStatus.BACKLOG,
            "provisioning": WorkItemStatus.READY,
            "underway": WorkItemStatus.IN_PROGRESS,
            "approaching": WorkItemStatus.REVIEW,
            "arrived": WorkItemStatus.DONE,
            # Custom statuses
            "intake": WorkItemStatus.BACKLOG,
            "planning": WorkItemStatus.READY,
            "active": WorkItemStatus.IN_PROGRESS,
            "complete": WorkItemStatus.DONE,
            "completed": WorkItemStatus.DONE,
            # Spec theme
            "draft": WorkItemStatus.BACKLOG,
            "proposed": WorkItemStatus.READY,
            "implementing": WorkItemStatus.IN_PROGRESS,
            "accepted": WorkItemStatus.DONE,
        }
        return mapping.get(status_str.lower())

    def get_board(self) -> Board:
        """Get the kanban board with all items."""
        if self._board is None:
            items = self.scan()
            columns = self._get_columns_from_theme()
            column_status_map = self._get_column_status_map()
            self._board = Board(
                id="main",
                name=self.config.theme.title() + " Board",
                columns=columns,
                items=items,
                column_status_map=column_status_map,
            )
        return self._board

    def _get_column_status_map(self) -> dict[str, WorkItemStatus]:
        """Get mapping from column IDs to WorkItemStatus for themed columns."""
        # Default nautical theme mappings
        mappings = {
            "harbor": WorkItemStatus.BACKLOG,
            "provisioning": WorkItemStatus.READY,
            "underway": WorkItemStatus.IN_PROGRESS,
            "approaching": WorkItemStatus.REVIEW,
            "arrived": WorkItemStatus.DONE,
            # Standard software theme (identity mapping)
            "backlog": WorkItemStatus.BACKLOG,
            "ready": WorkItemStatus.READY,
            "in_progress": WorkItemStatus.IN_PROGRESS,
            "review": WorkItemStatus.REVIEW,
            "done": WorkItemStatus.DONE,
            "blocked": WorkItemStatus.BLOCKED,
            # Spec theme
            "draft": WorkItemStatus.BACKLOG,
            "proposed": WorkItemStatus.READY,
            "implementing": WorkItemStatus.IN_PROGRESS,
            "accepted": WorkItemStatus.DONE,
        }
        return mappings

    def _get_columns_from_theme(self) -> list[Column]:
        """Get column definitions from theme."""
        theme = self.config.get_theme()
        columns = []

        if theme and "columns" in theme:
            for col_id, col_def in theme["columns"].items():
                columns.append(Column(
                    id=col_id,
                    name=col_def.get("name", col_id.title()),
                    order=col_def.get("order", 0),
                    wip_limit=col_def.get("wip_limit"),
                    description=col_def.get("description"),
                ))
        else:
            # Default software columns
            columns = [
                Column("backlog", "Backlog", 1),
                Column("ready", "Ready", 2, wip_limit=5),
                Column("in_progress", "In Progress", 3, wip_limit=3),
                Column("review", "Review", 4, wip_limit=2),
                Column("done", "Done", 5),
            ]

        return sorted(columns, key=lambda c: c.order)

    def get_item(self, item_id: str) -> WorkItem | None:
        """Get a work item by ID."""
        if not self._items:
            self.scan()
        return self._items.get(item_id)

    def get_items(
        self,
        status: WorkItemStatus | None = None,
        item_type: WorkItemType | None = None,
        assignee: str | None = None,
    ) -> list[WorkItem]:
        """Get items with optional filters."""
        if not self._items:
            self.scan()

        items = list(self._items.values())

        if status:
            items = [i for i in items if i.status == status]
        if item_type:
            items = [i for i in items if i.item_type == item_type]
        if assignee:
            items = [i for i in items if i.assignee == assignee]

        return sorted(items, key=lambda i: (-i.priority_score, i.id))

    def create_item(
        self,
        item_type: WorkItemType,
        title: str,
        path: Path | None = None,
        priority: str = "medium",
        assignee: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> WorkItem:
        """Create a new work item."""
        # Generate ID
        prefix = self._get_type_prefix(item_type)
        next_num = self._get_next_id_number(prefix)
        item_id = f"{prefix}-{next_num:03d}"

        # Determine file path
        if path is None:
            work_root = self.repo_root / self.config.paths.root
            type_path = getattr(self.config.paths, item_type.value + "s", None)
            if type_path:
                work_root = self.repo_root / type_path
            path = work_root / f"{item_id}.md"

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Create work item
        item = WorkItem(
            id=item_id,
            title=title,
            item_type=item_type,
            status=WorkItemStatus.BACKLOG,
            file_path=path,
            priority=priority,
            assignee=assignee,
            created=date.today(),
            description=description,
            tags=tags or [],
        )

        # Write file
        path.write_text(item.to_markdown())

        # Add to cache
        self._items[item_id] = item

        return item

    def _get_type_prefix(self, item_type: WorkItemType) -> str:
        """Get ID prefix for item type."""
        theme = self.config.get_theme()
        if theme and "item_types" in theme:
            for type_id, type_def in theme["item_types"].items():
                if type_id == item_type.value:
                    return type_def.get("id_prefix", item_type.value[:4].upper())
        # Default prefixes (software + nautical themes)
        prefixes = {
            # Software theme
            WorkItemType.FEATURE: "FEAT",
            WorkItemType.BUG: "BUG",
            WorkItemType.EPIC: "EPIC",
            WorkItemType.ISSUE: "ISSUE",
            WorkItemType.TASK: "TASK",
            WorkItemType.IDEA: "IDEA",
            # Nautical theme
            WorkItemType.EXPEDITION: "EXP",
            WorkItemType.VOYAGE: "VOY",
            WorkItemType.DIRECTIVE: "DIR",
            WorkItemType.HAZARD: "HAZ",
            WorkItemType.SIGNAL: "SIG",
            WorkItemType.CHORE: "CHORE",
        }
        return prefixes.get(item_type, "ITEM")

    def _get_next_id_number(self, prefix: str) -> int:
        """Get next available ID number for a prefix.

        Scans both:
        1. Item IDs from frontmatter (via self._items)
        2. Filenames directly (to catch files without proper frontmatter)
        """
        if not self._items:
            self.scan()

        max_num = 0

        # Check IDs from parsed items
        for item_id in self._items.keys():
            if item_id.startswith(prefix + "-"):
                try:
                    num = int(item_id.split("-")[1])
                    max_num = max(max_num, num)
                except (ValueError, IndexError):
                    pass

        # Also scan filenames directly to catch files without frontmatter
        for scan_path in self.config.get_work_paths():
            full_path = self.repo_root / scan_path
            if full_path.exists():
                for md_file in full_path.rglob("*.md"):
                    filename = md_file.stem  # e.g., "EXP-608-Some-Title"
                    if filename.startswith(prefix + "-"):
                        try:
                            # Extract number from filename
                            parts = filename.split("-")
                            if len(parts) >= 2:
                                num = int(parts[1])
                                max_num = max(max_num, num)
                        except (ValueError, IndexError):
                            pass

        return max_num + 1

    def allocate_next_id(
        self,
        prefix: str,
        sync_remote: bool = True,
        commit_allocation: bool = True,
    ) -> dict[str, Any]:
        """Allocate the next available ID for a prefix with git synchronization.

        This method prevents duplicate IDs when multiple agents create work items
        concurrently by:
        1. Fetching latest changes from remote (if sync_remote=True)
        2. Scanning all files to find the highest ID
        3. Writing an allocation lock file and committing it
        4. Returning the allocated ID

        Args:
            prefix: The ID prefix (e.g., "EXP", "FEAT", "BUG")
            sync_remote: Whether to fetch latest from remote first
            commit_allocation: Whether to commit the allocation lock file

        Returns:
            dict with 'id', 'prefix', 'number', and 'success' keys
        """
        import json
        from datetime import datetime

        prefix = prefix.upper()

        # Step 1: Fetch latest from remote
        if sync_remote:
            try:
                result = subprocess.run(
                    ["git", "fetch", "origin"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    logger.warning(f"Git fetch failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                logger.warning("Git fetch timed out")
            except Exception as e:
                logger.warning(f"Git fetch error: {e}")

        # Step 2: Re-scan to get latest items
        self._items.clear()
        self.scan()

        # Step 3: Find next available number
        next_num = self._get_next_id_number(prefix)
        item_id = f"{prefix}-{next_num:03d}"

        # Step 4: Write allocation lock file (only if committing)
        if commit_allocation:
            lock_file = self.repo_root / ".kanban" / "_ID_ALLOCATIONS.json"
            lock_file.parent.mkdir(parents=True, exist_ok=True)

            # Load existing allocations
            allocations = []
            if lock_file.exists():
                try:
                    allocations = json.loads(lock_file.read_text())
                except (json.JSONDecodeError, Exception):
                    allocations = []

            # Add new allocation
            allocation = {
                "id": item_id,
                "prefix": prefix,
                "number": next_num,
                "allocated_at": datetime.now().isoformat(),
                "allocated_by": self._get_git_user(),
            }
            allocations.append(allocation)

            # Keep only recent allocations (last 100)
            allocations = allocations[-100:]
            lock_file.write_text(json.dumps(allocations, indent=2))

        # Step 5: Commit the allocation
        if commit_allocation:
            try:
                subprocess.run(
                    ["git", "add", str(lock_file)],
                    cwd=self.repo_root,
                    capture_output=True,
                    check=True,
                )
                subprocess.run(
                    ["git", "commit", "-m", f"Allocate ID: {item_id}"],
                    cwd=self.repo_root,
                    capture_output=True,
                    check=True,
                )
                # Push to remote to claim the ID
                if sync_remote:
                    push_result = subprocess.run(
                        ["git", "push"],
                        cwd=self.repo_root,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if push_result.returncode != 0:
                        # Push failed - likely another agent allocated an ID
                        # Pull and retry
                        logger.warning(f"Push failed, will retry: {push_result.stderr}")
                        return self._retry_allocation(prefix)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Git commit failed: {e}")

        return {
            "success": True,
            "id": item_id,
            "prefix": prefix,
            "number": next_num,
            "message": f"Allocated {item_id}",
        }

    def _retry_allocation(self, prefix: str, max_retries: int = 3) -> dict[str, Any]:
        """Retry allocation after a conflict."""
        for attempt in range(max_retries):
            try:
                # Pull latest
                subprocess.run(
                    ["git", "pull", "--rebase"],
                    cwd=self.repo_root,
                    capture_output=True,
                    check=True,
                    timeout=30,
                )
                # Try allocation again
                return self.allocate_next_id(prefix, sync_remote=False, commit_allocation=True)
            except Exception as e:
                logger.warning(f"Retry {attempt + 1} failed: {e}")

        return {
            "success": False,
            "id": None,
            "prefix": prefix,
            "number": None,
            "message": "Failed to allocate ID after retries",
        }

    def _get_git_user(self) -> str:
        """Get current git user name."""
        try:
            result = subprocess.run(
                ["git", "config", "user.name"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() or "unknown"
        except Exception:
            return "unknown"

    def move_item(
        self,
        item_id: str,
        new_status: WorkItemStatus,
        commit: bool = True,
        message: str | None = None,
        validate_workflow: bool = True,
        assignee: str | None = None,
    ) -> WorkItem:
        """Move a work item to a new status.

        Args:
            item_id: The work item ID to move
            new_status: The target status
            commit: Whether to git commit the change
            message: Optional commit message
            validate_workflow: Whether to validate against workflow rules
            assignee: Optional assignee to set (e.g., 'Claude-M5', 'Claude-DGX')
        """
        item = self.get_item(item_id)
        if not item:
            raise ValueError(f"Item not found: {item_id}")

        old_status = item.status

        # Validate transition using workflow if available
        if validate_workflow:
            valid, error_msg = self._validate_transition(item, new_status)
            if not valid:
                raise ValueError(error_msg)

        # Check WIP limits
        board = self.get_board()
        for col in board.columns:
            if col.id == new_status.value:
                current_count = len(board.get_items_by_status(new_status))
                if col.wip_limit and current_count >= col.wip_limit:
                    raise ValueError(
                        f"WIP limit reached for {col.name} ({current_count}/{col.wip_limit})"
                    )

        # Update item
        item.status = new_status
        item.updated = datetime.now()

        # Update assignee if provided
        if assignee:
            item.assignee = assignee

        # Update file with status history
        self._update_item_file_with_history(item, old_status, new_status, assignee)

        # Git commit if requested
        if commit:
            commit_msg = message
            if not commit_msg:
                commit_msg = f"Move {item_id} to {new_status.value}"
                if assignee:
                    commit_msg += f" (assigned to {assignee})"
            self._git_commit(item.file_path, commit_msg)

        return item

    def _validate_transition(
        self, item: WorkItem, new_status: WorkItemStatus
    ) -> tuple[bool, str]:
        """Validate a status transition using workflow rules if available.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Try to load workflow for this item type
        item_type = item.item_type.value
        workflow = self._workflow_parser.load_workflow(item_type)

        if workflow:
            # Use workflow validation
            return self._workflow_parser.validate_transition(item, new_status, workflow)
        else:
            # Fall back to default validation
            if self._is_valid_transition(item.status, new_status):
                return True, ""
            else:
                return False, f"Invalid transition from {item.status.value} to {new_status.value}"

    def _is_valid_transition(
        self, from_status: WorkItemStatus, to_status: WorkItemStatus
    ) -> bool:
        """Check if a status transition is valid (default rules)."""
        # Define valid transitions
        valid_transitions = {
            WorkItemStatus.BACKLOG: [WorkItemStatus.READY, WorkItemStatus.BLOCKED],
            WorkItemStatus.READY: [
                WorkItemStatus.IN_PROGRESS,
                WorkItemStatus.BACKLOG,
                WorkItemStatus.BLOCKED,
            ],
            WorkItemStatus.IN_PROGRESS: [
                WorkItemStatus.REVIEW,
                WorkItemStatus.DONE,
                WorkItemStatus.BLOCKED,
                WorkItemStatus.READY,
            ],
            WorkItemStatus.REVIEW: [
                WorkItemStatus.DONE,
                WorkItemStatus.IN_PROGRESS,
                WorkItemStatus.BLOCKED,
            ],
            WorkItemStatus.BLOCKED: [
                WorkItemStatus.READY,
                WorkItemStatus.IN_PROGRESS,
                WorkItemStatus.BACKLOG,
            ],
            WorkItemStatus.DONE: [],  # Terminal state
        }

        return to_status in valid_transitions.get(from_status, [])

    def get_workflow(self, item_type: str) -> WorkflowConfig | None:
        """Get the workflow for a specific item type."""
        return self._workflow_parser.load_workflow(item_type)

    def get_allowed_transitions(self, item: WorkItem) -> list[str]:
        """Get list of allowed transitions for an item."""
        workflow = self._workflow_parser.load_workflow(item.item_type.value)
        if workflow:
            return workflow.get_allowed_transitions(item.status.value)
        else:
            # Default transitions
            default = self._get_default_transitions(item.status)
            return [s.value for s in default]

    def _get_default_transitions(self, status: WorkItemStatus) -> list[WorkItemStatus]:
        """Get default allowed transitions for a status."""
        transitions = {
            WorkItemStatus.BACKLOG: [WorkItemStatus.READY, WorkItemStatus.BLOCKED],
            WorkItemStatus.READY: [WorkItemStatus.IN_PROGRESS, WorkItemStatus.BACKLOG, WorkItemStatus.BLOCKED],
            WorkItemStatus.IN_PROGRESS: [WorkItemStatus.REVIEW, WorkItemStatus.DONE, WorkItemStatus.BLOCKED, WorkItemStatus.READY],
            WorkItemStatus.REVIEW: [WorkItemStatus.DONE, WorkItemStatus.IN_PROGRESS, WorkItemStatus.BLOCKED],
            WorkItemStatus.BLOCKED: [WorkItemStatus.READY, WorkItemStatus.IN_PROGRESS, WorkItemStatus.BACKLOG],
            WorkItemStatus.DONE: [],
        }
        return transitions.get(status, [])

    def _update_item_file(self, item: WorkItem) -> None:
        """Update the work item file with current state."""
        item.file_path.write_text(item.to_markdown())

    def _update_item_file_with_history(
        self,
        item: WorkItem,
        old_status: WorkItemStatus,
        new_status: WorkItemStatus,
        assignee: str | None = None,
    ) -> None:
        """Update file and append status change to yurtle knowledge block.

        Status history is stored in TTL (Turtle RDF) format:
        ```yurtle
        @prefix kb: <https://yurtle.dev/kanban/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        <> kb:statusChange [
            kb:status kb:ready ;
            kb:at "2024-01-15T10:30:00"^^xsd:dateTime ;
            kb:by "Claude-M5" ;
        ] .
        ```
        """
        content = item.file_path.read_text()

        # Update frontmatter for status and assignee
        content = self._update_frontmatter_field(content, "status", new_status.value)
        if assignee:
            content = self._update_frontmatter_field(content, "assignee", assignee)

        # Create TTL status change entry
        timestamp = datetime.now().isoformat(timespec='seconds')
        agent = assignee or self._get_git_user()
        ttl_entry = f'''    kb:status kb:{new_status.value} ;
    kb:at "{timestamp}"^^xsd:dateTime ;
    kb:by "{agent}" ;'''

        # Check if yurtle block with status changes exists
        import re
        # Match block with prefix declarations and statusChange predicates
        yurtle_pattern = r"```yurtle\n@prefix kb: <https://yurtle\.dev/kanban/> \.\n@prefix xsd: <http://www\.w3\.org/2001/XMLSchema#> \.\n\n<> kb:statusChange(.*?)\.\n```"
        match = re.search(yurtle_pattern, content, re.DOTALL)

        if match:
            # Append to existing block - add new blank node
            existing = match.group(1).rstrip()
            # Remove trailing period and add comma for new entry
            new_block = f'''```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> kb:statusChange{existing.rstrip(" ;")},
  [
{ttl_entry}
  ] .
```'''
            content = content[:match.start()] + new_block + content[match.end():]
        else:
            # Add new yurtle block at end
            new_block = f'''```yurtle
@prefix kb: <https://yurtle.dev/kanban/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> kb:statusChange [
{ttl_entry}
  ] .
```'''
            content = content.rstrip() + "\n\n" + new_block + "\n"

        item.file_path.write_text(content)

    def _update_frontmatter_field(self, content: str, field: str, value: str) -> str:
        """Update a single field in the frontmatter."""
        import re
        pattern = rf"^{field}:.*$"
        replacement = f"{field}: {value}"
        # Only replace in frontmatter (between first two ---)
        parts = content.split("---", 2)
        if len(parts) >= 3:
            parts[1] = re.sub(pattern, replacement, parts[1], flags=re.MULTILINE)
            return "---".join(parts)
        return content

    def _git_commit(self, file_path: Path, message: str) -> None:
        """Commit changes to git."""
        try:
            subprocess.run(
                ["git", "add", str(file_path)],
                cwd=self.repo_root,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_root,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git commit failed: {e}")

    def add_comment(
        self,
        item_id: str,
        content: str,
        author: str,
        commit: bool = True,
    ) -> WorkItem:
        """Add a comment to a work item."""
        item = self.get_item(item_id)
        if not item:
            raise ValueError(f"Item not found: {item_id}")

        comment = Comment(content=content, author=author)
        item.comments.append(comment)
        item.updated = datetime.now()

        # Update file (comments go in a special section)
        self._update_item_with_comment(item, comment)

        if commit:
            self._git_commit(
                item.file_path,
                f"Add comment to {item_id}",
            )

        return item

    def _update_item_with_comment(self, item: WorkItem, comment: Comment) -> None:
        """Update item file to include new comment."""
        content = item.file_path.read_text()

        # Add comment section if not exists
        if "## Comments" not in content:
            content += "\n\n## Comments\n"

        # Add comment
        timestamp = comment.created_at.strftime("%Y-%m-%d %H:%M")
        content += f"\n### {comment.author} ({timestamp})\n\n{comment.content}\n"

        item.file_path.write_text(content)

    def get_status_history(self, item_id: str) -> list[dict[str, Any]]:
        """Get status history for an item.

        Returns list of dicts: [{'status': str, 'at': datetime, 'by': str}, ...]

        Parses TTL (Turtle RDF) format in yurtle blocks:
        ```yurtle
        @prefix kb: <https://yurtle.dev/kanban/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        <> kb:statusChange [
            kb:status kb:ready ;
            kb:at "2024-01-15T10:30:00"^^xsd:dateTime ;
            kb:by "Claude-M5" ;
        ] .
        ```
        """
        item = self.get_item(item_id)
        if not item:
            return []

        content = item.file_path.read_text()

        # Parse yurtle block with TTL format
        import re

        # Find yurtle blocks
        yurtle_blocks = re.findall(r"```yurtle\n(.*?)```", content, re.DOTALL)
        if not yurtle_blocks:
            return []

        history = []

        for block in yurtle_blocks:
            # Find all blank nodes with statusChange data
            # Pattern matches: kb:status kb:XXX ; kb:at "..." ; kb:by "..." ;
            entry_pattern = r'kb:status kb:(\w+)\s*;\s*kb:at "([^"]+)"(?:\^\^xsd:dateTime)?\s*;\s*kb:by "([^"]+)"'
            for entry_match in re.finditer(entry_pattern, block):
                try:
                    history.append({
                        "status": entry_match.group(1),
                        "at": datetime.fromisoformat(entry_match.group(2)),
                        "by": entry_match.group(3),
                    })
                except ValueError:
                    pass

        return history

    def get_flow_metrics(self, item_id: str) -> dict[str, Any]:
        """Calculate flow metrics for an item.

        Returns:
            cycle_time: Time from in_progress to done (working time)
            lead_time: Time from ready to done (total queue + work time)
            time_in_status: Dict of status -> hours spent
        """
        history = self.get_status_history(item_id)
        if not history:
            return {"error": "No status history found"}

        metrics: dict[str, Any] = {
            "item_id": item_id,
            "transitions": len(history),
            "time_in_status": {},
            "cycle_time_hours": None,
            "lead_time_hours": None,
        }

        # Calculate time in each status
        for i, entry in enumerate(history):
            status = entry["status"]
            start_time = entry["at"]

            # End time is next transition or now
            if i + 1 < len(history):
                end_time = history[i + 1]["at"]
            else:
                end_time = datetime.now()

            hours = (end_time - start_time).total_seconds() / 3600
            metrics["time_in_status"][status] = metrics["time_in_status"].get(status, 0) + hours

        # Calculate cycle time (in_progress to done)
        in_progress_time = None
        done_time = None
        for entry in history:
            if entry["status"] == "in_progress" and in_progress_time is None:
                in_progress_time = entry["at"]
            if entry["status"] == "done":
                done_time = entry["at"]

        if in_progress_time and done_time:
            metrics["cycle_time_hours"] = (done_time - in_progress_time).total_seconds() / 3600

        # Calculate lead time (ready to done)
        ready_time = None
        for entry in history:
            if entry["status"] == "ready" and ready_time is None:
                ready_time = entry["at"]

        if ready_time and done_time:
            metrics["lead_time_hours"] = (done_time - ready_time).total_seconds() / 3600

        return metrics

    def get_board_metrics(self) -> dict[str, Any]:
        """Calculate aggregate flow metrics for the board."""
        board = self.get_board()

        total_cycle_time = 0
        total_lead_time = 0
        cycle_time_count = 0
        lead_time_count = 0
        total_time_in_status: dict[str, float] = {}

        for item in board.items:
            metrics = self.get_flow_metrics(item.id)
            if "error" not in metrics:
                if metrics["cycle_time_hours"]:
                    total_cycle_time += metrics["cycle_time_hours"]
                    cycle_time_count += 1
                if metrics["lead_time_hours"]:
                    total_lead_time += metrics["lead_time_hours"]
                    lead_time_count += 1
                for status, hours in metrics.get("time_in_status", {}).items():
                    total_time_in_status[status] = total_time_in_status.get(status, 0) + hours

        return {
            "total_items": len(board.items),
            "items_with_history": cycle_time_count,
            "avg_cycle_time_hours": total_cycle_time / cycle_time_count if cycle_time_count else None,
            "avg_lead_time_hours": total_lead_time / lead_time_count if lead_time_count else None,
            "total_time_in_status": total_time_in_status,
        }

    def get_blocked_items(self) -> list[WorkItem]:
        """Get all blocked items."""
        return self.get_items(status=WorkItemStatus.BLOCKED)

    def get_my_items(self, assignee: str) -> list[WorkItem]:
        """Get items assigned to a specific person."""
        return self.get_items(assignee=assignee)

    def suggest_next_item(self, assignee: str | None = None) -> WorkItem | None:
        """Suggest the next highest-priority item to work on."""
        items = self.get_items(status=WorkItemStatus.READY)

        if assignee:
            # Prefer items assigned to this person
            my_items = [i for i in items if i.assignee == assignee]
            if my_items:
                items = my_items

        if not items:
            return None

        # Sort by priority
        items.sort(key=lambda i: -i.priority_score)
        return items[0]

    def update_item(
        self,
        item_id: str,
        title: str | None = None,
        priority: str | None = None,
        assignee: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        commit: bool = True,
        message: str | None = None,
    ) -> WorkItem:
        """Update a work item's properties (not status - use move_item for that).

        Args:
            item_id: The work item ID to update
            title: New title (optional)
            priority: New priority level (optional)
            assignee: New assignee (optional)
            description: New description (optional)
            tags: New tags list (optional, replaces existing)
            commit: Whether to git commit the change
            message: Optional commit message
        """
        item = self.get_item(item_id)
        if not item:
            raise ValueError(f"Item not found: {item_id}")

        # Track what changed for commit message
        changes = []

        if title is not None and title != item.title:
            item.title = title
            changes.append("title")

        if priority is not None and priority != item.priority:
            item.priority = priority
            changes.append("priority")

        if assignee is not None and assignee != item.assignee:
            item.assignee = assignee
            changes.append("assignee")

        if description is not None and description != item.description:
            item.description = description
            changes.append("description")

        if tags is not None and tags != item.tags:
            item.tags = tags
            changes.append("tags")

        if not changes:
            return item  # Nothing to update

        item.updated = datetime.now()

        # Update file
        self._update_item_file(item)

        # Git commit if requested
        if commit:
            change_summary = ", ".join(changes)
            self._git_commit(
                item.file_path,
                message or f"Update {item_id}: {change_summary}",
            )

        return item
