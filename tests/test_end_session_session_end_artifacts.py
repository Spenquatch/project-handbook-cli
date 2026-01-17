from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def test_end_session_skip_codex_writes_session_end_artifacts(tmp_path: Path) -> None:
    ph_root = tmp_path / "ph_root"
    ph_root.mkdir()
    _write_minimal_ph_root(ph_root)

    rollout_path = tmp_path / "rollout.jsonl"
    session_meta = {
        "type": "session_meta",
        "payload": {
            "id": "sess-2",
            "timestamp": "2026-01-14T00:00:00Z",
            "cli_version": "0.0.0",
            "cwd": str(ph_root),
            "git": {},
        },
    }
    response_item = {
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Hello from fixture"}],
        },
    }
    rollout_path.write_text(
        json.dumps(session_meta, indent=2) + "\n" + json.dumps(response_item, indent=2) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "ph",
            "end-session",
            "--skip-codex",
            "--session-end-mode",
            "continue-task",
            "--force",
            "--log",
            str(rollout_path),
            "--root",
            str(ph_root),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)

    session_end_dir = ph_root / "process" / "sessions" / "session_end"
    index_path = session_end_dir / "session_end_index.json"
    assert index_path.exists()

    summaries = list(session_end_dir.glob("**/*.md"))
    prompts = list(session_end_dir.glob("**/*.prompt.txt"))
    assert summaries, "Expected at least one session_end summary markdown file"
    assert prompts, "Expected at least one session_end prompt file"

    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["records"], "Expected session_end index to contain at least one record"
    record = index["records"][0]
    summary_rel = Path(record["summary_path"])
    prompt_rel = Path(record["prompt_path"])
    assert (ph_root / summary_rel).exists()
    assert (ph_root / prompt_rel).exists()
