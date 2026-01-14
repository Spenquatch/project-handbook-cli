from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FENCE_RE = re.compile(r"^\\s*```")


@dataclass
class Summary:
    moved: list[dict[str, str]]
    skipped: list[dict[str, str]]
    errors: list[dict[str, str]]


def _to_rel_posix(ph_root: Path, path: Path) -> str:
    try:
        rel = path.relative_to(ph_root)
    except Exception:
        rel = path
    return rel.as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_routing_config(ph_root: Path) -> tuple[list[str], list[str], set[str]]:
    config_path = ph_root / "process" / "automation" / "system_scope_config.json"
    config = _read_json(config_path)
    routing = config.get("routing_rules") or {}
    feature_prefixes = routing.get("feature_name_prefixes_for_system_scope") or []
    lane_prefixes = routing.get("task_lane_prefixes_for_system_scope") or []
    adr_tags = set(routing.get("adr_tags_triggering_system_scope") or [])

    if not isinstance(feature_prefixes, list):
        feature_prefixes = []
    if not isinstance(lane_prefixes, list):
        lane_prefixes = []

    return [str(p) for p in feature_prefixes], [str(p) for p in lane_prefixes], {str(t) for t in adr_tags}


def _is_external_link(target: str) -> bool:
    t = target.strip().lower()
    return t.startswith(("http://", "https://", "mailto:", "tel:"))


def _split_target(target: str) -> tuple[str, str]:
    t = target.strip()
    if t.startswith("<") and t.endswith(">"):
        t = t[1:-1].strip()
    fragment = ""
    if "#" in t:
        t, frag = t.split("#", 1)
        fragment = "#" + frag
    return t, fragment


def _parse_front_matter_tags(text: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return []

    tags: list[str] = []
    collecting = False
    for line in lines[1:end]:
        raw = line.strip()
        if collecting:
            if raw.startswith("- "):
                value = raw[2:].strip().strip('"').strip("'")
                if value:
                    tags.append(value)
                continue
            collecting = False

        if not raw.startswith("tags:"):
            continue
        value = raw.split(":", 1)[1].strip()
        if not value:
            collecting = True
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


def _atomic_move(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)


def _iter_feature_dirs(features_dir: Path) -> Iterable[Path]:
    if not features_dir.exists():
        return []
    for entry in sorted(features_dir.iterdir()):
        if entry.is_dir() and entry.name != "implemented":
            yield entry


def _iter_adr_files(adr_dir: Path) -> Iterable[Path]:
    if not adr_dir.exists():
        return []
    yield from sorted(adr_dir.glob("*.md"))


def _read_lane_from_task_yaml(task_yaml: Path) -> str | None:
    try:
        for line in task_yaml.read_text(encoding="utf-8").splitlines():
            if line.startswith("lane:"):
                value = line.split(":", 1)[1].strip().strip('"').strip("'")
                return value or None
    except Exception:
        return None
    return None


def _is_system_lane(lane: str, lane_prefixes: list[str]) -> bool:
    return any(lane.startswith(prefix) for prefix in lane_prefixes)


def _project_task_dest(ph_root: Path, system_root: Path, task_dir: Path) -> Path | None:
    rel = task_dir.relative_to(ph_root)
    parts = list(rel.parts)
    if len(parts) < 5:
        return None
    if parts[0] != "sprints":
        return None

    if parts[1] == "archive":
        if len(parts) < 6:
            return None
        year = parts[2]
        sprint_id = parts[3]
        if parts[4] != "tasks":
            return None
        task_name = parts[5]
        return system_root / "sprints" / "archive" / year / sprint_id / "tasks" / task_name

    year = parts[1]
    sprint_id = parts[2]
    if parts[3] != "tasks":
        return None
    task_name = parts[4]
    return system_root / "sprints" / year / sprint_id / "tasks" / task_name


def _parse_front_matter_block(lines: list[str]) -> tuple[list[str], int]:
    if not lines:
        return [], -1
    if lines[0].strip() != "---":
        return [], -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[: i + 1], i
    return [], -1


def _iter_front_matter_links(lines: list[str], end_idx: int) -> Iterable[tuple[int, str]]:
    in_links = False
    links_indent: int | None = None
    for i in range(1, end_idx):
        line = lines[i]
        stripped = line.strip()
        if not in_links:
            if stripped == "links:":
                in_links = True
                links_indent = len(line) - len(line.lstrip(" "))
            continue

        indent = len(line) - len(line.lstrip(" "))
        if (
            stripped
            and ":" in stripped
            and not stripped.startswith("-")
            and links_indent is not None
            and indent <= links_indent
        ):
            break

        m = re.match(r"^\\s*-\\s+(.*)\\s*$", line)
        if m:
            yield i, m.group(1).strip().strip('"').strip("'")


def _rewrite_inline_links_in_line(
    *,
    md_path: Path,
    line: str,
    moved_features: dict[str, Path],
    moved_adrs: dict[str, Path],
    summary: Summary,
    ph_root: Path,
) -> str:
    out = []
    i = 0
    while True:
        j = line.find("](", i)
        if j == -1:
            out.append(line[i:])
            break
        k = j + 2
        out.append(line[i:k])
        if k >= len(line):
            break

        depth = 1
        pos = k
        while pos < len(line):
            c = line[pos]
            if c == "\\":
                pos += 2
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    raw_target = line[k:pos].strip()
                    new_target = _rewrite_target(
                        ph_root=ph_root,
                        md_path=md_path,
                        target=raw_target,
                        moved_features=moved_features,
                        moved_adrs=moved_adrs,
                        summary=summary,
                    )
                    out.append(new_target)
                    out.append(")")
                    i = pos + 1
                    break
            pos += 1
        else:
            out.append(line[k:])
            break
    return "".join(out)


def _try_resolve(*, ph_root: Path, md_path: Path, target: str) -> bool:
    t, _ = _split_target(target)
    if not t or _is_external_link(t) or t == "#":
        return True
    if t.startswith("/"):
        return Path(t).exists()

    if (md_path.parent / t).exists():
        return True

    if not t.startswith((".", "..")) and (ph_root / t).exists():
        return True

    return False


def _rewrite_target(
    *,
    ph_root: Path,
    md_path: Path,
    target: str,
    moved_features: dict[str, Path],
    moved_adrs: dict[str, Path],
    summary: Summary,
) -> str:
    raw, fragment = _split_target(target)
    if not raw or _is_external_link(raw) or raw == "#":
        return target

    if _try_resolve(ph_root=ph_root, md_path=md_path, target=target):
        return target

    for feature_name, feature_dst in moved_features.items():
        marker = f"features/{feature_name}"
        idx = raw.find(marker)
        if idx != -1:
            suffix = raw[idx + len(marker) :].lstrip("/")
            dest = feature_dst / suffix if suffix else feature_dst
            rel = os.path.relpath(str(dest), start=str(md_path.parent))
            return f"{Path(rel).as_posix()}{fragment}"

    for adr_filename, adr_dst in moved_adrs.items():
        marker = f"adr/{adr_filename}"
        idx = raw.find(marker)
        if idx != -1:
            rel = os.path.relpath(str(adr_dst), start=str(md_path.parent))
            return f"{Path(rel).as_posix()}{fragment}"

    repo_roots = [
        "backlog",
        "parking-lot",
        "releases",
        "roadmap",
        "status",
        "process",
        "docs",
        "decision-register",
    ]

    if raw.endswith("Makefile"):
        makefile = ph_root / "Makefile"
        if makefile.exists():
            rel = os.path.relpath(str(makefile), start=str(md_path.parent))
            return f"{Path(rel).as_posix()}{fragment}"

    for root_name in repo_roots:
        if raw.startswith(f"../{root_name}/"):
            repo_path = ph_root / raw[len("../") :]
            if repo_path.exists():
                rel = os.path.relpath(str(repo_path), start=str(md_path.parent))
                return f"{Path(rel).as_posix()}{fragment}"

        marker = f"{root_name}/"
        idx = raw.find(marker)
        if idx != -1 and (idx == 0 or raw[idx - 1] == "/"):
            repo_path = ph_root / raw[idx:]
            if repo_path.exists():
                rel = os.path.relpath(str(repo_path), start=str(md_path.parent))
                return f"{Path(rel).as_posix()}{fragment}"

    summary.errors.append(
        {
            "path": _to_rel_posix(ph_root, md_path),
            "message": f"unresolved_link:{target}",
        }
    )
    return target


def _rewrite_markdown_links_in_place(
    *,
    ph_root: Path,
    md_path: Path,
    moved_features: dict[str, Path],
    moved_adrs: dict[str, Path],
    summary: Summary,
) -> None:
    original = md_path.read_text(encoding="utf-8")
    lines = original.splitlines(True)

    fm_lines, fm_end = _parse_front_matter_block(lines)
    if fm_end != -1:
        for idx, raw_target in _iter_front_matter_links(fm_lines, fm_end):
            new_target = _rewrite_target(
                ph_root=ph_root,
                md_path=md_path,
                target=raw_target,
                moved_features=moved_features,
                moved_adrs=moved_adrs,
                summary=summary,
            )
            if new_target != raw_target:
                m = re.match(r"^(\\s*-\\s+)(.*?)(\\s*)$", fm_lines[idx])
                if m:
                    fm_lines[idx] = f"{m.group(1)}{new_target}{m.group(3)}"
        lines[: len(fm_lines)] = fm_lines

    out: list[str] = []
    in_fence = False
    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        out.append(
            _rewrite_inline_links_in_line(
                ph_root=ph_root,
                md_path=md_path,
                line=line,
                moved_features=moved_features,
                moved_adrs=moved_adrs,
                summary=summary,
            )
        )

    new_text = "".join(out)
    if new_text != original:
        md_path.write_text(new_text, encoding="utf-8")


def _rewrite_links_under_system_root(
    *,
    ph_root: Path,
    system_root: Path,
    moved_features: dict[str, Path],
    moved_adrs: dict[str, Path],
    summary: Summary,
) -> None:
    if not system_root.exists():
        return
    for md in sorted(system_root.rglob("*.md")):
        if "node_modules" in md.parts:
            continue
        try:
            _rewrite_markdown_links_in_place(
                ph_root=ph_root,
                md_path=md,
                moved_features=moved_features,
                moved_adrs=moved_adrs,
                summary=summary,
            )
        except Exception as exc:
            summary.errors.append({"path": _to_rel_posix(ph_root, md), "message": str(exc)})


def run_migrate_system_scope(*, ph_root: Path, confirm: str, force: str) -> int:
    if confirm != "RESET" or force != "true":
        return 2

    summary = Summary(moved=[], skipped=[], errors=[])

    feature_prefixes, lane_prefixes, system_adr_tags = _load_routing_config(ph_root)
    system_root = ph_root / ".project-handbook" / "system"

    features_dir = ph_root / "features"
    for feature_dir in _iter_feature_dirs(features_dir):
        name = feature_dir.name
        if not any(name.startswith(prefix) for prefix in feature_prefixes):
            continue
        dest = system_root / "features" / name
        if dest.exists():
            summary.skipped.append(
                {"path": _to_rel_posix(ph_root, feature_dir), "reason": f"dest_exists:{_to_rel_posix(ph_root, dest)}"}
            )
            continue
        try:
            _atomic_move(feature_dir, dest)
            summary.moved.append({"from": _to_rel_posix(ph_root, feature_dir), "to": _to_rel_posix(ph_root, dest)})
        except Exception as exc:
            summary.errors.append({"path": _to_rel_posix(ph_root, feature_dir), "message": str(exc)})

    adr_dir = ph_root / "adr"
    for adr_file in _iter_adr_files(adr_dir):
        try:
            text = adr_file.read_text(encoding="utf-8")
        except Exception as exc:
            summary.errors.append({"path": _to_rel_posix(ph_root, adr_file), "message": str(exc)})
            continue
        tags = set(_parse_front_matter_tags(text))
        if not tags.intersection(system_adr_tags):
            continue
        dest = system_root / "adr" / adr_file.name
        if dest.exists():
            summary.skipped.append(
                {"path": _to_rel_posix(ph_root, adr_file), "reason": f"dest_exists:{_to_rel_posix(ph_root, dest)}"}
            )
            continue
        try:
            _atomic_move(adr_file, dest)
            summary.moved.append({"from": _to_rel_posix(ph_root, adr_file), "to": _to_rel_posix(ph_root, dest)})
        except Exception as exc:
            summary.errors.append({"path": _to_rel_posix(ph_root, adr_file), "message": str(exc)})

    sprints_dir = ph_root / "sprints"
    if sprints_dir.exists():
        for task_yaml in sorted(sprints_dir.rglob("task.yaml")):
            if ".project-handbook" in task_yaml.parts:
                continue
            try:
                task_dir = task_yaml.parent
                task_dir.relative_to(ph_root)
            except Exception:
                continue

            lane = _read_lane_from_task_yaml(task_yaml)
            if not lane or not _is_system_lane(lane, lane_prefixes):
                continue

            dest = _project_task_dest(ph_root, system_root, task_dir)
            if not dest:
                summary.skipped.append({"path": _to_rel_posix(ph_root, task_dir), "reason": "unrecognized_task_layout"})
                continue
            if dest.exists():
                summary.skipped.append(
                    {"path": _to_rel_posix(ph_root, task_dir), "reason": f"dest_exists:{_to_rel_posix(ph_root, dest)}"}
                )
                continue
            try:
                _atomic_move(task_dir, dest)
                summary.moved.append({"from": _to_rel_posix(ph_root, task_dir), "to": _to_rel_posix(ph_root, dest)})
            except Exception as exc:
                summary.errors.append({"path": _to_rel_posix(ph_root, task_dir), "message": str(exc)})

    link_features: dict[str, Path] = {}
    link_adrs: dict[str, Path] = {}

    sys_features_dir = system_root / "features"
    if sys_features_dir.exists():
        for d in sorted(sys_features_dir.iterdir()):
            if d.is_dir() and any(d.name.startswith(prefix) for prefix in feature_prefixes):
                link_features[d.name] = d

    sys_adr_dir = system_root / "adr"
    if sys_adr_dir.exists():
        for f in sorted(sys_adr_dir.glob("*.md")):
            link_adrs[f.name] = f

    _rewrite_links_under_system_root(
        ph_root=ph_root,
        system_root=system_root,
        moved_features=link_features,
        moved_adrs=link_adrs,
        summary=summary,
    )

    print(json.dumps({"moved": summary.moved, "skipped": summary.skipped, "errors": summary.errors}, indent=2))
    return 0
