from __future__ import annotations

import shlex
from pathlib import Path


def shell_quote(path: Path) -> str:
    return shlex.quote(str(path))

