from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


def _utc_now_iso_z() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_status(*, ph_root: Path, ph_data_root: Path) -> tuple[Path, Path]:
    status_dir = ph_data_root / "status"
    status_dir.mkdir(parents=True, exist_ok=True)

    current_json = status_dir / "current.json"
    summary_md = status_dir / "current_summary.md"

    payload = {"generated_at": _utc_now_iso_z()}
    current_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Minimal parity: if there is no active sprint pointer, preserve the v0 empty-sprint summary output.
    current_link = ph_data_root / "sprints" / "current"
    if not current_link.exists():
        summary_md.write_text("# Current Sprint\n\n_No active sprint_\n", encoding="utf-8")
    else:
        summary_md.write_text("# Current Sprint\n\n_Current sprint detected._\n", encoding="utf-8")

    return current_json, summary_md
