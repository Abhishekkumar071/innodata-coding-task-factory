# Technical Explanation — Innodata Coding Task Factory (Track 1)

> **Living Deliverable Document:** Fill in the `[TO BE RECORDED]` sections continuously as milestones complete between 26 Nov and 5 Dec so nothing is rushed on submission day.

---

## 1. Executive Summary

We built an automated, Harbor `0.25.x`-compliant **Coding Task Factory** targeting **`pallets/click`** (release `8.5.1`, pinned at commit `cf19179e8e2fd54c601378cec9e0d21bb12b6fb1`). Rather than manually crafting tasks, the pipeline analyzes `click`'s Python AST and test suite, proposes **5 substantively different feature-development blueprints** across orthogonal subsystems, synthesizes non-leaky requirements (`instruction.md`), reference patches (`solution/`), and tests (`tests/fail_to_pass.json`, `tests/pass_to_pass.json`), iteratively self-repairs patches in an isolated Git worktree, and verifies every generated task inside Docker using official `harbor run -a nop` (`0.0`), `harbor run -a oracle` (`1.0`), and mutation testing.

---

## 2. Starting Repository & Commit Selection

- **Selected Repository:** `https://github.com/pallets/click`
- **Release Tag / Branch:** `8.5.1`
- **Pinned 40-Character `base_commit`:** `cf19179e8e2fd54c601378cec9e0d21bb12b6fb1`
- **Baseline Verification:** `2434 passed, 24 skipped, 1 xfailed, 31000 deselected` in Docker `python:3.11-slim` with `pytest==9.0.2` (click's `uv.lock` pin); identical across 3 runs. The 31000 deselected tests are click's own `stress` marker (`addopts = "-m 'not stress'"`). `pass_to_pass` = the 2434 stable passes; the 24 platform skips and 1 xfail are excluded and recorded.
- **Why `pallets/click`:** Fast editable install (`pip install -e .`), deterministic `pytest` node IDs, rich CLI/decorator/validation/formatting surface area, and direct Python AST introspection.

---

## 3. Core Architecture & Reused Components

### Reused Open-Source Components
- **Harbor Framework (`harbor==0.25.*`):** Standardized container execution, `nop` and `oracle` grading agents, trial log management.
- **`pallets/click` + `pytest`:** Target repository and native test runner.
- **Python `ast`, `GitPython`, `FastAPI`, `SQLAlchemy`, `React + Vite + Tailwind`:** Static code analysis, deterministic Git diff generation, API orchestration, and inspector UI.

### Key Engineering Decisions & Assumptions
1. **File-Edit + Deterministic `git diff` vs Raw Patch Generation:** Instead of asking LLMs to generate fragile unified diff hunk headers directly, the synthesizer generates targeted code edits on a clean worktree and extracts exact patches via `git diff`.
2. **Two-Stage Validation (Fast Worktree Pre-Check + Harbor Docker Gate):** Running rapid self-repair loops against local isolated Git worktrees cuts feedback latency from ~45s/container to ~3s/attempt, while official Harbor Docker runs remain the authoritative acceptance gate.
3. **Strict Anti-Leakage Separation:** `environment/Dockerfile` clones only `base_commit`; `tests/` and `solution/` remain strictly outside the base image, and automated string checks guard `instruction.md` against leaking test or implementation details.

---

## 4. Task Variation Strategy (5 Orthogonal Axes)

To guarantee meaningful variation rather than reworded prompts, the Variation Engine allocates tasks across five distinct behavioural axes of `pallets/click`:

1. **Axis 1 — Parameter & Type System** (`types.py`, `core.py`)
2. **Axis 2 — Command & Group Routing / Lifecycle** (`core.py`, `decorators.py`)
3. **Axis 3 — Help & Terminal Formatting** (`formatting.py`, `termui.py`)
4. **Axis 4 — Context, EnvVar & Value-Source Precedence** (`core.py`, `globals.py`)
5. **Axis 5 — Testing Harness & Shell Completion** (`testing.py`, `shell_completion.py`)

Each candidate feature must pass:
- **Feature-Only Guard:** Rejects bug-fix proposals.
- **Upstream Novelty Check:** Cross-checks AST symbols/docstrings at `base_commit` to ensure the feature does not already exist.
- **Pairwise Non-Overlap Check:** Ensures distinct target symbols, behavioural contracts, and assertions across all 5 tasks.

---

## 5. Declared Models, Agents & Tools

*(Mandatory per Participant Guide — list exact versions used during final evidence generation.)*

| Role in Pipeline | Provider / Tool | Exact Model / Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Task Ideation & Synthesis** | `[TO BE RECORDED]` | `[e.g., gemini-2.5-pro / gpt-4o]` | Feature blueprint, `instruction.md`, code & test synthesis |
| **Self-Repair Loop** | `[TO BE RECORDED]` | `[e.g., same or fast model]` | Fixing failing patches/tests using `pytest` tracebacks |
| **Harbor Evaluation** | Harbor CLI | `harbor==0.25.*` | `nop` & `oracle` Docker verification |
| **Dev Assistance** *(if used)* | `[TO BE RECORDED]` | `[Declare coding assistants used]` | Engineering & documentation |

---

## 6. Validation Evidence Summary

*(Populate from `artifacts/validation_evidence/` after Day-9 clean run.)*

| Task ID | Axis | `fail_to_pass` Count | `pass_to_pass` Count | Repair Retries | Harbor `nop` Reward | Harbor `oracle` Reward | Mutants Killed |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `[task-01]` | Parameter Validation | `[N]` | `[M]` | `[k]` | `0.0` | `1.0` | `[x/y]` |
| `[task-02]` | Command Routing | `[N]` | `[M]` | `[k]` | `0.0` | `1.0` | `[x/y]` |
| `[task-03]` | Formatting / TermUI | `[N]` | `[M]` | `[k]` | `0.0` | `1.0` | `[x/y]` |
| `[task-04]` | Context / EnvVar | `[N]` | `[M]` | `[k]` | `0.0` | `1.0` | `[x/y]` |
| `[task-05]` | Testing / Completion | `[N]` | `[M]` | `[k]` | `0.0` | `1.0` | `[x/y]` |

### Observed Failure Cases & Documented Fixes
- **Missing `less` in the base image (28 Nov):** the first baseline in `python:3.11-slim` had 24 failures in `tests/test_utils/test_echo_via_pager.py` because the slim image has no pager. Fix: the fixed Dockerfile template installs `less`; baseline became fully green.
- `[TO BE RECORDED: Document real failures encountered during pipeline development—e.g. CRLF shell script errors, LLM proposing an existing click option, flaky test assertions, self-repair examples—and the automated/engineering fixes implemented.]`
