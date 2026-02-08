from __future__ import annotations

import re
import subprocess
from pathlib import Path


def _write_minimal_ph_root(ph_root: Path, *, schema: int = 1) -> None:
    ph_project_root = ph_root / ".project-handbook"
    config = ph_project_root / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "{\n"
        f'  "handbook_schema_version": {schema},\n'
        '  "requires_ph_version": ">=0.0.1,<0.1.0",\n'
        '  "repo_root": "."\n'
        "}\n",
        encoding="utf-8",
    )

    (ph_project_root / "process" / "checks").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "automation").mkdir(parents=True, exist_ok=True)
    (ph_project_root / "process" / "sessions" / "templates").mkdir(parents=True, exist_ok=True)

    (ph_project_root / "process" / "checks" / "validation_rules.json").write_text("{}", encoding="utf-8")
    (ph_project_root / "process" / "automation" / "system_scope_config.json").write_text(
        '{"routing_rules": {}}', encoding="utf-8"
    )
    (ph_project_root / "process" / "automation" / "reset_spec.json").write_text("{}", encoding="utf-8")


def _history_path(ph_root: Path) -> Path:
    return ph_root / ".project-handbook" / "history.log"


def _validation_path(ph_root: Path) -> Path:
    return ph_root / ".project-handbook" / "status" / "validation.json"


def test_history_appends_default_entry(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0

    history_path = _history_path(tmp_path)
    assert history_path.exists()
    last_line = history_path.read_text(encoding="utf-8").strip().splitlines()[-1]
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| \(default\)$", last_line)


def test_no_history_flag_skips_logging(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph", "--root", str(tmp_path), "--no-history"], capture_output=True, text=True)
    assert result.returncode == 0
    assert not _history_path(tmp_path).exists()
    assert _validation_path(tmp_path).exists()


def test_no_post_hook_flag_skips_history_logging(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph", "--root", str(tmp_path), "--no-post-hook"], capture_output=True, text=True)
    assert result.returncode == 0
    assert not _history_path(tmp_path).exists()
    assert not _validation_path(tmp_path).exists()


def test_history_logs_on_failure(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path, schema=999)
    result = subprocess.run(["ph", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode != 0
    assert _history_path(tmp_path).exists()
    assert not _validation_path(tmp_path).exists()


def test_history_logs_doctor_failure(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    # remove a required asset so doctor fails
    (tmp_path / ".project-handbook" / "process" / "checks" / "validation_rules.json").unlink()
    result = subprocess.run(
        ["ph", "--root", str(tmp_path), "doctor"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    history_text = _history_path(tmp_path).read_text(encoding="utf-8")
    assert "ph --root" in history_text and " doctor" in history_text
    assert not _validation_path(tmp_path).exists()
