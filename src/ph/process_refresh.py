from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .clock import today as clock_today
from .context import Context
from .seed_assets import load_seed_markdown_dir, render_date_placeholder

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
