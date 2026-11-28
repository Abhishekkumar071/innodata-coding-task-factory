from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from task_factory.config import PINNED_BASE_COMMIT
from task_factory.schemas import (
    ALL_AXES,
    CandidateFiles,
    FeatureBlueprint,
    RunConfig,
    RunEvent,
    TaskStatus,
    ValidationOutcome,
    VerifierSummary,
)


def _blueprint(**overrides):
    data = {
        "task_id": "click-01-envvar-prefix-map",
        "axis": "context-envvar",
        "title": "t",
        "summary": "s",
        "target_files": ["src/click/core.py"],
        "target_symbols": ["click.core.Context"],
        "difficulty": "medium",
        "acceptance_criteria": ["a"],
        "non_goals": ["n"],
    }
    data.update(overrides)
    return FeatureBlueprint(**data)


@pytest.mark.parametrize("task_id", ["click-01-envvar-prefix-map", "click-15-x", "click-00-a-b-c"])
def test_valid_task_ids(task_id):
    assert _blueprint(task_id=task_id).task_id == task_id


@pytest.mark.parametrize(
    "task_id",
    [
        "click-1-short-number",
        "Click-01-upper",
        "click-01-Upper",
        "click-01-",
        "click-01--double",
        "click-01-../escape",
        "click-01-a/b",
        "click-01-a\\b",
        "feat-01-wrong-prefix",
        "click-01-" + "a" * 60,  # > 64 chars
    ],
)
def test_invalid_task_ids_rejected(task_id):
    with pytest.raises(ValidationError):
        _blueprint(task_id=task_id)


def test_invalid_axis_and_difficulty_rejected():
    with pytest.raises(ValidationError):
        _blueprint(axis="bug-fix")
    with pytest.raises(ValidationError):
        _blueprint(difficulty="trivial")


def test_run_config_defaults_and_bounds():
    cfg = RunConfig(base_commit=PINNED_BASE_COMMIT)
    assert cfg.repo == "pallets/click"
    assert cfg.count == 5
    assert tuple(cfg.axes) == ALL_AXES
    assert cfg.run_harbor is True and cfg.run_mutations is False
    assert cfg.llm_mode == "live"
    for bad in (0, 16):
        with pytest.raises(ValidationError):
            RunConfig(base_commit=PINNED_BASE_COMMIT, count=bad)
    with pytest.raises(ValidationError):
        RunConfig(base_commit=PINNED_BASE_COMMIT, axes=[])
    with pytest.raises(ValidationError):
        RunConfig(base_commit=PINNED_BASE_COMMIT, repo="pallets/flask")


@pytest.mark.parametrize("sha", ["abc", PINNED_BASE_COMMIT.upper(), PINNED_BASE_COMMIT + "0", ""])
def test_run_config_rejects_bad_sha(sha):
    with pytest.raises(ValidationError):
        RunConfig(base_commit=sha)


@pytest.mark.parametrize(
    ("name", "ok"),
    [
        ("tests/test_feature_result_lines.py", True),
        ("tests/test_feature_x1.py", True),
        ("tests/test_basic.py", False),
        ("tests/conftest.py", False),
        ("src/click/test_feature_x.py", False),
        ("tests/test_feature_X.py", False),
        ("tests/../test_feature_x.py", False),
    ],
)
def test_feature_test_filename_pattern(name, ok):
    kwargs = {"source_files": {}, "feature_test_filename": name, "feature_test_code": ""}
    if ok:
        assert CandidateFiles(**kwargs).feature_test_filename == name
    else:
        with pytest.raises(ValidationError):
            CandidateFiles(**kwargs)


def test_task_status_values_are_frozen():
    assert [s.value for s in TaskStatus] == [
        "proposed",
        "rejected",
        "synthesized",
        "precheck_failed",
        "precheck_passed",
        "packaged",
        "harbor_failed",
        "harbor_passed",
    ]


def test_run_event_round_trip_with_run_level_event():
    event = RunEvent(
        seq=1,
        run_id="run_20261128_100000",
        stage="run",
        message="completed",
        timestamp=datetime(2026, 11, 28, tzinfo=UTC),
    )
    assert event.task_id is None and event.level == "info" and event.data == {}
    assert RunEvent.model_validate_json(event.model_dump_json()) == event
    with pytest.raises(ValidationError):
        RunEvent(seq=1, run_id="r", stage="unknown", message="m", timestamp=event.timestamp)


def test_validation_outcome_allows_null_reward_for_crash():
    outcome = ValidationOutcome(
        task_id="click-01-x",
        mode="harbor_nop",
        reward=None,
        passed_feature=0,
        total_feature=3,
        passed_regression=0,
        total_regression=10,
        duration_sec=1.0,
        log_path="x",
    )
    assert outcome.reward is None and outcome.accepted is False and outcome.mutant_id is None


def test_verifier_summary_parses_compute_reward_output(run_compute_reward):
    _, summary = run_compute_reward(
        f2p=["t::f1"], p2p=["t::p1"], results={"t::f1": "passed", "t::p1": "passed"}, exit_code=0
    )
    parsed = VerifierSummary.model_validate(summary)
    assert parsed.status == "ok" and parsed.reward == 1.0
