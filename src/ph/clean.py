from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CleanResult:
    removed_pyc_files: int
    removed_pycache_dirs: int


def clean_python_caches(*, ph_root: Path) -> CleanResult:
    removed_pyc = 0
    for pyc in ph_root.rglob("*.pyc"):
        try:
            pyc.unlink()
            removed_pyc += 1
        except FileNotFoundError:
            continue
        except IsADirectoryError:
            continue
        except PermissionError:
            continue

    removed_dirs = 0
    pycache_dirs = [p for p in ph_root.rglob("__pycache__") if p.is_dir()]
    pycache_dirs.sort(key=lambda p: len(p.parts), reverse=True)
    for d in pycache_dirs:
        if not d.exists():
            continue
        shutil.rmtree(d, ignore_errors=True)
        removed_dirs += 1

    return CleanResult(removed_pyc_files=removed_pyc, removed_pycache_dirs=removed_dirs)
