from __future__ import annotations

import datetime as dt
import json
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .context import Context


class EvidenceError(RuntimeError):
    pass


_TASK_ID_RX = re.compile(r"^TASK-[0-9]+$")


def validate_task_id(task_id: str) -> str:
    task_id = (task_id or "").strip()
    if not _TASK_ID_RX.match(task_id):
        raise EvidenceError(f"Invalid task id: {task_id!r} (expected 'TASK-###')\n")
    return task_id


def slugify(name: str) -> str:
    value = (name or "").strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    value = value.strip("-")
    return value or "run"


def _validate_run_id(run_id: str) -> str:
    run_id = (run_id or "").strip()
    if not run_id:
        raise EvidenceError("Invalid run id: empty\n")
    if run_id in {".", ".."}:
        raise EvidenceError(f"Invalid run id: {run_id!r}\n")
    if "/" in run_id or "\\" in run_id:
        raise EvidenceError(f"Invalid run id: {run_id!r} (must not contain path separators)\n")
    return run_id


def utc_run_id(prefix: str) -> str:
    stamp = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{slugify(prefix)}"


def evidence_task_dir(*, ctx: Context, task_id: str) -> Path:
    task_id = validate_task_id(task_id)
    return ctx.ph_data_root / "status" / "evidence" / task_id


def evidence_run_dir(*, ctx: Context, task_id: str, run_id: str) -> Path:
    task_id = validate_task_id(task_id)
    run_id = _validate_run_id(run_id)
    return evidence_task_dir(ctx=ctx, task_id=task_id) / run_id


_EXPECTED_FILES = ("index.md", "cmd.txt", "stdout.txt", "stderr.txt", "meta.json")


def _index_markdown(*, task_id: str, run_id: str, today: dt.date) -> str:
    lines = [
        f"# Evidence: {task_id} / {run_id}",
        "",
        f"Created: {today:%Y-%m-%d}",
        "",
        "WARNING: Do not print or capture secret values in evidence (tokens, API keys, `.env` dumps).",
        "",
        "Expected artifacts (created by `ph evidence run`):",
        *[f"- `{name}`" for name in _EXPECTED_FILES],
        "",
    ]
    return "\n".join(lines)


def write_index_if_missing(*, run_dir: Path, task_id: str, run_id: str) -> None:
    index_path = run_dir / "index.md"
    if index_path.exists():
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    index_path.write_text(_index_markdown(task_id=task_id, run_id=run_id, today=dt.date.today()), encoding="utf-8")


@dataclass(frozen=True)
class CaptureResult:
    exit_code: int
    started_at_utc: str
    finished_at_utc: str
    duration_ms: int
    error: str | None = None


def _utc_iso(ts: dt.datetime) -> str:
    return ts.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_and_capture(*, cmd: list[str], run_dir: Path) -> int:
    if not cmd:
        raise EvidenceError("Missing command (use `-- <cmd> ...`)\n")

    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    meta_path = run_dir / "meta.json"
    cmd_path = run_dir / "cmd.txt"

    for path in (stdout_path, stderr_path, meta_path):
        if path.exists():
            raise EvidenceError(
                "Refusing to overwrite an existing evidence run capture.\n"
                f"Evidence run dir: {run_dir}\n"
                "Pick a new --run-id (or delete the existing stdout/stderr/meta files).\n"
            )

    run_dir.mkdir(parents=True, exist_ok=True)

    cmd_display = shlex.join(cmd)
    _write_text(cmd_path, cmd_display + "\n")

    started = dt.datetime.now(tz=dt.timezone.utc)
    try:
        with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
            proc = subprocess.run(cmd, stdout=out, stderr=err)
        exit_code = int(proc.returncode)
        finished = dt.datetime.now(tz=dt.timezone.utc)
        result = CaptureResult(
            exit_code=exit_code,
            started_at_utc=_utc_iso(started),
            finished_at_utc=_utc_iso(finished),
            duration_ms=int((finished - started).total_seconds() * 1000),
        )
    except FileNotFoundError as exc:
        finished = dt.datetime.now(tz=dt.timezone.utc)
        error_msg = f"Command not found: {cmd[0]!r} ({exc})\n"
        stdout_path.write_bytes(b"")
        stderr_path.write_text(error_msg, encoding="utf-8")
        result = CaptureResult(
            exit_code=127,
            started_at_utc=_utc_iso(started),
            finished_at_utc=_utc_iso(finished),
            duration_ms=int((finished - started).total_seconds() * 1000),
            error=error_msg.strip(),
        )

    meta: dict[str, object] = {
        "cmd": cmd,
        "cmd_display": cmd_display,
        "started_at_utc": result.started_at_utc,
        "finished_at_utc": result.finished_at_utc,
        "duration_ms": result.duration_ms,
        "exit_code": result.exit_code,
    }
    if result.error:
        meta["error"] = result.error
    _write_json(meta_path, meta)

    return result.exit_code


def run_evidence_new(*, ctx: Context, task_id: str, name: str | None, run_id: str | None) -> int:
    task_id = validate_task_id(task_id)
    label = (name or "").strip() or "manual"
    effective_run_id = _validate_run_id(run_id) if run_id else utc_run_id(label)

    task_dir = evidence_task_dir(ctx=ctx, task_id=task_id).resolve()
    run_dir = evidence_run_dir(ctx=ctx, task_id=task_id, run_id=effective_run_id).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    write_index_if_missing(run_dir=run_dir, task_id=task_id, run_id=effective_run_id)

    print(f"EVIDENCE_TASK_DIR={task_dir}")
    print(f"EVIDENCE_RUN_ID={effective_run_id}")
    print(f"EVIDENCE_RUN_DIR={run_dir}")
    print("FILES:")
    for name in _EXPECTED_FILES:
        print(f"- {name}")
    return 0


def run_evidence_run(*, ctx: Context, task_id: str, name: str, run_id: str | None, cmd: list[str]) -> int:
    task_id = validate_task_id(task_id)
    label = (name or "").strip()
    if not label:
        raise EvidenceError("Missing required flag: --name\n")

    effective_run_id = _validate_run_id(run_id) if run_id else utc_run_id(label)
    run_dir = evidence_run_dir(ctx=ctx, task_id=task_id, run_id=effective_run_id).resolve()
    write_index_if_missing(run_dir=run_dir, task_id=task_id, run_id=effective_run_id)

    exit_code = run_and_capture(cmd=cmd, run_dir=run_dir)
    print(f"EVIDENCE_RUN_DIR={run_dir}")
    print(f"EXIT_CODE={exit_code}")
    return exit_code
