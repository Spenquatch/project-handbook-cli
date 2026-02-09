#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tail_lines(path: Path, n: int = 200) -> str:
    if not path.exists():
        return ""
    try:
        with path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 4096
            data = b""
            while size > 0 and data.count(b"\n") <= n:
                step = min(block, size)
                size -= step
                f.seek(size)
                data = f.read(step) + data
            return b"\n".join(data.splitlines()[-n:]).decode("utf-8", errors="replace")
    except Exception:
        return ""


def is_process_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    else:
        return True


def kill_process(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return


def extract_verification_commands(kickoff_prompt: str) -> list[str]:
    lines = kickoff_prompt.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower() == "verification steps:":
            start = i + 1
            break
    if start is None:
        return []

    cmds: list[str] = []
    for line in lines[start:]:
        s = line.rstrip()
        if not s.strip():
            break
        if not s.lstrip().startswith("- "):
            break
        item = s.lstrip()[2:].strip()
        m = re.search(r"`([^`]+)`", item)
        if m:
            item = m.group(1).strip()
        lowered = item.lower()
        if lowered.startswith(("doc review", "documentation review", "doc review +", "doc review &")):
            continue
        if re.match(r"^(uv|pytest|python|rg|ruff|mypy|node|pnpm|npm|git|make|just|bash|zsh|sh)\\b", item):
            cmds.append(item)
        elif " " in item and any(tok in item for tok in (" -", " --", " ./", "src/", "tests/")):
            cmds.append(item)
    return cmds


def orchestrator_note(task_id: str) -> str:
    if task_id.startswith("I07-TTYPE-"):
        return (
            "Orchestrator note (to avoid common confusion):\n"
            "- `task_type` is a taxonomy and MUST NOT be the same thing as `session`.\n"
            "- Keep `session` values like `task-execution` and `research-discovery` as session templates.\n"
            "- Use a separate `task_type` default for legacy tasks (recommend `implementation` when missing).\n"
            "- Provide an explicit mapping table: `task_type` → required/allowed `session`.\n"
        )
    return ""


def format_worker_prompt(task_id: str, repo_root: Path, kickoff_prompt: str) -> str:
    note = orchestrator_note(task_id)
    note_block = (note + "\n") if note else ""
    return (
        f"You are a coding agent executing exactly one task: {task_id}.\n"
        f"Repo root: {repo_root}\n\n"
        "Hard rules:\n"
        "- Do not proceed to any other task IDs.\n"
        "- Follow the task’s kickoff_prompt exactly.\n"
        "- Only edit files under `cli_plan/` unless the kickoff_prompt explicitly lists non-`cli_plan/` paths.\n"
        "- Do NOT modify task queue JSON files (anything under `cli_plan/**/tasks*.json`, `cli_plan/backlog.json`) or anything under `.runs/`.\n"
        "- Do NOT edit/delete `scripts/` or `references/` unless the kickoff_prompt explicitly asks.\n"
        "- Do NOT run git commands that change state (`git restore|reset|checkout|clean|commit|rebase|merge`). Read-only is OK (`git diff`, `git status`).\n"
        "- If you notice unrelated working-tree changes, IGNORE them and continue; do not attempt to revert them.\n"
        "- Run the verification commands listed in the kickoff_prompt.\n"
        "- Produce a concise final message including: files changed, commands run, verification results, and any follow-ups.\n\n"
        + note_block
        + "Task kickoff_prompt (verbatim):\n"
        + kickoff_prompt.strip()
        + "\n"
    )


@dataclass
class ActiveTask:
    task_id: str
    workstream_id: str
    order: int
    run_dir: Path
    pid: int | None
    log_path: Path
    last_message_path: Path
    done_path: Path


def load_queue(queue_path: Path) -> dict[str, Any]:
    data = read_json(queue_path)
    if not isinstance(data.get("tasks"), list):
        raise SystemExit(f"Queue missing top-level tasks array: {queue_path}")
    return data


def done_set(queue: dict[str, Any]) -> set[str]:
    return {t["id"] for t in queue["tasks"] if t.get("status") == "done" and t.get("id")}


def runnable_todo_tasks(queue: dict[str, Any], done: set[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in queue["tasks"]:
        if t.get("status") != "todo":
            continue
        deps = t.get("depends_on") or []
        if all(d in done for d in deps):
            out.append(t)
    out.sort(key=lambda t: int(t.get("order", 10**9)))
    return out


def pick_dispatchable(
    queue: dict[str, Any],
    active_by_ws: set[str],
    active_ids: set[str],
    done: set[str],
) -> list[dict[str, Any]]:
    candidates = runnable_todo_tasks(queue, done)
    per_ws: dict[str, dict[str, Any]] = {}
    for t in candidates:
        ws = t.get("workstream_id") or "WS-UNKNOWN"
        if ws in active_by_ws:
            continue
        if t.get("id") in active_ids:
            continue
        if ws not in per_ws:
            per_ws[ws] = t
    return sorted(per_ws.values(), key=lambda t: int(t.get("order", 10**9)))


def ensure_prompt(run_dir: Path, task_id: str, repo_root: Path, kickoff_prompt: str) -> Path:
    prompt_path = run_dir / "prompt.md"
    if prompt_path.exists():
        return prompt_path
    write_text(prompt_path, format_worker_prompt(task_id, repo_root, kickoff_prompt))
    return prompt_path


def choose_workspace_root(repo_root: Path, kickoff_prompt: str) -> Path:
    """
    Constrain doc-only tasks to `cli_plan/` to prevent accidental code edits.
    If the kickoff prompt references non-cli_plan paths (e.g., src/ or tests/), use the full repo root.
    """
    text = kickoff_prompt or ""
    # Fast path: any mention of src/ or tests/ implies code changes.
    if re.search(r"(^|\\s)(src/|tests/)", text):
        return repo_root

    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower() == "files likely to change:":
            start = i + 1
            break
    if start is None:
        return repo_root

    paths: list[str] = []
    for line in lines[start:]:
        s = line.strip()
        if not s:
            break
        if not s.startswith("- "):
            break
        item = s[2:].strip()
        # Normalize and keep the leading path token.
        paths.append(item.split()[0])

    if paths and all(p.startswith("cli_plan/") for p in paths):
        return repo_root / "cli_plan"
    return repo_root


def spawn_worker(repo_root: Path, workspace_root: Path, run_dir: Path, task_id: str, prompt_path: Path) -> None:
    cmd = [
        sys.executable,
        str((repo_root / "scripts" / "spawn_worker.py").resolve()),
        "--task-id",
        task_id,
        "--repo-root",
        str(repo_root),
        "--workspace-root",
        str(workspace_root),
        "--run-dir",
        str(run_dir),
        "--prompt-file",
        str(prompt_path),
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(repo_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    # Claim the slot immediately to avoid races before the worker writes worker.pid.
    try:
        write_text(run_dir / "worker.pid", f"{proc.pid}\n")
    except Exception:
        pass


def active_tasks_from_runs(run_state_root: Path, queue: dict[str, Any]) -> dict[str, ActiveTask]:
    active: dict[str, ActiveTask] = {}
    for t in queue["tasks"]:
        if t.get("status") != "in_progress":
            continue
        task_id = t["id"]
        ws = t.get("workstream_id") or "WS-UNKNOWN"
        run_dir = run_state_root / task_id
        pid = None
        pid_path = run_dir / "worker.pid"
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text(encoding="utf-8").strip())
            except Exception:
                pid = None
        active[task_id] = ActiveTask(
            task_id=task_id,
            workstream_id=ws,
            order=int(t.get("order", 10**9)),
            run_dir=run_dir,
            pid=pid,
            log_path=run_dir / "worker.log",
            last_message_path=run_dir / "last_message.md",
            done_path=run_dir / f"{task_id}.done",
        )
    return active


def update_task(queue: dict[str, Any], task_id: str, patch: dict[str, Any]) -> None:
    for t in queue["tasks"]:
        if t.get("id") == task_id:
            t.update(patch)
            return
    raise KeyError(task_id)


def mark_in_progress(queue: dict[str, Any], task_id: str) -> None:
    task = next(t for t in queue["tasks"] if t.get("id") == task_id)
    task["status"] = "in_progress"
    task.setdefault("started_at", utc_now_iso())


def mark_done(queue: dict[str, Any], task_id: str) -> None:
    update_task(queue, task_id, {"status": "done", "completed_at": utc_now_iso()})


def mark_blocked(queue: dict[str, Any], task_id: str, blockers: list[str], unblock_steps: list[str]) -> None:
    update_task(
        queue,
        task_id,
        {
            "status": "blocked",
            "blocked_at": utc_now_iso(),
            "blockers": blockers,
            "unblock_steps": unblock_steps,
        },
    )


def load_done_payload(done_path: Path) -> dict[str, Any] | None:
    if not done_path.exists():
        return None
    try:
        return json.loads(done_path.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "failure", "exit_code": 1, "parse_error": True}


def run_verification(repo_root: Path, task: dict[str, Any]) -> tuple[bool, list[str]]:
    kickoff = task.get("kickoff_prompt") or ""
    cmds = extract_verification_commands(kickoff)
    ran: list[str] = []
    for cmd in cmds:
        ran.append(cmd)
        res = subprocess.run(cmd, cwd=str(repo_root), shell=True)
        if res.returncode != 0:
            return False, ran
    return True, ran


def queue_complete(queue: dict[str, Any]) -> bool:
    return all(t.get("status") == "done" for t in queue["tasks"])


def kqueue_wait_for_change(path: Path, timeout_s: int) -> int:
    try:
        import select  # noqa: PLC0415

        kq = select.kqueue()
        fd = os.open(str(path), os.O_RDONLY)
        try:
            kev = select.kevent(
                fd,
                filter=select.KQ_FILTER_VNODE,
                flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR,
                fflags=select.KQ_NOTE_WRITE | select.KQ_NOTE_EXTEND | select.KQ_NOTE_ATTRIB | select.KQ_NOTE_LINK,
            )
            kq.control([kev], 0, 0)
            events = kq.control(None, 1, timeout_s)
            return 1 if events else 0
        finally:
            os.close(fd)
    except Exception:
        return -1


def main() -> int:
    ap = argparse.ArgumentParser(description="Orchestrate a workstreamed task queue using DONE sentinels.")
    ap.add_argument("--queue", required=True, help="Path to canonical task queue JSON")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--run-state-root", required=True)
    ap.add_argument("--max-workers", type=int, default=4)
    ap.add_argument("--tick-seconds", type=int, default=600, help="Fallback check interval (>=600)")
    args = ap.parse_args()

    if args.tick_seconds < 600:
        raise SystemExit("--tick-seconds must be >= 600 (10 minutes) unless debugging")

    queue_path = Path(args.queue).resolve()
    repo_root = Path(args.repo_root).resolve()
    run_state_root = Path(args.run_state_root).resolve()
    run_state_root.mkdir(parents=True, exist_ok=True)

    blocked_seen = False
    stall_state: dict[str, tuple[tuple[float, int] | None, int]] = {}

    while True:
        queue = load_queue(queue_path)
        done = done_set(queue)
        active = active_tasks_from_runs(run_state_root, queue)

        running_active = [
            a for a in active.values() if not a.done_path.exists() and a.pid is not None and is_process_running(a.pid)
        ]
        available_slots = max(0, args.max_workers - len(running_active))

        # Resume in_progress tasks only up to available slots.
        if available_slots > 0:
            resume_candidates = []
            for task_id, a in active.items():
                if a.done_path.exists():
                    continue
                if a.pid is not None and is_process_running(a.pid):
                    continue
                resume_candidates.append(a)
            resume_candidates.sort(key=lambda a: a.order)
            for a in resume_candidates[:available_slots]:
                task = next(t for t in queue["tasks"] if t.get("id") == a.task_id)
                run_dir = run_state_root / a.task_id
                run_dir.mkdir(parents=True, exist_ok=True)
                prompt_path = ensure_prompt(run_dir, a.task_id, repo_root, task.get("kickoff_prompt") or "")
                ws_root = choose_workspace_root(repo_root, task.get("kickoff_prompt") or "")
                spawn_worker(repo_root, ws_root, run_dir, a.task_id, prompt_path)
                print(f"START {a.task_id} workstream={a.workstream_id} (resume in_progress)")
                available_slots -= 1
                if available_slots <= 0:
                    break

        # Reload after potential spawns.
        queue = load_queue(queue_path)
        done = done_set(queue)
        active = active_tasks_from_runs(run_state_root, queue)

        running_active = [
            a for a in active.values() if not a.done_path.exists() and a.pid is not None and is_process_running(a.pid)
        ]
        active_by_ws = {a.workstream_id for a in running_active}
        active_ids = {a.task_id for a in running_active}
        available_slots = max(0, args.max_workers - len(running_active))

        # Dispatch new tasks if not blocked.
        if not blocked_seen and available_slots > 0:
            dispatchables = pick_dispatchable(queue, active_by_ws, active_ids, done)
            for t in dispatchables[:available_slots]:
                task_id = t["id"]
                ws = t.get("workstream_id") or "WS-UNKNOWN"
                run_dir = run_state_root / task_id
                run_dir.mkdir(parents=True, exist_ok=True)
                prompt_path = ensure_prompt(run_dir, task_id, repo_root, t.get("kickoff_prompt") or "")
                mark_in_progress(queue, task_id)
                write_json(queue_path, queue)
                ws_root = choose_workspace_root(repo_root, t.get("kickoff_prompt") or "")
                spawn_worker(repo_root, ws_root, run_dir, task_id, prompt_path)
                print(f"START {task_id} workstream={ws} order={t.get('order')}")
                active_by_ws.add(ws)

        # Process any completed sentinels for tasks still marked in_progress.
        queue = load_queue(queue_path)
        active = active_tasks_from_runs(run_state_root, queue)
        for task_id, a in sorted(active.items(), key=lambda kv: kv[1].order):
            payload = load_done_payload(a.done_path)
            if not payload:
                continue
            if payload.get("parse_error"):
                continue

            task = next(t for t in queue["tasks"] if t.get("id") == task_id)
            if task.get("status") in ("done", "blocked"):
                continue

            status = payload.get("status") or "failure"
            # Note: payload exit_code may be 0; do not use `or` defaulting.
            exit_code = int(payload.get("exit_code", 1))
            if status == "success" and exit_code == 0:
                ok, ran = run_verification(repo_root, task)
                if ok:
                    mark_done(queue, task_id)
                    write_json(queue_path, queue)
                    print(f"DONE {task_id} verified={' && '.join(ran) if ran else 'none'}")
                else:
                    failure_path = a.run_dir / "failure.md"
                    write_text(
                        failure_path,
                        "# Verification failed\n\n"
                        f"- task_id: {task_id}\n"
                        f"- finished_at: {utc_now_iso()}\n"
                        f"- attempted: {ran}\n\n"
                        "Re-run the last command and fix the failure.\n",
                    )
                    mark_blocked(
                        queue,
                        task_id,
                        blockers=["Verification command failed (see failure.md)."],
                        unblock_steps=[
                            f"Open {failure_path} and re-run failing verification command(s).",
                            "Fix the underlying issue, then re-run verification.",
                        ],
                    )
                    write_json(queue_path, queue)
                    print(f"BLOCKED {task_id} reason=verification_failed")
                    blocked_seen = True
            else:
                failure_path = a.run_dir / "failure.md"
                log_tail = tail_lines(a.log_path, 200)
                write_text(
                    failure_path,
                    "# Worker failure\n\n"
                    f"- task_id: {task_id}\n"
                    f"- finished_at: {utc_now_iso()}\n"
                    f"- exit_code: {exit_code}\n\n"
                    "## Last 200 log lines\n\n"
                    "```text\n"
                    + log_tail
                    + "\n```\n",
                )
                mark_blocked(
                    queue,
                    task_id,
                    blockers=["Worker failed (see failure.md)."],
                    unblock_steps=[
                        f"Inspect {a.log_path} and {a.last_message_path}.",
                        f"Fix the root cause and re-run task {task_id}.",
                    ],
                )
                write_json(queue_path, queue)
                print(f"BLOCKED {task_id} reason=worker_failure exit_code={exit_code}")
                blocked_seen = True

        queue = load_queue(queue_path)
        if queue_complete(queue):
            print(f"QUEUE_COMPLETE {queue_path}")
            return 0

        unfinished_running = [
            a
            for a in active_tasks_from_runs(run_state_root, queue).values()
            if not a.done_path.exists() and a.pid is not None and is_process_running(a.pid)
        ]
        if blocked_seen and not unfinished_running:
            print(f"STOP_ON_BLOCKED {queue_path}")
            return 1

        wait_result = kqueue_wait_for_change(run_state_root, timeout_s=args.tick_seconds)
        if wait_result == 0:
            # 10-minute tick without filesystem activity → stall detection.
            queue = load_queue(queue_path)
            active = active_tasks_from_runs(run_state_root, queue)
            for task_id, a in active.items():
                if a.done_path.exists():
                    stall_state.pop(task_id, None)
                    continue
                stat = None
                if a.log_path.exists():
                    st = a.log_path.stat()
                    stat = (st.st_mtime, st.st_size)
                prev, unchanged = stall_state.get(task_id, (None, 0))
                if prev == stat:
                    unchanged += 1
                else:
                    unchanged = 0
                stall_state[task_id] = (stat, unchanged)
                if unchanged >= 2:
                    if a.pid is not None and is_process_running(a.pid):
                        kill_process(a.pid)
                    failure_path = a.run_dir / "failure.md"
                    write_text(
                        failure_path,
                        "# Worker stalled\n\n"
                        f"- task_id: {task_id}\n"
                        f"- detected_at: {utc_now_iso()}\n\n"
                        "## Last 200 log lines\n\n"
                        "```text\n"
                        + tail_lines(a.log_path, 200)
                        + "\n```\n",
                    )
                    mark_blocked(
                        queue,
                        task_id,
                        blockers=["Worker appears stalled (no log activity for 20+ minutes)."],
                        unblock_steps=[
                            f"Inspect {a.log_path} and {a.last_message_path}.",
                            "Re-run the task and ensure Codex can execute required commands.",
                        ],
                    )
                    write_json(queue_path, queue)
                    print(f"BLOCKED {task_id} reason=stalled")
                    blocked_seen = True

        if wait_result == -1:
            time.sleep(args.tick_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
