from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class RolloutParserError(Exception):
    """Raised when a rollout file cannot be parsed."""


def iter_json_objects(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    """
    Stream JSON objects from a Codex rollout file.

    Rollouts are formatted as pretty-printed JSON objects concatenated together
    (not strict JSONL). This reader incrementally feeds chunks into a JSON decoder
    and yields each object as soon as it can be decoded.
    """
    decoder = json.JSONDecoder()
    buffer = ""
    items: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            buffer += chunk
            buffer = buffer.lstrip()
            while buffer:
                try:
                    obj, index = decoder.raw_decode(buffer)
                except json.JSONDecodeError:
                    break
                if isinstance(obj, dict):
                    items.append(obj)
                if limit is not None:
                    limit -= 1
                    if limit == 0:
                        return items
                buffer = buffer[index:].lstrip()

        buffer = buffer.lstrip()
        if buffer:
            obj, _ = decoder.raw_decode(buffer)
            if isinstance(obj, dict):
                items.append(obj)

    return items


@dataclass(frozen=True)
class SessionMetadata:
    provider: str
    session_id: str
    timestamp: str
    cli_version: str
    cwd: str
    originator: str | None
    source: str | None
    model_provider: str | None
    instructions: str | None
    git: dict[str, Any]

    def to_manifest_entry(
        self,
        repo_root: Path,
        summary_path: Path,
        log_path: Path,
        generated_at: str,
    ) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "session_id": self.session_id,
            "provider": self.provider,
            "cli_version": self.cli_version,
            "cwd": self.cwd,
            "repo_root": str(repo_root),
            "summary_path": str(summary_path),
            "log_path": str(log_path),
            "generated_at": generated_at,
            "originator": self.originator,
            "source": self.source,
            "model_provider": self.model_provider,
            "instructions": self.instructions,
            "git": self.git,
        }
        return {k: v for k, v in entry.items() if v is not None}


class CodexRolloutParser:
    """Parser for Codex CLI rollout files."""

    provider = "codex"

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def read_session_meta(self, path: Path) -> SessionMetadata | None:
        entries = iter_json_objects(path, limit=1)
        for obj in entries:
            if obj.get("type") == "session_meta":
                return self._session_meta_from_obj(obj)
        return None

    def parse(self, path: Path) -> tuple[SessionMetadata, list[dict[str, Any]]]:
        entries = iter_json_objects(path)
        session_meta_obj = next((e for e in entries if e.get("type") == "session_meta"), None)
        if session_meta_obj is None:
            raise RolloutParserError(f"No session_meta found in {path}")
        metadata = self._session_meta_from_obj(session_meta_obj)
        return metadata, entries

    def _session_meta_from_obj(self, obj: dict[str, Any]) -> SessionMetadata:
        payload = obj.get("payload") or {}
        git_info = payload.get("git") or {}
        return SessionMetadata(
            provider=self.provider,
            session_id=str(payload.get("id", "")),
            timestamp=str(payload.get("timestamp", "")),
            cli_version=str(payload.get("cli_version", "")),
            cwd=str(payload.get("cwd", "")),
            originator=payload.get("originator"),
            source=payload.get("source"),
            model_provider=payload.get("model_provider"),
            instructions=payload.get("instructions"),
            git=git_info,
        )
