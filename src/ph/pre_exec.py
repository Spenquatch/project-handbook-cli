from __future__ import annotations

import dataclasses
import datetime as dt
import os
import re
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from .context import Context
from .feature_status_updater import run_feature_summary
from .question_manager import QuestionManager
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


ALLOWED_SESSIONS = {
    "task-execution",
    "research-discovery",
    "sprint-gate",
    "feature-research-planning",
    "task-docs-deep-dive",
}

TASK_TYPE_TO_SESSION = {
    "implementation": "task-execution",
    "research-discovery": "research-discovery",
    "sprint-gate": "sprint-gate",
    "feature-research-planning": "feature-research-planning",
    "task-docs-deep-dive": "task-docs-deep-dive",
}

DEFAULT_TASK_TYPE_BY_SESSION = {
    # Backwards-compatible defaulting for legacy tasks (BL-0007 / I07-TTYPE-0001).
    "task-execution": "implementation",
    "research-discovery": "research-discovery",
}

DISCOVERY_SESSIONS = {"research-discovery", "feature-research-planning", "task-docs-deep-dive"}
EXECUTION_SESSIONS = {"task-execution", "sprint-gate"}


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


def _extract_required_marker_values(*, text: str, marker: str) -> list[str]:
    rx = re.compile(rf"^{re.escape(marker)}\s*(.*)\s*$", flags=re.MULTILINE)
    return [m.group(1).strip() for m in rx.finditer(text)]


def _is_explicit_sprint_goal(value: str) -> bool:
    v = value.strip()
    if not v:
        return False
    if len(v) < 8:
        return False
    if v.strip().lower() in {"tbd", "goal", "todo"}:
        return False
    return True


def _compile_patterns() -> dict[str, list[tuple[str, re.Pattern[str]]]]:
    def ci(p: str) -> re.Pattern[str]:
        return re.compile(p, flags=re.IGNORECASE)

    def cs(p: str) -> re.Pattern[str]:
        return re.compile(p)

    universal = [
        ("TBD", cs(r"\bTBD\b")),
        ("TBC", cs(r"\bTBC\b")),
        ("TODO", ci(r"\bTODO\b")),
        ("WIP", cs(r"\bWIP\b")),
        ("FIXME", cs(r"\bFIXME\b")),
        ("OPEN_QUESTION", ci(r"\bopen question(s)?\b")),
        ("TO_BE_DETERMINED", ci(r"\bto be determined\b")),
        ("DEPENDS_LOCAL_SETUP", ci(r"\bdepends on (local|your) setup\b")),
        ("DEPENDS_ENVIRONMENT", ci(r"\bdepends on (your )?environment\b")),
        ("LOCAL_SETUP", ci(r"\blocal setup\b")),
        ("OPTIONAL", ci(r"\boptional\b")),
        ("NICE_TO_HAVE", ci(r"\bnice to have\b")),
        ("IF_TIME", ci(r"\bif time\b")),
        ("IF_POSSIBLE", ci(r"\bif possible\b")),
        ("MAYBE", ci(r"\bmaybe\b")),
        ("UNSURE", ci(r"\bnot sure\b")),
        ("UNCLEAR_HOW", ci(r"\bunclear (how|whether|what|when|where)\b")),
        ("UNKNOWN_HOW", ci(r"\bunknown (how|whether|what|when|where)\b")),
        ("FIGURE_OUT", ci(r"\bfigure out\b")),
        ("WE_WILL_DECIDE", ci(r"\bwe('?| wi)ll decide\b")),
    ]

    execution = [
        ("IMPLEMENTATION_DECISION", ci(r"\bimplementation decision(s)?\b")),
        ("IMPLEMENTATION_DETAILS_TBD", ci(r"\bimplementation detail(s)?\b.*\b(TBD|to be determined)\b")),
        ("CHOOSE_BETWEEN", ci(r"\bchoose between\b")),
        ("PICK_APPROACH", ci(r"\bpick (an )?(approach|strategy)\b")),
        ("DECIDE_APPROACH", ci(r"\bdecide (on|between)\b.*\b(approach|strategy|implementation)\b")),
        ("TUNE_LATER", ci(r"\b(tune|decide|choose|pick)\b.*\blater\b")),
        ("BEST_EFFORT", ci(r"\bbest[- ]effort\b")),
        ("SHOULD_RESEARCH", ci(r"\b(need(s)? to|should)\s+(research|investigate)\b")),
        ("IMPERATIVE_RESEARCH", ci(r"^\s*[-*]\s+research\b")),
        ("IMPERATIVE_INVESTIGATE", ci(r"^\s*[-*]\s+investigate\b")),
    ]

    discovery = [
        ("DISCOVERY_AMBIGUITY_BEST_EFFORT", ci(r"\bbest[- ]effort\b")),
    ]

    return {"universal": universal, "execution": execution, "discovery": discovery}


def _should_ignore_pattern(session: str, name: str, line: str) -> bool:
    if name == "TODO":
        # Avoid false positives on task.yaml status values like `status: todo`.
        if re.match(r"^status:\s*todo\s*$", line.strip(), flags=re.IGNORECASE):
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
        if session in EXECUTION_SESSIONS:
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
        if session in DISCOVERY_SESSIONS:
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

    task_yaml_text = _read_text(task_yaml_path)
    task_meta = _parse_task_yaml_top_level(task_yaml_text)
    session = task_meta.get("session", "").strip()
    decision = task_meta.get("decision", "").strip()
    task_type_raw = task_meta.get("task_type", "").strip()

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

    if session not in ALLOWED_SESSIONS:
        findings.append(
            Finding(
                task_id=task_id,
                severity="FAIL",
                message=(f"Unknown session '{session}' (expected one of: " + ", ".join(sorted(ALLOWED_SESSIONS)) + ")"),
                file=task_yaml_path,
            )
        )

    task_type = task_type_raw
    if task_type:
        if task_type not in TASK_TYPE_TO_SESSION:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=(
                        f"Unknown task_type '{task_type}' (expected one of: "
                        + ", ".join(sorted(TASK_TYPE_TO_SESSION.keys()))
                        + ")"
                    ),
                    file=task_yaml_path,
                )
            )
            task_type = ""
    else:
        task_type = DEFAULT_TASK_TYPE_BY_SESSION.get(session, "")
        if not task_type and session in ALLOWED_SESSIONS:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=(
                        "task.yaml missing required key: task_type "
                        f"(required for session '{session}'; legacy defaulting only applies to "
                        "task-execution and research-discovery)"
                    ),
                    file=task_yaml_path,
                )
            )

    if task_type and session:
        expected_session = TASK_TYPE_TO_SESSION.get(task_type, "")
        if expected_session and session != expected_session:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=(
                        f"task_type/session mismatch: task_type '{task_type}' requires session "
                        f"'{expected_session}', found '{session}'"
                    ),
                    file=task_yaml_path,
                )
            )

    if session and decision:
        session_norm = session.strip().lower()
        decision_norm = decision.strip().upper()
        if session_norm in DISCOVERY_SESSIONS:
            if not re.match(r"^DR-\d{4}$", decision_norm):
                findings.append(
                    Finding(
                        task_id=task_id,
                        severity="FAIL",
                        message=(f"Decision id mismatch for session {session}: expected DR-XXXX, found {decision}"),
                        file=task_yaml_path,
                    )
                )
        elif session_norm in EXECUTION_SESSIONS:
            if not (decision_norm.startswith("ADR-") or decision_norm.startswith("FDR-")):
                findings.append(
                    Finding(
                        task_id=task_id,
                        severity="FAIL",
                        message=(
                            "Decision id mismatch for session task-execution: "
                            f"expected ADR-XXXX or FDR-..., found {decision}"
                        ),
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
                        f"README.md front matter feature mismatch: task.yaml={task_feature}, README.md={readme_feature}"
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

    if session in EXECUTION_SESSIONS:
        if re.search(r"\bDecision Register\b|\bDR-\d{4}\b", session_alignment_text, flags=re.IGNORECASE):
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=(
                        f"{session} task contains Decision Register language; split or re-route to a discovery session"
                    ),
                    file=task_dir / "steps.md",
                )
            )

    if task_type == "sprint-gate":
        validation_path = task_dir / "validation.md"
        sprint_goal_values = _extract_required_marker_values(text=validation_text, marker="Sprint Goal:")
        if not sprint_goal_values:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message="sprint-gate validation.md missing required marker: 'Sprint Goal:'",
                    file=validation_path,
                )
            )
        elif not any(_is_explicit_sprint_goal(v) for v in sprint_goal_values):
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=(
                        "sprint-gate validation.md must state an explicit sprint goal after 'Sprint Goal:' "
                        "(avoid placeholders; consider copying the goal text from sprints/current/plan.md)"
                    ),
                    file=validation_path,
                )
            )
        if "Exit criteria:" not in validation_text:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message="sprint-gate validation.md missing required marker: 'Exit criteria:'",
                    file=validation_path,
                )
            )
        artifacts = {m.lower() for m in re.findall(r"\b[\w.-]+\.(?:txt|json)\b", validation_text, flags=re.IGNORECASE)}
        if "secret-scan.txt" not in artifacts:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message="sprint-gate validation.md must mention secret-scan.txt",
                    file=validation_path,
                )
            )
        if artifacts and "secret-scan.txt" in artifacts and len(artifacts) < 2:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=(
                        "sprint-gate validation.md must list at least one additional evidence artifact besides "
                        "secret-scan.txt (e.g., pre-exec-lint.txt, handbook-validate.txt, validation.json)"
                    ),
                    file=validation_path,
                )
            )
        if "status/evidence/" not in validation_text:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message="sprint-gate validation.md must mention evidence root prefix 'status/evidence/'",
                    file=validation_path,
                )
            )
        if "status/evidence/" not in task_yaml_text:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message="sprint-gate task.yaml must mention evidence root prefix 'status/evidence/'",
                    file=task_yaml_path,
                )
            )
        if not ("sprints/current/plan.md" in validation_text or "../../plan.md" in validation_text):
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=(
                        "sprint-gate validation.md must reference the sprint plan "
                        "(expected one of: 'sprints/current/plan.md', '../../plan.md')"
                    ),
                    file=validation_path,
                )
            )

    if task_type == "task-docs-deep-dive":
        forbidden_rx = re.compile(r"\b(implement|refactor|deploy|ship)\b", flags=re.IGNORECASE)
        m_steps = forbidden_rx.search(steps_text)
        if m_steps:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=(
                        "task-docs-deep-dive steps.md contains forbidden implementation word: "
                        f"'{m_steps.group(1).lower()}'"
                    ),
                    file=task_dir / "steps.md",
                )
            )
        m_val = forbidden_rx.search(validation_text)
        if m_val:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=(
                        "task-docs-deep-dive validation.md contains forbidden implementation word: "
                        f"'{m_val.group(1).lower()}'"
                    ),
                    file=task_dir / "validation.md",
                )
            )

    if task_type == "feature-research-planning":
        required_headings = {"## Contract updates", "## Execution tasks to create"}
        present = {line.strip() for line in steps_text.splitlines() if line.strip() in required_headings}
        missing = sorted(required_headings - present)
        for heading in missing:
            findings.append(
                Finding(
                    task_id=task_id,
                    severity="FAIL",
                    message=f"feature-research-planning steps.md missing required heading line exactly: '{heading}'",
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
    try:
        qm = QuestionManager(ph_data_root=ctx.ph_data_root, env=os.environ)
        blocking = qm.blocking_open_for_current_sprint()
    except Exception:
        blocking = []

    for q in blocking:
        all_findings.append(
            Finding(
                task_id="SPRINT",
                severity="FAIL",
                message=f"Blocking question is still open: {q.id} — {q.title}",
                file=ctx.ph_data_root / q.path,
            )
        )

    sprint_gate_task_ids: list[str] = []
    for task_dir in _iter_task_dirs(tasks_dir=tasks_dir):
        task_yaml_path = task_dir / "task.yaml"
        if task_yaml_path.exists():
            task_meta = _parse_task_yaml_top_level(_read_text(task_yaml_path))
            if task_meta.get("task_type", "").strip() == "sprint-gate":
                sprint_gate_task_ids.append(_task_id_from_dir_name(task_dir))
        all_findings.extend(_lint_task_dir(ph_data_root=ctx.ph_data_root, task_dir=task_dir))

    if not sprint_gate_task_ids:
        all_findings.append(
            Finding(
                task_id="SPRINT",
                severity="FAIL",
                message=(
                    "Current sprint is missing a required sprint gate task (task_type: sprint-gate). "
                    "Create one (recommended: `ph task create --gate`) and ensure its validation.md "
                    "references sprint goal(s) and required evidence artifacts (including secret-scan.txt)."
                ),
                file=tasks_dir,
            )
        )

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
        code, _out_path, message = run_validate(
            ph_root=ph_root,
            ph_project_root=ctx.ph_project_root,
            ph_data_root=ctx.ph_data_root,
            scope=ctx.scope,
            quick=False,
            silent_success=False,
        )
        if message:
            print(message, end="")
        return code

    steps: list[tuple[str, str, callable]] = [
        (
            "sprint-status",
            "sprint-status.txt",
            lambda: run_sprint_status(ph_project_root=ctx.ph_project_root, ctx=ctx, sprint=None),
        ),
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
        sys.stdout.write(out)
        _write_evidence_text(evidence_dir=evid, name=filename, text=out)
        if code != 0:
            if label == "release-status":
                continue
            raise PreExecError(f"{label} failed (exit {code}). See {evid / filename}")

    # Copy the validation report into the evidence bundle for immutability.
    validation_report = ctx.ph_data_root / "status" / "validation.json"
    if validation_report.exists():
        _write_evidence_text(evidence_dir=evid, name="validation.json", text=_read_text(validation_report))

    print("\n════════════════════════════════════════════════")
    print("PRE-EXEC: lint")
    print("════════════════════════════════════════════════")
    lint_code, lint_out = _capture_call("lint", lambda: run_pre_exec_lint(ctx=ctx))
    sys.stdout.write(lint_out)
    _write_evidence_text(evidence_dir=evid, name="pre-exec-lint.txt", text=lint_out)
    if lint_code != 0:
        raise PreExecError(f"Pre-exec lint failed. Evidence: {evid}")

    print("\nPRE-EXEC AUDIT PASSED")
    print("Next:")
    print(f"- Review evidence bundle: {evid}")
    print(
        "- Update `project-handbook/sprints/current/plan.md` to confirm the audit gate passed (date + evidence path)."
    )
    print(
        "- Start execution by claiming the first ready task (typically `TASK-001`) "
        "via `ph task status --id TASK-001 --status doing`."
    )
    return 0
