from __future__ import annotations

import datetime as dt
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .backlog_manager import BacklogManager
from .clock import now as clock_now
from .parking_lot_manager import ParkingLotManager


@dataclass(frozen=True)
class WorkItemRef:
    item_type: str  # "backlog" | "parking-lot"
    category: str
    item_id: str

    def source_dir(self, *, ph_data_root: Path) -> Path:
        if self.item_type == "backlog":
            return ph_data_root / "backlog" / self.category / self.item_id
        return ph_data_root / "parking-lot" / self.category / self.item_id

    def archive_dir(self, *, ph_data_root: Path) -> Path:
        if self.item_type == "backlog":
            return ph_data_root / "backlog" / "archive" / self.category / self.item_id
        return ph_data_root / "parking-lot" / "archive" / self.category / self.item_id


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _parse_front_matter(content: str) -> tuple[dict[str, str], str, str]:
    if not content.startswith("---"):
        return {}, "", content
    end_marker = content.find("---", 3)
    if end_marker == -1:
        return {}, "", content
    raw = content[3:end_marker].strip("\n")
    body = content[end_marker + 3 :]
    fm: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        if k:
            fm[k] = v
    return fm, raw, body


def _update_readme_front_matter(readme_path: Path, updates: dict[str, str]) -> None:
    content = _read_text(readme_path)
    if not content:
        raise ValueError(f"missing README or unreadable: {readme_path}")

    if not content.startswith("---"):
        raise ValueError(f"README missing front matter: {readme_path}")

    fm, raw, body = _parse_front_matter(content)
    if not raw:
        raise ValueError(f"README front matter malformed: {readme_path}")

    order: list[str] = []
    for line in raw.splitlines():
        if ":" not in line:
            continue
        k = line.split(":", 1)[0].strip()
        if k and k not in order:
            order.append(k)

    for k, v in updates.items():
        fm[k] = v
        if k not in order:
            order.append(k)

    rebuilt = "\n".join([f"{k}: {fm[k]}" for k in order if k in fm])
    readme_path.write_text(f"---\n{rebuilt}\n---{body}", encoding="utf-8")


_PATH_PREFIX = r"(?:\.{1,2}/)*(?:project-handbook/)?"
_BACKLOG_RE = re.compile(rf"{_PATH_PREFIX}backlog/(bugs|wildcards|work-items)/([A-Z0-9][A-Z0-9-]+)/README\.md")
_PARKING_RE = re.compile(
    rf"{_PATH_PREFIX}parking-lot/(features|technical-debt|research|external-requests)/([A-Z0-9][A-Z0-9-]+)/README\.md"
)


def _scan_text_for_refs(text: str) -> set[WorkItemRef]:
    refs: set[WorkItemRef] = set()
    for category, item_id in _BACKLOG_RE.findall(text):
        refs.add(WorkItemRef(item_type="backlog", category=category, item_id=item_id))
    for category, item_id in _PARKING_RE.findall(text):
        refs.add(WorkItemRef(item_type="parking-lot", category=category, item_id=item_id))
    return refs


def _parse_task_yaml_links(task_yaml: Path) -> list[str]:
    content = _read_text(task_yaml)
    if not content:
        return []

    lines = content.splitlines()
    links: list[str] = []
    in_links = False
    for raw in lines:
        if not raw.strip():
            continue
        if raw.startswith("links:"):
            in_links = True
            continue
        if in_links:
            if raw.startswith("  - "):
                links.append(raw.split("- ", 1)[1].strip())
                continue
            if not raw.startswith(" "):
                break
    return links


def collect_work_item_refs_from_task_dir(task_dir: Path) -> list[WorkItemRef]:
    refs: set[WorkItemRef] = set()

    task_yaml = task_dir / "task.yaml"
    if task_yaml.exists():
        for link in _parse_task_yaml_links(task_yaml):
            refs |= _scan_text_for_refs(link)

    for md in task_dir.rglob("*.md"):
        refs |= _scan_text_for_refs(_read_text(md))

    return sorted(refs, key=lambda r: (r.item_type, r.category, r.item_id))


def archive_work_items_for_task(
    *,
    task_id: str,
    sprint_id: str,
    task_dir: Path,
    ph_data_root: Path,
    strict: bool,
    env: dict[str, str] | None = None,
    dry_run: bool = False,
) -> tuple[list[WorkItemRef], list[str]]:
    archived: list[WorkItemRef] = []
    errors: list[str] = []

    refs = collect_work_item_refs_from_task_dir(task_dir)
    if not refs:
        return archived, errors

    use_env = env or os.environ
    raw_fake_now = (use_env.get("PH_FAKE_NOW") or "").strip()
    if raw_fake_now:
        base = clock_now(env=use_env)
    else:
        base = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    archived_at = base.replace(microsecond=0).isoformat() + "Z"

    for ref in refs:
        source_dir = ref.source_dir(ph_data_root=ph_data_root)
        target_dir = ref.archive_dir(ph_data_root=ph_data_root)

        if target_dir.exists():
            continue
        if not source_dir.exists():
            msg = f"{task_id}: referenced {ref.item_type} item missing: {source_dir}"
            if strict:
                errors.append(msg)
            else:
                print(f"⚠️  {msg}")
            continue

        readme = source_dir / "README.md"
        if dry_run:
            archived.append(ref)
            continue

        try:
            updates = {
                "archived_at": archived_at,
                "archived_by_task": task_id,
                "archived_by_sprint": sprint_id,
            }
            updates["status"] = "closed" if ref.item_type == "backlog" else "archived"
            _update_readme_front_matter(readme, updates)
        except Exception as exc:
            msg = f"{task_id}: failed to update front matter for {source_dir}: {exc}"
            if strict:
                errors.append(msg)
            else:
                print(f"⚠️  {msg}")
            continue

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(source_dir), str(target_dir))
            archived.append(ref)
        except Exception as exc:
            msg = f"{task_id}: failed to archive {source_dir} -> {target_dir}: {exc}"
            if strict:
                errors.append(msg)
            else:
                print(f"⚠️  {msg}")

    return archived, errors


def refresh_indexes(*, ph_data_root: Path, env: dict[str, str] | None = None) -> None:
    try:
        BacklogManager(project_root=ph_data_root, env=env).update_index()
    except Exception as exc:
        print(f"⚠️  backlog index refresh failed: {exc}")

    try:
        ParkingLotManager(project_root=ph_data_root, env=env).update_index()
    except Exception as exc:
        print(f"⚠️  parking-lot index refresh failed: {exc}")


def archive_done_tasks_in_sprint(
    *,
    sprint_dir: Path,
    sprint_id: str,
    ph_data_root: Path,
    strict: bool,
    env: dict[str, str] | None = None,
) -> list[str]:
    """
    Archive work-items referenced by tasks marked `done` within a sprint directory.
    Returns a list of errors (empty if success).
    """
    errors: list[str] = []
    tasks_dir = sprint_dir / "tasks"
    if not tasks_dir.exists():
        return errors

    for task_dir in sorted(tasks_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        task_yaml = task_dir / "task.yaml"
        if not task_yaml.exists():
            continue
        meta = _read_text(task_yaml)
        task_id_match = re.search(r"^id:\\s*(TASK-[0-9]+)\\s*$", meta, flags=re.MULTILINE)
        status_match = re.search(r"^status:\\s*([a-zA-Z_]+)\\s*$", meta, flags=re.MULTILINE)
        if not task_id_match or not status_match:
            continue
        task_id = task_id_match.group(1)
        status = status_match.group(1).strip().lower()
        if status != "done":
            continue

        _, task_errors = archive_work_items_for_task(
            task_id=task_id,
            sprint_id=sprint_id,
            task_dir=task_dir,
            ph_data_root=ph_data_root,
            strict=strict,
            env=env,
            dry_run=False,
        )
        errors.extend(task_errors)

    if not errors:
        refresh_indexes(ph_data_root=ph_data_root, env=env)
    return errors
