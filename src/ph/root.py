from __future__ import annotations

from pathlib import Path

ROOT_MARKER_RELATIVE_PATH = Path("cli_plan/project_handbook.config.json")


class RootResolutionError(RuntimeError):
    pass


def resolve_ph_root(*, override: str | None, cwd: Path | None = None) -> Path:
    """
    Resolve the Project Handbook repo root (PH_ROOT) by locating the root marker:
    `cli_plan/project_handbook.config.json`.
    """

    if override is not None:
        candidate = Path(override).expanduser().resolve()
        marker = candidate / ROOT_MARKER_RELATIVE_PATH
        if marker.is_file():
            return candidate
        raise RootResolutionError(_missing_root_message(start=(cwd or Path.cwd()).resolve()))

    start = (cwd or Path.cwd()).resolve()
    for directory in (start, *start.parents):
        marker = directory / ROOT_MARKER_RELATIVE_PATH
        if marker.is_file():
            return directory

    raise RootResolutionError(_missing_root_message(start=start))


def _missing_root_message(*, start: Path) -> str:
    return (
        "No Project Handbook root found.\n"
        f"Start directory: {start}\n"
        f"Expected marker: {ROOT_MARKER_RELATIVE_PATH}\n"
        "Example: ph --root /path/to/project-handbook\n"
    )
