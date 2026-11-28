# Implementation Guide (`IMPLEMENTATION.md`) — v2

Defines the tech stack, repository layout and ownership, environment setup, **frozen data contracts**, module function signatures, configuration, API contract, and engineering standards. Architecture rationale lives in [`architecture.md`](./architecture.md); the Harbor package format lives in [`TASK_INTERFACE.md`](./TASK_INTERFACE.md).

> **Contract freeze:** Sections 4 and 5 are frozen once Abhishek merges `task_factory/schemas.py` (target **27 Nov, 18:00 IST**). Changes after that need an announced PR from Abhishek. **Additive** fields with defaults are allowed by announcement; renames/removals are not.

---

## 1. Tech Stack & Dependencies

| Layer | Technology | Notes |
| :--- | :--- | :--- |
| Language & packaging | Python `3.11+`, single `pyproject.toml`, `pip install -e ".[dev]"` | `task_factory` + `backend` in one project |
| Harbor evaluation | `harbor==0.25.*` installed as an **isolated tool** (`pipx install "harbor==0.25.*"` or `uv tool install`) + Docker Engine/Desktop | Invoked as a CLI subprocess (ADR-12); exact version recorded in `environment.json` |
| Stage 1 sandbox | Docker (`docker run --network none`), image built from the Harbor Dockerfile template | ADR-01 |
| LLM client | **One** provider SDK behind `task_factory/llm_client.py` | **Decision D1 (provisional, 28 Nov):** `google-genai` with default model `gemini-2.5-flash` (env-configurable; final model name confirmed by Alok). Implement that one + a `FakeLLM` for tests. Do not add multiple SDKs. |
| Git & analysis | `GitPython` (or `git` subprocess), stdlib `ast`, `difflib` | Worktrees, diffs, AST symbol map |
| Backend | `fastapi`, `uvicorn`, `pydantic>=2`, `sqlalchemy>=2` (SQLite, WAL) | SSE via `StreamingResponse` (no extra lib) |
| Frontend | React 18 + Vite + TypeScript + Tailwind + `react-diff-viewer-continued` | Talks only to the backend contract (Section 5) |
| Quality | `pytest`, `ruff`, GitHub Actions | CI: ruff + unit tests + frontend build |

---

## 2. Repository Structure & File Ownership

```text
innodata-coding-task-factory/
├── AGENTS.md                         # [Abhishek] Agent & engineering rules
├── README.md                         # [Abhishek] Overview + judge quickstart
├── .gitignore / .gitattributes       # [Abhishek] Ignore rules / LF enforcement (architecture §13)
├── .env.example                      # [Abhishek] All env vars from §4.2 with safe defaults
├── pyproject.toml                    # [Abhishek] deps, ruff, pytest config (others request changes via PR comment)
├── docker-compose.yml                # [Abhishek] Judge execution container (path-parity mount)
├── .github/workflows/ci.yml          # [Abhishek]
├── docs/                             # [Abhishek] Contracts & plans (others propose edits via PR)
│
├── task_factory/
│   ├── __init__.py                   # [Abhishek] version string only
│   ├── __main__.py                   # [Mrityunjay] `python -m task_factory`
│   ├── cli.py                        # [Mrityunjay] doctor | analyze | generate | validate | mutate | report
│   ├── pipeline.py                   # [Mrityunjay] Orchestrator shared by CLI + backend (ADR-06)
│   ├── sandbox_precheck.py           # [Mrityunjay] Worktrees, sandbox image, Stage 1, baseline
│   ├── config.py                     # [Abhishek] Settings (only place that reads os.environ)
│   ├── schemas.py                    # [Abhishek] Frozen Pydantic contracts (§4.1)
│   ├── errors.py                     # [Abhishek] Exception hierarchy (architecture §10)
│   ├── harbor_writer.py              # [Abhishek] Render/validate packages, write_text_lf
│   ├── harbor_runner.py              # [Abhishek] harbor run nop/oracle/mutant + evidence
│   ├── mutation_tester.py            # [Abhishek] (P1) mutants + kill rate
│   ├── templates/harbor/             # [Abhishek] Dockerfile, solve.sh, test.sh, reward_plugin.py, compute_reward.py, task.toml
│   ├── llm_client.py                 # [Alok] Provider wrapper + record/replay cache + FakeLLM
│   ├── prompts/                      # [Alok] Versioned prompt templates (*.md / *.txt)
│   ├── repo_analyzer.py              # [Alok] Mirror, AST map, upstream feature index
│   ├── variation_engine.py           # [Alok] Blueprints + scope/novelty/diversity guards
│   └── synthesizer.py                # [Alok] instruction/patch/tests + self-repair + spec–test check
│
├── backend/                          # [Mrityunjay]
│   ├── main.py                       # App factory, routes, CORS, error handlers
│   ├── models.py / database.py       # SQLAlchemy tables (§4.3), SQLite WAL session
│   └── service.py                    # Background run worker, event → DB/SSE bridge
│
├── frontend/                         # [Subhasree] (current layout: src/features, src/services, src/types)
│
├── tests/                            # Unit/integration tests — file owned by the module's owner
│   ├── conftest.py                   # [Abhishek] shared fixtures (tmp mirror, FakeLLM factory)
│   ├── fixtures/                     # [Abhishek] sample_task/click-00-manual-sample + regenerate_sample_task.py
│   └── test_<module>.py              # e.g. test_synthesizer.py → Alok, test_pipeline.py → Mrityunjay
│
├── artifacts/                        # [Abhishek] curated outputs (committed)
│   ├── upstream/CHANGES.md           # Upstream click changelog snapshot (novelty-vs-upstream guard)
│   ├── tasks/<task_id>/              # Final Harbor packages
│   ├── validation_evidence/          # Evidence bundle (TASK_INTERFACE §5)
│   ├── llm_cache/                    # Recorded LLM I/O of the final run (replay)
│   ├── runs/                         # gitignored (final run's events copied into evidence)
│   └── harbor_runs/                  # gitignored raw Harbor output
└── .cache/                           # gitignored: click mirror, worktrees, mutants, upstream snapshot
```

**`.gitignore` must include:** `.venv/`, `.env`, `__pycache__/`, `*.pyc`, `*.db`, `.cache/`, `_tmp_*/`, `artifacts/runs/`, `artifacts/harbor_runs/`, `node_modules/`, `frontend/dist/`, `.pytest_cache/`, `.ruff_cache/`.

---

## 3. Environment Setup (every member, Day 1)

```bash
# 1. Tools
docker --version && docker info        # daemon running
git --version
python --version                       # 3.11+
git config --global core.longpaths true   # Windows: deep worktree paths

# 2. Project env
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   |   Linux/macOS/WSL: source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env                   # fill LLM key (Alok/Abhishek); others can use LLM_MODE=replay

# 3. Harbor (isolated)
pipx install "harbor==0.25.*"          # or: uv tool install "harbor==0.25.*"
harbor --version

# 4. Factory self-check (after Mrityunjay's doctor lands)
python -m task_factory doctor
```

**Windows notes:** Stage 2 evidence runs happen on **WSL2/Linux** (architecture §6). After `.gitattributes` lands, run `git add --renormalize .` once (Abhishek) and re-clone or `git checkout` on other machines.

**Pinning the click commit (Abhishek, 27 Nov):**
```bash
git clone -c core.autocrlf=false https://github.com/pallets/click.git _tmp_click && cd _tmp_click
git tag --sort=-v:refname | head -n 10
git checkout <STABLE_TAG> && git rev-parse HEAD   # → CLICK_BASE_COMMIT in config.py + .env.example
```
Then build the sandbox image and confirm the baseline is 100% green **inside Linux** (not on the Windows host) before announcing the SHA.

---

## 4. Internal Contracts

### 4.1 `task_factory/schemas.py` (frozen)

```python
from datetime import datetime
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, Field

SHA_PATTERN = r"^[0-9a-f]{40}$"
TASK_ID_PATTERN = r"^click-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$"          # ≤ 64 chars (ADR-10)
FEATURE_TEST_PATTERN = r"^tests/test_feature_[a-z0-9_]+\.py$"

AxisSlug = Literal["parameter-validation", "command-routing", "formatting-termui",
                   "context-envvar", "testing-completion"]
ALL_AXES: tuple[AxisSlug, ...] = ("parameter-validation", "command-routing", "formatting-termui",
                                  "context-envvar", "testing-completion")
Difficulty = Literal["easy", "medium", "hard"]
PipelineStage = Literal["run", "analyze", "baseline", "ideate", "synthesize", "precheck",
                        "package", "harbor_nop", "harbor_oracle", "mutate"]
ValidationMode = Literal["stage1_base", "stage1_oracle", "harbor_nop", "harbor_oracle", "mutant"]
LLMMode = Literal["live", "record", "replay"]


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
    run_mutations: bool = False                 # P1
    llm_mode: LLMMode = "live"
    resume_run_id: str | None = None


class SymbolInfo(BaseModel):
    qualname: str                               # e.g. "click.core.Context.lookup_default"
    kind: Literal["module", "class", "function", "method"]
    file: str                                   # repo-relative, e.g. "src/click/core.py"
    lineno: int
    signature: str = ""
    doc_head: str = ""                          # first docstring line


class RepoSnapshot(BaseModel):
    base_commit: str = Field(pattern=SHA_PATTERN)
    mirror_path: str
    source_files: list[str]                     # src/click/*.py
    symbols: list[SymbolInfo]
    test_files: list[str]
    upstream_features: list[str] = []           # feature lines from newer upstream CHANGES.md


class BaselineResult(BaseModel):
    base_commit: str = Field(pattern=SHA_PATTERN)
    pass_to_pass: list[str]                     # stable passes across all runs (ADR-09)
    excluded: dict[str, str] = {}               # nodeid -> "skipped" | "flaky" | "failed"
    runs: int = 3
    duration_sec: float


class FeatureBlueprint(BaseModel):
    task_id: str = Field(pattern=TASK_ID_PATTERN, max_length=64)
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
    source_files: dict[str, str]                # repo-relative path under src/click/ -> full new content
    feature_test_filename: str = Field(pattern=FEATURE_TEST_PATTERN)
    feature_test_code: str


class VerifierSummary(BaseModel):               # mirrors tests/verifier/compute_reward.py output
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
    solution_patch: str = ""                    # git diff of src/click from the worktree
    fail_to_pass: list[str]                     # collected via pytest --collect-only in sandbox
    base_summary: VerifierSummary | None = None
    oracle_summary: VerifierSummary | None = None
    full_suite: bool = False
    base_feature_failed: bool                   # all f2p fail on base, status ok, p2p green
    oracle_passed: bool                         # oracle reward == 1.0, status ok
    error_summary: str = ""                     # truncated (≤ 4 KB) log fed to self-repair
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
    reward: float | None                        # None = test.sh never wrote reward.txt (crash)
    passed_feature: int
    total_feature: int
    passed_regression: int
    total_regression: int
    duration_sec: float
    log_path: str
    accepted: bool = False                      # acceptance rule from TASK_INTERFACE §3
    status: Literal["ok", "error"] | None = None
    mutant_id: str | None = None


class MutantSpec(BaseModel):                    # P1
    mutant_id: str                              # e.g. "m01"
    operator: Literal["negate_condition", "drop_raise", "early_return", "off_by_one",
                      "swap_comparison", "drop_call"]
    file: str
    line: int
    description: str
    patch: str


class RunEvent(BaseModel):
    seq: int                                    # monotonically increasing per run (SSE id)
    run_id: str
    stage: PipelineStage
    task_id: str | None = None                  # None for run-level events
    level: Literal["info", "warn", "error"] = "info"
    message: str
    timestamp: datetime
    data: dict = {}                             # small structured payload (e.g. reward, attempt)


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
    run_id: str                                 # "run_YYYYMMDD_HHMMSS"
    status: Literal["completed", "failed"]
    config: RunConfig
    tasks: list[TaskRecord]
    started_at: datetime
    finished_at: datetime
    summary_path: str | None = None
```

### 4.2 Configuration (`task_factory/config.py` — the only module reading `os.environ`)

| Env var | Default | Used by |
| :--- | :--- | :--- |
| `CLICK_REPO_URL` | `https://github.com/pallets/click.git` | analyzer, writer |
| `CLICK_BASE_COMMIT` | `cf19179e8e2fd54c601378cec9e0d21bb12b6fb1` | all |
| `CLICK_RELEASE_TAG` | `8.5.1` | docs/evidence |
| `PYTEST_PIN` | `9.0.2` (from click 8.5.1 `uv.lock`) | writer (Dockerfile) |
| `UPSTREAM_CHANGES_PATH` | `artifacts/upstream/CHANGES.md` (fallback: a cached copy under `CACHE_DIR`) | analyzer (upstream guard) |
| `LLM_PROVIDER` / `LLM_MODEL` | `google-genai` / `gemini-2.5-flash` (D1, provisional) | llm_client |
| `LLM_API_KEY` | — (never logged) | llm_client |
| `LLM_MODE` | `live` | llm_client (`live`/`record`/`replay`) |
| `LLM_TEMPERATURE` | `0` | llm_client |
| `LLM_TIMEOUT_SEC` / `LLM_MAX_RETRIES` / `LLM_MAX_PARALLEL` | `120` / `3` / `3` | llm_client |
| `LLM_CACHE_DIR` | `artifacts/llm_cache` | llm_client |
| `ARTIFACTS_DIR` | `artifacts` | all |
| `CACHE_DIR` | `.cache` | analyzer, sandbox, mutation |
| `DB_PATH` | `artifacts/factory.db` | backend |
| `SANDBOX_IMAGE_PREFIX` | `click-sandbox` | sandbox |
| `SANDBOX_MAX_PARALLEL` / `SANDBOX_TIMEOUT_SEC` | `3` / `300` | sandbox |
| `MAX_REPAIR_ATTEMPTS` | `3` | synthesizer |
| `HARBOR_BIN` | `harbor` | runner |
| `HARBOR_TIMEOUT_SEC` / `HARBOR_MAX_PARALLEL` | `900` / `2` | runner |
| `CORS_ORIGINS` | `http://localhost:5173` | backend |
| `LOG_LEVEL` | `INFO` | all |

Exposed as a frozen Pydantic `Settings` object (`model_config = ConfigDict(frozen=True, extra="forbid")`) via `get_settings()` (`@lru_cache`; tests call `get_settings.cache_clear()`). No `pydantic-settings` dependency.

- **Field names** are the lower-case env var names: `click_repo_url`, `click_base_commit`, `click_release_tag`, `pytest_pin`, `upstream_changes_path`, `llm_provider`, `llm_model`, `llm_api_key`, `llm_mode`, `llm_temperature`, `llm_timeout_sec`, `llm_max_retries`, `llm_max_parallel`, `llm_cache_dir`, `artifacts_dir`, `cache_dir`, `db_path`, `sandbox_image_prefix`, `sandbox_max_parallel`, `sandbox_timeout_sec`, `max_repair_attempts`, `harbor_bin`, `harbor_timeout_sec`, `harbor_max_parallel`, `cors_origins` (comma-separated in env), `log_level`.
- `llm_api_key: SecretStr | None = None` — never printed; the LLM client reads it with `settings.require_llm_api_key()` (raises `ConfigError` when unset). `settings.sandbox_image` derives `click-sandbox:<sha12>`.
- **Resolution order:** process env > `.env` in the working directory > defaults. Empty values count as unset. Invalid values raise `ConfigError` listing field names only (input values are never echoed).
- `config.py` is the only module that reads `os.environ`. Modules never call `os.getenv`.

### 4.3 SQLite Tables (`backend/models.py`) — index over `artifacts/`, rebuildable
- **`runs`**: `id` (PK, run_id), `repo`, `base_commit`, `target_count`, `status` (`queued|running|completed|failed`), `llm_mode`, `model_used`, `error`, `created_at`, `completed_at`
- **`tasks`**: `id` (PK, task_id), `run_id` (FK), `axis`, `title`, `difficulty`, `status` (TaskStatus), `target_files_json`, `fail_to_pass_count`, `pass_to_pass_count`, `repair_attempts`, `package_path`, `reject_reason`
- **`validations`**: `id`, `task_id` (FK), `mode` (ValidationMode), `mutant_id`, `reward` (nullable), `status`, `accepted`, `passed_feature`, `total_feature`, `passed_regression`, `total_regression`, `duration_sec`, `log_path`, `created_at`

### 4.4 Module Function Signatures (pipeline handshake)

```python
# llm_client.py (Alok)
class LLMClient:
    def complete_json(self, *, system: str, user: str, schema: type[T], purpose: str) -> T: ...
def get_llm_client(mode: LLMMode | None = None) -> LLMClient          # FakeLLM in tests

# repo_analyzer.py (Alok)
def ensure_mirror() -> Path                                             # clone/verify .cache/click-mirror
def analyze_repo(mirror: Path, base_commit: str) -> RepoSnapshot        # raises RepoStateError

# sandbox_precheck.py (Mrityunjay)
def ensure_sandbox_image(base_commit: str) -> str                       # returns image tag
def collect_baseline(mirror: Path, base_commit: str, runs: int = 3) -> BaselineResult
def verify_in_worktree(task_id: str, attempt: int, candidate: CandidateFiles,
                       baseline: BaselineResult, *, full_suite: bool) -> PrecheckResult  # never raises on test failure

# variation_engine.py (Alok)
def propose_blueprints(snapshot: RepoSnapshot, axes: list[AxisSlug], count: int,
                       llm: LLMClient) -> tuple[list[FeatureBlueprint], list[RejectedBlueprint]]

# synthesizer.py (Alok)
def synthesize_task(blueprint: FeatureBlueprint, snapshot: RepoSnapshot, baseline: BaselineResult,
                    llm: LLMClient, emit: Callable[[str, str], None]) -> SynthesizedTask  # raises PrecheckFailed
#   emit(level, message): level is "info" | "warn" | "error"; pipeline.py wraps it into a RunEvent
#   (stage="synthesize"/"precheck", task_id=blueprint.task_id).

# harbor_writer.py (Abhishek)
def write_text_lf(path: Path, text: str) -> None
def render_dockerfile(base_commit: str, *, pytest_pin: str | None = None) -> str   # pin defaults to settings.pytest_pin
def render_task_toml(task_id: str, *, axis: str, difficulty: str, base_commit: str) -> str
def render_solve_sh() -> str
def render_verifier_files() -> dict[str, str]                           # test.sh + verifier/*.py (used by sandbox too)
def write_task_package(task: SynthesizedTask, out_dir: Path, *, base_commit: str | None = None,
                       overwrite: bool = False) -> Path                 # stages, validates, then moves into place
def validate_package(task_dir: Path, *, base_commit: str | None = None,
                     pass_to_pass: list[str] | None = None,           # run baseline -> equality check
                     apply_check_repo: Path | None = None) -> None    # clean checkout -> git apply --check
                                                                        # raises LeakageDetected / ScopeViolation (all issues in .issues)

# harbor_runner.py (Abhishek)
def validate_task(task_dir: Path, run_id: str,
                  modes: tuple[ValidationMode, ...] = ("harbor_nop", "harbor_oracle")) -> list[ValidationOutcome]
def write_evidence_summary(result: RunResult) -> Path

# mutation_tester.py (Abhishek, P1)
def run_mutations(task_dir: Path, run_id: str, max_mutants: int = 3) -> list[ValidationOutcome]

# pipeline.py (Mrityunjay)
def run_pipeline(cfg: RunConfig, on_event: Callable[[RunEvent], None] | None = None) -> RunResult
def validate_existing(tasks_dir: Path, on_event: ... = None) -> list[ValidationOutcome]   # judge path B
```

**Unblocking rule:** each owner lands a **stub** with the final signature (returning fixture data) on Day 1–2, so dependents integrate immediately and swap in the real implementation later.

---

## 5. Backend ↔ Frontend API Contract (v2, backward compatible with v1)

Error body for all non-2xx: `{"error": {"type": "<ExceptionClass>", "message": "..."}}`.

| Method & path | Request | Response | Notes |
| :--- | :--- | :--- | :--- |
| `GET /api/health` | — | `{"status":"ok","docker":true,"harbor_version":"0.25.x","base_commit":"…"}` | Used by UI banner |
| `POST /api/runs` | `{"repo","base_commit","count" (1–15),"axes"?,"run_harbor","run_mutations"?}` | `202 {"run_id":"run_20261127_101500","status":"queued"}` | `409` if a run is active, `400` on invalid input |
| `GET /api/runs` | — | `RunSummary[]` (newest first) | new in v2 |
| `GET /api/runs/{run_id}` | — | `{"run_id","repo","base_commit","status","tasks_generated","tasks_accepted","tasks_rejected","error","created_at","completed_at"}` | `tasks_accepted/rejected/error` additive |
| `GET /api/runs/{run_id}/events` | header `Last-Event-ID`? | SSE stream: `id: <seq>` + `data: <RunEvent JSON>`; default event type (so `EventSource.onmessage` receives all) | Replays from `events.jsonl`; `: ping` every 15 s; final event `stage:"run"`, message `completed`/`failed`, then close |
| `GET /api/tasks?run_id=` | optional filter | `TaskSummary[]`: `task_id, run_id, axis, title, difficulty, target_files, status, repair_attempts, nop_reward, oracle_reward, mutation_killed, mutation_total` | `run_id`, `target_files`, `status` additive |
| `GET /api/tasks/{task_id}` | — | `{task_toml, instruction_md, solution_patch, feature_test_code, fail_to_pass, pass_to_pass, validations[], package_path}` | unchanged |
| `POST /api/tasks/{task_id}/validate` | — | `ValidationOutcome[]` | Synchronous in MVP (can take ~2–5 min; client timeout ≥ 10 min); progress also emitted as events |
| `POST /api/tasks/{task_id}/mutate` **[P1]** | — | `ValidationOutcome[]` (mode `mutant`) | Same semantics as validate |
| `GET /api/tasks/{task_id}/logs/{evidence}` | `evidence` ∈ `stage1_attempt_<n>`, `harbor_nop`, `harbor_oracle`, `mutant_<id>` | `text/plain` (pytest.log, ≤ 2 MB, truncated head+tail) | new in v2 — required for the "raw trial logs" tab |
| `GET /api/tasks/{task_id}/export` | — | `application/zip` `<task_id>.zip` | Package dir only (no evidence) |

`task_id`/`run_id` path params are validated against their regex before touching the filesystem (path-traversal defence).

---

## 6. Engineering Standards & Pitfalls

1. **Secrets:** only via env → `config.py`. Never logged, never in `llm_cache`, never committed.
2. **All generated files through `write_text_lf`** (LF, UTF-8, no BOM). Never write generated files with PowerShell `Set-Content`/`Out-File`.
3. **Fixed templates only** for `.sh`, Dockerfile, `task.toml`, verifier scripts (ADR-05). Interpolate only regex-validated values.
4. **Whole-file edits → `git diff`** for patches; give the LLM exact file contents from the mirror at `base_commit` (ADR-04).
5. **Node IDs are collected, never generated** (`pytest --collect-only -q` in the sandbox).
6. **Subprocess:** list args, `shell=False`, explicit `timeout=`, capture output, kill container on timeout.
7. **No LLM-generated code on the host.** Anything importing or executing candidate code runs in the sandbox.
8. **Typed errors** from `errors.py`; task-level errors reject the task, run-level errors fail the run; every caught error becomes a `RunEvent`.
9. **Determinism:** temperature 0, sorted JSON output, stable ordering of tasks, recorded LLM I/O.
10. **Scratch Git operations** (`worktree add/remove`, `checkout`, `clean`) are allowed **only** inside `.cache/` and `_tmp_*` — never on the project repo.

### 6.1 `pyproject.toml` essentials (Abhishek)
```toml
[project]
name = "innodata-task-factory"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.6", "GitPython>=3.1", "fastapi>=0.110", "uvicorn[standard]>=0.29",
                "sqlalchemy>=2.0", "<LLM SDK per D1>"]
[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.5", "httpx>=0.27"]
[project.scripts]
task-factory = "task_factory.cli:main"

[tool.setuptools.packages.find]
include = ["task_factory*", "backend*"]
[tool.setuptools.package-data]
task_factory = ["templates/harbor/*", "prompts/*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
norecursedirs = ["artifacts", ".cache", "_tmp_*", "frontend", "node_modules", "fixtures", ".venv"]
markers = ["docker: needs a Docker daemon", "harbor: needs harbor CLI", "llm: needs a live LLM key"]
addopts = "-m 'not docker and not harbor and not llm'"

[tool.ruff]
line-length = 100
target-version = "py311"
```
`norecursedirs` matters: without it, root `pytest` collects `artifacts/tasks/*/tests/test_feature_*.py` and `tests/fixtures/sample_task/**/test_feature_*.py`, which use features that do not exist → CI red.

---

## 7. Testing Strategy

| Level | What | Where | Runs in CI |
| :--- | :--- | :--- | :---: |
| Unit | Pure logic: schemas, guards, leak checks, patch path checks, reward calculation (`compute_reward.py` with temp dirs), event serialization | `tests/test_<module>.py` | ✅ |
| Contract | `FakeLLM` returns fixture blueprints/files; pipeline runs with stubbed sandbox/harbor | `tests/test_pipeline.py` | ✅ |
| API | FastAPI `TestClient` with stubbed pipeline (status codes, 409, SSE framing, path validation) | `tests/test_backend_*.py` | ✅ |
| Sandbox integration | Real Docker: baseline collection, base/oracle run of `tests/fixtures/sample_task` | `@pytest.mark.docker` | ❌ (local) |
| Harbor integration | Real `harbor run` nop/oracle of the fixture task | `@pytest.mark.harbor` | ❌ (local/WSL) |
| Live LLM smoke | One blueprint + one synthesis round-trip | `@pytest.mark.llm` | ❌ |

Run integration tests with `pytest -m docker` / `pytest -m harbor`.

---

## 8. Definition of Done (every PR)

- [ ] Only owned files touched (or cross-owner change approved in chat and noted in PR).
- [ ] Matches §4/§5 contracts exactly; no new env var outside `config.py`.
- [ ] `ruff check .` and `pytest` green locally; `npm run build` for frontend PRs.
- [ ] New logic has unit tests, including at least one failure/edge case.
- [ ] No `\r`/BOM in generated files; no secrets; no LLM code executed on host.
- [ ] PR description: what works, how it was tested (exact commands), what is stubbed.
