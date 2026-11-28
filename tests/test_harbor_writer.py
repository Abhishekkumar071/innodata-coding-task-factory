import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from task_factory import harbor_writer as hw
from task_factory.config import PINNED_BASE_COMMIT
from task_factory.errors import ConfigError, LeakageDetected, ScopeViolation
from tests.conftest import REPO_ROOT, SAMPLE_FEATURE_TEST, SAMPLE_TASK_SRC, TEMPLATES_DIR

OTHER_SHA = "0" * 40
FEATURE = SAMPLE_FEATURE_TEST


def _issues(exc_info) -> str:
    return "\n".join(exc_info.value.issues)


def _edit(task_dir: Path, rel: str, transform) -> None:
    path = task_dir / rel
    path.write_bytes(transform(path.read_bytes()))


def _replace(task_dir: Path, rel: str, old: str, new: str) -> None:
    _edit(task_dir, rel, lambda b: b.replace(old.encode(), new.encode()))


# --------------------------------------------------------------------------------------
# write_text_lf / templates / rendering
# --------------------------------------------------------------------------------------


def test_write_text_lf_normalizes_crlf_cr_and_bom(tmp_path):
    target = tmp_path / "nested" / "a.sh"
    hw.write_text_lf(target, "﻿#!/usr/bin/env bash\r\necho hi\rexit 0")
    assert target.read_bytes() == b"#!/usr/bin/env bash\necho hi\nexit 0\n"


def test_write_text_lf_keeps_existing_trailing_newline_and_empty_text(tmp_path):
    hw.write_text_lf(tmp_path / "x.txt", "a\n")
    hw.write_text_lf(tmp_path / "empty.txt", "")
    assert (tmp_path / "x.txt").read_bytes() == b"a\n"
    assert (tmp_path / "empty.txt").read_bytes() == b""


def test_template_files_are_lf_utf8_without_bom():
    names = sorted(p.name for p in TEMPLATES_DIR.iterdir() if p.is_file())
    assert names == sorted(
        ["Dockerfile", "task.toml", "solve.sh", "test.sh", "reward_plugin.py", "compute_reward.py"]
    )
    for path in TEMPLATES_DIR.iterdir():
        data = path.read_bytes()
        assert b"\r" not in data, path.name
        assert not data.startswith(b"\xef\xbb\xbf"), path.name
        data.decode("utf-8")


@pytest.mark.parametrize(
    "root",
    [
        SAMPLE_TASK_SRC,
        REPO_ROOT / "artifacts" / "upstream",
    ],
)
def test_fixture_and_upstream_files_are_lf_without_bom(root):
    files = [p for p in root.rglob("*") if p.is_file()]
    assert files
    for path in files:
        data = path.read_bytes()
        assert b"\r" not in data, path
        assert not data.startswith(b"\xef\xbb\xbf"), path


def test_render_dockerfile_pins_commit_pytest_and_less():
    text = hw.render_dockerfile(PINNED_BASE_COMMIT)
    assert f"ARG BASE_COMMIT={PINNED_BASE_COMMIT}" in text
    assert '"pytest==9.0.2"' in text
    assert "git ca-certificates less" in text
    assert "--depth 1" in text and "remote remove origin" in text
    assert "{{" not in text
    assert hw.render_dockerfile(PINNED_BASE_COMMIT, pytest_pin="8.3.4").count("pytest==8.3.4") == 1


@pytest.mark.parametrize("sha", ["", "abc", PINNED_BASE_COMMIT.upper(), PINNED_BASE_COMMIT + "\n"])
def test_render_dockerfile_rejects_bad_sha(sha):
    with pytest.raises(ConfigError):
        hw.render_dockerfile(sha)


def test_render_dockerfile_rejects_bad_pytest_pin():
    with pytest.raises(ConfigError):
        hw.render_dockerfile(PINNED_BASE_COMMIT, pytest_pin="9.0.2; rm -rf /")


def test_render_task_toml_validates_inputs():
    text = hw.render_task_toml(
        "click-01-x", axis="command-routing", difficulty="hard", base_commit=PINNED_BASE_COMMIT
    )
    assert 'task_id = "click-01-x"' in text and 'axis = "command-routing"' in text
    with pytest.raises(ConfigError):
        hw.render_task_toml(
            'click-01-x"\n[evil]', axis="command-routing", difficulty="hard",
            base_commit=PINNED_BASE_COMMIT,
        )
    with pytest.raises(ConfigError):
        hw.render_task_toml(
            "click-01-x", axis="bug-fix", difficulty="hard", base_commit=PINNED_BASE_COMMIT
        )
    with pytest.raises(ConfigError):
        hw.render_task_toml(
            "click-01-x", axis="command-routing", difficulty="x", base_commit=PINNED_BASE_COMMIT
        )


def test_render_verifier_files_keys_relative_to_tests_dir():
    files = hw.render_verifier_files()
    assert set(files) == {"test.sh", "verifier/reward_plugin.py", "verifier/compute_reward.py"}
    assert files["test.sh"].startswith("#!/usr/bin/env bash\n")
    assert "--continue-on-collection-errors" in files["test.sh"]
    assert all("\r" not in v for v in files.values())


# --------------------------------------------------------------------------------------
# write_task_package
# --------------------------------------------------------------------------------------


def test_write_task_package_round_trip_matches_fixture(tmp_path, sample_synthesized_task):
    out = hw.write_task_package(sample_synthesized_task, tmp_path / "tasks")
    assert out == tmp_path / "tasks" / "click-00-manual-sample"
    written = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    assert written == sorted([*hw.REQUIRED_FILES, SAMPLE_FEATURE_TEST])
    for rel in written:  # the committed fixture is exactly what the writer produces
        assert (out / rel).read_bytes() == (SAMPLE_TASK_SRC / rel).read_bytes(), rel
    assert not list((tmp_path / "tasks").glob(".staging-*"))
    if os.name != "nt":
        assert os.access(out / "tests/test.sh", os.X_OK)
        assert os.access(out / "solution/solve.sh", os.X_OK)


def test_write_task_package_normalizes_llm_crlf(tmp_path, sample_synthesized_task):
    task = sample_synthesized_task.model_copy(
        update={
            "instruction_md": sample_synthesized_task.instruction_md.replace("\n", "\r\n"),
            "feature_test_code": "﻿" + sample_synthesized_task.feature_test_code,
        }
    )
    out = hw.write_task_package(task, tmp_path / "tasks")
    assert b"\r" not in (out / "instruction.md").read_bytes()
    assert not (out / SAMPLE_FEATURE_TEST).read_bytes().startswith(b"\xef\xbb\xbf")


def test_write_task_package_sorts_and_dedups_node_ids(tmp_path, sample_synthesized_task):
    f2p = list(reversed(sample_synthesized_task.fail_to_pass))
    task = sample_synthesized_task.model_copy(update={"fail_to_pass": f2p + f2p[:1]})
    out = hw.write_task_package(task, tmp_path / "tasks")
    assert json.loads((out / "tests/fail_to_pass.json").read_text()) == sorted(set(f2p))


def test_write_task_package_refuses_overwrite_unless_asked(tmp_path, sample_synthesized_task):
    hw.write_task_package(sample_synthesized_task, tmp_path / "tasks")
    with pytest.raises(ConfigError, match="already exists"):
        hw.write_task_package(sample_synthesized_task, tmp_path / "tasks")
    hw.write_task_package(sample_synthesized_task, tmp_path / "tasks", overwrite=True)


def test_rejected_package_never_lands_in_out_dir(tmp_path, sample_synthesized_task):
    bad = sample_synthesized_task.model_copy(
        update={"instruction_md": sample_synthesized_task.instruction_md + "\nSee fail_to_pass.\n"}
    )
    with pytest.raises(LeakageDetected):
        hw.write_task_package(bad, tmp_path / "tasks")
    assert not (tmp_path / "tasks" / "click-00-manual-sample").exists()
    assert not list((tmp_path / "tasks").glob(".staging-*"))


def test_write_task_package_rejects_other_base_commit_mismatch(tmp_path, sample_synthesized_task):
    out = hw.write_task_package(sample_synthesized_task, tmp_path / "tasks", base_commit=OTHER_SHA)
    with pytest.raises(ScopeViolation, match="invalid") as info:
        hw.validate_package(out)  # validated against the pinned SHA by default
    assert "base_commit does not match" in _issues(info)


# --------------------------------------------------------------------------------------
# validate_package — happy path and every rejection rule
# --------------------------------------------------------------------------------------


def test_sample_fixture_passes_validation(sample_synthesized_task):
    hw.validate_package(SAMPLE_TASK_SRC, pass_to_pass=sample_synthesized_task.pass_to_pass)


def test_missing_directory_is_rejected(tmp_path):
    with pytest.raises(ScopeViolation, match="not found"):
        hw.validate_package(tmp_path / "nope")


@pytest.mark.parametrize("rel", hw.REQUIRED_FILES)
def test_missing_required_file_is_rejected(sample_task_dir, rel):
    (sample_task_dir / rel).unlink()
    with pytest.raises((ScopeViolation, LeakageDetected)) as info:
        hw.validate_package(sample_task_dir)
    assert f"missing required file: {rel}" in _issues(info)


def test_unexpected_files_and_extra_feature_modules_are_rejected(sample_task_dir):
    hw.write_text_lf(sample_task_dir / "tests" / "conftest.py", "x = 1\n")
    hw.write_text_lf(sample_task_dir / "tests" / "test_feature_other.py", "")
    with pytest.raises(ScopeViolation) as info:
        hw.validate_package(sample_task_dir)
    issues = _issues(info)
    assert "unexpected file in package: tests/conftest.py" in issues
    assert "expected exactly one tests/test_feature_*.py, found 2" in issues


@pytest.mark.parametrize(
    ("rel", "transform", "needle"),
    [
        ("tests/test.sh", lambda b: b.replace(b"\n", b"\r\n"), "contains CR"),
        ("instruction.md", lambda b: b"\xef\xbb\xbf" + b, "has a UTF-8 BOM"),
        ("tests/pass_to_pass.json", lambda b: b + b"\xff", "not valid UTF-8"),
    ],
)
def test_encoding_violations_are_rejected(sample_task_dir, rel, transform, needle):
    _edit(sample_task_dir, rel, transform)
    with pytest.raises(ScopeViolation) as info:
        hw.validate_package(sample_task_dir)
    assert needle in _issues(info)


@pytest.mark.parametrize(
    "rel",
    [
        "tests/test.sh",
        "solution/solve.sh",
        "tests/verifier/reward_plugin.py",
        "tests/verifier/compute_reward.py",
        "environment/Dockerfile",
    ],
)
def test_template_drift_is_rejected(sample_task_dir, rel):
    _edit(sample_task_dir, rel, lambda b: b + b"# hand edit\n")
    with pytest.raises(ScopeViolation) as info:
        hw.validate_package(sample_task_dir)
    assert f"{rel}: differs from the fixed template" in _issues(info)


def test_task_toml_drift_and_identity_are_checked(sample_task_dir):
    _replace(sample_task_dir, "task.toml", "timeout_sec = 300.0", "timeout_sec = 1.0")
    with pytest.raises(ScopeViolation) as info:
        hw.validate_package(sample_task_dir)
    assert "task.toml: differs from the fixed template" in _issues(info)


@pytest.mark.parametrize(
    ("old", "new", "needle"),
    [
        ('task_id = "click-00-manual-sample"', 'task_id = "click-00-other"', "directory name"),
        ('task_id = "click-00-manual-sample"', 'task_id = "../evil"', "invalid task_id"),
        ('axis = "testing-completion"', 'axis = "bug-fix"', "invalid axis"),
        ('difficulty = "easy"', 'difficulty = "trivial"', "invalid difficulty"),
        (PINNED_BASE_COMMIT, OTHER_SHA, "base_commit does not match"),
        ("[metadata]", "[metadata", "invalid TOML"),
    ],
)
def test_task_toml_identity_violations(sample_task_dir, old, new, needle):
    _replace(sample_task_dir, "task.toml", old, new)
    with pytest.raises(ScopeViolation) as info:
        hw.validate_package(sample_task_dir)
    assert needle in _issues(info)


@pytest.mark.parametrize(
    ("line", "needle"),
    [
        ("COPY solution/ /solution/\n", "COPY/ADD is not allowed"),
        ("RUN echo tests\n", "must not reference solution/ or tests/"),
    ],
)
def test_dockerfile_leaks_are_rejected(sample_task_dir, line, needle):
    _edit(sample_task_dir, "environment/Dockerfile", lambda b: b + line.encode())
    with pytest.raises(LeakageDetected) as info:
        hw.validate_package(sample_task_dir)
    assert needle in _issues(info)


PATCH_HEADER = "diff --git a/{p} b/{p}\nindex 1111111..2222222 100644\n--- a/{p}\n+++ b/{p}\n"


def _patch(path: str, added: list[str], removed: int = 0) -> str:
    body = "".join(f"-old{i}\n" for i in range(removed)) + "".join(f"+{a}\n" for a in added)
    hunk = f"@@ -1,{removed} +1,{len(added)} @@\n"
    return PATCH_HEADER.format(p=path) + hunk + body


@pytest.mark.parametrize(
    ("patch", "needle"),
    [
        (_patch("tests/test_basic.py", ["x = 1"]), "disallowed path 'tests/test_basic.py'"),
        (_patch("src/click/conftest.py", ["x = 1"]), "disallowed path 'src/click/conftest.py'"),
        (_patch("pyproject.toml", ["x = 1"]), "disallowed path 'pyproject.toml'"),
        (_patch("src/click/../../x.py", ["x = 1"]), "disallowed path"),
        (_patch("src/click/core.py", ["import subprocess"]), "denied token 'subprocess'"),
        (_patch("src/click/core.py", ["open('/logs/verifier/x')"]), "denied token '/logs'"),
        (_patch("src/click/core.py", ["reward = 1.0"]), "denied token 'reward'"),
        (_patch("src/click/core.py", ["import socket"]), "denied token 'socket'"),
        (_patch("src/click/core.py", ["import pytest"]), "denied token 'import pytest'"),
        (_patch("src/click/core.py", ["sys.modules['x'] = y"]), "denied token 'sys.modules'"),
        (_patch("src/click/core.py", ["x = 1"] * 401), "401 changed lines > 400"),
        ("just some text\n", "no file headers found"),
        ("\n", "solution.patch: is empty"),
        (
            PATCH_HEADER.format(p="src/click/core.py") + "GIT binary patch\nliteral 1\n",
            "binary patches are not allowed",
        ),
    ],
)
def test_patch_scope_violations(sample_task_dir, patch, needle):
    hw.write_text_lf(sample_task_dir / "solution" / "solution.patch", patch)
    with pytest.raises(ScopeViolation) as info:
        hw.validate_package(sample_task_dir)
    assert needle in _issues(info)


def test_removed_line_starting_with_dashes_is_not_a_header(sample_task_dir):
    patch = _patch("src/click/core.py", ["x = 1"]).replace("@@ -1,0", "@@ -1,1") + "--- comment\n"
    hw.write_text_lf(sample_task_dir / "solution" / "solution.patch", patch)
    hw.validate_package(sample_task_dir)  # "--- comment" inside a hunk is a removed line


def test_deny_tokens_only_apply_to_added_lines(sample_task_dir):
    hunk = "@@ -1,2 +1,2 @@\n import subprocess\n-a\n+b\n"
    patch = PATCH_HEADER.format(p="src/click/core.py") + hunk
    hw.write_text_lf(sample_task_dir / "solution" / "solution.patch", patch)
    hw.validate_package(sample_task_dir)


@pytest.mark.parametrize(
    ("rel", "content", "needle"),
    [
        ("tests/fail_to_pass.json", "not json", "invalid JSON"),
        ("tests/fail_to_pass.json", '{"a": 1}', "must be a JSON array"),
        ("tests/fail_to_pass.json", json.dumps([f"{FEATURE}::a"]), "1 IDs, expected 3-10"),
        (
            "tests/fail_to_pass.json",
            json.dumps([f"{FEATURE}::t{i:02d}" for i in range(11)]),
            "11 IDs, expected 3-10",
        ),
        (
            "tests/fail_to_pass.json",
            json.dumps([f"tests/test_basic.py::{n}" for n in "abc"]),
            "IDs outside tests/test_feature_result_lines.py",
        ),
        (
            "tests/fail_to_pass.json",
            json.dumps([f"tests/test_feature_result_lines.py::{n}" for n in "cba"]),
            "node IDs must be sorted",
        ),
        (
            "tests/fail_to_pass.json",
            json.dumps([f"tests/test_feature_result_lines.py::{n}" for n in "aab"]),
            "duplicate node IDs",
        ),
        ("tests/pass_to_pass.json", "[]", "pass_to_pass.json: is empty"),
        (
            "tests/pass_to_pass.json",
            json.dumps(["tests/test_basic.py::a", "tests/test_feature_result_lines.py::x"]),
            "must not contain feature test IDs",
        ),
    ],
)
def test_node_id_list_violations(sample_task_dir, rel, content, needle):
    hw.write_text_lf(sample_task_dir / rel, content)
    with pytest.raises(ScopeViolation) as info:
        hw.validate_package(sample_task_dir)
    assert needle in _issues(info)


def test_pass_to_pass_must_equal_run_baseline(sample_task_dir, sample_synthesized_task):
    baseline = sample_synthesized_task.pass_to_pass[:-1]
    with pytest.raises(ScopeViolation) as info:
        hw.validate_package(sample_task_dir, pass_to_pass=baseline)
    assert "does not equal the run baseline" in _issues(info)


@pytest.mark.parametrize(
    "leak",
    [
        "Run tests/test_feature_result_lines.py to check.",
        "The fail_to_pass list contains everything.",
        "Regression set: pass_to_pass.",
        "Covered by ::test_output_lines_split_on_newline",
        "@@ -309,6 +309,32 @@",
        "diff --git a/src/click/testing.py b/src/click/testing.py",
        "--- a/src/click/testing.py",
        "+++ b/src/click/testing.py",
    ],
)
def test_instruction_banned_tokens_are_leaks(sample_task_dir, leak):
    _edit(sample_task_dir, "instruction.md", lambda b: b + f"\n{leak}\n".encode())
    with pytest.raises(LeakageDetected) as info:
        hw.validate_package(sample_task_dir)
    assert "instruction.md: contains banned token" in _issues(info)


def test_instruction_verbatim_patch_copy_is_a_leak(sample_task_dir):
    copied = '        """The terminal output (:attr:`output`) as a list of lines.'
    _edit(sample_task_dir, "instruction.md", lambda b: b + f"\n{copied}\n".encode())
    with pytest.raises(LeakageDetected) as info:
        hw.validate_package(sample_task_dir)
    assert "copies patch code verbatim" in _issues(info)


def test_instruction_may_repeat_public_signatures(sample_task_dir):
    signature = "    def output_lines(self) -> list[str]:"
    _edit(sample_task_dir, "instruction.md", lambda b: b + f"\n{signature}\n".encode())
    hw.validate_package(sample_task_dir)


@pytest.mark.parametrize(
    ("heading", "section"),
    [
        ("## Goal", "Goal"),
        ("## Required behaviour", "Required behaviour"),
        ("## Public API", "Public API"),
        ("## Errors and messages", "Errors"),
        ("## Examples", "Examples"),
        ("## Non-goals", "Non-goals"),
        ("## Compatibility", "Compatibility"),
    ],
)
def test_instruction_required_sections(sample_task_dir, heading, section):
    _replace(sample_task_dir, "instruction.md", heading + "\n", "## Something else\n")
    with pytest.raises(ScopeViolation) as info:
        hw.validate_package(sample_task_dir)
    assert f"missing required section heading {section!r}" in _issues(info)


def test_instruction_accepts_american_spelling(sample_task_dir):
    _replace(sample_task_dir, "instruction.md", "## Required behaviour\n", "## Required Behavior\n")
    hw.validate_package(sample_task_dir)


def test_leaks_take_precedence_and_include_all_issues(sample_task_dir):
    _edit(sample_task_dir, "instruction.md", lambda b: b + b"\nfail_to_pass\n")
    hw.write_text_lf(sample_task_dir / "tests" / "conftest.py", "")
    with pytest.raises(LeakageDetected) as info:
        hw.validate_package(sample_task_dir)
    issues = _issues(info)
    assert "banned token" in issues and "unexpected file in package: tests/conftest.py" in issues


# --------------------------------------------------------------------------------------
# git apply --check
# --------------------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def mini_repo(tmp_path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git not available")
    repo = tmp_path / "mini"
    (repo / "src" / "click").mkdir(parents=True)
    (repo / "src" / "click" / "core.py").write_bytes(b"a = 1\n")
    _git(repo, "init", "-q")
    _git(repo, "-c", "core.autocrlf=false", "add", ".")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "init")
    return repo


GOOD_PATCH = PATCH_HEADER.format(p="src/click/core.py") + "@@ -1 +1 @@\n-a = 1\n+a = 2\n"
BAD_PATCH = PATCH_HEADER.format(p="src/click/core.py") + "@@ -1 +1 @@\n-b = 1\n+b = 2\n"


def test_git_apply_check_accepts_clean_patch(sample_task_dir, mini_repo):
    hw.write_text_lf(sample_task_dir / "solution" / "solution.patch", GOOD_PATCH)
    hw.validate_package(sample_task_dir, apply_check_repo=mini_repo)


def test_git_apply_check_rejects_non_applying_patch(sample_task_dir, mini_repo):
    hw.write_text_lf(sample_task_dir / "solution" / "solution.patch", BAD_PATCH)
    with pytest.raises(ScopeViolation) as info:
        hw.validate_package(sample_task_dir, apply_check_repo=mini_repo)
    assert "does not apply cleanly" in _issues(info)


# --------------------------------------------------------------------------------------
# compute_reward.py (fixed template) — reward rule and status
# --------------------------------------------------------------------------------------

F2P = [f"t/test_feature_x.py::{n}" for n in "abcd"]
P2P = ["t/test_old.py::p1", "t/test_old.py::p2"]
ALL_P2P_PASS = {n: "passed" for n in P2P}


def test_reward_oracle_all_pass(run_compute_reward):
    reward, s = run_compute_reward(
        f2p=F2P, p2p=P2P, results={**ALL_P2P_PASS, **{n: "passed" for n in F2P}}, exit_code=0
    )
    assert reward == "1.0\n"
    assert s["status"] == "ok" and s["reward"] == 1.0 and s["errors"] == []
    assert (s["f2p_passed"], s["f2p_total"], s["p2p_passed"], s["p2p_total"]) == (4, 4, 2, 2)


def test_reward_nop_all_feature_fail(run_compute_reward):
    results = {**ALL_P2P_PASS, **{n: "failed" for n in F2P}}
    reward, s = run_compute_reward(f2p=F2P, p2p=P2P, results=results, exit_code=1)
    assert reward == "0.0\n"
    assert s["status"] == "ok" and s["f2p_passed"] == 0 and s["p2p_passed"] == 2
    assert s["f2p_not_passed"] == F2P


def test_reward_nop_with_missing_feature_results(run_compute_reward):
    # Collection error under nop: feature IDs never reported, regressions still green.
    results = {**ALL_P2P_PASS, "<collection-error>::t/test_feature_x.py": "error"}
    reward, s = run_compute_reward(f2p=F2P, p2p=P2P, results=results, exit_code=1)
    assert reward == "0.0\n" and s["status"] == "ok" and s["p2p_passed"] == 2


def test_reward_partial(run_compute_reward):
    results = {**ALL_P2P_PASS, F2P[0]: "passed", F2P[1]: "failed", F2P[2]: "passed"}
    reward, s = run_compute_reward(f2p=F2P, p2p=P2P, results=results, exit_code=1)
    assert reward == "0.5\n" and s["reward"] == 0.5 and s["status"] == "ok"


def test_reward_partial_is_rounded(run_compute_reward):
    f2p = F2P[:3]
    results = {**ALL_P2P_PASS, f2p[0]: "passed"}
    reward, s = run_compute_reward(f2p=f2p, p2p=P2P, results=results, exit_code=1)
    assert reward == "0.3333\n"


@pytest.mark.parametrize("p2p_outcome", ["failed", "skipped", None])
def test_reward_zero_when_any_regression_not_passed(run_compute_reward, p2p_outcome):
    results = {P2P[0]: "passed", **{n: "passed" for n in F2P}}
    if p2p_outcome is not None:
        results[P2P[1]] = p2p_outcome
    reward, s = run_compute_reward(f2p=F2P, p2p=P2P, results=results, exit_code=1)
    assert reward == "0.0\n"
    assert s["status"] == "ok" and s["p2p_passed"] == 1 and s["p2p_not_passed"] == [P2P[1]]


def test_reward_error_when_results_missing(run_compute_reward):
    reward, s = run_compute_reward(f2p=F2P, p2p=P2P, results=None, exit_code=1)
    assert reward == "0.0\n" and s["status"] == "error"
    assert "test_results.json missing (pytest did not finish)" in s["errors"]


@pytest.mark.parametrize("code", [2, 3, 4, 5, 124])
def test_reward_error_on_abnormal_pytest_exit(run_compute_reward, code):
    results = {**ALL_P2P_PASS, **{n: "passed" for n in F2P}}
    reward, s = run_compute_reward(f2p=F2P, p2p=P2P, results=results, exit_code=code)
    assert reward == "0.0\n" and s["status"] == "error"
    assert f"pytest exit code {code}" in s["errors"]


def test_reward_error_on_setup_failure(run_compute_reward):
    reward, s = run_compute_reward(f2p=F2P, p2p=P2P, results=None, setup_error="cannot cd /app")
    assert reward == "0.0\n" and s["status"] == "error"
    assert s["errors"] == ["setup: cannot cd /app"]


def test_reward_error_on_empty_fail_to_pass(run_compute_reward):
    reward, s = run_compute_reward(f2p=[], p2p=P2P, results=ALL_P2P_PASS, exit_code=0)
    assert reward == "0.0\n" and s["status"] == "error"
    assert "fail_to_pass.json is empty" in s["errors"]


def test_reward_fast_mode_grades_only_executed_regressions(run_compute_reward):
    results = {P2P[0]: "passed", **{n: "passed" for n in F2P}}  # P2P[1] did not run
    reward, s = run_compute_reward(f2p=F2P, p2p=P2P, results=results, exit_code=0, fast_mode=True)
    assert reward == "1.0\n" and s["fast_mode"] is True and s["p2p_total"] == 1
    reward_full, _ = run_compute_reward(f2p=F2P, p2p=P2P, results=results, exit_code=0)
    assert reward_full == "0.0\n"


def test_reward_lists_are_capped(run_compute_reward):
    f2p = [f"t/test_feature_x.py::t{i:03d}" for i in range(80)]
    reward, s = run_compute_reward(f2p=f2p, p2p=P2P, results=ALL_P2P_PASS, exit_code=1)
    assert len(s["f2p_not_passed"]) == 50 and s["f2p_total"] == 80


# --------------------------------------------------------------------------------------
# reward_plugin.py + compute_reward.py against a real pytest session (no LLM code involved)
# --------------------------------------------------------------------------------------

OLD_TESTS = """\
import pytest

def test_a():
    pass

@pytest.mark.parametrize("x", [1, 2])
def test_param(x):
    assert x

class TestGroup:
    def test_method(self):
        pass

@pytest.mark.skip(reason="platform")
def test_skipped():
    pass
"""
FEATURE_TESTS_NOP = (
    "from featmod import thing\n\n"
    "def test_f1():\n    assert thing()\n\n"
    "def test_f2():\n    assert thing()\n"
)
FEATURE_TESTS_LAZY = (
    "def test_f1():\n    from featmod import thing\n    assert thing()\n\n"
    "def test_f2():\n    from featmod import thing\n    assert thing() == 'two'\n"
)


def _pytest_session(tmp_path: Path, feature_code: str, featmod: str | None) -> tuple[str, dict]:
    project, verifier, logs, tests_dir = (
        tmp_path / n for n in ("proj", "verifier", "logs", "tests")
    )
    (project / "tests").mkdir(parents=True)
    for d in (verifier, logs, tests_dir):
        d.mkdir()
    shutil.copy(TEMPLATES_DIR / "reward_plugin.py", verifier / "reward_plugin.py")
    (project / "tests" / "test_old.py").write_text(OLD_TESTS, encoding="utf-8")
    (project / "tests" / "test_feature_x.py").write_text(feature_code, encoding="utf-8")
    if featmod is not None:
        (project / "featmod.py").write_text(featmod, encoding="utf-8")
    (tests_dir / "fail_to_pass.json").write_text(
        json.dumps(["tests/test_feature_x.py::test_f1", "tests/test_feature_x.py::test_f2"]),
        encoding="utf-8",
    )
    (tests_dir / "pass_to_pass.json").write_text(
        json.dumps([
            "tests/test_old.py::TestGroup::test_method",
            "tests/test_old.py::test_a",
            "tests/test_old.py::test_param[1]",
            "tests/test_old.py::test_param[2]",
        ]),
        encoding="utf-8",
    )
    env = {
        **os.environ,
        "PYTHONPATH": f"{verifier}{os.pathsep}{project}",
        "VERIFIER_LOG_DIR": str(logs),
        "VERIFIER_TESTS_DIR": str(tests_dir),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-p", "reward_plugin", "-p", "no:cacheprovider",
         "--continue-on-collection-errors", "-q", "-o", "addopts=", "--rootdir", str(project)],
        cwd=project, env=env, capture_output=True, text=True, timeout=120,
    )
    subprocess.run(
        [sys.executable, str(TEMPLATES_DIR / "compute_reward.py"),
         "--pytest-exit-code", str(proc.returncode)],
        env=env, check=True, timeout=60,
    )
    results = json.loads((logs / "test_results.json").read_text(encoding="utf-8"))["results"]
    summary = json.loads((logs / "verifier_summary.json").read_text(encoding="utf-8"))
    assert results["tests/test_old.py::test_skipped"] == "skipped"
    return (logs / "reward.txt").read_text(encoding="utf-8"), summary


def test_plugin_nop_with_module_level_import_error(tmp_path):
    reward, s = _pytest_session(tmp_path, FEATURE_TESTS_NOP, featmod=None)
    assert reward == "0.0\n"
    assert s["status"] == "ok" and s["pytest_exit_code"] == 1  # not 2: collection continued
    assert (s["p2p_passed"], s["p2p_total"], s["f2p_passed"]) == (4, 4, 0)


def test_plugin_oracle(tmp_path):
    reward, s = _pytest_session(tmp_path, FEATURE_TESTS_LAZY, featmod=THING_RETURNS % "two")
    assert reward == "1.0\n" and s["status"] == "ok" and s["pytest_exit_code"] == 0


THING_RETURNS = "def thing():\n    return '%s'\n"


def test_plugin_partial(tmp_path):
    reward, s = _pytest_session(tmp_path, FEATURE_TESTS_LAZY, featmod=THING_RETURNS % "one")
    assert reward == "0.5\n" and s["f2p_passed"] == 1
