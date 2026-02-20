from __future__ import annotations

import json
import re
from pathlib import Path

from .adr.validate import validate_adrs

_DR_ID_RE = re.compile(r"^DR-\d{4}$", re.IGNORECASE)
_HEADING_INSIDE_LIST_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+#{1,6}\s+\S")

_ALLOWED_TASK_TYPES: set[str] = {
    "implementation",
    "research-discovery",
    "sprint-gate",
    "feature-research-planning",
    "task-docs-deep-dive",
}

_TASK_TYPE_TO_REQUIRED_SESSION: dict[str, str] = {
    "implementation": "task-execution",
    "research-discovery": "research-discovery",
    "sprint-gate": "sprint-gate",
    "feature-research-planning": "feature-research-planning",
    "task-docs-deep-dive": "task-docs-deep-dive",
}

# Backwards compatibility for legacy tasks that predate `task_type`.
# Mapping is defined in cli_plan/v1_cli/CLI_CONTRACT.md ("Task types (BL-0007)").
_LEGACY_DEFAULT_TASK_TYPE_BY_SESSION: dict[str, str] = {
    "task-execution": "implementation",
    "research-discovery": "research-discovery",
}


def load_validation_rules(*, ph_project_root: Path) -> dict:
    rules_path = ph_project_root / "process" / "checks" / "validation_rules.json"
    default_rules = {
        "validation": {"require_front_matter": True, "skip_docs_directory": True},
        "system_scope_enforcement": {
            # Opt-in. When disabled, system-scope routing config is not required and no routing checks run.
            "enabled": False,
            "config_path": "process/automation/system_scope_config.json",
        },
        "sprint_tasks": {
            "require_task_yaml": True,
            "require_story_points": True,
            "required_task_fields": [
                "id",
                "title",
                "feature",
                "decision",
                "owner",
                "status",
                "story_points",
                "prio",
                "due",
                "acceptance",
            ],
            "required_task_files": ["README.md", "steps.md", "commands.md", "checklist.md", "validation.md"],
            "enforce_sprint_scoped_dependencies": True,
        },
        "story_points": {
            "validate_fibonacci_sequence": True,
            "allowed_story_points": [1, 2, 3, 5, 8, 13, 21],
        },
        "roadmap": {"normalize_links": True},
    }

    try:
        if rules_path.exists():
            return json.loads(rules_path.read_text(encoding="utf-8"))
    except Exception:
        return default_rules

    return default_rules


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def _strip(val: str) -> str:
    return val.strip().strip('"').strip("'")


def parse_simple_yaml_mapping(text: str) -> dict:
    data: dict = {}
    lines = text.splitlines()
    i = 0
    n = len(lines)

    def is_kv(line: str) -> bool:
        return ":" in line and not line.lstrip().startswith("-")

    while i < n:
        raw = lines[i]
        line = raw.rstrip("\n")
        if not line.strip():
            i += 1
            continue
        if not line.startswith(" ") and is_kv(line):
            key, val = line.split(":", 1)
            k = key.strip()
            v = val.strip()
            if v == "":
                if i + 1 < n and lines[i + 1].lstrip().startswith("- "):
                    i += 1
                    arr = []
                    while i < n and lines[i].startswith("  - "):
                        arr.append(_strip(lines[i].split("- ", 1)[1]))
                        i += 1
                    data[k] = arr
                    continue
                if i + 1 < n and lines[i + 1].startswith("  "):
                    i += 1
                    sub = {}
                    while i < n and lines[i].startswith("  ") and is_kv(lines[i].strip()):
                        sk, sv = lines[i].strip().split(":", 1)
                        sub[_strip(sk)] = _strip(sv)
                        i += 1
                    data[k] = sub
                    continue
                data[k] = ""
            else:
                data[k] = _strip(v)
            i += 1
            continue
        i += 1
    return data


def parse_simple_yaml_task_list(text: str) -> list:
    items = []
    current = None
    mode_list_key = None
    for raw in text.splitlines():
        if raw.startswith("- "):
            if current is not None:
                items.append(current)
            current = {}
            mode_list_key = None
            remainder = raw[2:].strip()
            if remainder and ":" in remainder:
                k, v = remainder.split(":", 1)
                current[_strip(k)] = _strip(v)
            continue
        if current is None:
            continue
        if raw.startswith("  ") and ":" in raw and not raw.strip().startswith("- "):
            k, v = raw.strip().split(":", 1)
            k = _strip(k)
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                list_content = v[1:-1].strip()
                if list_content:
                    current[k] = [_strip(item) for item in list_content.split(",")]
                else:
                    current[k] = []
                mode_list_key = None
            elif v == "":
                mode_list_key = k
                current[k] = []
            else:
                current[k] = _strip(v)
                mode_list_key = None
            continue
        if raw.startswith("    - ") and mode_list_key:
            current[mode_list_key].append(_strip(raw.split("- ", 1)[1]))
            continue
        mode_list_key = None
    if current is not None:
        items.append(current)
    return items


def parse_front_matter(text: str) -> tuple[dict, int, int]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, -1, -1
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return {}, -1, -1
    fm = {}
    for line in lines[1:end]:
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, 0, end


def _extract_front_matter_list_field(text: str, field: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return []

    i = 1
    n = end
    prefix = f"{field}:"
    while i < n:
        raw = lines[i].rstrip("\n")
        if not raw.strip():
            i += 1
            continue
        if not raw.startswith(prefix):
            i += 1
            continue

        rest = raw.split(":", 1)[1].strip()
        if rest.startswith("[") and rest.endswith("]"):
            inner = rest[1:-1].strip()
            if not inner:
                return []
            return [_strip(part) for part in inner.split(",") if _strip(part)]

        items: list[str] = []
        if rest:
            items.append(_strip(rest))
            return items

        j = i + 1
        while j < n:
            line = lines[j]
            stripped = line.strip()
            if not stripped:
                j += 1
                continue
            if stripped.startswith("- "):
                items.append(_strip(stripped[2:]))
                j += 1
                continue
            break
        return items

    return []


def _looks_like_dr_backlink(link: str) -> bool:
    candidate = (link or "").strip().strip('"').strip("'").strip()
    if not candidate:
        return False
    if "://" in candidate:
        return False
    if "decision-register/" not in candidate:
        return False
    if ".md" not in candidate:
        return False
    return bool(re.search(r"DR-\d{4}", candidate, flags=re.IGNORECASE))


def validate_adr_fdr_backlinks(*, issues: list[dict], root: Path) -> None:
    adr_dir = root / "adr"
    if adr_dir.exists():
        for md in sorted(adr_dir.rglob("*.md")):
            rel_path = md.relative_to(root).as_posix()
            text = read(md)
            _fm, start, end = parse_front_matter(text)
            if start == -1 or end == -1:
                continue
            links = _extract_front_matter_list_field(text, "links")
            if not any(_looks_like_dr_backlink(link) for link in links):
                issues.append(
                    {
                        "path": rel_path,
                        "code": "adr_missing_dr_backlink",
                        "severity": "error",
                        "message": (
                            "ADR YAML front matter must include at least one DR backlink in `links:`.\n"
                            "  expected: links contains a path like decision-register/DR-0001-....md\n"
                            f"  found_links: {links}\n"
                        ),
                        "found_links": links,
                    }
                )

    features_dir = root / "features"
    if not features_dir.exists():
        return

    for md in sorted(features_dir.rglob("fdr/*.md")):
        try:
            rel_path = md.relative_to(root).as_posix()
        except Exception:
            rel_path = str(md)
        text = read(md)
        _fm, start, end = parse_front_matter(text)
        if start == -1 or end == -1:
            continue
        links = _extract_front_matter_list_field(text, "links")
        if not any(_looks_like_dr_backlink(link) for link in links):
            issues.append(
                {
                    "path": rel_path,
                    "code": "fdr_missing_dr_backlink",
                    "severity": "error",
                    "message": (
                        "FDR YAML front matter must include at least one DR backlink in `links:`.\n"
                        "  expected: links contains a path like decision-register/DR-0001-....md\n"
                        f"  found_links: {links}\n"
                    ),
                    "found_links": links,
                }
            )


def _iter_dr_search_dirs(*, ph_data_root: Path, feature: str | None) -> tuple[list[Path], list[str]]:
    feature = (feature or "").strip()
    dirs: list[Path] = []
    labels: list[str] = []

    if feature:
        labels.append(f"features/{feature}/decision-register")
        dirs.append(ph_data_root / "features" / feature / "decision-register")
    else:
        labels.append("features/*/decision-register")
        features_dir = ph_data_root / "features"
        if features_dir.exists():
            for entry in sorted(features_dir.iterdir()):
                if not entry.is_dir() or entry.name == "implemented":
                    continue
                dirs.append(entry / "decision-register")
            implemented = features_dir / "implemented"
            if implemented.exists():
                for entry in sorted(implemented.iterdir()):
                    if entry.is_dir():
                        dirs.append(entry / "decision-register")

    labels.append("decision-register")
    dirs.append(ph_data_root / "decision-register")

    return dirs, labels


def _dr_entry_exists(*, ph_data_root: Path, dr_id: str, feature: str | None) -> bool:
    dr_id = (dr_id or "").strip().upper()
    if not _DR_ID_RE.match(dr_id):
        return False

    pattern = re.compile(rf"^#{{1,6}}\s+{re.escape(dr_id)}\b", flags=re.MULTILINE)
    dirs, _labels = _iter_dr_search_dirs(ph_data_root=ph_data_root, feature=feature)
    for folder in dirs:
        if not folder.exists():
            continue
        for candidate in sorted(folder.rglob("*.md")):
            if pattern.search(read(candidate)):
                return True
    return False


def validate_front_matter(*, issues: list[dict], rules: dict, root: Path, ph_root: Path, scope: str) -> None:
    if not rules.get("validation", {}).get("require_front_matter", True):
        return

    internal_system_root = ph_root / ".project-handbook" / "system"

    for md in root.rglob("*.md"):
        if scope == "project":
            try:
                md.resolve().relative_to(internal_system_root.resolve())
                continue
            except Exception:
                pass
        rel_path = md.relative_to(root)
        if rel_path.as_posix() == "status/current_summary.md":
            continue
        rel_str = rel_path.as_posix()
        if rules.get("validation", {}).get("skip_docs_directory", True):
            if "docs/" in rel_str:
                continue
        if "backlog/" in rel_str and md.name == "triage.md":
            continue

        fm, _, _ = parse_front_matter(read(md))
        if not fm:
            issues.append({"path": str(md), "code": "front_matter_missing", "severity": "error"})


def validate_session_end_index(*, issues: list[dict], ph_project_root: Path, ph_root: Path) -> None:
    index_path = ph_project_root / "process" / "sessions" / "session_end" / "session_end_index.json"
    if not index_path.exists():
        return

    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(
            {
                "path": str(index_path),
                "code": "session_end_index_parse_error",
                "severity": "error",
                "message": str(exc),
            }
        )
        return

    records = data.get("records")
    if not isinstance(records, list):
        issues.append(
            {
                "path": str(index_path),
                "code": "session_end_index_invalid",
                "severity": "error",
                "message": "Expected JSON object with list field 'records'.",
            }
        )
        return

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            issues.append(
                {
                    "path": str(index_path),
                    "code": "session_end_index_record_invalid",
                    "severity": "error",
                    "message": f"Record {i} is not an object.",
                }
            )
            continue

        for key in ("summary_path", "prompt_path"):
            raw = record.get(key)
            if not isinstance(raw, str) or not raw.strip():
                issues.append(
                    {
                        "path": str(index_path),
                        "code": "session_end_index_path_missing",
                        "severity": "error",
                        "message": f"Record {i} missing '{key}'.",
                    }
                )
                continue
            rel = Path(raw)
            if rel.is_absolute():
                issues.append(
                    {
                        "path": str(index_path),
                        "code": "session_end_index_path_invalid",
                        "severity": "error",
                        "message": f"Record {i} '{key}' must be repo-relative (got absolute path).",
                    }
                )
                continue
            try:
                resolved = (ph_root / rel).resolve()
                resolved.relative_to(ph_root.resolve())
            except Exception:
                issues.append(
                    {
                        "path": str(index_path),
                        "code": "session_end_index_path_invalid",
                        "severity": "error",
                        "message": f"Record {i} '{key}' escapes repo root: {raw}",
                    }
                )
                continue
            if not resolved.exists():
                issues.append(
                    {
                        "path": str(index_path),
                        "code": "session_end_index_path_not_found",
                        "severity": "error",
                        "message": f"Record {i} '{key}' not found: {raw}",
                    }
                )


def _load_system_scope_routing(*, rules: dict, issues: list[dict], ph_data_root: Path) -> dict | None:
    enforcement_raw = rules.get("system_scope_enforcement")
    if enforcement_raw is None:
        return None
    if not isinstance(enforcement_raw, dict):
        issues.append(
            {
                "path": "process/checks/validation_rules.json",
                "code": "system_scope_enforcement_invalid",
                "severity": "error",
                "message": "system_scope_enforcement must be an object when present",
            }
        )
        return None

    if enforcement_raw.get("enabled") is False:
        return None

    config_rel = None
    config_rel = enforcement_raw.get("config_path")
    if not isinstance(config_rel, str) or not config_rel.strip():
        config_rel = "process/automation/system_scope_config.json"

    try:
        config_path = (ph_data_root / Path(config_rel)).resolve()
        config_path.relative_to(ph_data_root.resolve())
    except Exception:
        issues.append(
            {
                "path": config_rel,
                "code": "system_scope_config_invalid_path",
                "severity": "error",
                "message": "system scope config_path must be repo-relative and MUST NOT escape the repo root",
            }
        )
        return None

    if not config_path.exists():
        issues.append(
            {
                "path": str(config_path),
                "code": "system_scope_config_missing",
                "severity": "error",
                "message": "Missing system scope config; expected process/automation/system_scope_config.json",
            }
        )
        return None

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(
            {
                "path": str(config_path),
                "code": "system_scope_config_parse_error",
                "severity": "error",
                "message": str(exc),
            }
        )
        return None

    routing = config.get("routing_rules")
    if not isinstance(routing, dict):
        issues.append(
            {
                "path": str(config_path),
                "code": "system_scope_config_invalid",
                "severity": "error",
                "message": "Invalid system scope config: routing_rules must be an object",
            }
        )
        return None

    return {
        "internal_system_root": config.get("internal_system_root", ".project-handbook/system"),
        "feature_prefixes": routing.get("feature_name_prefixes_for_system_scope", []),
        "lane_prefixes": routing.get("task_lane_prefixes_for_system_scope", []),
        "adr_tags": routing.get("adr_tags_triggering_system_scope", []),
    }


def _extract_front_matter_tags(text: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return []

    tags: list[str] = []
    collecting_list = False
    for line in lines[1:end]:
        raw = line.strip()
        if collecting_list:
            if raw.startswith("- "):
                value = raw[2:].strip().strip('"').strip("'")
                if value:
                    tags.append(value)
                continue
            collecting_list = False

        if not raw.startswith("tags:"):
            continue

        value = raw.split(":", 1)[1].strip()
        if not value:
            collecting_list = True
            continue

        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if inner:
                for item in inner.split(","):
                    cleaned = item.strip().strip('"').strip("'")
                    if cleaned:
                        tags.append(cleaned)
            continue

        cleaned = value.strip().strip('"').strip("'")
        if cleaned:
            tags.append(cleaned)

    return tags


def validate_system_scope_artifacts_in_project_scope(
    *, issues: list[dict], rules: dict, root: Path, ph_root: Path, scope: str
) -> None:
    if scope != "project":
        return

    routing = _load_system_scope_routing(rules=rules, issues=issues, ph_data_root=root)
    if not routing:
        return

    feature_prefixes = routing.get("feature_prefixes") or []
    lane_prefixes = routing.get("lane_prefixes") or []
    adr_tags = set(routing.get("adr_tags") or [])
    internal_system_root = routing.get("internal_system_root") or ".project-handbook/system"

    if not isinstance(feature_prefixes, list):
        feature_prefixes = []
    if not isinstance(lane_prefixes, list):
        lane_prefixes = []

    features_dir = root / "features"
    candidates: list[Path] = []
    if features_dir.exists():
        for entry in features_dir.iterdir():
            if entry.is_dir() and entry.name != "implemented":
                candidates.append(entry)
        implemented_dir = features_dir / "implemented"
        if implemented_dir.exists():
            for entry in implemented_dir.iterdir():
                if entry.is_dir():
                    candidates.append(entry)

    for feature_dir in sorted(candidates):
        name = feature_dir.name
        if any(name.startswith(str(prefix)) for prefix in feature_prefixes):
            issues.append(
                {
                    "path": str(feature_dir),
                    "code": "system_scope_feature_in_project",
                    "severity": "error",
                    "message": (
                        f"System-scope feature MUST NOT exist in project scope: {name}. "
                        f"Move to `{internal_system_root}` or recreate via "
                        f"`ph --scope system feature create --name {name}`."
                    ),
                }
            )

    sprints_dir = root / "sprints"
    if sprints_dir.exists():
        for task_yaml in sorted(sprints_dir.rglob("task.yaml")):
            if "tasks" not in task_yaml.parts:
                continue
            try:
                content = task_yaml.read_text(encoding="utf-8")
            except Exception:
                continue

            lane_value = None
            for line in content.splitlines():
                if line.startswith("lane:"):
                    lane_value = line.split(":", 1)[1].strip().strip('"').strip("'")
                    break
            if not lane_value:
                continue
            if any(lane_value.startswith(str(prefix)) for prefix in lane_prefixes):
                issues.append(
                    {
                        "path": str(task_yaml),
                        "code": "system_scope_lane_in_project",
                        "severity": "error",
                        "message": (
                            f"System-scope task lane MUST NOT exist in project scope: lane={lane_value}. "
                            f"Move to `{internal_system_root}` or recreate via `ph --scope system task create ...`."
                        ),
                    }
                )

    adr_dir = root / "adr"
    if adr_dir.exists():
        for md in sorted(adr_dir.rglob("*.md")):
            text = read(md)
            tags = _extract_front_matter_tags(text)
            if any(tag in adr_tags for tag in tags):
                issues.append(
                    {
                        "path": str(md),
                        "code": "system_scope_adr_in_project",
                        "severity": "error",
                        "message": (
                            "System-scope ADR MUST NOT exist in project scope. "
                            f"Move to `{internal_system_root}/adr/` and keep related work in system scope via "
                            "`ph --scope system ...` commands."
                        ),
                    }
                )


def normalize_roadmap_links(*, rules: dict, root: Path, scope: str, quick: bool) -> int:
    if quick:
        return 0
    if scope == "system":
        return 0
    if not rules.get("roadmap", {}).get("normalize_links", True):
        return 0

    roadmap_path = root / "roadmap" / "now-next-later.md"
    if not roadmap_path.exists():
        return 0

    try:
        text = roadmap_path.read_text(encoding="utf-8")
    except Exception:
        return 0

    if not text:
        return 0

    fm, start, end = parse_front_matter(text)
    if start == -1 or end == -1:
        body_start = 0
    else:
        body_start = end + 1

    lines = text.splitlines()
    head = lines[:body_start]
    body_lines = lines[body_start:]
    body_text = "\n".join(body_lines)

    pattern = re.compile(r"\[(\.\./[^\]\s]+)\](?!\()")

    def repl(match: re.Match) -> str:
        target = match.group(1)
        return f"[{target}]({target})"

    new_body, count = pattern.subn(repl, body_text)

    if count:
        prefix = "\n".join(head)
        if prefix:
            prefix += "\n"
        new_text = prefix + new_body
        if text.endswith("\n") and not new_text.endswith("\n"):
            new_text += "\n"
        roadmap_path.write_text(new_text, encoding="utf-8")

    return count


_SPRINT_GATE_EVIDENCE_PREFIX = "status/evidence/"
_SPRINT_GATE_VALIDATION_REQUIRED_LITERALS: tuple[str, ...] = (
    "Sprint Goal:",
    "Exit criteria:",
    "secret-scan.txt",
    _SPRINT_GATE_EVIDENCE_PREFIX,
)
_SPRINT_GATE_VALIDATION_SPRINT_PLAN_REFERENCE_OPTIONS: tuple[str, ...] = (
    "sprints/current/plan.md",
    "../../plan.md",
)


def _validate_sprint_gate_task_docs(*, issues: list[dict], task_dir: Path, task_yaml: Path, task_id: str) -> None:
    validation_md = task_dir / "validation.md"
    if not validation_md.exists():
        issues.append(
            {
                "path": str(task_dir),
                "code": "sprint_gate_validation_missing",
                "severity": "error",
                "task_id": task_id,
                "message": (
                    "Sprint gate task is missing required gate doc.\n"
                    f"  task_id: {task_id or '<unknown>'}\n"
                    "  expected_file: validation.md\n"
                ),
            }
        )
        return

    validation_text = read(validation_md)
    missing_markers = [marker for marker in _SPRINT_GATE_VALIDATION_REQUIRED_LITERALS if marker not in validation_text]
    if not any(opt in validation_text for opt in _SPRINT_GATE_VALIDATION_SPRINT_PLAN_REFERENCE_OPTIONS):
        missing_markers.append(
            "sprint plan reference (one of: " + ", ".join(_SPRINT_GATE_VALIDATION_SPRINT_PLAN_REFERENCE_OPTIONS) + ")"
        )

    if missing_markers:
        issues.append(
            {
                "path": str(validation_md),
                "code": "sprint_gate_validation_markers_missing",
                "severity": "error",
                "task_id": task_id,
                "missing_markers": missing_markers,
                "message": (
                    "Sprint gate validation.md is missing required marker(s).\n"
                    f"  task_id: {task_id or '<unknown>'}\n"
                    f"  missing: {missing_markers}\n"
                    f"  required_literals: {list(_SPRINT_GATE_VALIDATION_REQUIRED_LITERALS)}\n"
                    "  required_plan_reference: include at least one of "
                    f"{list(_SPRINT_GATE_VALIDATION_SPRINT_PLAN_REFERENCE_OPTIONS)}\n"
                ),
            }
        )

    task_yaml_text = read(task_yaml)
    if _SPRINT_GATE_EVIDENCE_PREFIX not in task_yaml_text:
        issues.append(
            {
                "path": str(task_yaml),
                "code": "sprint_gate_task_yaml_missing_evidence_prefix",
                "severity": "error",
                "task_id": task_id,
                "message": (
                    "Sprint gate task.yaml must mention the evidence root path prefix.\n"
                    f"  task_id: {task_id or '<unknown>'}\n"
                    f"  required_literal: {_SPRINT_GATE_EVIDENCE_PREFIX}\n"
                ),
            }
        )


def validate_sprints(*, issues: list[dict], rules: dict, root: Path) -> None:
    sprint_rules = rules.get("sprint_tasks", {})
    story_rules = rules.get("story_points", {})

    sprints_dir = root / "sprints"
    if not sprints_dir.exists():
        return

    for year_dir in sprints_dir.iterdir():
        if not year_dir.is_dir() or year_dir.name == "current":
            continue

        for sprint_dir in year_dir.iterdir():
            if not sprint_dir.is_dir() or not sprint_dir.name.startswith("SPRINT-"):
                continue

            tasks_dir = sprint_dir / "tasks"
            if not tasks_dir.exists():
                continue

            sprint_task_ids = set()
            sprint_tasks: list[tuple[Path, dict]] = []

            for task_dir in sorted(tasks_dir.iterdir()):
                if not task_dir.is_dir():
                    continue

                task_yaml = task_dir / "task.yaml"
                if not task_yaml.exists():
                    issues.append({"path": str(task_dir), "code": "task_yaml_missing", "severity": "error"})
                    continue

                try:
                    content = task_yaml.read_text(encoding="utf-8")
                    task_data: dict = {}

                    for line in content.splitlines():
                        if ":" in line and not line.strip().startswith("-"):
                            key, value = line.split(":", 1)
                            key = key.strip()
                            value = value.strip()

                            if value.startswith("[") and value.endswith("]"):
                                items = [item.strip().strip("\"'") for item in value[1:-1].split(",")]
                                task_data[key] = [item for item in items if item]
                            else:
                                task_data[key] = value

                    sprint_tasks.append((task_dir, task_data))

                    task_id = task_data.get("id")
                    if task_id:
                        sprint_task_ids.add(task_id)

                except Exception as exc:
                    issues.append(
                        {
                            "path": str(task_yaml),
                            "code": "task_yaml_parse_error",
                            "severity": "error",
                            "message": str(exc),
                        }
                    )

            status_map: dict[str, str] = {}
            for _, task in sprint_tasks:
                task_id = str(task.get("id", "")).strip()
                if not task_id:
                    continue
                status_map[task_id] = str(task.get("status", "")).strip().lower()

            sprint_gate_task_ids: list[str] = []

            for task_dir, task_data in sprint_tasks:
                task_yaml = task_dir / "task.yaml"

                required_fields = sprint_rules.get(
                    "required_task_fields",
                    [
                        "id",
                        "title",
                        "feature",
                        "decision",
                        "owner",
                        "status",
                        "story_points",
                        "prio",
                        "due",
                        "acceptance",
                    ],
                )
                missing = [k for k in required_fields if k not in task_data]
                if missing and sprint_rules.get("require_task_yaml", True):
                    issues.append(
                        {"path": str(task_yaml), "code": "task_missing_fields", "severity": "error", "missing": missing}
                    )

                session = _strip(str(task_data.get("session", ""))).strip().lower()
                raw_task_type = _strip(str(task_data.get("task_type", ""))).strip().lower()

                effective_task_type: str | None = None
                if raw_task_type:
                    if raw_task_type not in _ALLOWED_TASK_TYPES:
                        issues.append(
                            {
                                "path": str(task_yaml),
                                "code": "task_type_invalid",
                                "severity": "error",
                                "expected": sorted(_ALLOWED_TASK_TYPES),
                                "found": raw_task_type,
                                "message": (
                                    "Invalid task_type value in task.yaml.\n"
                                    f"  expected: one of {sorted(_ALLOWED_TASK_TYPES)}\n"
                                    f"  found: {raw_task_type}\n"
                                ),
                            }
                        )
                    else:
                        effective_task_type = raw_task_type
                else:
                    if session in _LEGACY_DEFAULT_TASK_TYPE_BY_SESSION:
                        effective_task_type = _LEGACY_DEFAULT_TASK_TYPE_BY_SESSION[session]
                    elif session:
                        issues.append(
                            {
                                "path": str(task_yaml),
                                "code": "task_type_missing",
                                "severity": "error",
                                "expected": sorted(_ALLOWED_TASK_TYPES),
                                "found": "<missing>",
                                "message": (
                                    "Missing task_type in task.yaml.\n"
                                    f"  session: {session}\n"
                                    f"  expected: one of {sorted(_ALLOWED_TASK_TYPES)}\n"
                                    "  found: <missing>\n"
                                ),
                            }
                        )

                if effective_task_type:
                    expected_session = _TASK_TYPE_TO_REQUIRED_SESSION.get(effective_task_type)
                    if expected_session and session and session != expected_session:
                        issues.append(
                            {
                                "path": str(task_yaml),
                                "code": "task_type_session_mismatch",
                                "severity": "error",
                                "task_type": effective_task_type,
                                "expected": expected_session,
                                "found": session,
                                "message": (
                                    "task_type and session are inconsistent.\n"
                                    f"  task_type: {effective_task_type}\n"
                                    f"  expected_session: {expected_session}\n"
                                    f"  found_session: {session}\n"
                                ),
                            }
                        )
                    elif expected_session and not session:
                        issues.append(
                            {
                                "path": str(task_yaml),
                                "code": "task_type_session_mismatch",
                                "severity": "error",
                                "task_type": effective_task_type,
                                "expected": expected_session,
                                "found": "<missing>",
                                "message": (
                                    "task_type requires a session value but session is missing.\n"
                                    f"  task_type: {effective_task_type}\n"
                                    f"  expected_session: {expected_session}\n"
                                    "  found_session: <missing>\n"
                                ),
                            }
                        )

                if effective_task_type == "sprint-gate":
                    task_id = _strip(str(task_data.get("id", ""))).strip()
                    if task_id:
                        sprint_gate_task_ids.append(task_id)
                    _validate_sprint_gate_task_docs(
                        issues=issues,
                        task_dir=task_dir,
                        task_yaml=task_yaml,
                        task_id=task_id,
                    )

                decision = task_data.get("decision")
                if decision and sprint_rules.get("require_single_decision_per_task", True):
                    decision = str(decision).strip()
                    decision_norm = decision.upper()
                    if session == "research-discovery":
                        if not re.match(r"^DR-\d{4}$", decision_norm):
                            issues.append(
                                {
                                    "path": str(task_yaml),
                                    "code": "task_decision_invalid",
                                    "severity": "error",
                                    "expected": "DR-XXXX",
                                    "found": decision,
                                    "message": (
                                        "Decision id mismatch for session research-discovery: "
                                        f"expected DR-XXXX, found {decision}"
                                    ),
                                }
                            )
                        else:
                            feature = str(task_data.get("feature", "")).strip()
                            if not _dr_entry_exists(ph_data_root=root, dr_id=decision_norm, feature=feature):
                                _dirs, dir_labels = _iter_dr_search_dirs(ph_data_root=root, feature=feature)
                                issues.append(
                                    {
                                        "path": str(task_yaml),
                                        "code": "task_dr_missing",
                                        "severity": "error",
                                        "dr_id": decision_norm,
                                        "searched_dirs": dir_labels,
                                        "message": (
                                            "Task references missing Decision Register entry.\n"
                                            f"  dr_id: {decision_norm}\n"
                                            f"  searched_dirs: {dir_labels}\n"
                                        ),
                                    }
                                )
                    elif session == "task-execution":
                        if not (decision_norm.startswith("ADR-") or decision_norm.startswith("FDR-")):
                            issues.append(
                                {
                                    "path": str(task_yaml),
                                    "code": "task_decision_invalid",
                                    "severity": "error",
                                    "expected": "ADR-XXXX or FDR-...",
                                    "found": decision,
                                    "message": (
                                        "Decision id mismatch for session task-execution: "
                                        f"expected ADR-XXXX or FDR-..., found {decision}"
                                    ),
                                }
                            )

                story_points = task_data.get("story_points")
                if story_points and story_rules.get("validate_fibonacci_sequence", True):
                    try:
                        sp_int = int(story_points)
                        allowed_points = story_rules.get("allowed_story_points", [1, 2, 3, 5, 8, 13, 21])
                        if sp_int not in allowed_points:
                            issues.append(
                                {
                                    "path": str(task_yaml),
                                    "code": "task_story_points_invalid",
                                    "severity": "warning",
                                    "message": f"Story points should use configured sequence: {allowed_points}",
                                }
                            )
                    except Exception:
                        issues.append(
                            {"path": str(task_yaml), "code": "task_story_points_not_integer", "severity": "error"}
                        )

                if sprint_rules.get("enforce_sprint_scoped_dependencies", True):
                    depends_on = task_data.get("depends_on", [])
                    if isinstance(depends_on, str):
                        depends_on = [depends_on]

                    for dep in depends_on:
                        if dep == "FIRST_TASK":
                            continue
                        if dep and dep not in sprint_task_ids:
                            issues.append(
                                {
                                    "path": str(task_yaml),
                                    "code": "task_dependency_out_of_sprint",
                                    "severity": "error",
                                    "message": (
                                        f"Task depends on {dep} which is not in current sprint. "
                                        "Dependencies must be sprint-scoped only."
                                    ),
                                }
                            )

                depends_on = task_data.get("depends_on", [])
                if isinstance(depends_on, str):
                    depends_on = [depends_on]

                normalized_status = str(task_data.get("status", "")).strip().lower()
                advanced_states = {"doing", "review", "done"}
                if depends_on and normalized_status in advanced_states:
                    unresolved = []
                    for dep in depends_on:
                        if dep == "FIRST_TASK":
                            continue
                        dep_status = status_map.get(dep)
                        if dep_status is None:
                            continue
                        if dep_status != "done":
                            unresolved.append(f"{dep} (status: {dep_status})")

                    if unresolved:
                        issues.append(
                            {
                                "path": str(task_yaml),
                                "code": "task_dependency_not_done",
                                "severity": "error",
                                "message": "Cannot advance because dependencies are not done: " + ", ".join(unresolved),
                            }
                        )

                if sprint_rules.get("require_task_directory_files", True):
                    required_files = sprint_rules.get(
                        "required_task_files", ["README.md", "steps.md", "commands.md", "checklist.md", "validation.md"]
                    )
                    for req_file in required_files:
                        if not (task_dir / req_file).exists():
                            issues.append(
                                {
                                    "path": str(task_dir),
                                    "code": f"task_missing_{req_file.replace('.', '_')}",
                                    "severity": "warning",
                                }
                            )

            if not sprint_gate_task_ids:
                issues.append(
                    {
                        "path": str(sprint_dir),
                        "code": "sprint_gate_task_missing",
                        "severity": "error",
                        "message": (
                            "Sprint is missing a sprint gate task.\n"
                            f"  sprint: {sprint_dir.name}\n"
                            "  expected: at least 1 task under tasks/ with `task_type: sprint-gate`\n"
                        ),
                    }
                )


def _as_int(val: object) -> int | None:
    try:
        s = str(val).strip()
    except Exception:
        return None
    if not s or s.lower() in {"null", "none"}:
        return None
    try:
        return int(s)
    except Exception:
        return None


def validate_current_sprint_plan_structure(*, issues: list[dict], root: Path, scope: str) -> None:
    plan_path = root / "sprints" / "current" / "plan.md"
    if not plan_path.exists():
        return

    text = read(plan_path)
    if not text.strip():
        return

    fm, _, _ = parse_front_matter(text)
    mode = str(fm.get("mode") or "").strip().lower()

    start = str(fm.get("start") or "").strip()
    end = str(fm.get("end") or "").strip()
    if mode not in {"bounded", "timeboxed"}:
        if start and end:
            mode = "timeboxed"
        else:
            issues.append(
                {
                    "path": str(plan_path),
                    "code": "sprint_plan_mode_missing_or_invalid",
                    "severity": "error",
                    "message": (
                        "Current sprint plan is missing a valid mode in front matter.\n"
                        "  expected: mode: bounded|timeboxed\n"
                        "  remediation: regenerate a template via `ph sprint plan --force` (or add front matter)\n"
                    ),
                }
            )
            return

    lines = text.splitlines()
    for idx, raw in enumerate(lines, start=1):
        if _HEADING_INSIDE_LIST_RE.match(raw):
            issues.append(
                {
                    "path": str(plan_path),
                    "code": "sprint_plan_heading_inside_list",
                    "severity": "error",
                    "line": idx,
                    "example": raw.strip(),
                    "message": (
                        "Sprint plan appears to contain a Markdown heading pasted into a list item.\n"
                        f"  line: {idx}\n"
                        f"  example: {raw.strip()}\n"
                        "  remediation: remove the list marker before the heading (e.g. `- ##` -> `##`).\n"
                        "  reference: compare to a fresh template (`ph sprint plan --force`).\n"
                    ),
                }
            )
            break

    in_fence = False
    h1_positions: list[tuple[str, int]] = []
    h2_positions: list[tuple[str, int]] = []
    for idx, raw in enumerate(lines, start=1):
        stripped = raw.rstrip("\n")
        if stripped.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("# "):
            h1_positions.append((stripped.strip(), idx))
        elif stripped.startswith("## "):
            h2_positions.append((stripped.strip(), idx))

    sprint_id = str(fm.get("sprint") or "").strip()
    expected_h1 = f"# Sprint Plan: {sprint_id}" if sprint_id else None
    h1_ok = False
    if expected_h1:
        h1_ok = any(h == expected_h1 for h, _ in h1_positions)
    else:
        h1_ok = any(h.startswith("# Sprint Plan:") for h, _ in h1_positions)

    if not h1_ok:
        issues.append(
            {
                "path": str(plan_path),
                "code": "sprint_plan_title_missing_or_mismatch",
                "severity": "error",
                "message": (
                    "Current sprint plan is missing the expected title heading.\n"
                    f"  expected: {expected_h1 or '# Sprint Plan: <SPRINT-ID>'}\n"
                    "  remediation: restore the template title heading near the top of the plan.\n"
                ),
            }
        )

    release_slot = _as_int(fm.get("release_sprint_slot"))

    required_h2: list[str] = []
    if mode == "bounded":
        required_h2 = [
            "## Sprint Model",
            "## Sprint Goal",
        ]
        if scope != "system":
            if release_slot is not None:
                required_h2.append(f"## Release Alignment (Slot {release_slot})")
            else:
                required_h2.append("## Release Alignment (Explicit)")
        required_h2.extend(
            [
                "## Boundaries (Lanes)",
                "## Integration Tasks",
                "## Task Creation Guide",
                "## Telemetry (Points)",
                "## Dependencies & Risks",
                "## Success Criteria",
            ]
        )
    else:
        required_h2 = [
            "## Sprint Duration",
            "## Sprint Goals",
        ]
        if release_slot is not None:
            required_h2.append(f"## Release Alignment (Slot {release_slot})")
        else:
            required_h2.append("## Release Alignment (Optional)")
        required_h2.extend(
            [
                "## Task Creation Guide",
                "## Capacity Planning (Optional)",
                "## Dependencies & Risks",
                "## Success Criteria",
            ]
        )

    h2_to_line: dict[str, int] = {}
    for heading, line_no in h2_positions:
        h2_to_line.setdefault(heading, line_no)

    for heading in required_h2:
        if heading not in h2_to_line:
            issues.append(
                {
                    "path": str(plan_path),
                    "code": "sprint_plan_missing_heading",
                    "severity": "error",
                    "expected_heading": heading,
                    "message": (
                        "Current sprint plan is missing a required section heading.\n"
                        f"  expected_heading: {heading}\n"
                        "  remediation: restore the missing heading to match the sprint plan template.\n"
                    ),
                }
            )

    present = [h for h in required_h2 if h in h2_to_line]
    for prev, nxt in zip(present, present[1:]):
        if h2_to_line[prev] > h2_to_line[nxt]:
            issues.append(
                {
                    "path": str(plan_path),
                    "code": "sprint_plan_heading_order",
                    "severity": "error",
                    "expected_order": required_h2,
                    "found_order": present,
                    "message": (
                        "Current sprint plan section headings are out of order.\n"
                        f"  expected_order: {required_h2}\n"
                        f"  found_order: {present}\n"
                        f"  first_inversion: {prev} appears after {nxt}\n"
                    ),
                }
            )
            break


def validate_release_plan_slots(*, issues: list[dict], root: Path) -> None:
    releases_dir = root / "releases"
    if not releases_dir.exists():
        return

    slot_heading_re = re.compile(r"^## Slot ([1-9][0-9]*):\s*(.+)$")
    legacy_slot_heading_re = re.compile(r"^###\s+Slot\s+([1-9][0-9]*)\b", flags=re.IGNORECASE)

    for release_dir in sorted(releases_dir.iterdir()):
        if not release_dir.is_dir():
            continue
        if not release_dir.name.startswith("v"):
            continue

        plan_path = release_dir / "plan.md"
        if not plan_path.exists():
            continue

        text = read(plan_path)
        fm, _, _ = parse_front_matter(text)
        planned_sprints = _as_int(fm.get("planned_sprints"))
        if planned_sprints is None or planned_sprints < 1:
            continue

        # Strict-only enforcement: legacy slot formats are disallowed even if strict slots also exist.
        legacy_detected = False
        if "## Slot Plans" in text:
            legacy_detected = True
        elif legacy_slot_heading_re.search(text):
            legacy_detected = True
        elif "#### Goal / Purpose" in text:
            legacy_detected = True
        if legacy_detected:
            issues.append(
                {
                    "path": str(plan_path),
                    "code": "release_slot_legacy_format",
                    "severity": "error",
                    "message": (
                        "Release plan uses a legacy slot format. Only strict slot sections are accepted.\n"
                        f"  release: {release_dir.name}\n"
                        "  expected_heading: ## Slot <n>: <label>\n"
                        "  remediation: ph release migrate-slot-format --release "
                        f"{release_dir.name} --diff\n"
                        "  apply_fix: ph release migrate-slot-format --release "
                        f"{release_dir.name} --write-back\n"
                    ),
                }
            )

        lines = text.splitlines()
        slot_starts: list[tuple[int, int]] = []
        for idx, line in enumerate(lines):
            match = slot_heading_re.match(line)
            if not match:
                continue
            slot_starts.append((int(match.group(1)), idx))

        by_slot: dict[int, list[int]] = {}
        for slot, idx in slot_starts:
            by_slot.setdefault(slot, []).append(idx)

        for slot, idxs in sorted(by_slot.items()):
            if len(idxs) > 1:
                issues.append(
                    {
                        "path": str(plan_path),
                        "code": "release_slot_duplicate",
                        "severity": "error",
                        "slot": slot,
                        "message": (
                            "Release plan has duplicate slot section headings.\n"
                            f"  slot: {slot}\n"
                            "  expected: exactly one `## Slot <n>: <label>` per slot\n"
                        ),
                    }
                )

        for slot in range(1, planned_sprints + 1):
            if slot not in by_slot:
                issues.append(
                    {
                        "path": str(plan_path),
                        "code": "release_slot_missing",
                        "severity": "error",
                        "slot": slot,
                        "message": (
                            "Release plan missing required slot section.\n"
                            f"  expected_heading: ## Slot {slot}: <label>\n"
                            "  required_subsection: ### Intended Gates (must include at least one `- Gate:` bullet)\n"
                        ),
                    }
                )

        if not slot_starts:
            continue

        slot_starts_sorted = sorted(slot_starts, key=lambda t: t[1])
        for i, (slot, start_idx) in enumerate(slot_starts_sorted):
            if slot < 1 or slot > planned_sprints:
                continue

            end_idx = slot_starts_sorted[i + 1][1] if i + 1 < len(slot_starts_sorted) else len(lines)
            section_lines = lines[start_idx:end_idx]

            intended_gates_idx = None
            for j, line in enumerate(section_lines):
                if line.strip() == "### Intended Gates":
                    intended_gates_idx = j
                    break

            if intended_gates_idx is None:
                issues.append(
                    {
                        "path": str(plan_path),
                        "code": "release_slot_intended_gates_missing",
                        "severity": "error",
                        "slot": slot,
                        "message": (
                            "Release plan slot section missing required subsection.\n"
                            f"  slot: {slot}\n"
                            "  expected_subsection: ### Intended Gates\n"
                            "  expected_list_item: - Gate: ...\n"
                        ),
                    }
                )
                continue

            gate_lines: list[str] = []
            for line in section_lines[intended_gates_idx + 1 :]:
                if re.match(r"^##\s", line) or re.match(r"^###\s", line):
                    break
                gate_lines.append(line)

            if not any(re.match(r"^\s*-\s*Gate:", line) for line in gate_lines):
                issues.append(
                    {
                        "path": str(plan_path),
                        "code": "release_slot_intended_gates_missing_gate_item",
                        "severity": "error",
                        "slot": slot,
                        "message": (
                            "Release plan slot '### Intended Gates' must include at least one gate bullet.\n"
                            f"  slot: {slot}\n"
                            "  expected_list_item_prefix: - Gate:\n"
                        ),
                    }
                )


def validate_sprint_release_alignment(*, issues: list[dict], root: Path) -> None:
    sprints_dir = root / "sprints"
    if not sprints_dir.exists():
        return

    for plan_path in sorted(sprints_dir.rglob("plan.md")):
        # Avoid double-validating through `sprints/current` when it is a link.
        try:
            rel = plan_path.relative_to(sprints_dir).as_posix()
        except Exception:
            rel = str(plan_path)
        if rel.startswith("current/"):
            continue

        text = read(plan_path)
        fm, _, _ = parse_front_matter(text)

        release = str(fm.get("release", "")).strip()
        if not release or release.lower() in {"null", "none"}:
            continue

        slot = _as_int(fm.get("release_sprint_slot"))
        if slot is None:
            continue

        heading_re = re.compile(rf"^## Release Alignment \(Slot {slot}\)\s*$", flags=re.MULTILINE)
        if not heading_re.search(text):
            sprint_id = str(fm.get("sprint", "")).strip()
            issues.append(
                {
                    "path": str(plan_path),
                    "code": "sprint_release_alignment_missing",
                    "severity": "error",
                    "slot": slot,
                    "release": release,
                    "message": (
                        "Sprint plan is assigned to a release slot but missing the required alignment section.\n"
                        f"  sprint: {sprint_id or '<unknown>'}\n"
                        f"  release: {release}\n"
                        f"  expected_heading: ## Release Alignment (Slot {slot})\n"
                    ),
                }
            )


def validate_release_features_schema(*, issues: list[dict], root: Path) -> None:
    releases_dir = root / "releases"
    if not releases_dir.exists():
        return

    def parse_features_file(path: Path) -> tuple[int | None, dict[str, dict[str, str]]]:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            return None, {}

        planned_sprints = None
        features: dict[str, dict[str, str]] = {}
        in_features = False
        current: str | None = None
        for raw in text.splitlines():
            line = raw.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("planned_sprints:"):
                planned_sprints = _as_int(stripped.split(":", 1)[1].strip())
                continue
            if stripped == "features:":
                in_features = True
                current = None
                continue
            if not in_features:
                continue
            if line.startswith("  ") and ":" in line and not line.startswith("    "):
                current = line.strip().split(":", 1)[0].strip()
                if current:
                    features[current] = {}
                continue
            if current and line.startswith("    ") and ":" in line:
                k, v = line.strip().split(":", 1)
                key = k.strip()
                value = v.strip().strip('"').strip("'")
                if key:
                    features[current][key] = value
        return planned_sprints, features

    for release_dir in sorted(releases_dir.iterdir()):
        if not release_dir.is_dir() or not release_dir.name.startswith("v"):
            continue
        features_path = release_dir / "features.yaml"
        if not features_path.exists():
            continue

        planned_sprints, features = parse_features_file(features_path)
        if planned_sprints is None or planned_sprints < 1:
            continue

        for feature_name, meta in sorted(features.items(), key=lambda t: t[0]):
            slot_raw = meta.get("slot")
            commitment = (meta.get("commitment") or "").strip().lower()
            intent = (meta.get("intent") or "").strip().lower()

            if slot_raw is None or str(slot_raw).strip() == "":
                issues.append(
                    {
                        "path": str(features_path),
                        "code": "release_feature_missing_slot",
                        "severity": "error",
                        "release": release_dir.name,
                        "feature": feature_name,
                        "message": (
                            "Release feature assignment is missing required field: slot\n"
                            f"  release: {release_dir.name}\n"
                            f"  feature: {feature_name}\n"
                            f"  expected: slot: <int> (1..{planned_sprints})\n"
                        ),
                    }
                )
            else:
                slot = _as_int(slot_raw)
                if slot is None or slot < 1 or slot > planned_sprints:
                    issues.append(
                        {
                            "path": str(features_path),
                            "code": "release_feature_slot_out_of_range",
                            "severity": "error",
                            "release": release_dir.name,
                            "feature": feature_name,
                            "slot": slot_raw,
                            "message": (
                                "Release feature assignment has an invalid slot.\n"
                                f"  release: {release_dir.name}\n"
                                f"  feature: {feature_name}\n"
                                f"  slot: {slot_raw}\n"
                                f"  expected_range: 1..{planned_sprints}\n"
                            ),
                        }
                    )

            if commitment not in {"committed", "stretch"}:
                issues.append(
                    {
                        "path": str(features_path),
                        "code": "release_feature_invalid_commitment",
                        "severity": "error",
                        "release": release_dir.name,
                        "feature": feature_name,
                        "message": (
                            "Release feature assignment has an invalid commitment.\n"
                            f"  release: {release_dir.name}\n"
                            f"  feature: {feature_name}\n"
                            f"  commitment: {meta.get('commitment')}\n"
                            "  expected: committed|stretch\n"
                        ),
                    }
                )

            if intent not in {"deliver", "decide", "enable"}:
                issues.append(
                    {
                        "path": str(features_path),
                        "code": "release_feature_invalid_intent",
                        "severity": "error",
                        "release": release_dir.name,
                        "feature": feature_name,
                        "message": (
                            "Release feature assignment has an invalid intent.\n"
                            f"  release: {release_dir.name}\n"
                            f"  feature: {feature_name}\n"
                            f"  intent: {meta.get('intent')}\n"
                            "  expected: deliver|decide|enable\n"
                        ),
                    }
                )


def validate_decision_register_sources(*, issues: list[dict], root: Path) -> None:
    dirs: list[Path] = []
    project_dir = root / "decision-register"
    if project_dir.exists():
        dirs.append(project_dir)
    features_dir = root / "features"
    if features_dir.exists():
        for feat in sorted([p for p in features_dir.iterdir() if p.is_dir()]):
            dr_dir = feat / "decision-register"
            if dr_dir.exists():
                dirs.append(dr_dir)

    sources_re = re.compile(r"^##\s+Sources\s*$", flags=re.MULTILINE)
    for dr_dir in dirs:
        for md in sorted(dr_dir.glob("DR-*.md")):
            text = read(md)
            fm, _, _ = parse_front_matter(text)
            if str(fm.get("type") or "").strip().lower() != "decision-register":
                continue
            if sources_re.search(text):
                continue
            issues.append(
                {
                    "path": str(md),
                    "code": "decision_register_sources_missing",
                    "severity": "error",
                    "message": (
                        "Decision Register entries must include a Sources section.\n"
                        "  expected_heading: ## Sources\n"
                        "  expected_items: URL + accessed date + relevance note\n"
                    ),
                }
            )


def validate_phase(*, issues: list[dict], root: Path) -> None:
    exec_dir = root / "execution"
    if not exec_dir.exists():
        return

    for pdir in [p for p in exec_dir.iterdir() if p.is_dir()]:
        readme = pdir / "README.md"
        phase_yaml = pdir / "phase.yaml"
        if readme.exists() and phase_yaml.exists():
            rfm, _, _ = parse_front_matter(read(readme))
            data = parse_simple_yaml_mapping(phase_yaml.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for k in ["phase", "title"]:
                    if str(data.get(k, "")) != str(rfm.get(k, "")):
                        issues.append({"path": str(pdir), "code": f"phase_mismatch_{k}", "severity": "error"})
                if not data.get("features"):
                    issues.append({"path": str(pdir), "code": "phase_features_missing", "severity": "error"})
                if not data.get("decisions"):
                    issues.append({"path": str(pdir), "code": "phase_decisions_missing", "severity": "error"})


def run_validate(
    *,
    ph_root: Path,
    ph_project_root: Path,
    ph_data_root: Path,
    scope: str,
    quick: bool,
    silent_success: bool,
) -> tuple[int, Path, str]:
    rules = load_validation_rules(ph_project_root=ph_project_root)

    normalized_count = normalize_roadmap_links(rules=rules, root=ph_project_root, scope=scope, quick=quick)
    normalization_message = f"Normalized {normalized_count} roadmap link(s)\n" if normalized_count else ""

    issues: list[dict] = []
    validate_front_matter(issues=issues, rules=rules, root=ph_data_root, ph_root=ph_root, scope=scope)
    validate_current_sprint_plan_structure(issues=issues, root=ph_data_root, scope=scope)
    validate_session_end_index(issues=issues, ph_project_root=ph_project_root, ph_root=ph_root)
    validate_system_scope_artifacts_in_project_scope(
        issues=issues, rules=rules, root=ph_project_root, ph_root=ph_root, scope=scope
    )
    validate_adrs(issues=issues, root=ph_data_root)
    validate_adr_fdr_backlinks(issues=issues, root=ph_data_root)

    try:
        validate_release_plan_slots(issues=issues, root=ph_data_root)
        validate_sprint_release_alignment(issues=issues, root=ph_data_root)
        validate_release_features_schema(issues=issues, root=ph_data_root)
        validate_decision_register_sources(issues=issues, root=ph_data_root)
    except Exception:
        pass

    try:
        validate_sprints(issues=issues, rules=rules, root=ph_data_root)
    except Exception:
        pass

    if not quick:
        try:
            validate_phase(issues=issues, root=ph_data_root)
        except Exception:
            pass

    out = ph_data_root / "status" / "validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"issues": issues}, indent=2) + "\n", encoding="utf-8")

    errs = sum(1 for i in issues if i.get("severity") == "error")
    warns = sum(1 for i in issues if i.get("severity") == "warning")

    if silent_success and errs == 0 and warns == 0:
        return 0, out, normalization_message

    return (
        (1 if errs > 0 else 0),
        out,
        (normalization_message + f"validation: {errs} error(s), {warns} warning(s), report: {out}\n"),
    )
