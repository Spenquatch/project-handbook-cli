from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from packaging.specifiers import InvalidSpecifier, SpecifierSet

from . import __version__


@dataclass(frozen=True)
class HandbookConfig:
    handbook_schema_version: int
    requires_ph_version: str
    repo_root: str


@dataclass(frozen=True)
class ConfigCheckResult:
    config: HandbookConfig | None
    errors: list[str]


class ConfigError(RuntimeError):
    pass


def load_handbook_config(ph_root: Path) -> HandbookConfig:
    config_path = ph_root / "cli_plan" / "project_handbook.config.json"
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(_config_error_message(f"Missing config: {config_path}")) from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(_config_error_message(f"Invalid JSON in {config_path}: {exc}")) from exc

    handbook_schema_version = raw.get("handbook_schema_version")
    requires_ph_version = raw.get("requires_ph_version")
    repo_root = raw.get("repo_root")

    if not isinstance(handbook_schema_version, int):
        raise ConfigError(_config_error_message("handbook_schema_version must be an integer"))
    if not isinstance(requires_ph_version, str) or not requires_ph_version.strip():
        raise ConfigError(_config_error_message("requires_ph_version must be a non-empty string"))
    if not isinstance(repo_root, str) or not repo_root.strip():
        raise ConfigError(_config_error_message("repo_root must be a non-empty string"))

    return HandbookConfig(
        handbook_schema_version=handbook_schema_version,
        requires_ph_version=requires_ph_version,
        repo_root=repo_root,
    )


def validate_handbook_config(config: HandbookConfig) -> None:
    if config.handbook_schema_version != 1:
        raise ConfigError(
            _config_error_message(f"Unsupported handbook_schema_version: {config.handbook_schema_version} (expected 1)")
        )
    if config.repo_root != ".":
        raise ConfigError(_config_error_message(f"Invalid repo_root: {config.repo_root!r} (expected '.')"))

    try:
        spec = SpecifierSet(config.requires_ph_version)
    except InvalidSpecifier as exc:
        raise ConfigError(
            _config_error_message(f"Invalid requires_ph_version specifier: {config.requires_ph_version}")
        ) from exc

    if not spec.contains(__version__, prereleases=True):
        raise ConfigError(
            _config_error_message(
                "Installed ph version does not satisfy requires_ph_version.\n"
                f"Installed: {__version__}\n"
                f"Required: {config.requires_ph_version}"
            )
        )


def check_handbook_config(ph_root: Path) -> ConfigCheckResult:
    try:
        config = load_handbook_config(ph_root)
    except ConfigError as exc:
        return ConfigCheckResult(config=None, errors=[str(exc).rstrip("\n")])

    errors: list[str] = []
    try:
        validate_handbook_config(config)
    except ConfigError as exc:
        errors.append(str(exc).rstrip("\n"))

    return ConfigCheckResult(config=config, errors=errors)


def _config_error_message(message: str) -> str:
    return f"{message}\nRemediation: uv tool install project-handbook-cli\n"
