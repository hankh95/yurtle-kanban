"""
Configuration management for yurtle-kanban.
"""

import importlib.resources
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


# Cache for loaded themes
_theme_cache: dict[str, dict[str, Any]] = {}


def _load_builtin_theme(theme_name: str, repo_root: Optional[Path] = None) -> Optional[dict[str, Any]]:
    """Load a theme from local .kanban/themes/ or package resources."""
    if theme_name in _theme_cache:
        return _theme_cache[theme_name]

    # Priority 1: Local .kanban/themes/ folder
    search_paths = []
    if repo_root:
        search_paths.append(repo_root / ".kanban" / "themes" / f"{theme_name}.yaml")
    search_paths.append(Path.cwd() / ".kanban" / "themes" / f"{theme_name}.yaml")

    # Priority 2: Package share directory (pip installed)
    try:
        import sys
        for path in sys.path:
            share_path = Path(path).parent / "share" / "yurtle-kanban" / "themes" / f"{theme_name}.yaml"
            if share_path.exists():
                search_paths.append(share_path)
    except Exception:
        pass

    # Priority 3: Source directory (development)
    try:
        import yurtle_kanban
        package_dir = Path(yurtle_kanban.__file__).parent.parent.parent
        search_paths.append(package_dir / "themes" / f"{theme_name}.yaml")
    except Exception:
        pass
    search_paths.append(Path(__file__).parent.parent.parent / "themes" / f"{theme_name}.yaml")

    # Try each path
    for theme_path in search_paths:
        try:
            if theme_path.exists():
                with open(theme_path) as f:
                    theme = yaml.safe_load(f)
                    _theme_cache[theme_name] = theme
                    return theme
        except Exception:
            continue

    return None


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

    def get_theme(self) -> Optional[dict[str, Any]]:
        """Get the theme configuration."""
        return _load_builtin_theme(self.theme)
