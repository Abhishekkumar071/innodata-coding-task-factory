"""Central configuration (docs/IMPLEMENTATION.md §4.2).

This is the ONLY module that reads ``os.environ``. Every other module calls
``get_settings()``.

Resolution order (highest wins): process environment > ``.env`` file in the working
directory > defaults below. Env var names are the upper-case field names
(``click_base_commit`` <- ``CLICK_BASE_COMMIT``). Empty values count as unset. Relative paths
resolve against the working directory (run commands from the repo root).
"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

from task_factory.errors import ConfigError
from task_factory.schemas import SHA_PATTERN, LLMMode

logger = logging.getLogger("task_factory.config")

PINNED_RELEASE_TAG = "8.5.1"
PINNED_BASE_COMMIT = "cf19179e8e2fd54c601378cec9e0d21bb12b6fb1"
PINNED_PYTEST_VERSION = "9.0.2"
DEFAULT_ENV_FILE = Path(".env")

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseModel):
    """Immutable runtime settings. ``llm_api_key`` is a ``SecretStr`` and never printed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Target repository (pinned)
    click_repo_url: str = "https://github.com/pallets/click.git"
    click_base_commit: str = Field(PINNED_BASE_COMMIT, pattern=SHA_PATTERN)
    click_release_tag: str = PINNED_RELEASE_TAG
    pytest_pin: str = Field(PINNED_PYTEST_VERSION, pattern=r"^\d+(\.\d+){1,2}$")
    upstream_changes_path: Path = Path("artifacts/upstream/CHANGES.md")

    # LLM (Decision D1, provisional)
    llm_provider: str = "google-genai"
    llm_model: str = "gemini-2.5-flash"
    llm_api_key: SecretStr | None = None
    llm_mode: LLMMode = "live"
    llm_temperature: float = Field(0.0, ge=0.0, le=2.0)
    llm_timeout_sec: float = Field(120.0, gt=0)
    llm_max_retries: int = Field(3, ge=0, le=10)
    llm_max_parallel: int = Field(3, ge=1, le=16)
    llm_cache_dir: Path = Path("artifacts/llm_cache")

    # Paths
    artifacts_dir: Path = Path("artifacts")
    cache_dir: Path = Path(".cache")
    db_path: Path = Path("artifacts/factory.db")

    # Stage 1 sandbox
    sandbox_image_prefix: str = Field("click-sandbox", pattern=r"^[a-z0-9][a-z0-9._/-]*$")
    sandbox_max_parallel: int = Field(3, ge=1, le=16)
    sandbox_timeout_sec: float = Field(300.0, gt=0)
    max_repair_attempts: int = Field(3, ge=0, le=10)

    # Stage 2 Harbor
    harbor_bin: str = "harbor"
    harbor_timeout_sec: float = Field(900.0, gt=0)
    harbor_max_parallel: int = Field(2, ge=1, le=8)

    # Backend / logging
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    log_level: LogLevel = "INFO"

    @property
    def sandbox_image(self) -> str:
        """Stage 1 image tag, e.g. ``click-sandbox:cf19179e8e2f``."""
        return f"{self.sandbox_image_prefix}:{self.click_base_commit[:12]}"

    def require_llm_api_key(self) -> str:
        """Return the raw key for the LLM client, or raise ``ConfigError`` if unset."""
        if self.llm_api_key is None or not self.llm_api_key.get_secret_value():
            raise ConfigError("LLM_API_KEY is not set (use LLM_MODE=replay to run without a key)")
        return self.llm_api_key.get_secret_value()


_LIST_FIELDS = frozenset({"cors_origins"})


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a minimal ``KEY=VALUE`` .env file (comments, blank lines, optional quotes)."""
    values: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        key, sep, value = line.partition("=")
        key = key.strip()
        if not sep or not key.isidentifier():
            raise ConfigError(f"{path}:{lineno}: expected KEY=VALUE")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def load_settings(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = DEFAULT_ENV_FILE,
) -> Settings:
    """Build ``Settings`` from an environment mapping plus an optional .env file.

    Raises ``ConfigError`` (without echoing input values) when validation fails.
    """
    environ = os.environ if environ is None else environ
    merged: dict[str, str] = {}
    if env_file is not None and env_file.is_file():
        merged.update(parse_env_file(env_file))
    merged.update(environ)

    raw: dict[str, object] = {}
    for name in Settings.model_fields:
        value = merged.get(name.upper())
        if value is None or value.strip() == "":
            continue
        value = value.strip()
        if name in _LIST_FIELDS:
            raw[name] = [item.strip() for item in value.split(",") if item.strip()]
        else:
            raw[name] = value

    try:
        return Settings.model_validate(raw)
    except ValidationError as exc:
        issues = [
            f"{'.'.join(str(p) for p in err['loc']).upper()}: {err['msg']}"
            for err in exc.errors(include_input=False, include_url=False)
        ]
        raise ConfigError("Invalid configuration", issues=issues) from None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide cached settings. Tests reset with ``get_settings.cache_clear()``."""
    settings = load_settings()
    logger.debug(
        "settings loaded: base_commit=%s llm=%s/%s mode=%s key_set=%s",
        settings.click_base_commit,
        settings.llm_provider,
        settings.llm_model,
        settings.llm_mode,
        settings.llm_api_key is not None,
    )
    return settings


__all__ = [
    "PINNED_BASE_COMMIT",
    "PINNED_PYTEST_VERSION",
    "PINNED_RELEASE_TAG",
    "Settings",
    "get_settings",
    "load_settings",
    "parse_env_file",
]
