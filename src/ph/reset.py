from __future__ import annotations

import json
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .context import Context


class ResetError(RuntimeError):
    pass


def _path_is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except Exception:
        return False


def _resolve_repo_relative(ph_root: Path, rel: str) -> Path:
    raw = (rel or "").strip()
    if not raw:
        raise ResetError("Invalid reset spec: empty path entry\n")
    p = Path(raw)
    if p.is_absolute():
        raise ResetError(f"Invalid reset spec: absolute paths are not allowed ({rel!r})\n")
    abs_path = (ph_root / p).absolute()
    if not _path_is_relative_to(abs_path, ph_root.absolute()):
        raise ResetError(f"Invalid reset spec: path escapes repo root ({rel!r})\n")
    return abs_path


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ResetError(f"Missing reset spec: {path}\n") from exc
    except json.JSONDecodeError as exc:
        raise ResetError(f"Invalid JSON in reset spec: {path} ({exc})\n") from exc


def _as_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ResetError(f"Invalid reset spec: {field} must be a list\n")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ResetError(f"Invalid reset spec: {field} entries must be non-empty strings\n")
        out.append(item.strip())
    return out


def _compute_delete_set_for_dir(root: Path, protected: list[Path], forbidden_subtree: Path | None) -> set[Path]:
    if not root.exists():
        return set()
    if not root.is_dir():
        raise ResetError(f"Invalid reset spec: delete_contents_roots entry is not a directory: {root}\n")

    if forbidden_subtree is not None and _path_is_relative_to(root.absolute(), forbidden_subtree.absolute()):
        raise ResetError(f"Refusing to compute delete set under forbidden subtree: {root}\n")

    delete_set: set[Path] = set()

    def contains_protected(candidate: Path) -> bool:
        cand_abs = candidate.absolute()
        return any(_path_is_relative_to(p, cand_abs) or p == cand_abs for p in protected)

    def walk_dir(dir_path: Path) -> None:
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: p.name)
        except FileNotFoundError:
            return

        for entry in entries:
            entry_abs = entry.absolute()
            if entry_abs in protected:
                continue

            if contains_protected(entry_abs):
                if entry.is_symlink():
                    continue
                if entry.is_dir():
                    walk_dir(entry)
                continue

            delete_set.add(entry_abs)

    walk_dir(root)
    return delete_set


def _dedupe_and_sort(paths: Iterable[Path]) -> list[Path]:
    unique = {p.absolute() for p in paths}
    return sorted(unique, key=lambda p: (len(p.parts), p.as_posix()))


def _delete_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink():
        path.unlink()
        return
    if path.is_dir():
        shutil.rmtree(path)
        return
    path.unlink()


def _rewrite_templates(ph_root: Path, rel_paths: list[str]) -> None:
    templates: dict[str, str] = {
        ".project-handbook/roadmap/now-next-later.md": """---
title: Now / Next / Later Roadmap
type: roadmap
date: 2025-09-18
tags: [roadmap]
links: []
---

# Now / Next / Later Roadmap

## Now

## Next

## Later
""",
        ".project-handbook/process/sessions/logs/latest_summary.md": """---
title: Latest Session Summary
type: session-summary
date: 2025-12-22
tags: [sessions, summary]
links: []
---

# Latest Session Summary

No session summary has been generated yet.

Run:
```bash
ph end-session --log <path-to-rollout-jsonl>
```
""",
        ".project-handbook/process/sessions/session_end/session_end_index.json": json.dumps({"records": []}, indent=2)
        + "\n",
        ".project-handbook/sprints/archive/index.json": json.dumps({"sprints": []}, indent=2) + "\n",
        ".project-handbook/backlog/index.json": json.dumps(
            {
                "last_updated": None,
                "total_items": 0,
                "by_severity": {"P0": [], "P1": [], "P2": [], "P3": [], "P4": []},
                "by_category": {"bugs": [], "wildcards": [], "work-items": []},
                "items": [],
            },
            indent=2,
        )
        + "\n",
        ".project-handbook/parking-lot/index.json": json.dumps(
            {
                "last_updated": None,
                "total_items": 0,
                "by_category": {
                    "features": [],
                    "technical-debt": [],
                    "research": [],
                    "external-requests": [],
                },
                "items": [],
            },
            indent=2,
        )
        + "\n",
    }

    for rel in rel_paths:
        content = templates.get(rel)
        if content is None:
            raise ResetError(f"Reset spec requested rewrite but no template is defined in reset.py: {rel}\n")
        out_path = _resolve_repo_relative(ph_root, rel)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")


def run_reset(*, ctx: Context, spec: str, include_system: bool, confirm: str, force: str) -> int:
    if ctx.scope == "system":
        print("Reset is project-scope only. Use: ph --scope project reset ...")
        return 1

    spec_path = _resolve_repo_relative(ctx.ph_root, spec)
    reset_spec = _load_json(spec_path)

    if int(reset_spec.get("schema_version") or 0) != 1:
        raise ResetError(f"Invalid reset spec schema_version (expected 1): {spec_path}\n")

    delete_contents_roots = _as_list(reset_spec.get("delete_contents_roots"), "delete_contents_roots")
    delete_paths = _as_list(reset_spec.get("delete_paths"), "delete_paths")
    preserve_paths = _as_list(reset_spec.get("preserve_paths"), "preserve_paths")
    rewrite_paths = _as_list(reset_spec.get("rewrite_paths"), "rewrite_paths")
    recreate_dirs = _as_list(reset_spec.get("recreate_dirs"), "recreate_dirs")
    recreate_files = _as_list(reset_spec.get("recreate_files"), "recreate_files")

    system_root = _resolve_repo_relative(ctx.ph_root, ".project-handbook/system")

    protected_abs = [_resolve_repo_relative(ctx.ph_root, rel) for rel in sorted(set(preserve_paths + rewrite_paths))]

    if not include_system:
        for rel in delete_contents_roots + delete_paths:
            if rel.startswith(".project-handbook/system") or rel.startswith(".project-handbook/system/"):
                raise ResetError("Invalid reset spec: .project-handbook/system/** MUST NOT appear in delete lists\n")

    delete_set: set[Path] = set()

    for root_rel in delete_contents_roots:
        root_abs = _resolve_repo_relative(ctx.ph_root, root_rel)
        forbidden = system_root if not include_system else None
        delete_set |= _compute_delete_set_for_dir(root_abs, protected_abs, forbidden)

    for rel in delete_paths:
        abs_path = _resolve_repo_relative(ctx.ph_root, rel)
        if abs_path in protected_abs:
            continue
        delete_set.add(abs_path)

    if include_system and (system_root.exists() or system_root.is_symlink()):
        delete_set.add(system_root.absolute())

    if not include_system:
        for p in delete_set:
            if _path_is_relative_to(p.absolute(), system_root.absolute()):
                raise ResetError(f"Refusing to run: computed delete set intersects .project-handbook/system/** ({p})\n")

    delete_list = _dedupe_and_sort(delete_set)
    delete_list_rel = [str(p.relative_to(ctx.ph_root).as_posix()) for p in delete_list]

    executing = confirm == "RESET" and force == "true"
    mode = "EXECUTE" if executing else "DRY-RUN"

    print("project-handbook reset report")
    print(f"spec: {spec_path.relative_to(ctx.ph_root).as_posix()}")
    print(f"mode: {mode}")
    print("")
    print("delete_set:")
    for rel in delete_list_rel:
        print(f"  - {rel}")
    print("")

    if not executing:
        print("No filesystem changes made.")
        include_note = " --include-system" if include_system else ""
        print(f"To execute: ph reset{include_note} --confirm RESET --force true")
        return 0

    for p in sorted(delete_list, key=lambda x: (-len(x.parts), x.as_posix())):
        _delete_path(p)

    for rel in recreate_dirs:
        _resolve_repo_relative(ctx.ph_root, rel).mkdir(parents=True, exist_ok=True)

    for rel in recreate_files:
        file_path = _resolve_repo_relative(ctx.ph_root, rel)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.write_text("", encoding="utf-8")

    _rewrite_templates(ctx.ph_root, rewrite_paths)

    print("✅ Reset complete.")
    return 0
