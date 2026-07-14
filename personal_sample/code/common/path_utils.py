"""Path resolution utilities."""

from __future__ import annotations

from pathlib import Path


def resolve_cli_path(path_str: str) -> Path:
    """Resolve a path provided via CLI arguments to an absolute Path."""
    return Path(path_str).resolve()


def resolve_from_file(relative: str, base_file: str | Path) -> Path:
    """Resolve a relative path against the directory of a base file."""
    base_dir = Path(base_file).resolve().parent
    return (base_dir / relative).resolve()
