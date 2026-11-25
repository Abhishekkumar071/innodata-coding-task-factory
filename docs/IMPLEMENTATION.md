# Implementation Guide (`IMPLEMENTATION.md`)

This guide defines the tech stack, folder ownership, Day-1 environment setup, data contracts, and engineering standards for all 4 team members.

---

## 1. Tech Stack & Dependencies

| Layer | Technology | Notes |
| :--- | :--- | :--- |
| **Language & Packaging** | Python `3.11+`, `pyproject.toml` | Core `task_factory` + `backend` share one Python project |
| **Harbor Evaluation** | `harbor==0.25.*` + Docker Desktop/Engine | Mandatory Track 1 evaluation runtime (`harbor` on `PATH`) |
| **AI / LLM Client** | `google-genai` / `openai` / `litellm` *(lock exact model in `.env` & declare in `TECHNICAL_EXPLANATION.md`)* | Structured JSON output + temperature control + retry wrapper |
| **Git & Code Analysis** | `GitPython`, Python stdlib `ast`, `subprocess` | Worktree isolation, clean diff extraction, AST symbol map |
| **Backend API & DB** | `fastapi`, `uvicorn`, `pydantic>=2`, `sqlalchemy` (SQLite) | Async job runner, SSE event stream, persistence |
| **Frontend UI** | React 18 + Vite + TypeScript + Tailwind CSS + `react-diff-viewer-continued` (or Monaco Diff) | Fast SPA communicating with FastAPI on `http://localhost:8000` |
| **Dev & Quality** | `pytest`, `ruff`, GitHub Actions | Automated lint & unit tests on every PR |

---

## 2. Repository Structure & File Ownership (Zero-Conflict Boundaries)

```text
innodata-coding-task-factory/
├── AGENTS.md                        # [Abhishek] Central engineering & AI agent rules
├── README.md
├── .gitignore                       # [Abhishek] Ignore .venv, .env, *.db, node_modules, _tmp_*
├── .gitattributes                   # [Abhishek] Enforce LF for *.sh
├── .env.example                     # [Abhishek] API keys & config template
├── pyproject.toml                   # [Abhishek + Mrityunjay] Editable packages (task_factory*, backend*), ruff, pytest
├── docker-compose.yml               # [Abhishek] Standardized execution container
├── .github/workflows/ci.yml         # [Abhishek] PR CI (ruff + pytest + frontend build)
│
├── docs/                            # [Abhishek + All] Planning & submission docs
│
├── task_factory/                    # Core CLI + Reusable Pipeline Engine
│   ├── __init__.py
│   ├── __main__.py                  # [Mrityunjay] Enables `python -m task_factory`
│   ├── cli.py                       # [Mrityunjay] Typer/Click/argparse CLI (`generate`, `validate`, `mutate`)
│   ├── config.py                    # [Abhishek] Settings, env vars, pinned repo URL & base_commit
│   ├── schemas.py                   # [Abhishek] Shared Pydantic contracts (FeatureBlueprint, SynthesizedTask, PrecheckResult, ValidationOutcome)
│   ├── repo_analyzer.py             # [Alok] Clone/checkout, AST module/class map, pytest collection
│   ├── variation_engine.py          # [Alok] 5-axis feature ideation, upstream guard, dedup filter
│   ├── synthesizer.py               # [Alok] instruction.md, solution.patch, test_feature.py, self-repair
│   ├── sandbox_precheck.py          # [Mrityunjay] Fast local git worktree + venv pytest pre-validator
│   ├── harbor_writer.py             # [Abhishek] Generates task.toml, Dockerfile, solve.sh, test.sh, JSONs
│   ├── harbor_runner.py             # [Abhishek] Invokes `harbor run -a nop` / `-a oracle`, parses rewards
│   └── mutation_tester.py           # [Abhishek] Applies broken mutants & checks reward < 1.0
│
├── backend/                         # [Mrityunjay] FastAPI Control Room Server
│   ├── main.py                      # FastAPI routes + SSE log streaming
│   ├── models.py                    # SQLAlchemy ORM tables (runs, tasks, validations)
│   ├── database.py                  # SQLite session setup
│   └── service.py                   # Background pipeline runner bridging FastAPI -> task_factory
│
├── frontend/                        # [Subhasree] React + TypeScript + Tailwind Studio UI
│   ├── package.json
│   └── src/
│       ├── api/                     # Typed fetch/SSE client matching Section 5 contracts
│       ├── components/              # PipelineStepper, VariationTable, DiffInspector, RewardMatrix
│       └── pages/                   # Dashboard, TaskDetailPage
│
├── artifacts/                       # Generated output (curated sample tasks + evidence logs)
│   ├── tasks/                       # Inspectable Harbor task folders
│   └── validation_evidence/         # nop/oracle logs, reward JSONs, mutation reports
└── tests/                           # Unit & integration tests for task_factory & backend
```

> **Rule:** Never edit files outside your module without posting in team chat / raising a small separate PR. Shared contract changes (`task_factory/schemas.py` and API routes) must be announced immediately.

---

## 3. Day-1 Environment Setup & Verification Checklist

Run these steps **before** writing pipeline code so everyone works against identical Harbor & `pallets/click` baselines:

```bash
# 1. Verify system tools
docker --version
docker info                          # Docker daemon MUST be running
git --version
python --version                     # 3.11+

# 2. Create venv and install Harbor 0.25.x + core deps
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install --upgrade pip
pip install "harbor==0.25.*"

# 3. Verify Harbor CLI & inspect exact 0.25.x task schema
harbor --version
harbor task init _tmp_harbor_check
# Inspect _tmp_harbor_check/task.toml, instruction.md, solution/solve.sh, tests/test.sh
# Record any exact field differences in docs/TASK_INTERFACE.md, then remove _tmp_harbor_check

# 4. Pin pallets/click stable release commit & verify baseline pytest passes
git clone https://github.com/pallets/click.git _tmp_click
cd _tmp_click
git tag --sort=-v:refname | head -n 10
git checkout <CHOSEN_STABLE_TAG>
git rev-parse HEAD                   # Copy exact 40-char SHA into task_factory/config.py!
pip install -e . pytest
pytest                               # Must pass 100% cleanly before starting!
```

---

## 4. Internal Data Contracts (`task_factory/schemas.py`)

Abhishek locks these Pydantic models on Day 1 so Alok, Mrityunjay, and Subhasree can develop in parallel:

```python
class FeatureBlueprint(BaseModel):
    task_id: str                     # e.g. "click-01-envvar-prefix-map"
    axis: Literal[
        "parameter-validation",
        "command-routing",
        "formatting-termui",
        "context-envvar",
        "testing-completion",
    ]
    title: str
    summary: str
    target_files: list[str]
    target_symbols: list[str]
    difficulty: Literal["easy", "medium", "hard"]
    acceptance_criteria: list[str]
    non_goals: list[str]

class SynthesizedTask(BaseModel):
    blueprint: FeatureBlueprint
    instruction_md: str              # Strict agent-facing spec (no patch/test leaks)
    solution_patch: str              # Unified git diff
    feature_test_filename: str       # e.g. "tests/test_feature_envvar_prefix.py"
    feature_test_code: str
    fail_to_pass: list[str]          # Pytest node IDs
    pass_to_pass: list[str]          # Baseline regression node IDs
    repair_attempts: int = 0

class ValidationOutcome(BaseModel):
    task_id: str
    mode: Literal["stage1_base", "stage1_oracle", "harbor_nop", "harbor_oracle", "mutant"]
    reward: float | None             # None means environment crash
    passed_feature: int
    total_feature: int
    passed_regression: int
    total_regression: int
    duration_sec: float
    log_path: str

class PrecheckResult(BaseModel):
    task_id: str
    patch_applies: bool
    fail_to_pass: list[str]          # Collected deterministically via pytest --collect-only
    base_feature_failed: bool        # True when all fail_to_pass tests fail on unpatched base_commit
    oracle_passed: bool              # True when all fail_to_pass + pass_to_pass pass after patch
    error_summary: str = ""          # Truncated pytest/git stderr fed into Alok's self-repair loop
```

### Canonical Config & Module Boundaries
- **Central Env Vars (`task_factory/config.py`):** `CLICK_REPO_URL` (default `https://github.com/pallets/click.git`), `CLICK_BASE_COMMIT` (pinned 40-char SHA), `LLM_PROVIDER` (`gemini|openai`), `LLM_MODEL`, `GEMINI_API_KEY` / `OPENAI_API_KEY`, `ARTIFACTS_DIR` (default `artifacts`), `DB_PATH` (default `artifacts/factory.db`), `HARBOR_TIMEOUT_SEC` (default `300`).
- **Pipeline Handshake:**
  1. `repo_analyzer.analyze_repo(...)` returns AST summary + baseline `pass_to_pass` node IDs.
  2. `variation_engine.propose_blueprints(...)` returns `list[FeatureBlueprint]`.
  3. `synthesizer.synthesize_task(...)` generates `instruction_md`, `solution_patch`, `feature_test_code` and calls `sandbox_precheck.verify_in_worktree(...) -> PrecheckResult` during self-repair (up to 3 retries), returning `SynthesizedTask` with `fail_to_pass` collected from `PrecheckResult`.
  4. `harbor_writer.write_task_package(task: SynthesizedTask, ...)` writes `artifacts/tasks/<task_id>/`.
  5. `harbor_runner.run_harbor_validation(task_dir, ...)` executes `nop` and `oracle` and returns `list[ValidationOutcome]`.
- **Packaging & CORS:** Configure `pyproject.toml` (`[tool.setuptools.packages.find]` including `task_factory*` and `backend*`) so `pip install -e .` resolves imports cleanly across CLI, `backend/`, and `tests/`. Enable FastAPI `CORSMiddleware` for `http://localhost:5173` during local Vite dev.

---

## 5. Backend $\leftrightarrow$ Frontend API Contract (For Subhasree & Mrityunjay)

Subhasree can mock the frontend on Day 1 using these exact payloads while Mrityunjay builds `backend/main.py`:

- **`POST /api/runs`**
  - Request: `{"repo": "pallets/click", "base_commit": "<40-char-sha>", "count": 5, "axes": ["parameter-validation", "command-routing", "formatting-termui", "context-envvar", "testing-completion"], "run_harbor": true, "run_mutations": false}` *(Note: `axes` is optional, defaulting to all 5; `run_mutations` is `[P1]`)*
  - Response: `{"run_id": "run_20261125_01", "status": "queued"}`
- **`GET /api/runs/{run_id}`**
  - Response: `{"run_id": "...", "repo": "pallets/click", "base_commit": "...", "status": "queued|running|completed|failed", "tasks_generated": 5, "created_at": "...", "completed_at": null}`
- **`GET /api/runs/{run_id}/events`** (SSE `text/event-stream`)
  - Events: `{"stage": "analyze|ideate|synthesize|precheck|harbor_nop|harbor_oracle|mutate", "task_id": "...", "message": "...", "timestamp": "..."}`
- **`GET /api/tasks`**
  - Response: List of task summaries (`task_id`, `axis`, `title`, `difficulty`, `repair_attempts`, `nop_reward`, `oracle_reward`, `mutation_killed`, `mutation_total`).
- **`GET /api/tasks/{task_id}`**
  - Response: Full inspector payload (`task_toml`, `instruction_md`, `solution_patch`, `feature_test_code`, `fail_to_pass`, `pass_to_pass`, `validations[]`, `package_path`).
- **`POST /api/tasks/{task_id}/validate`**
  - Triggers Harbor `nop` + `oracle` checks; returns `list[ValidationOutcome]`.
- **`POST /api/tasks/{task_id}/mutate`** **`[P1]`**
  - Triggers AST mutation checks; returns `list[ValidationOutcome]`.
- **`GET /api/tasks/{task_id}/export`**
  - Returns zipped Harbor task directory (`application/zip`, `<task_id>.zip`).

---

## 6. Critical Coding Standards & Pitfalls

1. **No Secrets in Git:** Never commit `.env` or API keys. Read `GEMINI_API_KEY` / `OPENAI_API_KEY` strictly via environment variables (`os.environ`).
2. **Always Force `LF` (`\n`) on Shell Scripts & Patches:** When writing `solve.sh`, `test.sh`, and `.patch` files in Python on Windows, always pass `encoding="utf-8", newline="\n"`.
3. **Never Leak Tests or Solutions:** `harbor_writer.py` must verify that `environment/Dockerfile` contains zero references to `solution/` or `tests/`, and `instruction.md` passes an automated leak check (no `test_feature`, `fail_to_pass`, or raw patch diff markers).
4. **Prompt & Patch Grounding:** Always pass exact file contents and line context of `src/click/*.py` from `base_commit` before asking the LLM to produce a unified diff (or generate full updated file content in Python and compute `difflib.unified_diff` / `git diff` deterministically — **generating whole modified target snippets or AST edits and computing `git diff` via GitPython avoids 90% of broken LLM line-number patch errors!**).
5. **Deterministic Test Collection:** Always collect `fail_to_pass` node IDs directly by running `pytest --collect-only -q <feature_test_file>` rather than letting the LLM guess node IDs.
