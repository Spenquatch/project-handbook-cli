from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

FDR_ID_RE = re.compile(r"^FDR-(?:(?:[a-z0-9]+(?:-[a-z0-9]+)*)-)?(\d{4})$")
FDR_FILENAME_RE = re.compile(r"^(\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
DR_ID_RE = re.compile(r"^DR-(\d{4})$")

REQUIRED_H1 = ["Context", "Decision", "Consequences", "Acceptance Criteria"]
RECOMMENDED_H1 = ["Rollout"]


@dataclass(frozen=True)
class FdrAddSpec:
    feature: str
    fdr_id: str
    number: str
    title: str
    date: str
    slug: str
    dr_links: list[str]


def _slugify_title(value: str, *, max_len: int = 80) -> str:
    raw = (value or "").strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    raw = re.sub(r"-{2,}", "-", raw).strip("-")
    raw = raw[:max_len].rstrip("-")
    return raw


def _validate_feature_name(value: str) -> str:
    feature = (value or "").strip()
    if not feature:
        raise ValueError("Invalid --feature: expected a non-empty string.")
    if any(sep in feature for sep in ("/", "\\")) or feature in {".", ".."}:
        raise ValueError("Invalid --feature: expected a simple feature name, not a path.")
    if feature == "implemented":
        raise ValueError("Invalid --feature: 'implemented' is reserved (use the real feature name).")
    return feature


def _parse_fdr_id(value: str) -> tuple[str, str]:
    value = (value or "").strip()
    match = FDR_ID_RE.match(value)
    if not match:
        raise ValueError(
            f"Invalid --id: {value!r}.\n"
            "  expected: FDR-NNNN or FDR-<slug>-NNNN (must start with FDR- and end with 4 digits)\n"
        )
    number = match.group(1)
    return value, number


def _parse_dr_id(value: str) -> str:
    value = (value or "").strip()
    match = DR_ID_RE.match(value)
    if not match:
        raise ValueError(f"Invalid --dr: {value!r}. Expected DR-NNNN (4 digits).")
    return value


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


def _find_existing_fdr_by_id(*, fdr_dir: Path, fdr_id: str) -> Path | None:
    if not fdr_dir.exists():
        return None
    needle = f"id: {fdr_id}"
    for candidate in sorted(fdr_dir.glob("*.md")):
        head = _read_head(candidate, max_lines=160)
        if needle in head:
            return candidate
    return None


def _resolve_dr_markdown_match(*, feature_root: Path, ph_data_root: Path, dr_id: str) -> tuple[Path | None, list[Path]]:
    feature_dir = feature_root / "decision-register"
    if feature_dir.exists():
        matches = sorted(feature_dir.glob(f"{dr_id}-*.md"))
        if matches:
            return (matches[0] if len(matches) == 1 else None), matches

    project_dir = ph_data_root / "decision-register"
    matches = sorted(project_dir.glob(f"{dr_id}-*.md")) if project_dir.exists() else []
    if matches:
        return (matches[0] if len(matches) == 1 else None), matches

    return None, []


def _render_fdr_markdown(*, spec: FdrAddSpec) -> str:
    links = spec.dr_links
    links_yaml = "[]" if not links else "[" + ", ".join(links) + "]"
    lines = [
        "---",
        f"id: {spec.fdr_id}",
        f"title: {spec.title}",
        "type: fdr",
        f"date: {spec.date}",
        f"links: {links_yaml}",
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


def _validate_generated_fdr(*, path: Path, content: str, expected_number: str) -> None:
    match = FDR_FILENAME_RE.match(path.name)
    if not match:
        raise ValueError(
            "Generated FDR filename violates convention.\n"
            f"  path: {path}\n"
            "  expected: NNNN-<slug>.md (lowercase kebab-case)\n"
            f"  found: {path.name}\n"
        )

    prefix = match.group(1)
    if prefix != expected_number:
        raise ValueError(
            "Generated FDR filename/id mismatch.\n"
            f"  path: {path}\n"
            f"  expected prefix: {expected_number}\n"
            f"  found prefix: {prefix}\n"
        )

    h1 = [line.strip()[2:].strip() for line in content.splitlines() if line.startswith("# ")]
    missing = [heading for heading in REQUIRED_H1 if heading not in h1]
    if missing:
        raise ValueError(
            "Generated FDR is missing required H1 headings.\n"
            f"  path: {path}\n"
            f"  missing: {missing}\n"
            f"  found_h1: {h1}\n"
        )

    _ = [heading for heading in RECOMMENDED_H1 if heading not in h1]


def run_fdr_add(
    *,
    ph_root: Path,
    ph_data_root: Path,
    feature: str,
    fdr_id: str,
    title: str,
    dr: list[str],
    date: str | None,
) -> int:
    try:
        normalized_feature = _validate_feature_name(feature)
        parsed_id, number = _parse_fdr_id(fdr_id)
        normalized_title = str(title or "").strip()
        if not normalized_title:
            raise ValueError("Invalid --title: expected a non-empty string.")

        slug = _slugify_title(normalized_title)
        if not slug:
            raise ValueError(
                "Unable to derive FDR slug from --title.\n"
                f"  title: {normalized_title!r}\n"
                "  expected: title contains at least one letter/number\n"
            )

        if not dr:
            raise ValueError(
                "Missing required --dr.\n"
                "  expected: --dr DR-NNNN (4 digits)\n"
                "  remediation: Create a DR first via 'ph dr add --id DR-NNNN --title <t>', then re-run.\n"
            )

        seen_dr_ids: set[str] = set()
        normalized_dr_ids: list[str] = []
        for raw in dr:
            parsed_dr = _parse_dr_id(str(raw))
            if parsed_dr in seen_dr_ids:
                continue
            seen_dr_ids.add(parsed_dr)
            normalized_dr_ids.append(parsed_dr)

        parsed_date = _parse_date(date)
    except ValueError as exc:
        print(f"❌ {exc}\n", end="")
        return 2

    feature_root = ph_data_root / "features" / normalized_feature
    if not feature_root.is_dir():
        print("❌ Feature does not exist.\n", end="")
        print(f"  feature: {normalized_feature}")
        print(f"  expected: {feature_root.relative_to(ph_root).as_posix()}/")
        print("  remediation: Run 'ph feature create --name <feature>' first, then re-run.\n")
        return 1

    resolved_dr_links: list[str] = []
    for dr_id in normalized_dr_ids:
        resolved, matches = _resolve_dr_markdown_match(
            feature_root=feature_root,
            ph_data_root=ph_data_root,
            dr_id=dr_id,
        )
        if resolved is None and matches:
            print("❌ Referenced DR id is ambiguous (multiple matches found).\n", end="")
            print(f"  dr: {dr_id}")
            print("  found:")
            for candidate in matches:
                try:
                    rel = candidate.relative_to(ph_data_root).as_posix()
                except Exception:
                    rel = str(candidate)
                print(f"    - {rel}")
            print(
                "  expected: exactly one matching markdown file.\n"
                "  remediation: Remove/rename duplicates so the DR id maps to a single file.\n"
            )
            return 1
        if resolved is None and not matches:
            print("❌ Referenced DR does not exist (DR-first workflow gate).\n", end="")
            print(f"  dr: {dr_id}")
            print("  expected: exactly one matching markdown file in either:")
            print(f"    - features/{normalized_feature}/decision-register/{dr_id}-*.md")
            print(f"    - decision-register/{dr_id}-*.md")
            print("  remediation: Create the DR first, then re-run with the correct --dr.\n")
            return 1
        assert resolved is not None
        resolved_dr_links.append(resolved.relative_to(ph_data_root).as_posix())

    spec = FdrAddSpec(
        feature=normalized_feature,
        fdr_id=parsed_id,
        number=number,
        title=normalized_title,
        date=parsed_date,
        slug=slug,
        dr_links=resolved_dr_links,
    )

    fdr_dir = feature_root / "fdr"
    fdr_dir.mkdir(parents=True, exist_ok=True)

    existing_by_id = _find_existing_fdr_by_id(fdr_dir=fdr_dir, fdr_id=spec.fdr_id)
    target = fdr_dir / f"{spec.number}-{spec.slug}.md"

    if existing_by_id is not None and existing_by_id.resolve() != target.resolve():
        print("❌ FDR id already exists.\n", end="")
        print(f"  id: {spec.fdr_id}")
        print(f"  found: {existing_by_id.relative_to(ph_root).as_posix()}")
        print(f"  requested: {target.relative_to(ph_root).as_posix()}")
        print("  remediation: Use the existing FDR id, or pick a new --id.\n")
        return 1

    if target.exists():
        print("❌ FDR already exists (refusing to overwrite).\n", end="")
        print(f"  path: {target.relative_to(ph_root).as_posix()}")
        print("  remediation: Pick a new id/title, or edit the existing file manually.\n")
        return 1

    content = _render_fdr_markdown(spec=spec)
    try:
        _validate_generated_fdr(path=target, content=content, expected_number=spec.number)
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"❌ Failed to write FDR.\n  path: {target}\n  error: {exc}\n")
        return 1
    except ValueError as exc:
        print(f"❌ {exc}\n", end="")
        return 2

    print(target.relative_to(ph_root).as_posix())
    return 0


def add_fdr_add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--feature", required=True, help="Owning feature name (features/<feature>/)")
    parser.add_argument("--id", required=True, help="FDR id (FDR-NNNN or FDR-<slug>-NNNN)")
    parser.add_argument("--title", required=True, help="FDR title")
    parser.add_argument(
        "--dr",
        action="append",
        required=True,
        help="Upstream DR id (DR-NNNN). May be repeated (DR-first workflow gate).",
    )
    parser.add_argument("--date", help="Override date (default: today YYYY-MM-DD)")
