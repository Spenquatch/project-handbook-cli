from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .clock import today as clock_today
from .context import Context
from .seed_assets import load_seed_markdown_dir, render_date_placeholder
from .task_taxonomy import SESSION_TO_LEGACY_TASK_TYPE, TASK_TYPE_TO_SESSION, normalize_session, normalize_task_type

_SYSTEM_SCOPE_REMEDIATION = "Process refresh is project-scope only. Use: ph --scope project process refresh ..."


_FRONT_MATTER_BOUNDARY = "---"


def _normalize_for_seed_hash(text: str) -> str:
    """
    Normalize process markdown for seed ownership hashing:
    - ignore the front matter `seed_hash:` line
    - ignore the front matter `date:` line (playbooks are date-stamped on write)
    """
    if not text.startswith(f"{_FRONT_MATTER_BOUNDARY}\n"):
        return text.rstrip() + "\n"
    lines = text.splitlines()
    out: list[str] = []
    in_fm = False
    fm_done = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == _FRONT_MATTER_BOUNDARY:
            in_fm = True
            out.append(line)
            continue
        if in_fm and line.strip() == _FRONT_MATTER_BOUNDARY and not fm_done:
            fm_done = True
            in_fm = False
            out.append(line)
            continue
        if in_fm:
            if line.startswith("seed_hash:"):
                continue
            if line.startswith("date:"):
                continue
            out.append(line)
        else:
            out.append(line)
    return "\n".join(out).rstrip() + "\n"


def _compute_seed_hash(text: str) -> str:
    normalized = _normalize_for_seed_hash(text).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def _upsert_front_matter_kv(text: str, *, key: str, value: str) -> str:
    if not text.startswith(f"{_FRONT_MATTER_BOUNDARY}\n"):
        text = f"{_FRONT_MATTER_BOUNDARY}\n{_FRONT_MATTER_BOUNDARY}\n\n" + text.lstrip("\n")

    lines = text.splitlines()
    out: list[str] = []
    in_fm = False
    inserted = False

    for i, line in enumerate(lines):
        if i == 0 and line.strip() == _FRONT_MATTER_BOUNDARY:
            in_fm = True
            out.append(line)
            continue
        if in_fm and line.strip() == _FRONT_MATTER_BOUNDARY:
            if not inserted:
                out.append(f"{key}: {value}")
                inserted = True
            out.append(line)
            in_fm = False
            continue
        if in_fm and line.startswith(f"{key}:"):
            out.append(f"{key}: {value}")
            inserted = True
            continue
        out.append(line)

    if not inserted:
        # If we didn't find the end boundary, just append; malformed file will be rewritten.
        out.append(f"{key}: {value}")
    return "\n".join(out).rstrip() + "\n"


def inject_seed_id_and_hash(*, text: str, seed_id: str) -> str:
    text = _upsert_front_matter_kv(text, key="seed_id", value=seed_id)
    # seed_hash value computed on the resulting content (hash ignores seed_hash/date lines).
    text = _upsert_front_matter_kv(text, key="seed_hash", value="__PENDING__")
    digest = _compute_seed_hash(text)
    text = _upsert_front_matter_kv(text, key="seed_hash", value=digest)
    return text


def _read_front_matter_value(text: str, key: str) -> str | None:
    if not text.startswith(f"{_FRONT_MATTER_BOUNDARY}\n"):
        return None
    lines = text.splitlines()
    for line in lines[1:]:
        if line.strip() == _FRONT_MATTER_BOUNDARY:
            break
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip() or None
    return None


def _is_seed_owned_and_unmodified(*, path: Path, expected_seed_id: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False
    seed_id = _read_front_matter_value(text, "seed_id")
    seed_hash = _read_front_matter_value(text, "seed_hash")
    if not seed_id or not seed_hash:
        return False
    if seed_id.strip() != expected_seed_id:
        return False
    current_hash = _compute_seed_hash(text)
    return current_hash == seed_hash.strip()


def run_process_refresh(
    *,
    ctx: Context,
    templates: bool,
    playbooks: bool,
    force: bool,
    disable_system_scope_enforcement: bool,
    migrate_tasks_drop_session: bool,
    env: dict[str, str],
) -> int:
    if ctx.scope == "system":
        print(_SYSTEM_SCOPE_REMEDIATION)
        return 1

    if not templates and not playbooks:
        templates = True
        playbooks = True

    today = clock_today(env=env).strftime("%Y-%m-%d")

    wrote = 0
    skipped = 0

    enforcement_disabled = False
    system_scope_config_deleted = False
    if disable_system_scope_enforcement:
        rules_path = ctx.ph_project_root / "process" / "checks" / "validation_rules.json"
        try:
            rules = json.loads(rules_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(f"❌ Missing validation rules: {rules_path}")
            return 1
        except Exception as exc:
            print(f"❌ Failed to read validation rules: {rules_path} ({exc})")
            return 1

        if not isinstance(rules, dict):
            rules = {}
        enforcement = rules.get("system_scope_enforcement")
        if not isinstance(enforcement, dict):
            enforcement = {}
        enforcement["enabled"] = False
        rules["system_scope_enforcement"] = enforcement

        try:
            rules_path.write_text(json.dumps(rules, indent=2) + "\n", encoding="utf-8")
            enforcement_disabled = True
        except Exception as exc:
            print(f"❌ Failed to write validation rules: {rules_path} ({exc})")
            return 1

        config_path = ctx.ph_project_root / "process" / "automation" / "system_scope_config.json"
        try:
            if config_path.exists():
                config_path.unlink()
                system_scope_config_deleted = True
        except Exception as exc:
            print(f"❌ Failed to delete system scope config: {config_path} ({exc})")
            return 1

    if templates:
        seed = load_seed_markdown_dir(rel_dir="process/sessions/templates")
        dest_dir = ctx.ph_project_root / "process" / "sessions" / "templates"
        dest_dir.mkdir(parents=True, exist_ok=True)
        for name, raw in seed.items():
            seed_id = f"process/sessions/templates/{name}.md"
            desired = inject_seed_id_and_hash(text=raw, seed_id=seed_id)
            dest = dest_dir / f"{name}.md"
            if dest.exists() and not force and not _is_seed_owned_and_unmodified(path=dest, expected_seed_id=seed_id):
                skipped += 1
                continue
            dest.write_text(desired, encoding="utf-8")
            wrote += 1

    if playbooks:
        seed = load_seed_markdown_dir(rel_dir="process/playbooks")
        dest_dir = ctx.ph_project_root / "process" / "playbooks"
        dest_dir.mkdir(parents=True, exist_ok=True)
        for name, raw in seed.items():
            seed_id = f"process/playbooks/{name}.md"
            rendered = render_date_placeholder(raw, date=today)
            desired = inject_seed_id_and_hash(text=rendered, seed_id=seed_id)
            dest = dest_dir / f"{name}.md"
            if dest.exists() and not force and not _is_seed_owned_and_unmodified(path=dest, expected_seed_id=seed_id):
                skipped += 1
                continue
            dest.write_text(desired, encoding="utf-8")
            wrote += 1

    def _resolve_current_sprint_dir() -> Path | None:
        link = ctx.ph_data_root / "sprints" / "current"
        if not link.exists():
            return None
        try:
            resolved = link.resolve()
        except FileNotFoundError:
            return None
        return resolved if resolved.exists() else None

    def _rewrite_task_yaml_drop_session(text: str) -> tuple[str, bool, str | None]:
        """
        Returns: (new_text, changed, inferred_task_type)
        """
        lines = text.splitlines()
        out: list[str] = []
        saw_session = False
        raw_session: str | None = None
        raw_task_type: str | None = None

        for line in lines:
            if re.match(r"^session:\s*", line):
                saw_session = True
                raw_session = normalize_session(line.split(":", 1)[1]) if ":" in line else None
                continue
            if re.match(r"^task_type:\s*", line):
                raw_task_type = normalize_task_type(line.split(":", 1)[1]) if ":" in line else None
                out.append(line)
                continue
            out.append(line)

        inferred_task_type: str | None = None
        if not raw_task_type and raw_session:
            inferred = SESSION_TO_LEGACY_TASK_TYPE.get(raw_session, "")
            if inferred:
                inferred_task_type = inferred
                insert_after = None
                for idx, line in enumerate(out):
                    if line.startswith("decision:"):
                        insert_after = idx
                        break
                if insert_after is None:
                    for idx, line in enumerate(out):
                        if line.startswith("feature:"):
                            insert_after = idx
                            break
                if insert_after is None:
                    for idx, line in enumerate(out):
                        if line.startswith("title:"):
                            insert_after = idx
                            break
                if insert_after is None:
                    insert_after = 0
                out.insert(insert_after + 1, f"task_type: {inferred_task_type}")
            else:
                # Unmappable legacy session with no task_type: do not mutate the file (avoid deleting
                # the only routing hint). We'll report it in the migration summary.
                return text.rstrip() + "\n", False, None

        new_text = "\n".join(out).rstrip() + "\n"
        changed = saw_session or (inferred_task_type is not None)
        return new_text, changed, inferred_task_type

    def _rewrite_readme_drop_session(text: str) -> tuple[str, bool]:
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            # Best-effort removal of a body line (legacy format).
            filtered = [ln for ln in lines if not ln.strip().startswith("**Session**:")]
            new_text = "\n".join(filtered).rstrip() + "\n"
            return new_text, new_text != (text.rstrip() + "\n")

        out: list[str] = []
        in_fm = False
        fm_done = False
        changed = False
        for idx, line in enumerate(lines):
            if idx == 0 and line.strip() == "---":
                in_fm = True
                out.append(line)
                continue
            if in_fm and line.strip() == "---" and not fm_done:
                fm_done = True
                in_fm = False
                out.append(line)
                continue
            if in_fm and line.startswith("session:"):
                changed = True
                continue
            if not in_fm and line.strip().startswith("**Session**:"):
                changed = True
                continue
            out.append(line)
        new_text = "\n".join(out).rstrip() + "\n"
        return new_text, changed

    if migrate_tasks_drop_session:
        sprint_dir = _resolve_current_sprint_dir()
        if sprint_dir is None:
            print("⚠️  Task migration skipped: no current sprint is set (sprints/current missing).")
        else:
            tasks_dir = sprint_dir / "tasks"
            scanned = 0
            updated_yaml = 0
            updated_readme = 0
            inferred_types = 0
            unmappable_sessions: set[str] = set()

            if tasks_dir.exists():
                for task_dir in sorted(tasks_dir.iterdir()):
                    if not task_dir.is_dir() or not task_dir.name.startswith("TASK-"):
                        continue
                    scanned += 1

                    task_yaml = task_dir / "task.yaml"
                    if task_yaml.exists():
                        try:
                            before = task_yaml.read_text(encoding="utf-8")
                        except Exception:
                            before = ""
                        if before:
                            after, changed, inferred = _rewrite_task_yaml_drop_session(before)
                            if inferred is None:
                                # If session was present but unmappable and task_type missing, record for summary.
                                raw_session = None
                                for line in before.splitlines():
                                    if line.startswith("session:"):
                                        raw_session = normalize_session(line.split(":", 1)[1])
                                        break
                                if raw_session and not normalize_task_type(
                                    next(
                                        (
                                            ln.split(":", 1)[1]
                                            for ln in before.splitlines()
                                            if ln.startswith("task_type:")
                                        ),
                                        "",
                                    )
                                ):
                                    if raw_session not in TASK_TYPE_TO_SESSION.values():
                                        unmappable_sessions.add(raw_session)
                            if changed and after != before:
                                task_yaml.write_text(after, encoding="utf-8")
                                updated_yaml += 1
                            if inferred is not None:
                                inferred_types += 1
                    readme = task_dir / "README.md"
                    if readme.exists():
                        try:
                            before = readme.read_text(encoding="utf-8")
                        except Exception:
                            before = ""
                        if before:
                            after, changed = _rewrite_readme_drop_session(before)
                            if changed and after != before:
                                readme.write_text(after, encoding="utf-8")
                                updated_readme += 1

            print(
                "✅ Task migration complete (drop deprecated `session:`): "
                f"scanned={scanned} task_yaml_updated={updated_yaml} readme_updated={updated_readme} "
                f"task_type_inferred={inferred_types}"
            )
            if unmappable_sessions:
                csv = ", ".join(sorted(unmappable_sessions))
                print(f"⚠️  Unmappable session values encountered (manual cleanup needed): {csv}")

    print(f"✅ Process refresh complete: wrote={wrote} skipped={skipped}")
    if disable_system_scope_enforcement:
        print(
            "System scope enforcement disabled:"
            f" validation_rules.json={'updated' if enforcement_disabled else 'unchanged'}"
            f", system_scope_config.json={'deleted' if system_scope_config_deleted else 'absent'}"
        )
    if skipped and not force:
        print("Tip: re-run with `--force` to overwrite locally modified seed-owned files.")
    return 0
