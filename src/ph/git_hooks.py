from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

POST_COMMIT_HOOK = """#!/bin/bash
python3 process/automation/daily_status_check.py --check-only
"""

PRE_PUSH_HOOK = """#!/bin/bash
python3 process/checks/validate_docs.py
"""


@dataclass(frozen=True)
class HooksInstallResult:
    post_commit_path: Path
    pre_push_path: Path


def install_git_hooks(*, ph_root: Path) -> HooksInstallResult:
    hooks_dir = ph_root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    post_commit_path = hooks_dir / "post-commit"
    post_commit_path.write_text(POST_COMMIT_HOOK, encoding="utf-8")
    post_commit_path.chmod(0o755)

    pre_push_path = hooks_dir / "pre-push"
    pre_push_path.write_text(PRE_PUSH_HOOK, encoding="utf-8")
    pre_push_path.chmod(0o755)

    return HooksInstallResult(post_commit_path=post_commit_path, pre_push_path=pre_push_path)
