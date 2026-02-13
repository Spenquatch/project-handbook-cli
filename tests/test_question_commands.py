from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ph", "--root", str(cwd), "--no-post-hook", *cmd],
        capture_output=True,
        text=True,
        env=env,
    )


def test_question_lifecycle_and_pre_exec_block(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    assert _run(["init"], cwd=tmp_path, env=env).returncode == 0
    assert _run(["sprint", "plan", "--sprint", "SPRINT-2099-01-01"], cwd=tmp_path, env=env).returncode == 0

    created = _run(
        [
            "question",
            "add",
            "--title",
            "Need operator decision",
            "--severity",
            "blocking",
            "--q-scope",
            "sprint",
            "--sprint",
            "SPRINT-2099-01-01",
            "--body",
            "Which environment should we deploy to?",
        ],
        cwd=tmp_path,
        env=env,
    )
    assert created.returncode == 0
    assert "✅ Created question: Q-0001" in created.stdout

    q_index = tmp_path / ".project-handbook" / "status" / "questions" / "index.json"
    assert q_index.exists()
    payload = json.loads(q_index.read_text(encoding="utf-8"))
    assert "Q-0001" in payload.get("open", [])
    assert "Q-0001" in payload.get("blocking_open", [])

    listing = _run(["question", "list", "--format", "json"], cwd=tmp_path, env=env)
    assert listing.returncode == 0
    listing_payload = json.loads(listing.stdout)
    assert any(i.get("id") == "Q-0001" for i in listing_payload.get("items", []))

    lint = _run(["pre-exec", "lint"], cwd=tmp_path, env=env)
    assert lint.returncode == 1
    assert "Blocking question is still open: Q-0001" in lint.stdout

    answered = _run(
        ["question", "answer", "--id", "Q-0001", "--answer", "Deploy to staging", "--by", "@user"],
        cwd=tmp_path,
        env=env,
    )
    assert answered.returncode == 0

    closed = _run(["question", "close", "--id", "Q-0001", "--resolution", "answered"], cwd=tmp_path, env=env)
    assert closed.returncode == 0
