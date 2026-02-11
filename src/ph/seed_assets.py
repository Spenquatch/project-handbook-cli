from __future__ import annotations

from importlib import resources


def load_seed_markdown_dir(*, rel_dir: str) -> dict[str, str]:
    """
    Load packaged seed markdown files under ph/seed/<rel_dir> as a mapping:
      filename-stem -> file contents
    """
    root = resources.files("ph.seed").joinpath(rel_dir)
    if not root.exists():
        return {}

    out: dict[str, str] = {}
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if not entry.is_file() or entry.suffix.lower() != ".md":
            continue
        out[entry.stem] = entry.read_text(encoding="utf-8")
    return out


def render_date_placeholder(text: str, *, date: str) -> str:
    """
    Replace `{date}` in seed playbooks with an ISO date. Avoid str.format so
    brace-heavy markdown doesn't explode.
    """

    return text.replace("{date}", date)
