from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .clock import local_today_from_now as clock_local_today_from_now
from .clock import now as clock_now
from .context import Context
from .sprint import get_sprint_dates, sprint_dir_from_id


def _get_current_sprint_path(*, ph_data_root: Path) -> Path | None:
    link = ph_data_root / "sprints" / "current"
    if not link.exists():
        return None
    try:
        resolved = link.resolve()
    except FileNotFoundError:
        return None
    return resolved if resolved.exists() else None


def _resolve_sprint_dir(*, ctx: Context, sprint: str | None) -> Path | None:
    if sprint is None or sprint.strip() in {"", "current"}:
        return _get_current_sprint_path(ph_data_root=ctx.ph_data_root)
    return sprint_dir_from_id(ph_data_root=ctx.ph_data_root, sprint_id=sprint.strip())


def _read_plan_meta(*, sprint_dir: Path) -> dict[str, str]:
    plan_path = sprint_dir / "plan.md"
    if not plan_path.exists():
        return {}
    lines = plan_path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end_idx = lines[1:].index("---") + 1
    except ValueError:
        return {}
    meta: dict[str, str] = {}
    for line in lines[1:end_idx]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"')
    return meta


def _record_sprint_archive_entry(*, ph_data_root: Path, sprint_id: str, target: Path, env: dict[str, str]) -> None:
    archive_root = ph_data_root / "sprints" / "archive"
    archive_root.mkdir(parents=True, exist_ok=True)
    index_path = archive_root / "index.json"

    entries: list[dict[str, Any]] = []
    if index_path.exists():
        try:
            entries = json.loads(index_path.read_text(encoding="utf-8")).get("sprints", [])
        except Exception:
            entries = []

    entries = [e for e in entries if e.get("sprint") != sprint_id]

    meta = _read_plan_meta(sprint_dir=target)
    mode = (meta.get("mode") or "").strip().lower()
    archived_at = clock_now(env=env).replace(tzinfo=None).isoformat() + "Z"

    start_str = meta.get("start") or meta.get("date") or meta.get("created")
    end_str = meta.get("end")

    if mode == "bounded":
        today_str = clock_local_today_from_now(env=env).isoformat()
        if not start_str:
            start_str = today_str
        if not end_str:
            end_str = today_str
    else:
        if not start_str or not end_str:
            start_date, end_date = get_sprint_dates(sprint_id)
            start_str = start_str or start_date.isoformat()
            end_str = end_str or end_date.isoformat()

    entry = {
        "sprint": sprint_id,
        "archived_at": archived_at,
        "path": str(target.relative_to(ph_data_root)),
        "start": start_str,
        "end": end_str,
    }
    entries.append(entry)
    entries.sort(key=lambda e: e["archived_at"])
    index_path.write_text(json.dumps({"sprints": entries}, indent=2) + "\n", encoding="utf-8")


def archive_sprint_directory(*, ctx: Context, sprint_dir: Path, env: dict[str, str]) -> Path:
    sprint_id = sprint_dir.name
    year = sprint_id.split("-")[1] if "-" in sprint_id else sprint_id

    archive_year_dir = ctx.ph_data_root / "sprints" / "archive" / year
    archive_year_dir.mkdir(parents=True, exist_ok=True)
    target = archive_year_dir / sprint_id

    if target.exists():
        raise FileExistsError(f"Archive target already exists: {target}")

    shutil.move(str(sprint_dir), str(target))

    current_link = ctx.ph_data_root / "sprints" / "current"
    if current_link.exists() or current_link.is_symlink():
        try:
            current_link.unlink()
        except FileNotFoundError:
            pass

    _record_sprint_archive_entry(ph_data_root=ctx.ph_data_root, sprint_id=sprint_id, target=target, env=env)
    return target


def run_sprint_archive(*, ph_root: Path, ctx: Context, sprint: str | None, env: dict[str, str]) -> int:
    _ = ph_root  # reserved for future parity (link rewriting); v1 must not run repo-local scripts

    sprint_raw = sprint.strip() if sprint is not None else None
    if sprint_raw is None or sprint_raw in {"", "current"}:
        sprint_dir = _get_current_sprint_path(ph_data_root=ctx.ph_data_root)
        if sprint_dir is None:
            print("❌ No active sprint (sprints/current is not set).")
            print("Set one via `make sprint-plan` / `make sprint-open`, or pass `--sprint SPRINT-...`.")
            return 1
        sprint_id = sprint_dir.name
    else:
        sprint_id = sprint_raw
        sprint_dir = sprint_dir_from_id(ph_data_root=ctx.ph_data_root, sprint_id=sprint_id)

    if not sprint_dir.exists():
        print(f"⚠️  Sprint directory {sprint_dir} not found; nothing to archive.")
        return 0

    try:
        target = archive_sprint_directory(ctx=ctx, sprint_dir=sprint_dir, env=env)
    except FileExistsError as exc:
        print(f"⚠️  {exc}")
        return 1

    print(f"📦 Archived sprint {sprint_id} to {target}")
    return 0
