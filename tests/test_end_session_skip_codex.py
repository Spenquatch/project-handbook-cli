from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
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


def test_end_session_skip_codex_writes_summary_and_manifest(tmp_path: Path) -> None:
    ph_root = tmp_path / "ph_root"
    ph_root.mkdir()
    _write_minimal_ph_root(ph_root)

    rollout_path = tmp_path / "rollout.jsonl"
    session_meta = {
        "type": "session_meta",
        "timestamp": "2026-01-14T00:00:00Z",
        "payload": {
            "id": "sess-1",
            "timestamp": "2026-01-14T00:00:00Z",
            "cli_version": "0.0.0",
            "cwd": str(ph_root),
            "git": {},
        },
    }
    response_item = {
        "type": "response_item",
        "timestamp": "2026-01-14T00:00:00Z",
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
        ["ph", "end-session", "--skip-codex", "--force", "--log", str(rollout_path), "--root", str(ph_root)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)

    logs_dir = ph_root / "process" / "sessions" / "logs"
    manifest_path = logs_dir / "manifest.json"
    assert (logs_dir / "latest_summary.md").exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["sessions"][0]["session_id"] == "sess-1"

    expected_summary = (
        Path("process")
        / "sessions"
        / "logs"
        / "2026"
        / "01"
        / "14"
        / "sess-1"
        / "000000_summary.md"
    )
    assert manifest["sessions"][0]["summary_path"] == expected_summary.as_posix()
    assert (ph_root / expected_summary).exists()
    summary_text = (ph_root / expected_summary).read_text(encoding="utf-8")
    # Local time zone differs across machines (CI runners are typically UTC).
    # Only assert the stable transcript payload.
    assert "USER :: Hello from fixture" in summary_text
    assert "- Hello from fixture (?) – no file changes" in summary_text
