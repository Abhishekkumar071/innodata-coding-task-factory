# Harbor `0.25.x` Task Interface Contract (`TASK_INTERFACE.md`)

This document is the **single source of truth** for the output task package format produced by `task_factory/harbor_writer.py`, consumed by Harbor (`harbor==0.25.*`), and displayed in the frontend inspector.

> **Day-1 Verification Rule:** Before finalizing `harbor_writer.py`, install `pip install "harbor==0.25.*"` and run `harbor task init _schema_check` to confirm exact `task.toml` key nesting against the installed `0.25.x` build. Update this document immediately if `0.25.x` expects any additional required key.

---

## 1. Required Task Package Directory Structure

Each generated task lives in its own directory (`artifacts/tasks/<task-id>/`, e.g., `click-feat-01-envvar-prefix-map/`):

```text
<task-id>/
├── task.toml                  # Task metadata, 40-char base_commit, timeouts, license
├── instruction.md             # Complete requirement spec (ONLY file visible to evaluated agent)
├── environment/
│   └── Dockerfile             # Builds pallets/click cleanly at base_commit
├── solution/
│   ├── solve.sh               # Oracle entrypoint script (LF line endings, chmod +x)
│   └── solution.patch         # Clean git diff applied by solve.sh
└── tests/
    ├── test.sh                # Harbor verifier script writing /logs/verifier/reward.txt
    ├── fail_to_pass.json      # JSON array of new feature pytest node IDs
    ├── pass_to_pass.json      # JSON array of existing regression pytest node IDs
    └── test_feature_*.py      # New feature test module(s) copied into repo only at verify time
```

### Critical Isolation Rules
1. **No Leakage in `environment/Dockerfile`:**
   - The container built by `environment/Dockerfile` MUST only contain the clean repository checked out at `base_commit` with dependencies installed (`pip install -e .` + `pytest`).
   - NEVER copy `solution/` or `tests/` into the Docker image inside `environment/Dockerfile`. Harbor mounts/injects `/tests` only during verification, and `/solution` only when running `-a oracle`.
2. **No Spoilers in `instruction.md`:**
   - Must specify clear requirements, public API signatures, CLI behaviour, edge cases, and error conditions.
   - Must NEVER reference `test_feature_*.py`, `fail_to_pass.json`, or paste reference patch snippets.
3. **Unix LF (`\n`) Safety on Windows:**
   - All `.sh` scripts (`solution/solve.sh`, `tests/test.sh`) MUST be written with `newline="\n"` (LF only, never Windows CRLF `\r\n`) and executable mode so Docker Linux `/bin/bash` never fails with `bad interpreter`.

---

## 2. File-by-File Specification

### 2.1 `task.toml`
Required fields per Participant Guide + Harbor `0.25.x`:
- Full **40-character commit hash** recorded under `base_commit`
- Repository identifier (`pallets/click`) and license (`BSD-3-Clause` — matches `pallets/click`)
- Verifier / agent timeouts and environment CPU/memory settings

```toml
version = "1.0"

[metadata]
author_name = "Innodata Task Factory Team"
difficulty = "medium"                  # easy | medium | hard
category = "feature-development"
repo = "pallets/click"
repo_url = "https://github.com/pallets/click.git"
base_commit = "<40_CHAR_FULL_GIT_COMMIT_SHA>"
license = "BSD-3-Clause"
axis = "parameter-validation"          # Variation axis tag
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

*(Note: When `harbor task init` is verified on Day 1, confirm whether `base_commit` should live under `[metadata]`, `[task]`, or top-level in `harbor==0.25.*`.)*

---

### 2.2 `environment/Dockerfile`
Builds an isolated Python environment for `pallets/click` pinned strictly at `base_commit`:

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone and checkout exact 40-char starting commit (never dirty, never upstream HEAD)
ARG BASE_COMMIT=<40_CHAR_FULL_GIT_COMMIT_SHA>
RUN git clone https://github.com/pallets/click.git /app \
    && git checkout "${BASE_COMMIT}"

# Install click in editable mode + pytest (matching pallets/click dev commands)
RUN pip install --no-cache-dir -e . pytest
```

*(Optimization note: Confirm whether `pallets/click` at the pinned commit requires any test extras from `requirements/tests.txt` or `pyproject.toml`, e.g., `pip install --no-cache-dir -e ".[dev]"` or `pip install --no-cache-dir pytest` — check on Day 1 baseline container build!)*

---

### 2.3 `solution/solve.sh`
Executed inside `/app` when running `harbor run -a oracle`:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd /app
git apply --whitespace=nowarn /solution/solution.patch
```

---

### 2.4 `tests/fail_to_pass.json` & `tests/pass_to_pass.json`
SWE-bench-style JSON lists of exact `pytest` node IDs:

```json
// tests/fail_to_pass.json
[
  "tests/test_feature_envvar_map.py::test_feature_basic_behavior",
  "tests/test_feature_envvar_map.py::test_feature_edge_case_override",
  "tests/test_feature_envvar_map.py::test_feature_invalid_input_raises"
]
```

```json
// tests/pass_to_pass.json
[
  "tests/test_basic.py::test_basic_functionality",
  "tests/test_options.py::test_add_option"
  // Full or complete pinned regression suite node IDs from baseline pytest collection
]
```

---

### 2.5 `tests/test.sh` & Exact Harbor Reward Logic
Harbor runs `/tests/test.sh` inside the container after the agent (`nop`, `oracle`, or an evaluated coding agent) finishes.

**Mandatory Contract:**
1. Copy feature test file(s) from `/tests/test_feature_*.py` into `/app/tests/`.
2. Execute `pytest` with `--junitxml=/tmp/junit.xml` covering all `/tests/fail_to_pass.json` and `/tests/pass_to_pass.json` node IDs. **Always capture `pytest`'s exit status without letting `set -e` abort** (`pytest ... --junitxml=/tmp/junit.xml || true`), because `fail_to_pass` tests are expected to fail under `nop`.
3. Parse `/tmp/junit.xml` against `/tests/fail_to_pass.json` and `/tests/pass_to_pass.json` using Python stdlib (`xml.etree.ElementTree` + `json` — zero extra pip dependencies needed inside Docker) and compute reward strictly according to the Participant Guide specification:
   - If **any** test in `pass_to_pass.json` fails, errors, or is missing/skipped unexpectedly $\rightarrow$ `reward = 0.0`
   - Else if **all** tests in `fail_to_pass.json` pass $\rightarrow$ `reward = 1.0`
   - Else $\rightarrow$ `reward = passed_fail_to_pass / total_fail_to_pass`
4. Write the single floating-point value to `/logs/verifier/reward.txt` (creating `/logs/verifier` if needed) AND save a structured breakdown `/logs/verifier/verifier_summary.json` for validation evidence!
5. Always exit `0` after writing `/logs/verifier/reward.txt` (unless a genuine environment crash prevents running `pytest`), so Harbor does not report `null` reward on expected `nop` test failures!

---

## 3. Official Harbor Validation Commands

Every generated task package MUST pass both commands below before being accepted into `artifacts/tasks/`:

```bash
# Baseline Check (Expected reward: 0.0)
harbor run -p artifacts/tasks/<task-id> -a nop -k 1 -o artifacts/harbor_runs/nop --no-delete -y

# Oracle Check (Expected reward: 1.0)
harbor run -p artifacts/tasks/<task-id> -a oracle -k 1 -o artifacts/harbor_runs/oracle --no-delete -y
```

### Acceptance Thresholds
- `nop` run $\rightarrow$ `reward == 0.0`, `pass_to_pass` 100% pass, `fail_to_pass` 100% fail (no environmental crash / no `null` reward).
- `oracle` run $\rightarrow$ `reward == 1.0`, `pass_to_pass` 100% pass, `fail_to_pass` 100% pass.
- `mutant` check (via `mutation_tester.py`) $\rightarrow$ `reward < 1.0` (confirms feature tests fail when implementation is subtly broken).
