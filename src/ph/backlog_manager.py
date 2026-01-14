from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class BacklogManager:
    def __init__(self, *, project_root: Path) -> None:
        self.project_root = Path(project_root).absolute()
        self.backlog_dir = self.project_root / "backlog"
        self.index_file = self.backlog_dir / "index.json"

    def update_index(self) -> None:
        index_data: dict[str, Any] = {
            "last_updated": datetime.now().isoformat(),
            "total_items": 0,
            "by_severity": {"P0": [], "P1": [], "P2": [], "P3": [], "P4": []},
            "by_category": {"bugs": [], "wildcards": [], "work-items": []},
            "items": [],
        }

        for category in ["bugs", "wildcards", "work-items"]:
            category_dir = self.backlog_dir / category
            if not category_dir.exists():
                continue

            for issue_dir in category_dir.iterdir():
                if not issue_dir.is_dir():
                    continue

                readme_path = issue_dir / "README.md"
                if not readme_path.exists():
                    continue

                issue_info = self._parse_front_matter(readme_path)
                if not issue_info:
                    continue

                issue_info["id"] = issue_dir.name
                issue_info["path"] = str(issue_dir.relative_to(self.project_root))

                triage_path = issue_dir / "triage.md"
                issue_info["has_triage"] = triage_path.exists()

                index_data["items"].append(issue_info)
                index_data["by_category"][category].append(issue_info["id"])

                severity = issue_info.get("severity", "P2")
                if severity in index_data["by_severity"]:
                    index_data["by_severity"][severity].append(issue_info["id"])

                index_data["total_items"] += 1

        severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
        index_data["items"].sort(key=lambda x: (severity_order.get(x.get("severity", "P2"), 2), x.get("created", "")))

        self.backlog_dir.mkdir(parents=True, exist_ok=True)
        self.index_file.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
        print(f"📊 Updated backlog index: {index_data['total_items']} items")

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
            if key:
                result[key] = value
        return result
