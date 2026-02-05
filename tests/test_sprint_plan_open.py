from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path, *, validation_rules: str = "{}") -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.1.0,<0.2.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_root / "process" / "checks" / "validation_rules.json").write_text(validation_rules, encoding="utf-8")
    (ph_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def test_sprint_plan_creates_skeleton_and_prints_project_hints(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    sprint_dir = tmp_path / "sprints" / "2099" / "SPRINT-2099-01-01"
    plan_file = sprint_dir / "plan.md"
    assert result.stdout.splitlines() == [
        f"Created sprint plan: {plan_file}",
        "Sprint structure seeded:",
        f"  📁 {sprint_dir}/",
        f"  📁 {sprint_dir}/tasks/ (ready for task creation)",
        "Next steps:",
        "  1. Edit plan.md with goals, lanes, and integration tasks",
        "  2. Create tasks via `make task-create ...`",
        "  3. Review `status/current_summary.md` after generating status",
        "  4. Re-run `make onboarding session sprint-planning` for facilitation tips",
        "Sprint scaffold ready:",
        "  1. Edit sprints/current/plan.md with goals, lanes, and integration tasks",
        "  2. Seed tasks via 'make task-create title=... feature=... decision=ADR-###'",
        "  3. Re-run 'make sprint-status' to confirm health + next-up ordering",
        "  4. Run 'make validate-quick' before handing off to another agent",
        "  5. Need facilitation tips? 'make onboarding session sprint-planning'",
    ]
    assert sprint_dir.exists()
    assert (sprint_dir / "tasks").exists()
    assert (sprint_dir / "plan.md").exists()
    assert (tmp_path / "sprints" / "current").resolve() == sprint_dir.resolve()

def test_sprint_plan_bounded_template_matches_legacy(tmp_path: Path) -> None:
    _write_minimal_ph_root(
        tmp_path,
        validation_rules='{"sprint_management": {"mode": "bounded"}}\n',
    )
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    plan_path = tmp_path / "sprints" / "2099" / "SPRINT-2099-01-01" / "plan.md"
    assert plan_path.exists()

    expected_lines = [
        "---",
        "title: Sprint Plan - SPRINT-2099-01-01",
        "type: sprint-plan",
        "date: 2099-01-01",
        "sprint: SPRINT-2099-01-01",
        "mode: bounded",
        "tags: [sprint, planning]",
        "release: null",
        "---",
        "",
        "# Sprint Plan: SPRINT-2099-01-01",
        "",
        "## Sprint Model",
        (
            "This sprint uses **bounded planning** (ADR-0013): sprint scope is defined by "
            "*work boundaries* and *parallel lanes*, not a fixed calendar window or points cap."
        ),
        "",
        "## Sprint Goal",
        "1. [ ] Primary outcome (clear deliverable + validation gate)",
        "2. [ ] Secondary outcome",
        "3. [ ] Integration outcome (if multiple lanes)",
        "",
        "## Release Alignment (Explicit)",
        "If you have an active release, it is a *measurement context* — not an automatic scope cap.",
        "",
        "| Bucket | Intention | Notes |",
        "|--------|-----------|-------|",
        "| Release-critical | Work that must move critical-path features | |",
        "| Release-support | Work that enables the release but lives outside assigned features | |",
        "| Non-release | Necessary work that does not serve the active release | |",
        "",
        "## Boundaries (Lanes)",
        "Define lanes to maximize parallel execution and minimize cross-lane coupling.",
        "",
        "| Lane | Scope | Success Output |",
        "|------|-------|----------------|",
        "| `service/<name>` | | |",
        "| `infra/<name>` | | |",
        "| `handbook/<area>` | | |",
        "| `integration/<scope>` | | |",
        "",
        "## Integration Tasks",
        "- List explicit cross-lane integration tasks and their dependencies.",
        "",
        "## Task Creation Guide",
        "```bash",
        (
            "make task-create title=\"Task Name\" feature=feature-name decision=ADR-XXX points=3 "
            "lane=\"handbook/automation\" release=current"
        ),
        (
            "make task-create title=\"Gate: <name>\" feature=feature-name decision=ADR-XXX points=3 "
            "lane=\"integration/<scope>\" release=current gate=true"
        ),
        "```",
        "",
        "## Telemetry (Points)",
        "- Story points are tracked for throughput/velocity trends, not for limiting sprint scope.",
        "",
        "## Dependencies & Risks",
        "- External dependencies",
        "- Cross-lane dependencies (integration risk)",
        "- Unknowns / validation gaps",
        "",
        "## Success Criteria",
        "- [ ] Lanes are explicit and independently executable",
        "- [ ] Integration tasks are explicit and dependency-linked",
        "- [ ] All committed tasks completed (points recorded for telemetry)",
    ]
    expected = "\n".join(expected_lines) + "\n"

    assert plan_path.read_text(encoding="utf-8") == expected


def test_sprint_plan_prints_pnpm_make_preamble_when_package_json_present(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )
    env = dict(os.environ)

    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "sprint", "plan", "--sprint", "SPRINT-2099-01-01"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    lines = result.stdout.splitlines()
    assert lines[0:4] == [
        "",
        f"> project-handbook@0.0.0 make {tmp_path.resolve()}",
        "> make -- sprint-plan",
        "",
    ]


def test_sprint_plan_and_open_work_in_system_scope(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    env = dict(os.environ)

    planned = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--scope",
            "system",
            "--no-post-hook",
            "sprint",
            "plan",
            "--sprint",
            "SPRINT-2099-01-02",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert planned.returncode == 0
    assert planned.stdout.splitlines() == [
        "System-scope sprint scaffold ready:",
        "  1. Edit .project-handbook/system/sprints/current/plan.md with goals, lanes, and integration tasks",
        "  2. Seed tasks via 'ph --scope system task create --title ... --feature ... --decision ADR-###'",
        "  3. Re-run 'ph --scope system sprint status' to confirm health + next-up ordering",
        "  4. Run 'ph --scope system validate --quick' before handing off to another agent",
    ]

    sprint_dir = tmp_path / ".project-handbook" / "system" / "sprints" / "2099" / "SPRINT-2099-01-02"
    plan_md = sprint_dir / "plan.md"
    assert plan_md.exists()
    text = plan_md.read_text(encoding="utf-8")
    assert "release: null" in text
    assert "Release Context" not in text

    opened = subprocess.run(
        [
            "ph",
            "--root",
            str(tmp_path),
            "--scope",
            "system",
            "--no-post-hook",
            "sprint",
            "open",
            "--sprint",
            "SPRINT-2099-01-02",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert opened.returncode == 0
    assert opened.stdout.strip() == "✅ Current sprint set to: SPRINT-2099-01-02"
    assert (tmp_path / ".project-handbook" / "system" / "sprints" / "current").resolve() == sprint_dir.resolve()
