from __future__ import annotations

from pathlib import Path
from typing import Any

from .context import Context
from .sprint_status import run_sprint_status
from .validate_docs import run_validate

BANNER_LINE = "════════════════════════════════════════════════"
BANNER_PROJECT = "           PROJECT HANDBOOK DASHBOARD           "
BANNER_SYSTEM = "        PROJECT HANDBOOK DASHBOARD (HB)         "


def _iter_recent_daily(*, ph_root: Path, ctx: Context) -> list[str]:
    daily_dir = ctx.ph_data_root / "status" / "daily"
    if not daily_dir.exists():
        return []

    def _sort_key(path: Path) -> Any:
        rel = path.relative_to(daily_dir)
        parts = rel.parts
        if len(parts) == 1:
            stem = path.stem
            pieces = stem.split("-")
            if len(pieces) == 3 and all(p.isdigit() for p in pieces):
                return (int(pieces[0]), int(pieces[1]), int(pieces[2]), rel.as_posix())
        if len(parts) >= 3 and parts[-1].endswith(".md"):
            year, month = parts[-3], parts[-2]
            day = Path(parts[-1]).stem
            if year.isdigit() and month.isdigit() and day.isdigit():
                return (int(year), int(month), int(day), rel.as_posix())
        return (9999, 99, 99, rel.as_posix())

    paths = [p for p in daily_dir.rglob("*.md") if p.is_file()]
    paths.sort(key=_sort_key)
    recent = paths[-3:]
    out: list[str] = []
    for path in recent:
        try:
            out.append(path.relative_to(ph_root).as_posix())
        except Exception:
            out.append(str(path))
    return out


def run_dashboard(*, ph_root: Path, ctx: Context) -> int:
    print(BANNER_LINE)
    print(BANNER_SYSTEM if ctx.scope == "system" else BANNER_PROJECT)
    print(BANNER_LINE)
    print()

    _ = run_sprint_status(ph_project_root=ctx.ph_project_root, ctx=ctx, sprint="current")
    print()

    print("Recent Daily Status:")
    recent = _iter_recent_daily(ph_root=ph_root, ctx=ctx)
    if recent:
        for entry in recent:
            print(entry)
    print()

    print("Validation:")
    exit_code, _out_path, message = run_validate(
        ph_root=ph_root,
        ph_project_root=ctx.ph_project_root,
        ph_data_root=ctx.ph_data_root,
        scope=ctx.scope,
        quick=False,
        silent_success=False,
    )
    if message:
        print(message, end="")
    print()
    print(BANNER_LINE)
    return exit_code
