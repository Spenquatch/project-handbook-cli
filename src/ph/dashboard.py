from __future__ import annotations

from pathlib import Path

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

    paths = [p for p in daily_dir.glob("*.md") if p.is_file()]
    paths.sort(key=lambda p: p.name)
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

    _ = run_sprint_status(ph_root=ph_root, ctx=ctx, sprint="current")
    print()

    print("Recent Daily Status:")
    recent = _iter_recent_daily(ph_root=ph_root, ctx=ctx)
    if recent:
        for entry in recent:
            print(entry)
    else:
        print("  No daily status files yet")
    print()

    print("Validation:")
    exit_code, _out_path, message = run_validate(
        ph_root=ph_root,
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
