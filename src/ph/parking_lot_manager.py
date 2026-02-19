from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from . import clock


class ParkingLotManager:
    def __init__(self, *, project_root: Path, env: dict[str, str]) -> None:
        self.project_root = Path(project_root).absolute()
        self.env = env
        self.parking_lot_dir = self.project_root / "parking-lot"
        self.index_file = self.parking_lot_dir / "index.json"
        self.roadmap_dir = self.project_root / "roadmap"

    def add_item(
        self,
        item_type: str,
        title: str,
        desc: str = "",
        owner: str = "",
        tags: list[str] | None = None,
    ) -> str | None:
        """Add a new item to the parking lot."""
        if item_type not in ["features", "technical-debt", "research", "external-requests"]:
            print(f"Error: Invalid type '{item_type}'")
            print("Valid types: features, technical-debt, research, external-requests")
            return None

        type_dir = self.parking_lot_dir / item_type
        type_dir.mkdir(parents=True, exist_ok=True)

        item_id = self._generate_item_id(item_type, title)
        item_dir = type_dir / item_id

        if item_dir.exists():
            print(f"Error: Item '{item_id}' already exists")
            return None

        item_dir.mkdir(parents=True)

        readme_path = item_dir / "README.md"
        front_matter = {
            "title": title,
            "type": item_type,
            "status": "parking-lot",
            "created": clock.now(env=self.env).strftime("%Y-%m-%d"),
            "owner": owner or "unassigned",
            "tags": tags or [],
            "description": desc,
        }

        content = f"""---
title: {front_matter["title"]}
type: {front_matter["type"]}
status: {front_matter["status"]}
created: {front_matter["created"]}
owner: {front_matter["owner"]}
tags: {json.dumps(front_matter["tags"])}
---

# {title}

{desc}

## Context

_Add context and background information here_

## Potential Value

_Describe the potential value this could bring_

## Considerations

_Note any technical, resource, or timing considerations_
"""

        readme_path.write_text(content, encoding="utf-8")
        print(f"✅ Created parking lot item: {item_id}")
        print(f"   Location: {item_dir.relative_to(self.project_root)}")

        self.update_index()
        return item_id

    def promote_to_roadmap(self, item_id: str, target: str = "later") -> bool:
        """Promote a specific item to the roadmap."""
        if target not in ["now", "next", "later"]:
            print(f"Error: Invalid target '{target}'. Must be: now, next, or later")
            return False

        if not self.index_file.exists():
            self.update_index()

        index_data = json.loads(self.index_file.read_text(encoding="utf-8"))
        item: dict[str, Any] | None = None

        for candidate in index_data["items"]:
            if candidate["id"] == item_id:
                item = candidate
                break

        if not item:
            print(f"Error: Item '{item_id}' not found")
            return False

        roadmap_target_dir = self.roadmap_dir / target
        roadmap_target_dir.mkdir(parents=True, exist_ok=True)

        source_path = self.project_root / item["path"]
        dest_path = roadmap_target_dir / item["id"]

        if not source_path.exists():
            print(f"Error: Source path not found: {source_path}")
            return False

        shutil.copytree(source_path, dest_path)

        readme_path = dest_path / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            content = content.replace("status: parking-lot", f"status: roadmap-{target}")
            content = content.replace(
                "status: parking-lot", f"promoted: {clock.now(env=self.env).strftime('%Y-%m-%d')}"
            )
            readme_path.write_text(content, encoding="utf-8")

        shutil.rmtree(source_path)
        print(f"✅ Promoted {item_id} to roadmap/{target}/")

        self.update_index()
        return True

    def update_index(self, *, print_summary: bool = True) -> None:
        """Update the index.json file by scanning all directories."""
        index_data: dict[str, Any] = {
            "last_updated": clock.now(env=self.env).isoformat(),
            "total_items": 0,
            "by_category": {
                "features": [],
                "technical-debt": [],
                "research": [],
                "external-requests": [],
            },
            "items": [],
        }

        for category in index_data["by_category"].keys():
            category_dir = self.parking_lot_dir / category
            if not category_dir.exists():
                continue

            for item_dir in category_dir.iterdir():
                if not item_dir.is_dir():
                    continue

                readme_path = item_dir / "README.md"
                if not readme_path.exists():
                    continue

                item_info = self._parse_front_matter(readme_path)
                if item_info:
                    item_info["id"] = item_dir.name
                    item_info["path"] = str(item_dir.relative_to(self.project_root))

                    index_data["items"].append(item_info)
                    index_data["by_category"][category].append(item_info["id"])
                    index_data["total_items"] += 1

        index_data["items"].sort(key=lambda x: x.get("created", ""), reverse=True)

        self.parking_lot_dir.mkdir(parents=True, exist_ok=True)
        self.index_file.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
        if print_summary:
            print(f"📊 Updated parking lot index: {index_data['total_items']} items")

    def list_items(self, category: str | None = None, format: str = "table") -> None:
        """List all parking lot items."""
        if not self.index_file.exists():
            self.update_index(print_summary=format != "json")

        index_data = json.loads(self.index_file.read_text(encoding="utf-8"))

        if format == "json":
            print(json.dumps(index_data, indent=2))
            return

        print("\n📦 PARKING LOT ITEMS")
        print("=" * 80)

        if index_data["total_items"] == 0:
            print("No items in parking lot")
            return

        for cat in ["features", "technical-debt", "research", "external-requests"]:
            if category and category != cat:
                continue

            items = [item for item in index_data["items"] if item.get("type") == cat]
            if not items:
                continue

            print(f"\n📁 {cat.upper().replace('-', ' ')} ({len(items)} items)")
            print("-" * 40)

            for item in items:
                created = item.get("created", "unknown")
                owner = item.get("owner", "unassigned")
                title = item.get("title", item["id"])
                tags = item.get("tags", [])

                print(f"  • {item['id']}")
                print(f"    {title}")
                print(f"    Created: {created} | Owner: {owner}")
                if tags:
                    print(f"    Tags: {', '.join(tags)}")
                print()

        print(f"\nTotal items: {index_data['total_items']}")
        print(f"Last updated: {index_data.get('last_updated', 'never')}")

    def review_items(self, *, format: str = "text") -> int:
        """Non-interactive review report (no prompts; safe for CI/non-tty contexts)."""
        if not self.index_file.exists():
            self.update_index()

        try:
            index_data = json.loads(self.index_file.read_text(encoding="utf-8"))
        except Exception:
            print("Error: parking-lot/index.json is missing or invalid JSON")
            return 1

        items = index_data.get("items", [])
        total_items = int(index_data.get("total_items", len(items)) or 0)
        last_updated = index_data.get("last_updated")

        by_category = index_data.get("by_category") or {}
        counts_by_category: dict[str, int] = {}
        for cat in ["features", "technical-debt", "research", "external-requests"]:
            value = by_category.get(cat, [])
            counts_by_category[cat] = int(len(value)) if isinstance(value, list) else 0

        norm_items: list[dict[str, Any]] = [i for i in items if isinstance(i, dict)]
        norm_items.sort(key=lambda i: (str(i.get("created", "")), str(i.get("id", ""))))

        if str(format).strip().lower() == "json":
            payload = {
                "type": "parking-review",
                "schema_version": 1,
                "last_updated": last_updated,
                "total_items": total_items,
                "by_category": counts_by_category,
                "items": [
                    {
                        "id": str(i.get("id", "")),
                        "type": str(i.get("type", "")),
                        "title": str(i.get("title", "")),
                        "created": str(i.get("created", "")),
                        "owner": str(i.get("owner", "")),
                        "tags": i.get("tags", []) if isinstance(i.get("tags"), list) else [],
                        "path": str(i.get("path", "")),
                    }
                    for i in norm_items
                ],
            }
            print(json.dumps(payload, indent=2))
            return 0

        print("\n📦 PARKING LOT REVIEW (NON-INTERACTIVE)")
        print("=" * 80)
        print(f"Total items: {total_items}")
        if last_updated:
            print(f"Last updated: {last_updated}")
        print("By category:")
        for cat in ["features", "technical-debt", "research", "external-requests"]:
            print(f"  - {cat}: {counts_by_category.get(cat, 0)}")

        if total_items == 0:
            print("\n(no items)")
            return 0

        print("\nQueue:")
        for cat in ["features", "technical-debt", "research", "external-requests"]:
            group = [i for i in norm_items if str(i.get("type", "")).strip() == cat]
            if not group:
                continue
            print(f"\n📁 {cat.upper().replace('-', ' ')} ({len(group)} items)")
            print("-" * 40)
            for item in group:
                item_id = str(item.get("id", ""))
                title = str(item.get("title", item_id))
                created = str(item.get("created", "unknown"))
                owner = str(item.get("owner", "unassigned"))
                tags = item.get("tags", [])
                path = str(item.get("path", ""))

                print(f"ID: {item_id}")
                print(f"Title: {title}")
                print(f"Created: {created} | Owner: {owner}")
                if tags:
                    printable_tags = [str(t) for t in tags] if isinstance(tags, list) else []
                    if printable_tags:
                        print(f"Tags: {', '.join(printable_tags)}")
                print(f"Path: {path}")
                print()

        print("Suggested actions (explicit; no prompting):")
        print("- Promote an item:")
        print("  ph parking promote --item <ID> --target later")
        print("- List items (table/json):")
        print("  ph parking list --format table")
        print("  ph parking list --format json")
        return 0

    def _generate_item_id(self, item_type: str, title: str) -> str:
        """Generate a clean ID from type and title."""
        prefix_map = {
            "features": "FEAT",
            "technical-debt": "DEBT",
            "research": "RES",
            "external-requests": "EXT",
        }
        prefix = prefix_map[item_type]

        clean_title = re.sub(r"[^a-zA-Z0-9-]", "-", title.lower())
        clean_title = re.sub(r"-+", "-", clean_title).strip("-")[:30]

        timestamp = clock.now(env=self.env).strftime("%Y%m%d")
        return f"{prefix}-{timestamp}-{clean_title}"

    def _parse_front_matter(self, file_path: Path) -> dict[str, Any] | None:
        """Parse YAML front matter from a markdown file."""
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if not content.startswith("---"):
            return None

        try:
            end_marker = content.find("---", 3)
            if end_marker == -1:
                return None

            front_matter = content[3:end_marker].strip()

            result: dict[str, Any] = {}
            for line in front_matter.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    if value.startswith("["):
                        try:
                            value = json.loads(value)
                        except Exception:
                            pass

                    result[key] = value

            content_start = content.find("\n", end_marker + 3)
            if content_start != -1:
                lines = content[content_start:].strip().split("\n")
                for line in lines:
                    if line and not line.startswith("#"):
                        result["description"] = line.strip()
                        break

            return result
        except Exception as exc:
            print(f"Warning: Could not parse front matter from {file_path}: {exc}")
            return None
