"""Shared fixtures (owner: Abhishek).

FakeLLM is intentionally NOT defined here: it belongs to ``task_factory/llm_client.py``
(Alok, IMPLEMENTATION.md §2/§4.4) and will be shared from there.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from task_factory.config import Settings, get_settings
from task_factory.schemas import FeatureBlueprint, SynthesizedTask

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = REPO_ROOT / "task_factory" / "templates" / "harbor"
SAMPLE_TASK_ID = "click-00-manual-sample"
SAMPLE_TASK_SRC = REPO_ROOT / "tests" / "fixtures" / "sample_task" / SAMPLE_TASK_ID
SAMPLE_FEATURE_TEST = "tests/test_feature_result_lines.py"


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Every test starts with default settings: no factory env vars, no .env, fresh cache."""
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def sample_task_dir(tmp_path: Path) -> Path:
    """A writable copy of the sample package at ``<tmp>/tasks/click-00-manual-sample``."""
    dest = tmp_path / "tasks" / SAMPLE_TASK_ID
    shutil.copytree(SAMPLE_TASK_SRC, dest)
    return dest


def _read(rel: str) -> str:
    return (SAMPLE_TASK_SRC / rel).read_text(encoding="utf-8")


@pytest.fixture
def sample_synthesized_task() -> SynthesizedTask:
    """The sample fixture expressed as a ``SynthesizedTask`` (as the synthesizer would emit)."""
    return SynthesizedTask(
        blueprint=FeatureBlueprint(
            task_id=SAMPLE_TASK_ID,
            axis="testing-completion",
            title="Line-oriented access to captured CLI output",
            summary="Result.output_lines / stdout_lines / stderr_lines",
            target_files=["src/click/testing.py"],
            target_symbols=["click.testing.Result"],
            difficulty="easy",
            acceptance_criteria=["split on \\n only"],
            non_goals=["no CliRunner changes"],
        ),
        instruction_md=_read("instruction.md"),
        solution_patch=_read("solution/solution.patch"),
        feature_test_filename=SAMPLE_FEATURE_TEST,
        feature_test_code=_read(SAMPLE_FEATURE_TEST),
        fail_to_pass=json.loads(_read("tests/fail_to_pass.json")),
        pass_to_pass=json.loads(_read("tests/pass_to_pass.json")),
    )


RewardRunner = Callable[..., tuple[str, dict]]


@pytest.fixture
def run_compute_reward(tmp_path: Path) -> RewardRunner:
    """Run the fixed compute_reward.py template against synthetic inputs.

    Returns ``(reward_txt, verifier_summary)``. ``results=None`` simulates pytest never
    writing test_results.json.
    """

    def _run(
        *,
        f2p: list[str],
        p2p: list[str],
        results: dict[str, str] | None,
        exit_code: int | None = None,
        setup_error: str | None = None,
        fast_mode: bool = False,
    ) -> tuple[str, dict]:
        case = tmp_path / f"reward_case_{len(list(tmp_path.glob('reward_case_*')))}"
        tests_dir, log_dir = case / "tests", case / "logs"
        tests_dir.mkdir(parents=True)
        log_dir.mkdir()
        (tests_dir / "fail_to_pass.json").write_text(json.dumps(f2p), encoding="utf-8")
        (tests_dir / "pass_to_pass.json").write_text(json.dumps(p2p), encoding="utf-8")
        if results is not None:
            payload = {"exitstatus": exit_code or 0, "results": results}
            (log_dir / "test_results.json").write_text(json.dumps(payload), encoding="utf-8")
        args = [sys.executable, str(TEMPLATES_DIR / "compute_reward.py")]
        if exit_code is not None:
            args += ["--pytest-exit-code", str(exit_code)]
        if setup_error is not None:
            args += ["--setup-error", setup_error]
        env = {
            **os.environ,
            "VERIFIER_LOG_DIR": str(log_dir),
            "VERIFIER_TESTS_DIR": str(tests_dir),
        }
        env.pop("FAST_MODE", None)
        if fast_mode:
            env["FAST_MODE"] = "1"
        subprocess.run(args, check=True, env=env, timeout=60)
        reward = (log_dir / "reward.txt").read_text(encoding="utf-8")
        summary = json.loads((log_dir / "verifier_summary.json").read_text(encoding="utf-8"))
        return reward, summary

    return _run
