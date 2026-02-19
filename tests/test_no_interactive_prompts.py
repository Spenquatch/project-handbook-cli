from __future__ import annotations

import ast
from pathlib import Path


def test_no_python_input_calls_in_ph_cli() -> None:
    ph_src = Path(__file__).resolve().parents[1] / "src" / "ph"
    offenders: list[str] = []

    for path in sorted(ph_src.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name) and func.id == "input":
                offenders.append(f"{path}:{getattr(node, 'lineno', '?')}")

    assert offenders == [], "Found input() calls:\n" + "\n".join(offenders)

