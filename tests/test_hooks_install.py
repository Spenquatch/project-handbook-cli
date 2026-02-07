from __future__ import annotations

import stat
import subprocess
from pathlib import Path

from ph.git_hooks import POST_COMMIT_HOOK, PRE_PUSH_HOOK


def _write_minimal_ph_root(ph_root: Path) -> None:
    config = ph_root / ".project-handbook" / "config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{\n  "handbook_schema_version": 1,\n  "requires_ph_version": ">=0.0.1,<0.1.0",\n  "repo_root": "."\n}\n',
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


def _is_executable(path: Path) -> bool:
    return bool(path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


def test_hooks_install_writes_executable_hook_files(tmp_path: Path) -> None:
    _write_minimal_ph_root(tmp_path)
    (tmp_path / ".git" / "hooks").mkdir(parents=True, exist_ok=True)

    result = subprocess.run(["ph", "hooks", "install", "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0

    post_commit = tmp_path / ".git" / "hooks" / "post-commit"
    pre_push = tmp_path / ".git" / "hooks" / "pre-push"

    assert post_commit.read_text(encoding="utf-8") == POST_COMMIT_HOOK
    assert pre_push.read_text(encoding="utf-8") == PRE_PUSH_HOOK
    assert _is_executable(post_commit)
    assert _is_executable(pre_push)
