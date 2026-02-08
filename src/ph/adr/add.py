from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

ADR_ID_RE = re.compile(r"^ADR-(\d{4})$")
ADR_FILENAME_RE = re.compile(r"^(\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")

REQUIRED_H1 = ["Context", "Decision", "Consequences", "Acceptance Criteria"]
RECOMMENDED_H1 = ["Rollout"]


@dataclass(frozen=True)
class AdrAddSpec:
    adr_id: str
    number: str
    title: str
    status: str
    date: str
    slug: str
    superseded_by: str | None


def _slugify_title(value: str, *, max_len: int = 80) -> str:
    raw = (value or "").strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    raw = re.sub(r"-{2,}", "-", raw).strip("-")
    raw = raw[:max_len].rstrip("-")
    return raw


def _parse_adr_id(value: str) -> tuple[str, str]:
    value = (value or "").strip()
    match = ADR_ID_RE.match(value)
    if not match:
        raise ValueError(f"Invalid --id: {value!r}. Expected ADR-NNNN (4 digits).")
    number = match.group(1)
    return value, number


def _parse_date(value: str | None) -> str:
    if value is None:
        return dt.date.today().isoformat()
    candidate = str(value).strip()
    try:
        parsed = dt.date.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"Invalid --date: {candidate!r}. Expected YYYY-MM-DD.") from exc
    return parsed.isoformat()


def _read_head(path: Path, *, max_lines: int = 120) -> str:
    try:
        with path.open("r", encoding="utf-8") as handle:
            lines: list[str] = []
            for _ in range(max_lines):
                line = handle.readline()
                if not line:
                    break
                lines.append(line)
            return "".join(lines)
    except Exception:
        return ""


def _find_existing_adr_by_id(*, adr_dir: Path, adr_id: str) -> Path | None:
    if not adr_dir.exists():
        return None
    needle = f"id: {adr_id}"
    for candidate in sorted(adr_dir.glob("*.md")):
        head = _read_head(candidate, max_lines=160)
        if needle in head:
            return candidate
    return None


def _render_adr_markdown(*, spec: AdrAddSpec) -> str:
    superseded_by = spec.superseded_by if spec.superseded_by is not None else "null"
    lines = [
        "---",
        f"id: {spec.adr_id}",
        f"title: {spec.title}",
        "type: adr",
        f"status: {spec.status}",
        f"date: {spec.date}",
        "supersedes: null",
        f"superseded_by: {superseded_by}",
        "tags: []",
        "links: []",
        "---",
        "",
        "# Context",
        "",
        "TODO",
        "",
        "# Decision",
        "",
        "TODO",
        "",
        "# Consequences",
        "",
        "TODO",
        "",
        "# Rollout",
        "",
        "TODO",
        "",
        "# Acceptance Criteria",
        "",
        "TODO",
        "",
    ]
    return "\n".join(lines)


def _validate_generated_adr(*, path: Path, content: str, expected_number: str) -> None:
    match = ADR_FILENAME_RE.match(path.name)
    if not match:
        raise ValueError(
            "Generated ADR filename violates convention.\n"
            f"  path: {path}\n"
            "  expected: NNNN-<slug>.md (lowercase kebab-case)\n"
            f"  found: {path.name}\n"
        )

    prefix = match.group(1)
    if prefix != expected_number:
        raise ValueError(
            "Generated ADR filename/id mismatch.\n"
            f"  path: {path}\n"
            f"  expected prefix: {expected_number}\n"
            f"  found prefix: {prefix}\n"
        )

    h1 = [line.strip()[2:].strip() for line in content.splitlines() if line.startswith("# ")]
    missing = [heading for heading in REQUIRED_H1 if heading not in h1]
    if missing:
        raise ValueError(
            "Generated ADR is missing required H1 headings.\n"
            f"  path: {path}\n"
            f"  missing: {missing}\n"
            f"  found_h1: {h1}\n"
        )

    # Recommended H1 headings are not fatal, but we keep this for future strict validation parity.
    _ = [heading for heading in RECOMMENDED_H1 if heading not in h1]


def run_adr_add(
    *,
    ph_root: Path,
    ph_data_root: Path,
    adr_id: str,
    title: str,
    status: str,
    date: str | None,
    superseded_by: str | None,
    force: bool,
) -> int:
    try:
        parsed_id, number = _parse_adr_id(adr_id)
        normalized_title = str(title or "").strip()
        if not normalized_title:
            raise ValueError("Invalid --title: expected a non-empty string.")

        slug = _slugify_title(normalized_title)
        if not slug:
            raise ValueError(
                "Unable to derive ADR slug from --title.\n"
                f"  title: {normalized_title!r}\n"
                "  expected: title contains at least one letter/number\n"
            )

        normalized_status = str(status or "").strip().lower()
        if normalized_status not in {"draft", "accepted", "rejected", "superseded"}:
            raise ValueError(
                "Invalid --status.\n"
                "  expected: draft|accepted|rejected|superseded\n"
                f"  found: {status!r}\n"
            )

        normalized_superseded_by = (str(superseded_by or "").strip() or None) if superseded_by is not None else None
        if normalized_status == "superseded":
            if normalized_superseded_by is None:
                raise ValueError(
                    "Missing required --superseded-by when --status is superseded.\n"
                    "  expected: --superseded-by ADR-NNNN (4 digits)\n"
                )
            normalized_superseded_by, _ = _parse_adr_id(normalized_superseded_by)
        elif normalized_superseded_by is not None:
            raise ValueError("--superseded-by is only valid when --status is superseded.")

        parsed_date = _parse_date(date)
        spec = AdrAddSpec(
            adr_id=parsed_id,
            number=number,
            title=normalized_title,
            status=normalized_status,
            date=parsed_date,
            slug=slug,
            superseded_by=normalized_superseded_by,
        )
    except ValueError as exc:
        print(f"❌ {exc}\n", end="")
        return 2

    adr_dir = ph_data_root / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)

    existing_by_id = _find_existing_adr_by_id(adr_dir=adr_dir, adr_id=spec.adr_id)
    target = adr_dir / f"{spec.number}-{spec.slug}.md"

    if spec.status == "superseded" and spec.superseded_by is not None:
        existing_superseded_by = _find_existing_adr_by_id(adr_dir=adr_dir, adr_id=spec.superseded_by)
        if existing_superseded_by is None:
            print("❌ superseded_by target ADR does not exist.\n", end="")
            print(f"  superseded_by: {spec.superseded_by}")
            print("  expected: an existing ADR markdown file under `adr/` with matching front matter id")
            print("  remediation: Create the referenced ADR first, or correct --superseded-by.\n")
            return 1

    if existing_by_id is not None and existing_by_id.resolve() != target.resolve():
        print("❌ ADR id already exists.\n", end="")
        print(f"  id: {spec.adr_id}")
        print(f"  found: {existing_by_id.relative_to(ph_root).as_posix()}")
        print(f"  requested: {target.relative_to(ph_root).as_posix()}")
        print("  remediation: Use the existing ADR id, or pick a new --id.\n")
        return 1

    if target.exists():
        if force:
            print(target.relative_to(ph_root).as_posix())
            return 0
        print("❌ ADR already exists (refusing to overwrite).\n", end="")
        print(f"  path: {target.relative_to(ph_root).as_posix()}")
        print("  remediation: Re-run with --force for a non-destructive success.\n")
        return 1

    content = _render_adr_markdown(spec=spec)
    try:
        _validate_generated_adr(path=target, content=content, expected_number=spec.number)
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"❌ Failed to write ADR.\n  path: {target}\n  error: {exc}\n")
        return 1
    except ValueError as exc:
        print(f"❌ {exc}\n", end="")
        return 2

    print(target.relative_to(ph_root).as_posix())
    return 0


def add_adr_add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--id", required=True, help="ADR id (ADR-NNNN)")
    parser.add_argument("--title", required=True, help="ADR title")
    parser.add_argument(
        "--status",
        default="draft",
        choices=["draft", "accepted", "rejected", "superseded"],
        help="Status (default: draft)",
    )
    parser.add_argument(
        "--superseded-by",
        dest="superseded_by",
        help="When --status is superseded, the ADR id that supersedes this ADR (ADR-NNNN)",
    )
    parser.add_argument("--date", help="Override date (default: today YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)
