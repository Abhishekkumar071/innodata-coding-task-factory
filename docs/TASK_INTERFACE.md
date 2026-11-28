# Harbor `0.25.x` Task Interface Contract (`TASK_INTERFACE.md`) — v2

This document is the **single source of truth** for the task package format produced by `task_factory/harbor_writer.py`, consumed by Harbor (`harbor==0.25.*`), executed by the Stage 1 sandbox (`sandbox_precheck.py`), and displayed in the Control Room.

> **Verification status:** Items marked **[VERIFY]** are assumptions until checked against the installed `harbor==0.25.*` (`harbor task init _tmp_harbor_check`). Owner: Abhishek, due **28 Nov 2026**. On verification, replace the marker with the confirmed behaviour and announce the change in team chat. See [`architecture.md` §15](./architecture.md#15-day-1-verification-items-owner-abhishek-due-28-nov).

**v2 changes vs v1:** shallow-fetch Dockerfile (no future upstream history), pinned `pytest`, node-ID-exact reward plugin instead of JUnit parsing, `verifier_summary.json` schema, `--continue-on-collection-errors`, deterministic env vars, `task_id` regex, package validation checklist. Rationale: [`architecture.md` §14](./architecture.md#14-architecture-decision-records-adrs).

---

## 1. Package Directory Structure

Each task lives in `artifacts/tasks/<task_id>/`.

**`task_id` format (ADR-10):** `^click-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$`, max 64 chars, e.g. `click-01-envvar-prefix-map`. The number is the position in the curated set; the slug is derived from the blueprint title. Anything else is rejected with `ConfigError` (also prevents path traversal).

```text
<task_id>/
├── task.toml                     # Metadata, 40-char base_commit, timeouts, resources
├── instruction.md                # ONLY file visible to the evaluated agent
├── environment/
│   └── Dockerfile                # FIXED TEMPLATE, byte-identical across tasks
├── solution/
│   ├── solve.sh                  # FIXED TEMPLATE (LF, +x)
│   └── solution.patch            # git diff touching src/click/** only
└── tests/
    ├── test.sh                   # FIXED TEMPLATE verifier (LF, +x)
    ├── fail_to_pass.json         # JSON array: new feature test node IDs (3–10)
    ├── pass_to_pass.json         # JSON array: stable baseline node IDs
    ├── test_feature_<slug>.py    # Exactly one feature test module
    └── verifier/
        ├── reward_plugin.py      # FIXED TEMPLATE pytest plugin (stdlib only)
        └── compute_reward.py     # FIXED TEMPLATE reward calculator (stdlib only)
```

"FIXED TEMPLATE" files live in `task_factory/templates/harbor/` and are rendered with **only** validated values (`base_commit`, `task_id`, `axis`, `difficulty`, pinned versions). They are **never** produced or edited by an LLM (ADR-05).

### 1.1 Isolation Rules
1. **No leakage via the image:** `environment/Dockerfile` contains no `COPY`/`ADD` and no reference to `solution` or `tests`. Harbor provides `/tests` only at verification time and `/solution` only for `-a oracle`. **[VERIFY: mount vs copy, and exact paths]**
2. **No future history:** the image contains exactly one commit (`base_commit`) fetched with `--depth 1`; the remote is removed. The evaluated agent cannot `git log` its way to later upstream code.
3. **No spoilers in `instruction.md`:** never references `test_feature_*`, `fail_to_pass`, `pass_to_pass`, node IDs, or diff markers; never pastes patch code (declared public signatures excepted).
4. **Complete spec in `instruction.md`:** every literal, exception type, flag name, and public symbol asserted by the tests must be stated in `instruction.md` (spec–test consistency rule). A task that tests something the instruction does not specify is rejected.
5. **LF + UTF-8 without BOM** for every file in the package; `.sh` files committed with the executable bit (`git update-index --chmod=+x`). **[VERIFY: whether Harbor execs scripts directly or via `bash`]**

---

## 2. File-by-File Specification

### 2.1 `task.toml`

```toml
version = "1.0"

[metadata]
task_id = "click-01-envvar-prefix-map"
author_name = "Innodata Task Factory Team"
difficulty = "medium"                  # easy | medium | hard
category = "feature-development"
repo = "pallets/click"
repo_url = "https://github.com/pallets/click.git"
base_commit = "<40_CHAR_FULL_GIT_COMMIT_SHA>"
license = "BSD-3-Clause"
axis = "context-envvar"                # one of the 5 canonical slugs
tags = ["python", "cli", "click", "feature-development"]

[verifier]
timeout_sec = 300.0

[agent]
timeout_sec = 600.0

[environment]
build_timeout_sec = 600.0
cpus = 2
memory_mb = 4096
```

**[VERIFY]** Placement of `base_commit` (`[metadata]` vs top level), whether unknown `[metadata]` keys are allowed, and whether an internet toggle exists for agent/verifier phases. Required keys reported by `harbor task init` that are missing above must be added here first, then in the template.

### 2.2 `environment/Dockerfile` (fixed template)

```dockerfile
# FIXED TEMPLATE rendered by task_factory/harbor_writer.py. Identical for every task.
FROM python:3.11-slim

# less: required by click's echo_via_pager suite (24 failures without it).
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates less \
 && rm -rf /var/lib/apt/lists/*

ARG BASE_COMMIT={{BASE_COMMIT}}
WORKDIR /app

# Fetch exactly one commit: no future upstream history inside the image.
RUN git init -q /app \
 && git -C /app remote add origin https://github.com/pallets/click.git \
 && git -C /app fetch -q --depth 1 origin "${BASE_COMMIT}" \
 && git -C /app checkout -q --detach FETCH_HEAD \
 && git -C /app remote remove origin \
 && test "$(git -C /app rev-parse HEAD)" = "${BASE_COMMIT}"

# Editable install + pytest pinned to click's own lockfile at base_commit.
RUN pip install --no-cache-dir -e /app "pytest=={{PYTEST_PIN}}"
```

- **Verified 28 Nov:** `{{PYTEST_PIN}}` = `9.0.2` (from click 8.5.1 `uv.lock`, `settings.pytest_pin`); `{{BASE_COMMIT}}` = `cf19179e8e2fd54c601378cec9e0d21bb12b6fb1` (tag `8.5.1`). `python:3.11-slim` lacks `less`, which made 24 tests in `tests/test_utils/test_echo_via_pager.py` fail; with `less` the baseline is `2434 passed, 24 skipped, 1 xfailed, 31000 deselected` (`-m 'not stress'` from click's own pytest config). No other plugins are needed. Never leave versions floating.
- Template source: `task_factory/templates/harbor/Dockerfile`; placeholders are `{{NAME}}` and are filled only with regex-validated values.
- The same rendered Dockerfile builds the Stage 1 image `click-sandbox:<sha12>` (ADR-01).

### 2.3 `solution/solve.sh` (fixed template)

```bash
#!/usr/bin/env bash
# Oracle entrypoint. FIXED TEMPLATE rendered by task_factory/harbor_writer.py.
set -euo pipefail
cd /app
git apply --whitespace=nowarn /solution/solution.patch
```

### 2.4 `solution/solution.patch`
- Produced by `git diff --no-color --no-ext-diff --binary -- src/click` in the Stage 1 worktree (never hand-written by the LLM).
- Paths: **only** `src/click/**`. No new files outside `src/click/`, no edits to `tests/`, `conftest.py`, `pyproject.toml`, `setup.*`, `requirements/*`.
- ≤ 400 changed lines; must apply cleanly on `base_commit` (`git apply --check`).
- Deny-list tokens in added lines (rejected with `ScopeViolation`): `/logs`, `reward`, `subprocess`, `socket`, `os.system`, `urllib`, `requests`, `http.client`, `import pytest`, `sys.modules`, `conftest`.

### 2.5 `tests/fail_to_pass.json` & `tests/pass_to_pass.json`
- JSON arrays of exact pytest node IDs relative to `/app` (e.g. `tests/test_feature_envvar_prefix_map.py::test_prefix_applies_to_nested_commands`), sorted, UTF-8, LF.
- `fail_to_pass`: collected via `pytest --collect-only -q tests/test_feature_<slug>.py` inside the sandbox — **never** guessed by the LLM. 3–10 entries.
- `pass_to_pass`: the **stable baseline** — tests passing in all 3 baseline sandbox runs (ADR-09). Skipped/xfail/flaky tests are excluded and listed in `artifacts/validation_evidence/baseline.json`. Identical for every task in a run.

### 2.6 `tests/test_feature_<slug>.py`
- One module per task, `pytest` + `click.testing.CliRunner` + stdlib only. No network, no files outside `tmp_path`, no `sleep`, no randomness without a fixed seed, no fixtures that modify global state without restoring it.
- **Import new symbols inside test functions**, not at module top level, so each test fails independently under `nop`.
- Uses only public API that exists at base or is declared in `instruction.md`.

### 2.7 `tests/test.sh` (fixed template)

```bash
#!/usr/bin/env bash
# Harbor verifier. FIXED TEMPLATE rendered by task_factory/harbor_writer.py. Never LLM-authored.
# Contract: ALWAYS writes /logs/verifier/reward.txt and verifier_summary.json, ALWAYS exits 0.
set -uo pipefail

LOG_DIR=/logs/verifier
VERIFIER=/tests/verifier
mkdir -p "$LOG_DIR"

setup_error() {
  python3 "$VERIFIER/compute_reward.py" --setup-error "$1" \
    || echo "0.0" > "$LOG_DIR/reward.txt"
  exit 0
}

export COLUMNS=80 LINES=24 TERM=dumb LC_ALL=C.UTF-8
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$VERIFIER${PYTHONPATH:+:$PYTHONPATH}"

cd /app || setup_error "cannot cd /app"
cp /tests/test_feature_*.py /app/tests/ || setup_error "cannot copy feature tests"
python -c "import click, sys; sys.exit(0 if click.__file__.startswith('/app/src') else 1)" \
  || setup_error "click is not imported from /app/src"

# PYTEST_TARGETS / FAST_MODE are only set by the Stage 1 sandbox. Harbor always runs the full suite.
TARGETS="${PYTEST_TARGETS:-tests}"
# shellcheck disable=SC2086
timeout "${VERIFIER_PYTEST_TIMEOUT:-270}" python -m pytest $TARGETS \
  -p reward_plugin -p no:cacheprovider --continue-on-collection-errors -q \
  > "$LOG_DIR/pytest.log" 2>&1
rc=$?

python3 "$VERIFIER/compute_reward.py" --pytest-exit-code "$rc" \
  || echo "0.0" > "$LOG_DIR/reward.txt"
exit 0
```

Why these flags:
- `--continue-on-collection-errors`: under `nop`, a feature module may fail to import; without the flag pytest aborts the **whole** session (exit 2) and `pass_to_pass` can't be proven green.
- `-p no:cacheprovider`: no `.pytest_cache` writes; no cross-run state.
- Pinned `COLUMNS`/`TERM`/locale: click's help and formatting output depends on terminal width.

### 2.8 `tests/verifier/reward_plugin.py` (fixed template)

```python
"""Records exact pytest node-ID outcomes. Stdlib only. FIXED TEMPLATE."""
import json
import os

_OUT = os.path.join(os.environ.get("VERIFIER_LOG_DIR", "/logs/verifier"), "test_results.json")
_results = {}


def pytest_runtest_logreport(report):
    nodeid = report.nodeid
    if report.failed:                       # failure in setup, call, or teardown
        _results[nodeid] = "failed"
    elif report.skipped:                    # skip / xfail
        _results.setdefault(nodeid, "skipped")
    elif report.when == "call" and report.passed and _results.get(nodeid) != "failed":
        _results[nodeid] = "passed"


def pytest_collectreport(report):
    if report.failed:
        _results["<collection-error>::" + report.nodeid] = "error"


def pytest_sessionfinish(session, exitstatus):
    with open(_OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"exitstatus": int(exitstatus), "results": _results}, fh, indent=1, sort_keys=True)
```

### 2.9 `tests/verifier/compute_reward.py` (fixed template)

```python
"""Computes the Harbor reward from exact node-ID outcomes. Stdlib only. FIXED TEMPLATE."""
import argparse
import json
import os
from pathlib import Path

# Overridable only so the factory's own unit tests can run this file outside a container.
LOG_DIR = Path(os.environ.get("VERIFIER_LOG_DIR", "/logs/verifier"))
TESTS_DIR = Path(os.environ.get("VERIFIER_TESTS_DIR", "/tests"))
MAX_LISTED = 50


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pytest-exit-code", type=int, default=None)
    ap.add_argument("--setup-error", default=None)
    args = ap.parse_args()

    f2p = _load(TESTS_DIR / "fail_to_pass.json")
    p2p = _load(TESTS_DIR / "pass_to_pass.json")
    fast_mode = os.environ.get("FAST_MODE") == "1"
    errors, results = [], {}

    if args.setup_error:
        errors.append("setup: " + args.setup_error)
    results_file = LOG_DIR / "test_results.json"
    if results_file.exists():
        results = _load(results_file)["results"]
    elif not args.setup_error:
        errors.append("test_results.json missing (pytest did not finish)")
    if args.pytest_exit_code not in (None, 0, 1):   # 0=all passed, 1=some failed; else crash/timeout
        errors.append("pytest exit code %s" % args.pytest_exit_code)
    if not f2p:
        errors.append("fail_to_pass.json is empty")
    if fast_mode:                                   # Stage 1 fast mode: only grade what ran
        p2p = [n for n in p2p if n in results]

    f2p_passed = [n for n in f2p if results.get(n) == "passed"]
    f2p_not_passed = [n for n in f2p if results.get(n) != "passed"]
    p2p_not_passed = [n for n in p2p if results.get(n) != "passed"]

    status = "error" if errors else "ok"
    if status == "error" or p2p_not_passed:
        reward = 0.0
    elif len(f2p_passed) == len(f2p):
        reward = 1.0
    else:
        reward = round(len(f2p_passed) / len(f2p), 4)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "reward.txt").write_text("%s\n" % reward, encoding="utf-8")
    summary = {
        "schema_version": 1,
        "status": status,
        "reward": reward,
        "errors": errors,
        "fast_mode": fast_mode,
        "pytest_exit_code": args.pytest_exit_code,
        "f2p_total": len(f2p),
        "f2p_passed": len(f2p_passed),
        "p2p_total": len(p2p),
        "p2p_passed": len(p2p) - len(p2p_not_passed),
        "f2p_not_passed": f2p_not_passed[:MAX_LISTED],
        "p2p_not_passed": p2p_not_passed[:MAX_LISTED],
    }
    (LOG_DIR / "verifier_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
```

### 2.10 Reward Rule (Participant Guide) & Status
| Condition | Reward |
| :--- | :---: |
| `status == "error"` (setup failure, pytest crash/timeout, missing results) | `0.0` + `status=error` |
| Any `pass_to_pass` test not `passed` (failed, error, skipped, or missing) | `0.0` |
| All `fail_to_pass` passed | `1.0` |
| Otherwise | `passed_fail_to_pass / total_fail_to_pass` |

A `null` reward in Harbor means `test.sh` never wrote `reward.txt` (container crash) and is always a validation failure.

---

## 3. Official Validation Commands & Acceptance

```bash
# Baseline (expected 0.0)
harbor run -p artifacts/tasks/<task_id> -a nop    -k 1 -o artifacts/harbor_runs/<run_id>/<task_id>/harbor_nop    --no-delete -y
# Oracle (expected 1.0)
harbor run -p artifacts/tasks/<task_id> -a oracle -k 1 -o artifacts/harbor_runs/<run_id>/<task_id>/harbor_oracle --no-delete -y
```

Output dirs are **unique per run/task/mode** (never shared). **[VERIFY: layout of job/trial folders under `-o`]**

**Acceptance (computed from `verifier_summary.json`, ADR-11):**
| Mode | Accepted when |
| :--- | :--- |
| `harbor_nop` | `status == "ok"` ∧ `p2p_passed == p2p_total` ∧ `f2p_passed == 0` ∧ `reward == 0.0` |
| `harbor_oracle` | `status == "ok"` ∧ `reward == 1.0` |
| `mutant` (P1) | `reward < 1.0`; a **meaningful kill** additionally has `p2p_passed == p2p_total` |
| `stage1_base` / `stage1_oracle` | Same rules as `harbor_nop` / `harbor_oracle`, executed in the sandbox |

---

## 4. Package Validation Checklist (`harbor_writer.validate_package()`)

Run after writing and before Harbor. Any failure → `LeakageDetected` / `ScopeViolation`, task rejected, reason logged.

- [ ] All 10 required files exist (Section 1), plus exactly one `tests/test_feature_*.py`, and no other files (e.g. no `conftest.py`).
- [ ] `task_id` matches regex; directory name equals `task.toml` `task_id`; `base_commit` is 40-hex and equals `settings.click_base_commit`; `axis` is a canonical slug.
- [ ] Every file is UTF-8 without BOM and contains no `\r`.
- [ ] Fixed-template files are byte-identical to a fresh render (no drift/hand edits).
- [ ] Dockerfile: no `COPY`/`ADD`, no `solution`/`tests` reference.
- [ ] `solution.patch`: only `src/click/**`, ≤ 400 changed lines, deny-list clean, `git apply --check` passes on a clean worktree.
- [ ] `fail_to_pass.json`: 3–10 unique, sorted IDs, all inside the feature module; `pass_to_pass.json`: non-empty, unique, sorted, no feature IDs, equals the run baseline (when given).
- [ ] `instruction.md`: no banned tokens (`test_feature`, `fail_to_pass`, `pass_to_pass`, `::test_`, `@@`, `+++ `, `--- a/`, `diff --git`); no verbatim copy of an added patch line > 40 chars except declared signatures; contains all required template sections (Goal, Required behaviour, Public API, Errors, Examples, Non-goals, Compatibility).

---

## 5. Evidence Layout (`artifacts/validation_evidence/`)

```text
validation_evidence/
├── summary.json / summary.md        # One row per task: axis, f2p, p2p, repairs, nop, oracle, mutants
├── environment.json                 # OS, Docker, Harbor, Python, image digest, factory git SHA, model IDs
├── baseline.json                    # Baseline pass count, excluded flaky/skipped tests
├── diversity.json                   # Pairwise similarity across tasks (P1 report)
└── <task_id>/
    ├── stage1/attempt_<n>.json      # Self-repair history (PrecheckResult)
    ├── harbor_nop/                  # reward.txt, verifier_summary.json, test_results.json, pytest.log, harbor job files
    ├── harbor_oracle/
    └── mutant_<id>/                 # (P1) same files + mutant.patch + operator description
```
