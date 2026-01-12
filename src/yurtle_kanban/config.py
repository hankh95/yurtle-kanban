"""
Configuration management for yurtle-kanban.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class PathConfig:
    """Configuration for work item paths."""
    root: Optional[str] = "work/"
    scan_paths: list[str] = field(default_factory=list)
    ignore: list[str] = field(default_factory=lambda: ["**/archive/**", "**/templates/**"])

    # Type-specific paths (optional)
    features: Optional[str] = None
    bugs: Optional[str] = None
    epics: Optional[str] = None
    tasks: Optional[str] = None


@dataclass
class KanbanConfig:
    """Main configuration for yurtle-kanban."""

    theme: str = "software"
    paths: PathConfig = field(default_factory=PathConfig)
    workflows: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Path) -> "KanbanConfig":
        """Load configuration from a YAML file."""
        if not config_path.exists():
            return cls()

        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        kanban_data = data.get("kanban", data)

        paths_data = kanban_data.get("paths", {})
        paths = PathConfig(
            root=paths_data.get("root", "work/"),
            scan_paths=paths_data.get("scan_paths", []),
            ignore=paths_data.get("ignore", ["**/archive/**", "**/templates/**"]),
            features=paths_data.get("features"),
            bugs=paths_data.get("bugs"),
            epics=paths_data.get("epics"),
            tasks=paths_data.get("tasks"),
        )

        return cls(
            theme=kanban_data.get("theme", "software"),
            paths=paths,
            workflows=kanban_data.get("workflows", {}),
        )

    def save(self, config_path: Path) -> None:
        """Save configuration to a YAML file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "kanban": {
                "theme": self.theme,
                "paths": {
                    "root": self.paths.root,
                },
                "workflows": self.workflows,
            }
        }

        if self.paths.scan_paths:
            data["kanban"]["paths"]["scan_paths"] = self.paths.scan_paths

        if self.paths.ignore:
            data["kanban"]["paths"]["ignore"] = self.paths.ignore

        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_work_paths(self) -> list[Path]:
        """Get all paths where work items might be found."""
        paths = []

        if self.paths.scan_paths:
            paths.extend(Path(p) for p in self.paths.scan_paths)
        elif self.paths.root:
            paths.append(Path(self.paths.root))

        # Add type-specific paths
        for type_path in [self.paths.features, self.paths.bugs,
                          self.paths.epics, self.paths.tasks]:
            if type_path:
                paths.append(Path(type_path))

        return paths
