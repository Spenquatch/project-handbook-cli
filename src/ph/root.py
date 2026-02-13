from __future__ import annotations

from pathlib import Path

PH_CONFIG_RELATIVE_PATH = Path(".project-handbook") / "config.json"

ROOT_MARKER_RELATIVE_PATHS: tuple[Path, ...] = (PH_CONFIG_RELATIVE_PATH,)


class RootResolutionError(RuntimeError):
    pass


def resolve_ph_root(*, override: str | None, cwd: Path | None = None) -> Path:
    """
    Resolve the Project Handbook repo root (PH_ROOT) by locating the root marker.
    """

    if override is not None:
        candidate = Path(override).expanduser().resolve()
        if any((candidate / rel).is_file() for rel in ROOT_MARKER_RELATIVE_PATHS):
            return candidate
        raise RootResolutionError(_missing_root_message(start=(cwd or Path.cwd()).resolve()))

    start = (cwd or Path.cwd()).resolve()
    for directory in (start, *start.parents):
        if any((directory / rel).is_file() for rel in ROOT_MARKER_RELATIVE_PATHS):
            return directory

    raise RootResolutionError(_missing_root_message(start=start))


def _missing_root_message(*, start: Path) -> str:
    expected = ", ".join(p.as_posix() for p in ROOT_MARKER_RELATIVE_PATHS)
    return (
        "No Project Handbook root found.\n"
        f"Start directory: {start}\n"
        f"Expected marker file(s): {expected}\n"
        'Example: ph --root "$PWD"\n'
    )


def find_root_marker(*, ph_root: Path) -> Path | None:
    for rel in ROOT_MARKER_RELATIVE_PATHS:
        if (ph_root / rel).is_file():
            return rel
    return None
