from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ParkingLotManager:
    def __init__(self, *, project_root: Path) -> None:
        self.project_root = Path(project_root).absolute()
        self.parking_lot_dir = self.project_root / "parking-lot"
        self.index_file = self.parking_lot_dir / "index.json"

    def update_index(self) -> None:
        index_data: dict[str, Any] = {
            "last_updated": datetime.now().isoformat(),
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
                if not item_info:
                    continue

                item_info["id"] = item_dir.name
                item_info["path"] = str(item_dir.relative_to(self.project_root))

                index_data["items"].append(item_info)
                index_data["by_category"][category].append(item_info["id"])
                index_data["total_items"] += 1

        index_data["items"].sort(key=lambda x: x.get("created", ""), reverse=True)

        self.parking_lot_dir.mkdir(parents=True, exist_ok=True)
        self.index_file.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
        print(f"📊 Updated parking lot index: {index_data['total_items']} items")

    def _parse_front_matter(self, file_path: Path) -> dict[str, Any] | None:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if not content.startswith("---"):
            return None

        end_marker = content.find("---", 3)
        if end_marker == -1:
            return None

        front_matter = content[3:end_marker].strip()

        result: dict[str, Any] = {}
        for line in front_matter.split("\n"):
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if value.startswith("["):
                try:
                    value = json.loads(value)
                except Exception:
                    pass

            if key:
                result[key] = value

        content_start = content.find("\n", end_marker + 3)
        if content_start != -1:
            lines = content[content_start:].strip().split("\n")
            for line in lines:
                if line and not line.startswith("#"):
                    result["description"] = line.strip()
                    break

        return result
