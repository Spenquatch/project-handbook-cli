from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .config import ConfigCheckResult, check_handbook_config
from .root import find_root_marker

REQUIRED_ASSET_PATHS: tuple[str, ...] = (
    "process/checks/validation_rules.json",
    "process/automation/system_scope_config.json",
    "process/automation/reset_spec.json",
    "process/sessions/templates",
)


@dataclass(frozen=True)
class DoctorResult:
    exit_code: int
    output: str


def run_doctor(ph_root: Path) -> DoctorResult:
    lines: list[str] = []
    lines.append(f"PH_ROOT: {ph_root}")
    marker = find_root_marker(ph_root=ph_root)
    lines.append(f"Marker: {marker.as_posix() if marker is not None else '(missing)'}")
    lines.append(f"ph version: {__version__}")

    config_check: ConfigCheckResult = check_handbook_config(ph_root)
    if config_check.config is not None:
        lines.append(f"handbook_schema_version: {config_check.config.handbook_schema_version}")
        lines.append(f"requires_ph_version: {config_check.config.requires_ph_version}")
    else:
        lines.append("handbook_schema_version: (unavailable)")
        lines.append("requires_ph_version: (unavailable)")

    if config_check.errors:
        lines.append("config: FAIL")
        for err in config_check.errors:
            lines.append(err)
        return DoctorResult(exit_code=2, output="\n".join(lines) + "\n")

    missing: list[str] = []
    lines.append("required_assets:")
    if marker is None:
        lines.append("- MISSING project_handbook.config.json")
        missing.append(str((ph_root / "project_handbook.config.json").resolve()))
    else:
        lines.append(f"- OK {marker.as_posix()}")

    for rel in REQUIRED_ASSET_PATHS:
        p = ph_root / rel
        ok = p.exists()
        status = "OK" if ok else "MISSING"
        lines.append(f"- {status} {rel}")
        if not ok:
            missing.append(str(p))

    if missing:
        lines.append("missing_paths:")
        for p in missing:
            lines.append(f"- {p}")
        return DoctorResult(exit_code=3, output="\n".join(lines) + "\n")

    return DoctorResult(exit_code=0, output="\n".join(lines) + "\n")
