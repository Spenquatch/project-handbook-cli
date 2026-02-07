from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from ph.help_text import get_help_text


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": "1",\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
        encoding="utf-8",
    )


def _write_legacy_like_package_json(ph_root: Path) -> None:
    (ph_root / "package.json").write_text(
        '{\n  "name": "project-handbook",\n  "version": "0.0.0"\n}\n',
        encoding="utf-8",
    )


def _expected_help_topic_stdout(*, resolved: Path, topic: str | None) -> bytes:
    text = get_help_text(topic)
    assert text is not None
    cmd_args = ["help"] + ([topic] if topic else [])
    preamble = "\n" f"> project-handbook@0.0.0 ph {resolved}\n" f"> ph {shlex.join(cmd_args)}\n\n"
    return (preamble + text).encode()


def test_help_stdout_matches_expected_help(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph", "help", "--root", str(tmp_path)], capture_output=True)
    assert result.returncode == 0
    expected = get_help_text(None)
    assert expected is not None
    assert result.stdout == expected.encode()


def test_help_sprint_stdout_prints_preamble_when_package_json_present(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    resolved = tmp_path.resolve()
    result = subprocess.run(["ph", "help", "sprint", "--root", str(tmp_path)], capture_output=True)
    assert result.returncode == 0
    assert result.stdout == _expected_help_topic_stdout(resolved=resolved, topic="sprint")
    history_log = tmp_path / ".project-handbook" / "history.log"
    assert history_log.exists()
    assert history_log.stat().st_size > 0
    assert not (tmp_path / ".project-handbook" / "status" / "validation.json").exists()


def test_help_sprint_accepts_root_before_command(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    resolved = tmp_path.resolve()
    result = subprocess.run(["ph", "--root", str(tmp_path), "help", "sprint"], capture_output=True)
    assert result.returncode == 0
    assert result.stdout == _expected_help_topic_stdout(resolved=resolved, topic="sprint")
    history_log = tmp_path / ".project-handbook" / "history.log"
    assert history_log.exists()
    assert history_log.stat().st_size > 0
    assert not (tmp_path / ".project-handbook" / "status" / "validation.json").exists()


def test_help_topics_print_preamble_when_package_json_present(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    _write_legacy_like_package_json(tmp_path)
    resolved = tmp_path.resolve()

    for topic in ("sprint", "task", "feature", "release", "backlog", "parking", "validation", "utilities", "roadmap"):
        result = subprocess.run(["ph", "--root", str(tmp_path), "help", topic], capture_output=True)
        assert result.returncode == 0
        assert result.stdout == _expected_help_topic_stdout(resolved=resolved, topic=topic)


def test_help_unknown_topic_exits_non_zero(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    result = subprocess.run(["ph", "help", "nope", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode != 0

