from __future__ import annotations

import re
import subprocess
from pathlib import Path


def _write_config(ph_root: Path, *, schema: int = 1) -> None:
    config = ph_root / "cli_plan" / "project_handbook.config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "{\n"
        f'  "handbook_schema_version": {schema},\n'
        '  "requires_ph_version": ">=0.1.0,<0.2.0",\n'
        '  "repo_root": "."\n'
        "}\n",
        encoding="utf-8",
    )


def _history_path(ph_root: Path) -> Path:
    return ph_root / ".project-handbook" / "history.log"


def test_history_appends_default_entry(tmp_path: Path) -> None:
    _write_config(tmp_path)
    result = subprocess.run(["ph", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0

    history_path = _history_path(tmp_path)
    assert history_path.exists()
    last_line = history_path.read_text(encoding="utf-8").strip().splitlines()[-1]
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| \(default\)$", last_line)


def test_no_history_flag_skips_logging(tmp_path: Path) -> None:
    _write_config(tmp_path)
    result = subprocess.run(["ph", "--root", str(tmp_path), "--no-history"], capture_output=True, text=True)
    assert result.returncode == 0
    assert not _history_path(tmp_path).exists()


def test_no_post_hook_flag_skips_history_logging(tmp_path: Path) -> None:
    _write_config(tmp_path)
    result = subprocess.run(["ph", "--root", str(tmp_path), "--no-post-hook"], capture_output=True, text=True)
    assert result.returncode == 0
    assert not _history_path(tmp_path).exists()


def test_history_logs_on_failure(tmp_path: Path) -> None:
    _write_config(tmp_path, schema=999)
    result = subprocess.run(["ph", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode != 0
    assert _history_path(tmp_path).exists()


def test_history_logs_doctor_failure(tmp_path: Path) -> None:
    _write_config(tmp_path)
    result = subprocess.run(["ph", "doctor", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 3
    history_text = _history_path(tmp_path).read_text(encoding="utf-8")
    assert "ph doctor --root" in history_text
