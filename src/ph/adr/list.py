from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .add import ADR_FILENAME_RE, ADR_ID_RE


@dataclass(frozen=True)
class AdrListItem:
    number: str
    adr_id: str
    title: str
    status: str
    date: str
    relpath: str


def _parse_front_matter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return {}
    fm: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def _read_head(path: Path, *, max_bytes: int = 16_384) -> str:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return handle.read(max_bytes)
    except Exception:
        return ""


def _coerce_non_empty(value: str | None) -> str:
    normalized = str(value or "").strip()
    return normalized if normalized else "?"


def list_adrs(*, ph_root: Path) -> list[AdrListItem]:
    adr_dir = ph_root / "adr"
    if not adr_dir.exists():
        return []

    items: list[AdrListItem] = []
    for md in sorted(adr_dir.glob("*.md")):
        filename_match = ADR_FILENAME_RE.match(md.name)
        if not filename_match:
            continue

        number = filename_match.group(1)
        expected_id = f"ADR-{number}"

        head = _read_head(md)
        fm = _parse_front_matter(head)

        found_id = str(fm.get("id") or "").strip()
        if ADR_ID_RE.match(found_id or ""):
            adr_id = found_id
        else:
            adr_id = expected_id

        title = _coerce_non_empty(fm.get("title"))
        status = _coerce_non_empty(fm.get("status"))
        date = _coerce_non_empty(fm.get("date"))

        try:
            relpath = str(md.relative_to(ph_root).as_posix())
        except Exception:
            relpath = str(md)

        items.append(
            AdrListItem(
                number=number,
                adr_id=adr_id,
                title=title,
                status=status,
                date=date,
                relpath=relpath,
            )
        )

    items.sort(key=lambda item: item.number)
    return items


def run_adr_list(*, ph_root: Path) -> int:
    items = list_adrs(ph_root=ph_root)
    if not items:
        print("No ADRs found.")
        return 0

    for item in items:
        print(f"{item.adr_id} | {item.status} | {item.date} | {item.title}")
    return 0

