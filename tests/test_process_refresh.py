from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ph", "--root", str(cwd), "--no-post-hook", *cmd],
        capture_output=True,
        text=True,
        env=env,
    )


def test_process_refresh_respects_seed_ownership_and_force(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PH_FAKE_TODAY"] = "2099-01-01"

    assert _run(["init"], cwd=tmp_path, env=env).returncode == 0

    template_path = tmp_path / ".project-handbook" / "process" / "sessions" / "templates" / "release-planning.md"
    original = template_path.read_text(encoding="utf-8")
    assert "seed_id:" in original
    assert "seed_hash:" in original

    marker = "\n\n<!-- local-modification -->\n"
    template_path.write_text(original + marker, encoding="utf-8")

    # Default refresh must NOT overwrite modified seed-owned files.
    refreshed = _run(["process", "refresh", "--templates"], cwd=tmp_path, env=env)
    assert refreshed.returncode == 0
    assert template_path.read_text(encoding="utf-8").endswith(marker)

    # Force refresh must overwrite.
    forced = _run(["process", "refresh", "--templates", "--force"], cwd=tmp_path, env=env)
    assert forced.returncode == 0
    assert "<!-- local-modification -->" not in template_path.read_text(encoding="utf-8")
