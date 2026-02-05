from __future__ import annotations

from .context import Context
from .parking_lot_manager import ParkingLotManager


def _parse_tags(tags_csv: str | None) -> list[str]:
    raw = (tags_csv or "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def run_parking_add(
    *,
    ctx: Context,
    item_type: str,
    title: str,
    desc: str,
    owner: str,
    tags: str | None,
    env: dict[str, str],
) -> int:
    manager = ParkingLotManager(project_root=ctx.ph_data_root, env=env)
    item_id = manager.add_item(item_type=item_type, title=title, desc=desc, owner=owner, tags=_parse_tags(tags))
    if item_id is None:
        return 1

    if ctx.scope == "project":
        print("Parking lot updated → review via 'make parking-list' or 'make parking-review'")
        print(f"  - Capture owner/priority inside parking-lot/{item_type}/ entries if missing")
        print("  - Promote items with 'make parking-promote' once they graduate to roadmap")

    return 0


def run_parking_list(
    *,
    ctx: Context,
    category: str | None,
    format: str,
    env: dict[str, str],
) -> int:
    manager = ParkingLotManager(project_root=ctx.ph_data_root, env=env)
    manager.list_items(category=category, format=format)
    return 0


def run_parking_review(*, ctx: Context, env: dict[str, str]) -> int:
    manager = ParkingLotManager(project_root=ctx.ph_data_root, env=env)
    return int(manager.review_items())


def run_parking_promote(*, ctx: Context, item_id: str, target: str, env: dict[str, str]) -> int:
    if ctx.scope == "system":
        print("Error: Roadmap is project-scope-only and MUST NOT be created or written in system scope")
        return 1

    manager = ParkingLotManager(project_root=ctx.ph_data_root, env=env)
    ok = manager.promote_to_roadmap(item_id=item_id, target=target)
    return 0 if ok else 1
