from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )

    (ph_root / "package.json").write_text(
        json.dumps({"name": "project-handbook", "version": "0.0.0"}, indent=2) + "\n",
        encoding="utf-8",
    )

    (ph_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def test_check_all_parity_v1p0068(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)

    env = dict(os.environ)
    env["PH_FAKE_NOW"] = "2099-01-01T09:00:00Z"
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "--no-post-hook", "check-all"],
        capture_output=True,
        text=True,
        env=env,
        stdin=subprocess.DEVNULL,
    )
    assert result.returncode == 0

    resolved = tmp_path.resolve()
    validation_json = (tmp_path / "status" / "validation.json").resolve()
    current_json = (tmp_path / "status" / "current.json").resolve()
    summary_md = (tmp_path / "status" / "current_summary.md").resolve()

    expected = (
        f"\n> project-handbook@0.0.0 make {resolved}\n"
        "> make -- check-all\n\n"
        f"validation: 0 error(s), 0 warning(s), report: {validation_json}\n"
        f"Generated: {current_json}\n"
        f"Updated: {summary_md}\n"
        "\n===== status/current_summary.md =====\n\n"
        "# Current Sprint\n\n_No active sprint_\n"
        "\n====================================\n\n"
        "Updated feature status files\n"
        "✅ All checks complete\n"
    )
    assert result.stdout == expected

    data = json.loads((tmp_path / "status" / "current.json").read_text(encoding="utf-8"))
    assert data["generated_at"] == "2099-01-01T09:00:00Z"
