from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class HistoryEntry:
    timestamp: str
    entry: str


def format_history_entry(*, command: str | None, invocation_args: list[str]) -> str:
    if command is None:
        return "(default)"
    return "ph " + " ".join(invocation_args)


def append_history(*, ph_root: Path, entry: str, now: datetime | None = None) -> HistoryEntry:
    ts = (now or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} | {entry}\n"

    history_path = ph_root / ".project-handbook" / "history.log"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(line)

    return HistoryEntry(timestamp=ts, entry=entry)
