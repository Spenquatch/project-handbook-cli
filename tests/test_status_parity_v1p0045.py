from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    ph_project_root = ph_root / ".project-handbook"
    config = ph_project_root / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_project_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_project_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_project_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_project_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")

    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "private": true,\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def _write_minimal_feature(ph_root: Path) -> None:
    feature_dir = ph_root / ".project-handbook" / "features" / "feature-a"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "overview.md").write_text(
        "\n".join(
            [
                "---",
                "title: Feature A",
                "type: feature",
                'dependencies: ["feature:feature-b"]',
                "---",
                "",
                "# Feature A",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (feature_dir / "status.md").write_text(
        "\n".join(
            [
                "# Status",
                "",
                "stage: in-progress",
                "",
                "now:",
                "- Implement core flow",
                "",
                "next:",
                "- Polish UX",
                "",
                "risks:",
                "- External dependency risk",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_minimal_sprint(ph_root: Path) -> None:
    sprint_dir = ph_root / ".project-handbook" / "sprints" / "2026" / "SPRINT-2026-01-01"
    (sprint_dir / "tasks").mkdir(parents=True, exist_ok=True)
    task_dir = sprint_dir / "tasks" / "TASK-001-minimal"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-001",
                "title: Implement minimal task",
                "owner: @owner",
                "lane: lane-a",
                "feature: feature-a",
                "decision: ADR-0001",
                "session: task-execution",
                "status: doing",
                "story_points: 3",
                "prio: P1",
                "due: 2026-01-01",
                "acceptance: done",
                "depends_on: FIRST_TASK",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_minimal_roadmap(ph_root: Path) -> None:
    roadmap_dir = ph_root / ".project-handbook" / "roadmap"
    roadmap_dir.mkdir(parents=True, exist_ok=True)
    (roadmap_dir / "now-next-later.md").write_text(
        "\n".join(
            [
                "now",
                "- feature-a: core",
                "next",
                "- feature-b: follow-up",
                "later",
                "- feature-c: someday",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_status_stdout_and_outputs_match_expected_shape(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_minimal_feature(tmp_path)
    _write_minimal_sprint(tmp_path)
    _write_minimal_roadmap(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2026-01-01T00:00:00Z"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "status"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    resolved = tmp_path.resolve()
    expected_preamble = f"\n> project-handbook@0.0.0 ph {resolved}\n> ph status\n\n"
    assert result.stdout.startswith(expected_preamble)

    current_json = (tmp_path / ".project-handbook" / "status" / "current.json").resolve()
    summary_md = (tmp_path / ".project-handbook" / "status" / "current_summary.md").resolve()
    assert current_json.exists()
    assert summary_md.exists()

    assert f"Generated: {current_json}\n" in result.stdout
    assert f"Updated: {summary_md}\n" in result.stdout
    assert "Updated feature status files\n" in result.stdout

    payload = json.loads(current_json.read_text(encoding="utf-8"))
    assert payload["generated_at"] == "2026-01-01T00:00:00Z"
    assert set(payload.keys()) == {"generated_at", "phases", "totals", "features", "features_summary", "project"}

    totals = payload["totals"]
    assert isinstance(totals, dict)
    assert set(totals.keys()) == {"backlog", "planned", "in_progress", "review", "blocked", "done"}

    phases = payload["phases"]
    assert isinstance(phases, list)
    assert phases and phases[0]["phase"].startswith("SPRINT-")

    decisions = set(phases[0].get("decisions") or [])
    assert {"ADR-0001"}.issubset(decisions)
