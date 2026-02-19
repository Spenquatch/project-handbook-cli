from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Ensure in-process imports of `ph.*` use the in-repo sources.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = str((_REPO_ROOT / "src").resolve())
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
os.environ["PYTHONPATH"] = f"{_SRC_DIR}{os.pathsep}{os.environ.get('PYTHONPATH', '')}".rstrip(os.pathsep)

# Ensure subprocess calls to `ph` execute the in-repo CLI (not a globally installed shim).
_BIN_DIR = Path(tempfile.mkdtemp(prefix="project-handbook-cli-pytest-bin-"))

_PH_SCRIPT = _BIN_DIR / "ph"
_PYTHON = sys.executable.replace('"', '\\"')
_PH_SCRIPT.write_text(
    "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            f'export PYTHONPATH="{_SRC_DIR}${{PYTHONPATH:+:$PYTHONPATH}}"',
            f'exec "{_PYTHON}" -m ph "$@"',
            "",
        ]
    ),
    encoding="utf-8",
)
_PH_SCRIPT.chmod(0o755)
os.environ["PATH"] = f"{_BIN_DIR}{os.pathsep}{os.environ.get('PATH', '')}"
