from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

DR_ID_RE = re.compile(r"^DR-(\d{4})$")
DR_FILENAME_RE = re.compile(r"^(DR-\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")


@dataclass(frozen=True)
class DrAddSpec:
    dr_id: str
    number: str
    title: str
    date: str
    slug: str
    feature: str | None


def _slugify_title(value: str, *, max_len: int = 80) -> str:
    raw = (value or "").strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    raw = re.sub(r"-{2,}", "-", raw).strip("-")
    raw = raw[:max_len].rstrip("-")
    return raw


def _parse_dr_id(value: str) -> tuple[str, str]:
    value = (value or "").strip()
    match = DR_ID_RE.match(value)
    if not match:
        raise ValueError(f"Invalid --id: {value!r}. Expected DR-NNNN (4 digits).")
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


def _validate_feature_name(value: str) -> str:
    feature = (value or "").strip()
    if not feature:
        raise ValueError("Invalid --feature: expected a non-empty string.")
    if any(sep in feature for sep in ("/", "\\")) or feature in {".", ".."}:
        raise ValueError("Invalid --feature: expected a simple feature name, not a path.")
    if feature == "implemented":
        raise ValueError("Invalid --feature: 'implemented' is reserved (use the real feature name).")
    return feature


def _find_existing_dr_by_id(*, dr_dir: Path, dr_id: str) -> Path | None:
    if not dr_dir.exists():
        return None
    matches = sorted(dr_dir.glob(f"{dr_id}-*.md"))
    if matches:
        return matches[0]
    fallback = sorted(dr_dir.glob(f"{dr_id}*.md"))
    return fallback[0] if fallback else None


def _render_dr_markdown(*, spec: DrAddSpec) -> str:
    title = f"{spec.dr_id} — {spec.title}"
    lines = [
        "---",
        f"title: {title}",
        "type: decision-register",
        f"date: {spec.date}",
        "tags: [decision-register]",
        "links: []",
        "---",
        "",
        "# Decision Register Entry",
        "",
        f"### {title}",
        "",
        "**Decision owner(s):** <role/team>  ",
        f"**Date:** {spec.date}  ",
        "**Status:** Proposed | Accepted | Superseded  ",
        "**Related docs:** <links>",
        "",
        "**Problem / Context**",
        "- <what is being decided and why now?>",
        "",
        "**Option A — <name>**",
        "- **Pros:** …",
        "- **Cons:** …",
        "- **Cascading implications:** …",
        "- **Risks:** …",
        "- **Unlocks:** …",
        "- **Quick wins / low-hanging fruit:** …",
        "",
        "**Option B — <name>**",
        "- **Pros:** …",
        "- **Cons:** …",
        "- **Cascading implications:** …",
        "- **Risks:** …",
        "- **Unlocks:** …",
        "- **Quick wins / low-hanging fruit:** …",
        "",
        "**Recommendation**",
        "- **Recommended:** Option <A|B> — <name>",
        "- **Rationale:** <why this tradeoff wins>",
        "",
        "**Follow-up tasks (explicit)**",
        "- <concrete tasks/spec edits/tests/scripts>",
        "",
    ]
    return "\n".join(lines)


def _validate_generated_dr(*, path: Path, content: str, expected_id: str) -> None:
    match = DR_FILENAME_RE.match(path.name)
    if not match:
        raise ValueError(
            "Generated DR filename violates convention.\n"
            f"  path: {path}\n"
            "  expected: DR-NNNN-<slug>.md (lowercase kebab-case)\n"
            f"  found: {path.name}\n"
        )

    found_id = match.group(1)
    if found_id != expected_id:
        raise ValueError(
            "Generated DR filename/id mismatch.\n"
            f"  path: {path}\n"
            f"  expected id: {expected_id}\n"
            f"  found id: {found_id}\n"
        )

    if not re.search(rf"^###\s+{re.escape(expected_id)}\b", content, flags=re.MULTILINE):
        raise ValueError(
            "Generated DR is missing required heading id.\n"
            f"  path: {path}\n"
            f"  expected: a heading like '### {expected_id} — ...'\n"
        )


def run_dr_add(
    *,
    ph_root: Path,
    ph_data_root: Path,
    dr_id: str,
    title: str,
    feature: str | None,
    date: str | None,
    force: bool,
) -> int:
    try:
        parsed_id, number = _parse_dr_id(dr_id)
        normalized_title = str(title or "").strip()
        if not normalized_title:
            raise ValueError("Invalid --title: expected a non-empty string.")

        slug = _slugify_title(normalized_title)
        if not slug:
            raise ValueError(
                "Unable to derive DR slug from --title.\n"
                f"  title: {normalized_title!r}\n"
                "  expected: title contains at least one letter/number\n"
            )

        normalized_feature = _validate_feature_name(feature) if feature is not None else None
        parsed_date = _parse_date(date)
        spec = DrAddSpec(
            dr_id=parsed_id,
            number=number,
            title=normalized_title,
            date=parsed_date,
            slug=slug,
            feature=normalized_feature,
        )
    except ValueError as exc:
        print(f"❌ {exc}\n", end="")
        return 2

    if spec.feature is None:
        dr_dir = ph_data_root / "decision-register"
    else:
        feature_root = ph_data_root / "features" / spec.feature
        if not feature_root.exists():
            print("❌ Feature does not exist (refusing to create new feature directory implicitly).\n", end="")
            print(f"  feature: {spec.feature}")
            print(f"  expected: {feature_root.relative_to(ph_root).as_posix()}/")
            print("  remediation: Run 'ph feature create --name <feature>' first, or omit --feature.\n")
            return 1
        dr_dir = feature_root / "decision-register"

    dr_dir.mkdir(parents=True, exist_ok=True)

    existing_by_id = _find_existing_dr_by_id(dr_dir=dr_dir, dr_id=spec.dr_id)
    target = dr_dir / f"{spec.dr_id}-{spec.slug}.md"

    if existing_by_id is not None and existing_by_id.resolve() != target.resolve():
        print("❌ DR id already exists.\n", end="")
        print(f"  id: {spec.dr_id}")
        print(f"  found: {existing_by_id.relative_to(ph_root).as_posix()}")
        print(f"  requested: {target.relative_to(ph_root).as_posix()}")
        print("  remediation: Use the existing DR file, or pick a new --id.\n")
        return 1

    if target.exists():
        if force:
            print(target.relative_to(ph_root).as_posix())
            return 0
        print("❌ DR already exists (refusing to overwrite).\n", end="")
        print(f"  path: {target.relative_to(ph_root).as_posix()}")
        print("  remediation: Re-run with --force for a non-destructive success.\n")
        return 1

    content = _render_dr_markdown(spec=spec)
    try:
        _validate_generated_dr(path=target, content=content, expected_id=spec.dr_id)
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"❌ Failed to write DR.\n  path: {target}\n  error: {exc}\n")
        return 1
    except ValueError as exc:
        print(f"❌ {exc}\n", end="")
        return 2

    print(target.relative_to(ph_root).as_posix())
    return 0


def add_dr_add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--id", required=True, help="DR id (DR-NNNN)")
    parser.add_argument("--title", required=True, help="DR title")
    parser.add_argument("--feature", help="Create as a feature-scoped DR under features/<feature>/decision-register/")
    parser.add_argument("--date", help="Override date (default: today YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)
