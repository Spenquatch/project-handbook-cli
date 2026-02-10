#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class DonePayload:
    status: str
    task_id: str
    finished_at: str
    log_path: str
    last_message_path: str
    exit_code: int


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(text)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Spawn a single Codex worker for exactly one task id.")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--workspace-root", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--full-auto", action="store_true", default=True)
    args = ap.parse_args()

    task_id = args.task_id
    workspace_root = Path(args.workspace_root).resolve()
    run_dir = Path(args.run_dir).resolve()
    prompt_file = Path(args.prompt_file).resolve()

    run_dir.mkdir(parents=True, exist_ok=True)
    done_path = run_dir / f"{task_id}.done"
    log_path = run_dir / "worker.log"
    pid_path = run_dir / "worker.pid"
    last_message_path = run_dir / "last_message.md"

    if done_path.exists():
        append_text(log_path, f"[spawn_worker] Refusing to start: {done_path} already exists.\n")
        return 2

    write_text(pid_path, f"{os.getpid()}\n")
    append_text(log_path, f"[spawn_worker] started_at={utc_now_iso()} task_id={task_id}\n")
    if not last_message_path.exists():
        write_text(last_message_path, "")

    prompt_text = prompt_file.read_text(encoding="utf-8")
    child: subprocess.Popen[bytes] | None = None

    def finalize(status: str, exit_code: int) -> None:
        payload = DonePayload(
            status=status,
            task_id=task_id,
            finished_at=utc_now_iso(),
            log_path=str(log_path),
            last_message_path=str(last_message_path),
            exit_code=exit_code,
        )
        atomic_write_text(done_path, json.dumps(payload.__dict__, indent=2, sort_keys=True) + "\n")

    def handle_term(signum: int, _frame) -> None:
        nonlocal child
        append_text(log_path, f"[spawn_worker] received signal={signum} at={utc_now_iso()}\n")
        if child and child.poll() is None:
            try:
                child.terminate()
            except Exception:
                pass
        finalize(status="failure", exit_code=128 + signum)
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, handle_term)
    signal.signal(signal.SIGINT, handle_term)

    cmd: list[str] = [
        "script",
        "-q",
        "/dev/null",
        "codex",
        "exec",
        "--json",
        "--color",
        "never",
        "--output-last-message",
        str(last_message_path),
        "-C",
        str(workspace_root),
    ]
    if args.full_auto:
        cmd.append("--full-auto")
    if args.model:
        cmd.extend(["-m", args.model])
    cmd.append(prompt_text)

    append_text(log_path, f"[spawn_worker] cmd={' '.join(cmd)}\n")

    with log_path.open("ab") as log_f:
        try:
            child = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=log_f,
                stderr=subprocess.STDOUT,
            )
        except FileNotFoundError as e:
            append_text(log_path, f"[spawn_worker] failed_to_spawn error={e}\n")
            finalize(status="failure", exit_code=127)
            return 127

        exit_code = child.wait()

    status = "success" if exit_code == 0 else "failure"
    append_text(log_path, f"[spawn_worker] finished status={status} exit_code={exit_code} at={utc_now_iso()}\n")
    finalize(status=status, exit_code=exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
