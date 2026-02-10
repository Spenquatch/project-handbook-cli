#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_queue_file(path: Path) -> bool:
    try:
        data = read_json(path)
    except Exception:
        return False
    if data.get("deprecated") is True:
        return False
    tasks = data.get("tasks")
    return isinstance(tasks, list)


def discover_queues(plan_root: Path) -> list[Path]:
    queues: list[Path] = []

    initiatives_index = plan_root / "initiatives" / "index.json"
    if initiatives_index.exists():
        idx = read_json(initiatives_index)
        for init in idx.get("initiatives") or []:
            if init.get("status") != "active":
                continue
            p = init.get("path")
            if not p:
                continue
            queues.append((plan_root.parent / p).resolve())

    legacy = sorted(plan_root.glob("**/tasks_initiatives_*.json"))
    for p in legacy:
        if is_queue_file(p):
            queues.append(p.resolve())

    # Stable order, but avoid duplicates when an initiative path also matches legacy globbing.
    seen: set[Path] = set()
    out: list[Path] = []
    for p in queues:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Discover and orchestrate all runnable plan queues.")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--plan-root", required=True)
    ap.add_argument("--run-state-root", required=True)
    ap.add_argument("--max-workers", type=int, default=4)
    ap.add_argument("--tick-seconds", type=int, default=600)
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    plan_root = Path(args.plan_root).resolve()
    run_state_root = Path(args.run_state_root).resolve()

    queues = discover_queues(plan_root)
    if not queues:
        print(f"NO_QUEUES plan_root={plan_root}", flush=True)
        return 0

    print("QUEUES_DISCOVERED", flush=True)
    for p in queues:
        print(f"- {p}", flush=True)

    child: subprocess.Popen[str] | None = None

    def _terminate_child(signum: int) -> None:
        nonlocal child
        if child is None:
            return
        if child.poll() is not None:
            return
        try:
            child.terminate()
            child.wait(timeout=10)
        except Exception:
            try:
                child.kill()
            except Exception:
                pass

    def handle_term(signum: int, _frame) -> None:
        print(f"PLAN_SIGNAL {signum}", flush=True)
        _terminate_child(signum)
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, handle_term)
    signal.signal(signal.SIGINT, handle_term)

    for queue_path in queues:
        print(f"QUEUE_START {queue_path}", flush=True)
        cmd = [
            sys.executable,
            "-u",
            str((repo_root / "scripts" / "orchestrate_queue.py").resolve()),
            "--queue",
            str(queue_path),
            "--repo-root",
            str(repo_root),
            "--run-state-root",
            str(run_state_root),
            "--max-workers",
            str(args.max_workers),
            "--tick-seconds",
            str(args.tick_seconds),
        ]
        try:
            child = subprocess.Popen([str(c) for c in cmd], cwd=str(repo_root), text=True)
            return_code = child.wait()
        finally:
            child = None

        if return_code != 0:
            print(f"QUEUE_STOP return_code={return_code} {queue_path}", flush=True)
            return return_code
        print(f"QUEUE_COMPLETE {queue_path}", flush=True)

    print("ALL_QUEUES_COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
