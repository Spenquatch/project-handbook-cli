from __future__ import annotations

from pathlib import Path

from .add import ADR_FILENAME_RE, ADR_ID_RE, RECOMMENDED_H1, REQUIRED_H1


def _parse_front_matter(text: str) -> tuple[dict, int, int]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, -1, -1
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return {}, -1, -1
    fm: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm, 0, end


def _extract_h1(text: str) -> list[str]:
    h1: list[str] = []
    in_fence = False
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.startswith("# "):
            continue
        heading = line[2:].strip()
        if heading:
            h1.append(heading)
    return h1


def _normalize_optional_yaml_scalar(value: str | None) -> str | None:
    if value is None:
        return None
    candidate = value.strip().strip('"').strip("'").strip()
    if not candidate:
        return None
    lowered = candidate.lower()
    if lowered in {"null", "~", "none"}:
        return None
    return candidate


def validate_adrs(*, issues: list[dict], root: Path) -> None:
    adr_dir = root / "adr"
    if not adr_dir.exists():
        return

    id_to_paths: dict[str, list[str]] = {}
    superseded_refs: list[tuple[str, str]] = []

    for md in sorted(adr_dir.rglob("*.md")):
        rel_path = md.relative_to(root).as_posix()
        text = ""
        try:
            text = md.read_text(encoding="utf-8")
        except Exception as exc:
            issues.append(
                {
                    "path": rel_path,
                    "code": "adr_read_error",
                    "severity": "error",
                    "message": f"Failed to read ADR markdown.\n  error: {exc}",
                }
            )
            continue

        filename_match = ADR_FILENAME_RE.match(md.name)
        filename_prefix = filename_match.group(1) if filename_match else None

        if not filename_match:
            issues.append(
                {
                    "path": rel_path,
                    "code": "adr_filename_invalid",
                    "severity": "error",
                    "message": (
                        "ADR filename violates convention.\n"
                        "  expected: NNNN-<slug>.md (4 digits + lowercase kebab-case slug)\n"
                        f"  found: {md.name}\n"
                    ),
                    "expected": "NNNN-<slug>.md",
                    "found": md.name,
                }
            )

        fm, start, end = _parse_front_matter(text)
        if start == -1 or end == -1:
            issues.append(
                {
                    "path": rel_path,
                    "code": "adr_front_matter_missing",
                    "severity": "error",
                    "message": (
                        "ADR front matter is missing or malformed.\n"
                        "  expected: YAML front matter delimited by --- on first/last line\n"
                    ),
                    "expected": "---\\n...\\n---",
                    "found": None,
                }
            )
            adr_id = None
            id_number = None
            status = None
            superseded_by = None
        else:
            adr_id = fm.get("id")
            status = _normalize_optional_yaml_scalar(fm.get("status"))
            superseded_by = _normalize_optional_yaml_scalar(fm.get("superseded_by"))
            if not adr_id:
                issues.append(
                    {
                        "path": rel_path,
                        "code": "adr_front_matter_id_missing",
                        "severity": "error",
                        "message": "ADR front matter missing required field.\n  missing: ['id']\n",
                        "missing": ["id"],
                    }
                )
                id_number = None
            else:
                id_match = ADR_ID_RE.match(adr_id.strip())
                if not id_match:
                    issues.append(
                        {
                            "path": rel_path,
                            "code": "adr_front_matter_id_invalid",
                            "severity": "error",
                            "message": (
                                "ADR front matter id violates convention.\n"
                                "  expected: ADR-NNNN (4 digits)\n"
                                f"  found: {adr_id!r}\n"
                            ),
                            "expected": "ADR-NNNN",
                            "found": adr_id,
                        }
                    )
                    id_number = None
                else:
                    id_number = id_match.group(1)
                    id_to_paths.setdefault(adr_id.strip(), []).append(rel_path)

        if filename_prefix and id_number and filename_prefix != id_number:
            expected_id = f"ADR-{filename_prefix}"
            issues.append(
                {
                    "path": rel_path,
                    "code": "adr_filename_id_mismatch",
                    "severity": "error",
                    "message": (
                        "ADR filename prefix and front matter id do not match.\n"
                        f"  expected (from filename) id: {expected_id}\n"
                        f"  found id: {adr_id}\n"
                        f"  expected (from id) filename prefix: {id_number}\n"
                        f"  found filename prefix: {filename_prefix}\n"
                    ),
                    "expected_id": expected_id,
                    "found_id": adr_id,
                    "expected_filename_prefix": id_number,
                    "found_filename_prefix": filename_prefix,
                }
            )

        if id_number and not filename_prefix:
            issues.append(
                {
                    "path": rel_path,
                    "code": "adr_id_filename_prefix_missing",
                    "severity": "error",
                    "message": (
                        "ADR front matter id implies a filename prefix, but filename is not compliant.\n"
                        f"  expected filename prefix: {id_number}\n"
                        f"  found: {md.name}\n"
                    ),
                    "expected": {"filename_prefix": id_number},
                    "found": {"filename": md.name},
                }
            )

        if status and status.strip().lower() == "superseded":
            if superseded_by is None:
                issues.append(
                    {
                        "path": rel_path,
                        "code": "adr_superseded_missing_superseded_by",
                        "severity": "error",
                        "message": (
                            "ADR marked superseded is missing required front matter field.\n"
                            "  status: superseded\n"
                            "  missing: ['superseded_by']\n"
                        ),
                        "status": "superseded",
                        "missing": ["superseded_by"],
                    }
                )
            else:
                superseded_by_id = superseded_by.strip()
                if not ADR_ID_RE.match(superseded_by_id):
                    issues.append(
                        {
                            "path": rel_path,
                            "code": "adr_superseded_by_invalid",
                            "severity": "error",
                            "message": (
                                "ADR marked superseded has invalid superseded_by.\n"
                                "  expected: ADR-NNNN (4 digits)\n"
                                f"  found: {superseded_by_id!r}\n"
                            ),
                            "status": "superseded",
                            "expected": "ADR-NNNN",
                            "found": superseded_by_id,
                        }
                    )
                else:
                    superseded_refs.append((rel_path, superseded_by_id))

        h1 = _extract_h1(text)
        missing_required = [heading for heading in REQUIRED_H1 if heading not in h1]
        if missing_required:
            issues.append(
                {
                    "path": rel_path,
                    "code": "adr_missing_required_h1",
                    "severity": "error",
                    "message": (
                        "ADR is missing required H1 headings.\n"
                        f"  missing: {missing_required}\n"
                        f"  found_h1: {h1}\n"
                    ),
                    "missing": missing_required,
                    "found_h1": h1,
                }
            )

        missing_recommended = [heading for heading in RECOMMENDED_H1 if heading not in h1]
        if missing_recommended:
            issues.append(
                {
                    "path": rel_path,
                    "code": "adr_missing_recommended_h1",
                    "severity": "warning",
                    "message": (
                        "ADR is missing recommended H1 headings.\n"
                        f"  missing: {missing_recommended}\n"
                        f"  found_h1: {h1}\n"
                    ),
                    "missing": missing_recommended,
                    "found_h1": h1,
                }
            )

    for adr_id, paths in sorted(id_to_paths.items()):
        if len(paths) < 2:
            continue
        issues.append(
            {
                "path": paths[0],
                "code": "adr_duplicate_id",
                "severity": "error",
                "message": (
                    "ADR id is duplicated across multiple files.\n"
                    f"  id: {adr_id}\n"
                    f"  paths: {sorted(paths)}\n"
                ),
                "id": adr_id,
                "paths": sorted(paths),
            }
        )

    known_ids = set(id_to_paths.keys())
    for source_path, target_id in superseded_refs:
        if target_id in known_ids:
            continue
        issues.append(
            {
                "path": source_path,
                "code": "adr_superseded_by_target_missing",
                "severity": "error",
                "message": (
                    "ADR marked superseded references a missing target ADR.\n"
                    f"  superseded_by: {target_id}\n"
                    "  expected: target ADR exists\n"
                    "  found: target ADR missing\n"
                ),
                "superseded_by": target_id,
                "expected": {"id": target_id, "exists": True},
                "found": {"id": target_id, "exists": False},
            }
        )
