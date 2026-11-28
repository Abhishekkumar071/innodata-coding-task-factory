"""Frozen cross-module contracts (docs/IMPLEMENTATION.md §4.1).

Contract freeze: only additive fields with defaults may be added, by announced PR from
Abhishek. Never rename or remove fields, enum values, or patterns.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

SHA_PATTERN = r"^[0-9a-f]{40}$"
TASK_ID_PATTERN = r"^click-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$"  # ≤ 64 chars (ADR-10)
TASK_ID_MAX_LENGTH = 64
FEATURE_TEST_PATTERN = r"^tests/test_feature_[a-z0-9_]+\.py$"

AxisSlug = Literal[
    "parameter-validation",
    "command-routing",
    "formatting-termui",
    "context-envvar",
    "testing-completion",
]
ALL_AXES: tuple[AxisSlug, ...] = (
    "parameter-validation",
    "command-routing",
    "formatting-termui",
    "context-envvar",
    "testing-completion",
)
Difficulty = Literal["easy", "medium", "hard"]
PipelineStage = Literal[
    "run",
    "analyze",
    "baseline",
    "ideate",
    "synthesize",
    "precheck",
    "package",
    "harbor_nop",
    "harbor_oracle",
    "mutate",
]
ValidationMode = Literal["stage1_base", "stage1_oracle", "harbor_nop", "harbor_oracle", "mutant"]
LLMMode = Literal["live", "record", "replay"]
EventLevel = Literal["info", "warn", "error"]


class TaskStatus(StrEnum):
    PROPOSED = "proposed"
    REJECTED = "rejected"
    SYNTHESIZED = "synthesized"
    PRECHECK_FAILED = "precheck_failed"
    PRECHECK_PASSED = "precheck_passed"
    PACKAGED = "packaged"
    HARBOR_FAILED = "harbor_failed"
    HARBOR_PASSED = "harbor_passed"


class RunConfig(BaseModel):
    repo: Literal["pallets/click"] = "pallets/click"
    base_commit: str = Field(pattern=SHA_PATTERN)
    count: int = Field(5, ge=1, le=15)
    axes: list[AxisSlug] = Field(default_factory=lambda: list(ALL_AXES), min_length=1)
    run_harbor: bool = True
    run_mutations: bool = False  # P1
    llm_mode: LLMMode = "live"
    resume_run_id: str | None = None


class SymbolInfo(BaseModel):
    qualname: str  # e.g. "click.core.Context.lookup_default"
    kind: Literal["module", "class", "function", "method"]
    file: str  # repo-relative, e.g. "src/click/core.py"
    lineno: int
    signature: str = ""
    doc_head: str = ""  # first docstring line


class RepoSnapshot(BaseModel):
    base_commit: str = Field(pattern=SHA_PATTERN)
    mirror_path: str
    source_files: list[str]  # src/click/*.py
    symbols: list[SymbolInfo]
    test_files: list[str]
    upstream_features: list[str] = []  # feature lines from newer upstream CHANGES.md


class BaselineResult(BaseModel):
    base_commit: str = Field(pattern=SHA_PATTERN)
    pass_to_pass: list[str]  # stable passes across all runs (ADR-09)
    excluded: dict[str, str] = {}  # nodeid -> "skipped" | "flaky" | "failed"
    runs: int = 3
    duration_sec: float


class FeatureBlueprint(BaseModel):
    task_id: str = Field(pattern=TASK_ID_PATTERN, max_length=TASK_ID_MAX_LENGTH)
    axis: AxisSlug
    title: str
    summary: str
    target_files: list[str]
    target_symbols: list[str]
    difficulty: Difficulty
    acceptance_criteria: list[str]
    non_goals: list[str]


class RejectedBlueprint(BaseModel):
    blueprint: FeatureBlueprint
    guard: Literal["schema", "scope", "novelty", "upstream", "diversity"]
    reason: str


class CandidateFiles(BaseModel):
    source_files: dict[str, str]  # repo-relative path under src/click/ -> full new content
    feature_test_filename: str = Field(pattern=FEATURE_TEST_PATTERN)
    feature_test_code: str


class VerifierSummary(BaseModel):
    """Mirrors the JSON written by tests/verifier/compute_reward.py."""

    schema_version: int = 1
    status: Literal["ok", "error"]
    reward: float
    errors: list[str] = []
    fast_mode: bool = False
    pytest_exit_code: int | None = None
    f2p_total: int
    f2p_passed: int
    p2p_total: int
    p2p_passed: int
    f2p_not_passed: list[str] = []
    p2p_not_passed: list[str] = []


class PrecheckResult(BaseModel):
    task_id: str
    attempt: int = 1
    patch_applies: bool
    solution_patch: str = ""  # git diff of src/click from the worktree
    fail_to_pass: list[str]  # collected via pytest --collect-only in sandbox
    base_summary: VerifierSummary | None = None
    oracle_summary: VerifierSummary | None = None
    full_suite: bool = False
    base_feature_failed: bool  # all f2p fail on base, status ok, p2p green
    oracle_passed: bool  # oracle reward == 1.0, status ok
    error_summary: str = ""  # truncated (≤ 4 KB) log fed to self-repair
    duration_sec: float = 0.0
    log_dir: str = ""


class SynthesizedTask(BaseModel):
    blueprint: FeatureBlueprint
    instruction_md: str
    solution_patch: str
    feature_test_filename: str = Field(pattern=FEATURE_TEST_PATTERN)
    feature_test_code: str
    fail_to_pass: list[str]
    pass_to_pass: list[str]
    repair_attempts: int = 0
    attempts: list[PrecheckResult] = []


class ValidationOutcome(BaseModel):
    task_id: str
    mode: ValidationMode
    reward: float | None  # None = test.sh never wrote reward.txt (crash)
    passed_feature: int
    total_feature: int
    passed_regression: int
    total_regression: int
    duration_sec: float
    log_path: str
    accepted: bool = False  # acceptance rule from TASK_INTERFACE §3
    status: Literal["ok", "error"] | None = None
    mutant_id: str | None = None


class MutantSpec(BaseModel):  # P1
    mutant_id: str  # e.g. "m01"
    operator: Literal[
        "negate_condition",
        "drop_raise",
        "early_return",
        "off_by_one",
        "swap_comparison",
        "drop_call",
    ]
    file: str
    line: int
    description: str
    patch: str


class RunEvent(BaseModel):
    seq: int  # monotonically increasing per run (SSE id)
    run_id: str
    stage: PipelineStage
    task_id: str | None = None  # None for run-level events
    level: EventLevel = "info"
    message: str
    timestamp: datetime
    data: dict = {}  # small structured payload (e.g. reward, attempt)


class TaskRecord(BaseModel):
    task_id: str
    run_id: str
    axis: AxisSlug
    title: str
    difficulty: Difficulty
    target_files: list[str]
    status: TaskStatus
    repair_attempts: int = 0
    package_path: str | None = None
    reject_reason: str | None = None
    validations: list[ValidationOutcome] = []


class RunResult(BaseModel):
    run_id: str  # "run_YYYYMMDD_HHMMSS"
    status: Literal["completed", "failed"]
    config: RunConfig
    tasks: list[TaskRecord]
    started_at: datetime
    finished_at: datetime
    summary_path: str | None = None


__all__ = [
    "ALL_AXES",
    "FEATURE_TEST_PATTERN",
    "SHA_PATTERN",
    "TASK_ID_MAX_LENGTH",
    "TASK_ID_PATTERN",
    "AxisSlug",
    "BaselineResult",
    "CandidateFiles",
    "Difficulty",
    "EventLevel",
    "FeatureBlueprint",
    "LLMMode",
    "MutantSpec",
    "PipelineStage",
    "PrecheckResult",
    "RejectedBlueprint",
    "RepoSnapshot",
    "RunConfig",
    "RunEvent",
    "RunResult",
    "SymbolInfo",
    "SynthesizedTask",
    "TaskRecord",
    "TaskStatus",
    "ValidationMode",
    "ValidationOutcome",
    "VerifierSummary",
]
