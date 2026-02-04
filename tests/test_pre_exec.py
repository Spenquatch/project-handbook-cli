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

