"""Typed exception hierarchy (docs/architecture.md §10).

Every exception carries ``http_status`` so ``backend/`` can map errors without re-deciding
policy. Task-level errors (``PrecheckFailed``, ``GuardViolation`` and subclasses) reject a
single task; the pipeline continues. Run-level errors abort the run.
"""

from __future__ import annotations

from typing import ClassVar


class FactoryError(Exception):
    """Base class for all task-factory errors."""

    http_status: ClassVar[int] = 500
    task_level: ClassVar[bool] = False

    def __init__(self, message: str, *, issues: list[str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.issues: list[str] = list(issues or [])

    def __str__(self) -> str:
        if not self.issues:
            return self.message
        details = "\n".join(f"  - {issue}" for issue in self.issues)
        return f"{self.message}\n{details}"


class ConfigError(FactoryError):
    """Invalid configuration, env var, SHA, task_id, or request input."""

    http_status = 400


class RepoStateError(FactoryError):
    """Mirror dirty, SHA mismatch, or baseline not 100% green."""


class LLMError(FactoryError):
    """LLM provider failure after retries (or replay-cache miss)."""

    http_status = 502


class LLMResponseInvalid(LLMError):
    """LLM output failed JSON/schema validation after retries."""


class SandboxError(FactoryError):
    """Docker unavailable, image build failed, or sandbox container timed out."""


class PrecheckFailed(FactoryError):
    """Stage 1 self-repair attempts exhausted; the task is rejected."""

    task_level = True


class GuardViolation(FactoryError):
    """A scope/leak/quality guard rejected a task; the task is rejected."""

    task_level = True


class LeakageDetected(GuardViolation):
    """instruction.md or the environment leaks tests or solution content."""


class ScopeViolation(GuardViolation):
    """Package, patch, or tests violate the Harbor contract or scope rules."""


class HarborError(FactoryError):
    """Harbor CLI missing, wrong version, or crashed."""


class NotFound(FactoryError):
    """Requested run/task/evidence does not exist."""

    http_status = 404


class RunConflict(FactoryError):
    """A pipeline run is already active."""

    http_status = 409


__all__ = [
    "ConfigError",
    "FactoryError",
    "GuardViolation",
    "HarborError",
    "LLMError",
    "LLMResponseInvalid",
    "LeakageDetected",
    "NotFound",
    "PrecheckFailed",
    "RepoStateError",
    "RunConflict",
    "SandboxError",
    "ScopeViolation",
]
