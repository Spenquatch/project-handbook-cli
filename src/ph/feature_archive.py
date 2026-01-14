from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path

from .context import Context

PLACEHOLDER_STRINGS = [
    "brief description",
    "key outcome",
    "_describe",
    "todo",
    "tbd",
]

REQUIRED_FILES = [
    "overview.md",
    "status.md",
    "architecture/ARCHITECTURE.md",
    "implementation/IMPLEMENTATION.md",
    "testing/TESTING.md",
    "changelog.md",
    "risks.md",
]


def detect_placeholders(feature_dir: Path) -> list[str]:
    flagged: list[str] = []
    files_to_check = [
        "overview.md",
        "status.md",
        "architecture/ARCHITECTURE.md",
        "implementation/IMPLEMENTATION.md",
        "testing/TESTING.md",
    ]
    for relative in files_to_check:
        path = feature_dir / relative
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        lowered = text.lower()
        if any(token in lowered for token in PLACEHOLDER_STRINGS):
            flagged.append(relative)
    return flagged


def list_missing_files(feature_dir: Path) -> list[str]:
    missing: list[str] = []
    for relative in REQUIRED_FILES:
        if not (feature_dir / relative).exists():
            missing.append(relative)
    return missing


def list_empty_files(feature_dir: Path) -> list[str]:
    empties: list[str] = []
    for relative in REQUIRED_FILES:
        path = feature_dir / relative
        if not path.exists():
            continue
        try:
            if not path.read_text(encoding="utf-8").strip():
                empties.append(relative)
        except Exception:
            empties.append(f"{relative} (unreadable)")
    return empties


def audit_feature_completeness(feature_dir: Path) -> dict[str, list[str]]:
    return {
        "missing_files": list_missing_files(feature_dir),
        "placeholder_files": detect_placeholders(feature_dir),
        "empty_files": list_empty_files(feature_dir),
    }


def extract_feature_owner(feature_dir: Path) -> str:
    overview = feature_dir / "overview.md"
    if overview.exists():
        try:
            for line in overview.read_text(encoding="utf-8").splitlines():
                normalized = line.strip().lower()
                if normalized.startswith("- owner"):
                    return line.split(":", 1)[1].strip()
        except Exception:
            pass
    return "@owner"


def update_feature_archive_index(*, implemented_dir: Path, entry: dict[str, object]) -> None:
    index_path = implemented_dir / "index.json"
    data: dict[str, list[dict[str, object]]] = {"features": []}
    if index_path.exists():
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except Exception:
            data = {"features": []}

    data["features"] = [f for f in data["features"] if f.get("name") != entry["name"]]
    data["features"].append(entry)
    data["features"].sort(key=lambda f: str(f.get("implemented_on", "")))
    index_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def run_feature_archive(*, ctx: Context, name: str, force: bool) -> int:
    name = (name or "").strip()
    features_dir = ctx.ph_data_root / "features"
    implemented_dir = features_dir / "implemented"
    implemented_dir.mkdir(parents=True, exist_ok=True)

    source_dir = features_dir / name
    if not source_dir.exists():
        print(f"❌ Feature '{name}' not found")
        return 1

    status_file = source_dir / "status.md"
    stage = "unknown"
    if status_file.exists():
        content = status_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("Stage:"):
                stage = line.split(":", 1)[1].strip()
                break

    allowed_stages = {"complete", "completed", "live", "deprecated"}
    if stage.lower() not in allowed_stages and not force:
        print(
            f"❌ Feature '{name}' must be in a completed stage before archiving (current: {stage}). "
            "Use --force only with approval."
        )
        return 1

    audit = audit_feature_completeness(source_dir)
    outstanding = any(audit.values())
    if outstanding and not force:
        print("⚠️  Archive blocked: completeness issues detected.")
        if audit["missing_files"]:
            print("   Missing files:")
            for item in audit["missing_files"]:
                print(f"     - {item}")
        if audit["placeholder_files"]:
            print("   Placeholder text found:")
            for item in audit["placeholder_files"]:
                print(f"     - {item}")
        if audit["empty_files"]:
            print("   Empty or unreadable files:")
            for item in audit["empty_files"]:
                print(f"     - {item}")
        print("Resolve these issues or rerun with --force after manual review.")
        return 1
    if outstanding:
        print("⚠️  Proceeding with archive despite outstanding documentation issues (--force).")
    else:
        print("✅ Completeness check passed (all critical docs present and filled).")

    target_dir = implemented_dir / name
    if target_dir.exists():
        shutil.rmtree(target_dir)

    owner = extract_feature_owner(source_dir)
    shutil.move(str(source_dir), str(target_dir))

    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry: dict[str, object] = {
        "name": name,
        "implemented_on": timestamp,
        "stage": stage,
        "path": str(target_dir.relative_to(ctx.ph_data_root)),
        "owner": owner,
        "doc_health": audit,
        "force": bool(force),
    }

    (target_dir / "metadata.json").write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    report = {**entry, "notes": "Generated by feature_manager --archive"}
    (target_dir / "archive_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    update_feature_archive_index(implemented_dir=implemented_dir, entry=entry)

    print(f"📦 Moved feature '{name}' to features/implemented/")
    return 0
