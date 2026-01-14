from __future__ import annotations

import subprocess


def test_ph_help_exits_zero() -> None:
    result = subprocess.run(["ph", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
