from __future__ import annotations

import dataclasses
import datetime as dt
import os
import re
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from .context import Context
from .feature_status_updater import run_feature_summary
from .release import run_release_status
from .sprint_status import run_sprint_status
from .task_view import run_task_list
from .validate_docs import run_validate


@dataclasses.dataclass(frozen=True)
class Finding:
    task_id: str
    severity: str  # "FAIL" | "WARN"
    message: str
    file: Path | None = None
    line: int | None = None
    excerpt: str | None = None


class PreExecError(RuntimeError):
    pass


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_simple_front_matter(markdown: str) -> dict[str, str]:
    if not markdown.startswith("---\n"):
        return {}
    end = markdown.find("\n---\n", 4)
    if end == -1:
        return {}
    block = markdown[4:end]
    out: dict[str, str] = {}
    for raw in block.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)\s*$", raw)
        if not m:
            continue
        key = m.group(1)
        value = m.group(2).strip().strip('"').strip("'")
        out[key] = value
    return out


def _parse_task_yaml_top_level(task_yaml: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in task_yaml.splitlines():
        if not raw or raw.startswith((" ", "\t")):
            continue
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)\s*$", raw)
        if not m:
            continue
        key = m.group(1)
        value = m.group(2).strip()
        out[key] = value.strip('"').strip("'")
    return out


def _extract_sprint_id_from_plan(*, plan_path: Path) -> str:
    fm = _parse_simple_front_matter(_read_text(plan_path))
    if "sprint" in fm and fm["sprint"]:
        return fm["sprint"]
    for raw in _read_text(plan_path).splitlines():
        m = re.match(r"^sprint:\s*(\S+)\s*$", raw)
        if m:
            return m.group(1)
    raise ValueError(f"Unable to determine sprint id from {plan_path}")


def _iter_task_dirs(*, tasks_dir: Path) -> list[Path]:
    return sorted([p for p in tasks_dir.glob("TASK-*") if p.is_dir()])


def _task_id_from_dir_name(task_dir: Path) -> str:
    m = re.match(r"^(TASK-\d{3})-", task_dir.name)
    return m.group(1) if m else task_dir.name


def _is_nonempty_file(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except FileNotFoundError:
        return False


def _compile_patterns() -> dict[str, list[tuple[str, re.Pattern[str]]]]:
    def ci(p: str) -> re.Pattern[str]:
        return re.compile(p, flags=re.IGNORECASE)

    def cs(p: str) -> re.Pattern[str]:
        return re.compile(p)

    universal = [
        ("TBD", cs(r"\bTBD\b")),
        ("TODO", cs(r"\bTODO\b")),
        ("FIXME", cs(r"\bFIXME\b")),
        ("WIP", cs(r"\bWIP\b")),
        ("MAYBE", ci(r"\bmaybe\b")),
        ("PROBABLY", ci(r"\bprobably\b")),
        ("SOMEHOW", ci(r"\bsomehow\b")),
        ("SOMETIME", ci(r"\bsometime\b")),
        ("LATER", ci(r"\blater\b")),
        ("EVENTUALLY", ci(r"\beventually\b")),
        ("ASAP", ci(r"\basap\b")),
        ("TBD_DATE", cs(r"\b20\d{2}-\d{2}-\d{2}\b.*\bTBD\b")),
    ]

    execution = [
        ("DECIDE", ci(r"\bdecide\b|\bdecision\b")),
        ("RESEARCH", ci(r"\bresearch\b|\binvestigate\b|\bexplore\b")),
        ("FIGURE_OUT", ci(r"\bfigure out\b|\bwork out\b")),
    ]

    discovery = [
        ("UNCLEAR", ci(r"\bunclear\b|\bnot sure\b")),
        ("MAYBE", ci(r"\bmaybe\b|\bpossibly\b")),
    ]

    return {"universal": universal, "execution": execution, "discovery": discovery}


def _should_ignore_pattern(session: str, name: str, line: str) -> bool:
    # Allow deliberate/structured uses.
    if name in {"TODO", "TBD", "FIXME"}:
        if line.strip().startswith("- [ ]"):
            return True
    # Don't flag YAML defaults like `status: todo`.
    if re.match(r"^status:\s*todo\s*$", line.strip(), flags=re.IGNORECASE):
        return True
    # In discovery sessions, "maybe" can appear inside explicitly enumerated options.
    if session == "research-discovery" and name in {"MAYBE"}:
        if re.search(r"\bOption [AB]\b", line):
            return True
    return False


def _scan_file_for_ambiguity(
    *,
    task_id: str,
    session: str,
    path: Path,
    patterns: dict[str, list[tuple[str, re.Pattern[str]]]],
) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = _read_text(path).splitlines()
    except UnicodeDecodeError:
        return findings

    for idx, raw in enumerate(lines, start=1):
        for name, rx in patterns["universal"]:
            if rx.search(raw) and not _should_ignore_pattern(session, name, raw):
                findings.append(
                    Finding(
                        task_id=task_id,
                        severity="FAIL",
                        message=f"Ambiguity language detected ({name})",
                        file=path,
                        line=idx,
                        excerpt=raw.strip(),
                    )
                )
        if session == "task-execution":
            for name, rx in patterns["execution"]:
                if rx.search(raw) and not _should_ignore_pattern(session, name, raw):
                    findings.append(
                        Finding(
                            task_id=task_id,
                            severity="FAIL",
                            message=f"Execution task contains ambiguous/decision language ({name})",
                            file=path,
                            line=idx,
                            excerpt=raw.strip(),
                        )
                    )
        if session == "research-discovery":
            for name, rx in patterns["discovery"]:
                if rx.search(raw) and not _should_ignore_pattern(session, name, raw):
                    findings.append(
                        Finding(
                            task_id=task_id,
                            severity="FAIL",
                            message=f"Discovery task contains ambiguous language ({name})",
                            file=path,
                            line=idx,
                            excerpt=raw.strip(),
                        )
                    )

    return findings


def _gather_task_text_files(task_dir: Path) -> list[Path]:
    files: list[Path] = []
    for p in task_dir.rglob("*"):
        if p.is_dir():
            if p.name in {".git", "node_modules", "__pycache__"}:
                continue
            continue
        if p.suffix.lower() in {".md", ".yaml", ".yml"}:
            files.append(p)
    return sorted(files)


def _lint_task_dir(*, ph_data_root: Path, task_dir: Path) -> list[Finding]:
    task_id = _task_id_from_dir_name(task_dir)

    required_files = [
        "task.yaml",
        "README.md",
        "steps.md",
        "commands.md",
        "checklist.md",
        "validation.md",
        "references.md",
    ]
    findings: list[Finding] = []

    for f in required_files:
        p = task_dir / f
        if not _is_nonempty_file(p):
            findings.append(
                Finding(task_id=task_id, severity="FAIL", message=f"Missing or empty required file: {f}", file=p)
            )

    task_yaml_path = task_dir / "task.yaml"
    if not task_yaml_path.exists():
        return findings

    task_meta = _parse_task_yaml_top_level(_read_text(task_yaml_path))
    session = task_meta.get("session", "").strip()

    required_yaml_keys = [
        "id",
        "title",
        "owner",
        "lane",
        "feature",
        "decision",
        "session",
        "story_points",
        "depends_on",
    ]
    for k in required_yaml_keys:
        if k not in task_meta or not task_meta[k]:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=f"task.yaml missing required key: {k}",
                    file=task_yaml_path,
                )
            )

    if task_meta.get("id") and task_meta["id"] != task_id:
        findings.append(
            Finding(
                task_id=task_id,
                severity="FAIL",
                message=f"task.yaml id mismatch: expected {task_id}, got {task_meta['id']}",
                file=task_yaml_path,
            )
        )

    if session not in {"task-execution", "research-discovery"}:
        findings.append(
            Finding(
                task_id=task_id,
                severity="FAIL",
                message=f"Unknown session '{session}' (expected task-execution or research-discovery)",
                file=task_yaml_path,
            )
        )

    readme_path = task_dir / "README.md"
    if readme_path.exists():
        fm = _parse_simple_front_matter(_read_text(readme_path))
        if "task_id" in fm and fm["task_id"] and fm["task_id"] != task_id:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=f"README.md front matter task_id mismatch: expected {task_id}, got {fm['task_id']}",
                    file=readme_path,
                )
            )
        if "session" in fm and fm["session"] and session and fm["session"] != session:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=f"README.md front matter session mismatch: task.yaml={session}, README.md={fm['session']}",
                    file=readme_path,
                )
            )
        if "feature" in fm and fm["feature"] and task_meta.get("feature") and fm["feature"] != task_meta["feature"]:
            task_feature = task_meta.get("feature")
            readme_feature = fm["feature"]
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=(
                        "README.md front matter feature mismatch: "
                        f"task.yaml={task_feature}, README.md={readme_feature}"
                    ),
                    file=readme_path,
                )
            )

    steps_text = _read_text(task_dir / "steps.md") if (task_dir / "steps.md").exists() else ""
    validation_text = _read_text(task_dir / "validation.md") if (task_dir / "validation.md").exists() else ""
    session_alignment_text = steps_text + "\n" + validation_text

    if session == "research-discovery":
        if not re.search(r"\bDecision Register\b|\bDR-\d{4}\b", session_alignment_text, flags=re.IGNORECASE):
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message="research-discovery task does not clearly produce a Decision Register (DR-XXXX) artefact",
                    file=task_dir / "steps.md",
                )
            )
        if not re.search(r"\bOption A\b", session_alignment_text) or not re.search(
            r"\bOption B\b", session_alignment_text
        ):
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message="research-discovery task must explicitly require exactly two options (Option A / Option B)",
                    file=task_dir / "steps.md",
                )
            )

    if session == "task-execution":
        if re.search(r"\bDecision Register\b|\bDR-\d{4}\b", session_alignment_text, flags=re.IGNORECASE):
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=(
                        "task-execution task contains Decision Register language; "
                        "split or re-route to research-discovery"
                    ),
                    file=task_dir / "steps.md",
                )
            )

    all_text = "\n".join(_read_text(p) for p in _gather_task_text_files(task_dir) if p.is_file())
    if task_id not in all_text:
        findings.append(
            Finding(
                task_id=task_id,
                severity="FAIL",
                message="Task docs do not reference the task id anywhere (expected explicit evidence paths and links)",
                file=task_dir / "README.md",
            )
        )
    if not re.search(rf"status/evidence/{re.escape(task_id)}/", all_text):
        findings.append(
            Finding(
                task_id=task_id,
                severity="FAIL",
                message=f"Task docs must explicitly reference evidence path 'status/evidence/{task_id}/...'",
                file=task_dir / "commands.md",
            )
        )
    if not re.search(r"secret-scan\.txt", all_text):
        findings.append(
            Finding(
                task_id=task_id,
                severity="FAIL",
                message="Task docs must include a secret scan evidence file expectation (secret-scan.txt)",
                file=task_dir / "validation.md",
            )
        )

    patterns = _compile_patterns()
    for path in _gather_task_text_files(task_dir):
        findings.extend(_scan_file_for_ambiguity(task_id=task_id, session=session, path=path, patterns=patterns))

    return findings


def _print_findings(*, ph_data_root: Path, findings: list[Finding]) -> None:
    for f in findings:
        loc = ""
        if f.file is not None:
            try:
                loc = str(f.file.relative_to(ph_data_root))
            except Exception:
                loc = str(f.file)
            if f.line is not None:
                loc = f"{loc}:{f.line}"
        msg = f"{f.severity} {f.task_id}: {f.message}"
        if loc:
            msg = f"{msg} ({loc})"
        print(msg)
        if f.excerpt:
            print(f"  ↳ {f.excerpt}")


def run_pre_exec_lint(*, ctx: Context) -> int:
    tasks_dir = ctx.ph_data_root / "sprints" / "current" / "tasks"
    if not tasks_dir.exists():
        print(f"FAIL: No sprint tasks directory found at {tasks_dir}")
        return 1

    all_findings: list[Finding] = []
    for task_dir in _iter_task_dirs(tasks_dir=tasks_dir):
        all_findings.extend(_lint_task_dir(ph_data_root=ctx.ph_data_root, task_dir=task_dir))

    failures = [f for f in all_findings if f.severity == "FAIL"]
    _print_findings(ph_data_root=ctx.ph_data_root, findings=failures)

    if failures:
        print(f"\nPRE-EXEC LINT FAILED: {len(failures)} issue(s)")
        print("Next:")
        print(
            "- Fix the flagged task docs/metadata (remove ambiguity, align session↔purpose, "
            "fill required fields/files)."
        )
        print("- Re-run: `ph pre-exec lint`")
        return 1

    print("\nPRE-EXEC LINT PASSED")
    return 0


def _write_evidence_text(*, evidence_dir: Path, name: str, text: str) -> None:
    path = evidence_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _capture_call(label: str, fn) -> tuple[int, str]:
    buf = StringIO()
    with redirect_stdout(buf):
        code = fn()
    return code, buf.getvalue()


def run_pre_exec_audit(
    *,
    ph_root: Path,
    ctx: Context,
    sprint: str | None,
    date: str | None,
    evidence_dir: str | None,
) -> int:
    sprint_plan = ctx.ph_data_root / "sprints" / "current" / "plan.md"
    sprint_id = (sprint or "").strip() or _extract_sprint_id_from_plan(plan_path=sprint_plan)
    date_str = (date or "").strip() or dt.date.today().isoformat()
    if evidence_dir:
        evid = Path(evidence_dir)
    else:
        evid = ctx.ph_data_root / "status" / "evidence" / "PRE-EXEC" / sprint_id / date_str
    evid = evid.resolve()

    print(f"EVIDENCE_DIR={evid}")
    evid.mkdir(parents=True, exist_ok=True)

    def _validate_code() -> int:
        code, _out_path, _message = run_validate(
            ph_root=ph_root,
            ph_data_root=ctx.ph_data_root,
            scope=ctx.scope,
            quick=False,
            silent_success=False,
        )
        return code

    steps: list[tuple[str, str, callable]] = [
        ("sprint-status", "sprint-status.txt", lambda: run_sprint_status(ph_root=ph_root, ctx=ctx, sprint=None)),
        ("release-status", "release-status.txt", lambda: run_release_status(ctx=ctx, env=os.environ)),
        ("task-list", "task-list.txt", lambda: run_task_list(ctx=ctx)),
        ("feature-summary", "feature-summary.txt", lambda: run_feature_summary(ctx=ctx, env=os.environ)),
        ("validate", "handbook-validate.txt", _validate_code),
    ]

    for label, filename, fn in steps:
        print("\n════════════════════════════════════════════════")
        print(f"PRE-EXEC: {label}")
        print("════════════════════════════════════════════════")
        code, out = _capture_call(label, fn)
        _write_evidence_text(evidence_dir=evid, name=filename, text=out)
        if code != 0:
            raise PreExecError(f"{label} failed (exit {code}). See {evid / filename}")

    # Copy the validation report into the evidence bundle for immutability.
    validation_report = ctx.ph_data_root / "status" / "validation.json"
    if validation_report.exists():
        _write_evidence_text(evidence_dir=evid, name="validation.json", text=_read_text(validation_report))

    print("\n════════════════════════════════════════════════")
    print("PRE-EXEC: lint")
    print("════════════════════════════════════════════════")
    lint_code, lint_out = _capture_call("lint", lambda: run_pre_exec_lint(ctx=ctx))
    _write_evidence_text(evidence_dir=evid, name="pre-exec-lint.txt", text=lint_out)
    if lint_code != 0:
        raise PreExecError(f"Pre-exec lint failed. Evidence: {evid}")

    print("\nPRE-EXEC AUDIT PASSED")
    print("Next:")
    print(f"- Review evidence bundle: {evid}")
    print("- Update sprints/current/plan.md to confirm the audit gate passed (date + evidence path).")
    print(
        "- Start execution by claiming the first ready task (typically `TASK-001`) "
        "via `ph task status --id TASK-001 --status doing`."
    )
    return 0
