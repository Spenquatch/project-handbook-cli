from __future__ import annotations

import re
import subprocess
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def test_pre_exec_lint_and_audit_create_evidence_bundle(tmp_path: Path) -> None:
    assert _run(["ph", "init"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "sprint", "plan"], cwd=tmp_path).returncode == 0
    assert _run(["ph", "release", "plan", "--activate"], cwd=tmp_path).returncode == 0
    # Ensure the release plan scaffold satisfies the current validator contract so pre-exec audit
    # reaches the lint step (this test is about evidence bundling, not release plan authoring).
    releases_dir = tmp_path / ".project-handbook" / "releases"
    plan_paths = sorted(releases_dir.glob("v*/plan.md"))
    assert plan_paths, "Expected release plan.md under .project-handbook/releases/v*/plan.md"
    plan_path = plan_paths[0]
    existing = plan_path.read_text(encoding="utf-8")
    required = "\n".join(
        [
            "",
            "## Slot 1: Slot 1",
            "",
            "### Intended Gates",
            "- Gate: Placeholder",
            r"\s-\sGate: Placeholder",
            "",
            "## Slot 2: Slot 2",
            "",
            "### Intended Gates",
            "- Gate: Placeholder",
            r"\s-\sGate: Placeholder",
            "",
            "## Slot 3: Slot 3",
            "",
            "### Intended Gates",
            "- Gate: Placeholder",
            r"\s-\sGate: Placeholder",
            "",
        ]
    )
    if "## Slot 1:" not in existing:
        plan_path.write_text(existing + required, encoding="utf-8")

    create = _run(
        [
            "ph",
            "task",
            "create",
            "--title",
            "T",
            "--feature",
            "f",
            "--decision",
            "ADR-0001",
            "--points",
            "5",
            "--owner",
            "@a",
            "--prio",
            "P1",
            "--lane",
            "ops",
            "--session",
            "task-execution",
        ],
        cwd=tmp_path,
    )
    assert create.returncode == 0

    # Ensure the current sprint satisfies sprint gate validation so pre-exec audit reaches the lint step.
    tasks_dir = tmp_path / ".project-handbook" / "sprints" / "current" / "tasks"
    gate_dir = tasks_dir / "TASK-000-gate"
    gate_dir.mkdir(parents=True, exist_ok=True)
    (gate_dir / "task.yaml").write_text(
        "\n".join(
            [
                "id: TASK-000",
                "title: Sprint gate",
                "feature: f",
                "decision: ADR-0001",
                "owner: @a",
                "status: done",
                "story_points: 1",
                "prio: P1",
                "due: 2099-01-01",
                "acceptance: Gate is satisfied",
                "lane: ops",
                "depends_on: [FIRST_TASK]",
                "task_type: sprint-gate",
                "session: sprint-gate",
                "evidence_dir: status/evidence/TASK-000/",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (gate_dir / "validation.md").write_text(
        "\n".join(
            [
                "---",
                "task_id: TASK-000",
                "session: sprint-gate",
                "feature: f",
                "---",
                "",
                "# Validation",
                "",
                "Sprint Goal: Ensure the sprint is closeable",
                "Exit criteria: All checks pass",
                "",
                "- Evidence root: status/evidence/",
                "- Include secret-scan.txt",
                "- Sprint plan: sprints/current/plan.md",
                "",
            ]
        ),
        encoding="utf-8",
    )

    lint = _run(["ph", "pre-exec", "lint"], cwd=tmp_path)
    assert lint.returncode == 1
    assert "PRE-EXEC LINT FAILED" in lint.stdout

    audit = _run(["ph", "pre-exec", "audit"], cwd=tmp_path)
    assert audit.returncode == 1
    m = re.search(r"^EVIDENCE_DIR=(.+)$", audit.stdout, flags=re.MULTILINE)
    assert m, audit.stdout
    evidence_dir = Path(m.group(1)).expanduser()
    assert evidence_dir.exists()

    expected = [
        "sprint-status.txt",
        "release-status.txt",
        "task-list.txt",
        "feature-summary.txt",
        "handbook-validate.txt",
        "validation.json",
        "pre-exec-lint.txt",
    ]
    for name in expected:
        assert (evidence_dir / name).exists(), name
