# AGENTS.md — Central Engineering & Multi-Agent Workflow Rules

This file is the authoritative engineering rulebook for all AI coding agents (including Antigravity) and developers working in `innodata-coding-task-factory`. Keep this file concise and aligned with `docs/`.

---

## A. Project Context

- **What We Are Building:** An automated, repeatable **Coding Task Factory** for **Innodata AI Hackathon 2026 (Track 1)** that analyzes a pinned clean commit of **`pallets/click`**, generates **5+ substantively different feature-development task packages** in **Harbor `0.25.x`** format, validates them via fast local worktrees and official Harbor Docker runs (`nop` = `0.0`, `oracle` = `1.0`), and exposes live execution and evidence inspection through a CLI + Control Room UI.
- **Why & Target Outcome:** Replace hand-crafted coding benchmarks with a judge-reproducible pipeline producing inspectable task packages, automated `nop`/`oracle` validation logs, mutation test evidence, and a technical walkthrough.
- **Target Users:** AI evaluation benchmarks, Hackathon judges running the pipeline inside a standardized Docker environment, and our 4-member team demoing end-to-end task generation and verification.
- **Mandatory Hackathon Constraints:**
  1. Target repository is strictly **`pallets/click`** (arbitrary repos and Django/Flask/FastAPI/React/Java/Kotlin targets are forbidden).
  2. Every task starts from one pinned, clean 40-character **`base_commit`** where 100% of existing `pytest` tests pass.
  3. Tasks must introduce **new features or intentional behaviour changes** not already present upstream; **bug-fix tasks are out of scope**.
  4. Minimum **5 substantively different tasks** differing in behaviour, rules, or component interactions (not rewording or renaming).
  5. Strict **Harbor `0.25.x`** package structure (`task.toml`, `instruction.md`, `environment/Dockerfile`, `solution/solve.sh`, `tests/test.sh`, `tests/fail_to_pass.json`, `tests/pass_to_pass.json`) with `nop` reward `0.0` and `oracle` reward `1.0`.
  6. No external network calls or real credentials inside generated tasks or tests; declare all models/tools used in `docs/TECHNICAL_EXPLANATION.md`.
- **Approved Tech Stack & Architecture:**
  - **Core Engine (`task_factory/`):** Python 3.11+, `pydantic>=2`, `GitPython`, Python `ast`, `pytest`, `harbor==0.25.*`, Docker, unified LLM client (`google-genai` / `openai` / `litellm`). Must run standalone as a CLI (`python -m task_factory`).
  - **Control Room Backend (`backend/`):** FastAPI, Uvicorn, SQLAlchemy + SQLite, SSE streaming. Wraps `task_factory/` without duplicating pipeline logic.
  - **Control Room UI (`frontend/`):** React 18, Vite, TypeScript, Tailwind CSS. Communicates strictly via `backend/` REST + SSE APIs (no login/auth UI).
  - **Two-Stage Validation:** Stage 1 Git worktree mounted into a `--network none` **Docker sandbox built from the same Harbor Dockerfile and running the same `tests/test.sh`** (LLM self-repair loop) $\rightarrow$ Stage 2 authoritative Docker `harbor run` (`nop` / `oracle`) + P1 mutation testing. See `docs/architecture.md` ADR-01.
  - **Orchestration:** CLI and backend both call `task_factory/pipeline.py`; no other module orchestrates stages.

---

## B. Documentation Reading Rules

Before editing any file or running implementation commands, every agent **MUST**:
1. Read `AGENTS.md` completely.
2. Read the docs relevant to your task:
   - Always check [`docs/TASK_INTERFACE.md`](docs/TASK_INTERFACE.md) and [`docs/architecture.md`](docs/architecture.md) — these are **authoritative** for Harbor contracts, validation reward formulas, and system boundaries.
   - Check [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md) for Python schemas (§4.1), env vars (§4.2), **module function signatures (§4.4)**, API payloads (§5), and file ownership (§2).
   - Check the ADR table (`architecture.md` §14) before proposing a design change, and [`docs/day-wise-plan.md`](docs/day-wise-plan.md) for today's assigned deliverable.
   - Items marked **[VERIFY]** in `TASK_INTERFACE.md` are unconfirmed Harbor behaviour — do not build on them as fact; ask Abhishek for the verified result.
   - Check [`docs/MVP_FEATURES.md`](docs/MVP_FEATURES.md) vs [`docs/goodtohave.md`](docs/goodtohave.md) before starting P1/P2 work.
3. **Never silently change** an agreed schema, API route, enum slug, Harbor file layout, or architecture boundary.
4. **Report conflicts or missing requirements immediately** to the developer instead of guessing or inventing unapproved workarounds.

---

## C. Standard Task Execution Workflow

Follow these 10 steps in order for every assigned task:
1. **Understand Scope:** Restate the assigned task, deliverable, and acceptance criteria.
2. **Inspect Context:** Read relevant code and authoritative docs (`TASK_INTERFACE.md`, `architecture.md`, `IMPLEMENTATION.md`).
3. **Map Dependencies:** Identify upstream/downstream modules, schemas, env vars, or API routes affected.
4. **Plan First:** Formulate a minimal, targeted implementation plan touching only owned files.
5. **Check Team Conflicts:** Verify `git status`, active branch, and whether another member owns adjacent files or shared contracts.
6. **Implement Assigned Scope Only:** Write clean, typed code matching agreed contracts; avoid unrelated edits or speculative features.
7. **Run Tests & Validations:** Execute relevant unit, integration, lint, and (when applicable) Harbor `nop`/`oracle` checks.
8. **Review Implementation:** Inspect `git diff` against edge cases, leakage rules, LF line endings, and coding standards.
9. **Update Documentation:** Update `docs/` only if an approved contract/setup detail changed or `docs/TECHNICAL_EXPLANATION.md` needs recorded evidence.
10. **Deliver Completion Report:** Return the mandatory 8-part completion report (Section H).

---

## D. Coding & Architecture Rules

- **Folder Structure:** Keep standalone pipeline logic in `task_factory/`, HTTP/DB wrappers in `backend/`, React UI in `frontend/`, verification tests in `tests/`, and generated sample tasks/logs in `artifacts/`. Follow the exact module layout in [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md).
- **Naming Conventions:**
  - Python: `snake_case` modules/functions/variables, `PascalCase` classes/Pydantic models, `UPPER_SNAKE_CASE` constants.
  - TypeScript/React: `PascalCase` components/types, `camelCase` functions/props/hooks.
  - Canonical axis slugs: `parameter-validation`, `command-routing`, `formatting-termui`, `context-envvar`, `testing-completion`.
- **Error Handling:** Raise explicit typed exceptions in `task_factory/`; convert them cleanly into HTTP status codes (`400`/`404`/`409`/`500`) in `backend/`. Never swallow failures silently or let `tests/test.sh` crash before writing `/logs/verifier/reward.txt`.
- **Logging:** Use Python `logging` (`task_factory.*` / `backend.*`). Keep CLI stdout clean for structured output or command output; never log secrets or full API keys.
- **Configuration Management:** Centralize all env vars and path defaults in `task_factory/config.py` (never scatter `os.getenv` across modules). Read secrets exclusively from environment variables (`.env` stays untracked).
- **Type Safety & Validation:** Use Pydantic v2 models (`task_factory/schemas.py`) at all pipeline boundaries and FastAPI request/response schemas. Enable TypeScript strict typing in `frontend/src/api/` matching `IMPLEMENTATION.md` Section 5.
- **Reusability & Separation of Concerns:**
  - `backend/` must invoke `task_factory/` functions — never re-implement Git, LLM, or Harbor logic inside FastAPI routes.
  - Keep LLM provider calls behind one thin shared client helper in `task_factory/` rather than duplicating SDK setup per module.
  - Avoid unnecessary abstractions, factories, or over-engineered plugin frameworks beyond the documented Harbor/pipeline modules.
- **API & Interface Consistency:** Request/response payloads, axis slugs, and `task_id` formats must match `IMPLEMENTATION.md` and `TASK_INTERFACE.md` identically.
- **Security & Input Validation:**
  - Validate repo/commit hashes (`40`-char hex SHA), sanitize `task_id` slugs against path traversal (`..`, `/`, `\`), and pass subprocess arguments as lists (`shell=False`) where possible.
  - **Anti-Leakage Rule:** `environment/Dockerfile` must never copy `solution/` or `tests/`. `instruction.md` must never leak test filenames, `fail_to_pass` node IDs, or solution diffs.
  - **Windows-to-Docker Rule:** Write every generated file through `harbor_writer.write_text_lf()` (UTF-8, no BOM, LF only). Never write `.sh`, `.patch`, `.json`, `.toml`, or Dockerfiles with PowerShell `Set-Content`/`Out-File` (they add BOM/CRLF). Clone `pallets/click` with `-c core.autocrlf=false`.
  - **Fixed-Template Rule:** `test.sh`, `solve.sh`, `Dockerfile`, `task.toml`, and `tests/verifier/*.py` come only from `task_factory/templates/harbor/`. LLM output must never be written into these files or into shell commands; interpolate only regex-validated values (SHA, `task_id`, axis).
  - **No-Host-Execution Rule:** LLM-generated code (patches, feature tests) is imported/executed **only** inside the Stage 1 sandbox or Harbor containers, never on a developer machine or CI host.
  - **Patch Scope Rule:** `solution.patch` may touch only `src/click/**`; feature tests live in exactly one `tests/test_feature_<slug>.py`; neither may add `conftest.py` or touch existing tests.
- **Testing & Code Quality:** Run `ruff check` and `pytest` (or `npm run build` / lint in `frontend/`) for every change. Unit tests use `FakeLLM` and stubs; tests needing Docker, Harbor, or a live LLM are marked `@pytest.mark.docker` / `harbor` / `llm` and are excluded from CI. Each module's tests live in `tests/test_<module>.py`, owned by the module's owner. Do not build P1/P2 features from `docs/goodtohave.md` until P0 MVP items in `docs/MVP_FEATURES.md` pass.

---

## E. Multi-Agent Coordination & Ownership

### Team Ownership Boundaries

| Member | Role | Strictly Owned Paths |
| :--- | :--- | :--- |
| **Abhishek Kumar** *(Leader)* | Architecture, Contracts, Harbor Infra, DB/Config, Testing, DevOps, Integration | `AGENTS.md`, `README.md`, `docs/*`, `.gitattributes`, `.gitignore`, `.env.example`, `pyproject.toml`, `docker-compose.yml`, `.github/*`, `task_factory/__init__.py`, `task_factory/config.py`, `task_factory/schemas.py`, `task_factory/errors.py`, `task_factory/harbor_writer.py`, `task_factory/templates/harbor/*`, `task_factory/harbor_runner.py`, `task_factory/mutation_tester.py`, `tests/conftest.py`, `tests/fixtures/*`, `artifacts/*` |
| **Alok Tiwari** | AI Task Generation & Prompt Engineering | `task_factory/llm_client.py`, `task_factory/prompts/*`, `task_factory/repo_analyzer.py`, `task_factory/variation_engine.py`, `task_factory/synthesizer.py` (plus their `tests/test_<module>.py`) |
| **Mrityunjay Pandey** | Backend Orchestration & Sandbox Execution | `task_factory/__main__.py`, `task_factory/cli.py`, `task_factory/pipeline.py`, `task_factory/sandbox_precheck.py`, `backend/*` (plus their `tests/test_<module>.py` / `tests/test_backend_*.py`) |
| **Subhasree Sahu** | Frontend Control Room | `frontend/*` |

### Coordination Rules
1. **Strict Path Isolation:** Agents must **not** edit files outside their assigned developer's ownership without explicit cross-member coordination and approval.
2. **Shared Contract Freeze:** Only Abhishek modifies `task_factory/schemas.py`, `task_factory/config.py`, or `docs/TASK_INTERFACE.md`, and changes must be announced to the team immediately before dependent modules update.
3. **No Duplicate Implementations:** Before creating any helper (Git worktrees, LLM calls, diff parsing, API types), inspect `task_factory/` and `IMPLEMENTATION.md` to reuse existing functions.
4. **Respect In-Progress Work:** Never modify, rebase, or "clean up" another member's branch or unfinished files, and never introduce incompatible libraries into `pyproject.toml` or `frontend/package.json` without coordinator approval.
5. **No Unrequested Refactoring:** Do not rename symbols, reformat untouched files, or refactor modules outside your task.
6. **Branch & Integration Workflow:**
   - Branching model: `docs` $\rightarrow$ `main` $\rightarrow$ `dev` $\rightarrow$ `feat/<member>-<topic>`.
   - Cut short-lived feature branches from `dev` (`feat/alok-...`, `feat/mrityunjay-...`, `feat/subhasree-...`, `feat/abhishek-...`).
   - Merge into `dev` via reviewed PRs after local tests/CI pass; merge `dev` $\rightarrow$ `main` only at stable team milestones.

---

## F. Git Safety Rules

Every agent executing shell or file operations **MUST**:
1. Run `git status` and check the active branch before making any edit.
2. Preserve all existing uncommitted changes (never silently revert or stash-drop them).
3. **Never** run destructive Git commands (`git reset --hard`, `git checkout --`, `git clean -fd`, `git push --force`) on the project repository without explicit developer command. *Scope note:* pipeline code may run `git worktree add/remove`, `checkout`, `apply`, and `clean` **only** inside pipeline-managed scratch clones under `.cache/` or `_tmp_*` — this rule does not forbid implementing that.
4. **Never** overwrite another developer's work or merge/rebase branches unasked.
5. **Never** stage, commit, or push to GitHub unless the assigned developer explicitly instructs you to do so.
6. Run `git diff` and review all modified/untracked files before delivering your final report.

---

## G. Testing & Validation Rules

- **Verify Everything You Claim:** Never state that tests, builds, or Harbor runs passed unless you executed them after your final edit and observed the output directly.
- **Required Checks per Layer:**
  - `task_factory/` & `backend/`: `pytest` (unit + error/edge-case tests using mocked LLM/temp repos where needed) + `ruff check`.
  - `frontend/`: `npm run build` (and lint/typecheck if configured).
  - Regression guard: verify existing tests continue passing after edits.
- **Honest Reporting:** Explicitly report any tests skipped, mocked, or blocked (e.g., Docker daemon unavailable, missing API key).
- **Harbor `0.25.x` Task Validation:** Every generated task package must satisfy `docs/TASK_INTERFACE.md`:
  - `harbor run -p <task_dir> -a nop -k 1 -o <out_dir> --no-delete -y` $\rightarrow$ reward `0.0` (all `pass_to_pass` pass, all `fail_to_pass` fail, never `null`).
  - `harbor run -p <task_dir> -a oracle -k 1 -o <out_dir> --no-delete -y` $\rightarrow$ reward `1.0` (all `fail_to_pass` + `pass_to_pass` pass).

---

## H. Mandatory Agent Completion Report

Every agent must end every implementation task with this exact 8-section summary:

1. **Task Completed:** Concise title/scope completed.
2. **Files Created or Modified:** Exact relative paths and brief purpose of each.
3. **Implementation Summary:** What was built and key technical choices made.
4. **Tests Executed and Results:** Exact commands run, pass/fail counts, and any skipped/unrun checks.
5. **Contract or Interface Changes:** Exact schema/API/config changes made (or `None`).
6. **Known Limitations:** Edge cases, mocks, or incomplete areas.
7. **Pending Dependencies:** Any teammate work, env vars, or external setup required next.
8. **Recommended Next Steps:** Concrete immediate action for the developer or next agent.

---

## I. Agent Session Preamble (paste at the start of every AI-agent session)

Each member pastes the **common block** plus **their own block** as the first message of every agent session (and again after any context reset).

**Common block (everyone):**
```text
You are working in innodata-coding-task-factory. Before any edit:
1. Read AGENTS.md fully, then docs/architecture.md, docs/TASK_INTERFACE.md, docs/IMPLEMENTATION.md (§2, §4, §5), and today's row in docs/day-wise-plan.md.
2. Run `git status` and `git branch --show-current`. Work only on my feat/<member>-<topic> branch cut from dev. Do not stage, commit, or push unless I say so.
3. Edit ONLY the files I own (listed below). If my task needs a change elsewhere (schemas.py, config.py, another member's module, API routes), STOP and tell me exactly what change to request.
4. Match the frozen contracts exactly: Pydantic models in IMPLEMENTATION §4.1, function signatures in §4.4, API in §5, Harbor layout in TASK_INTERFACE. Never rename fields, slugs, or routes. Do not build on [VERIFY] items as facts.
5. Never put LLM output into shell scripts or templates; never execute LLM-generated code on this machine; write generated files only via write_text_lf (LF, UTF-8, no BOM); never use PowerShell Set-Content/Out-File for generated files.
6. Read env vars only through task_factory/config.py. Never print or log API keys.
7. Before finishing: run `ruff check .` and `pytest` (frontend: `npm run build` and `npm run lint`), review `git diff`, and give the 8-part completion report from AGENTS.md §H. Report any skipped or mocked check honestly.
```

**Abhishek (Architecture/Harbor):**
```text
I own: AGENTS.md, README.md, docs/*, root config files, .github/*, task_factory/{__init__,config,schemas,errors,harbor_writer,harbor_runner,mutation_tester}.py, task_factory/templates/harbor/*, tests/conftest.py, tests/fixtures/*, artifacts/*.
Any schema/config/contract change must be additive with defaults unless I explicitly approve a breaking change; list the change so I can announce it to the team.
Harbor templates must match docs/TASK_INTERFACE.md byte-for-byte in behaviour.
```

**Alok (AI generation):**
```text
I own: task_factory/{llm_client,repo_analyzer,variation_engine,synthesizer}.py, task_factory/prompts/*, and their tests/test_<module>.py.
All LLM calls go through llm_client.complete_json() with a Pydantic schema; temperature 0; record/replay cache must keep working.
Unit tests use FakeLLM only; live calls only under @pytest.mark.llm.
Generated tasks must pass the guards in architecture.md §11 and §18 (feature-only, novelty, diversity, spec-test consistency, anti-weakening).
```

**Mrityunjay (Pipeline/Backend/Sandbox):**
```text
I own: task_factory/{__main__,cli,pipeline,sandbox_precheck}.py, backend/*, and their tests.
CLI and backend call pipeline.run_pipeline() / validate_existing(); never duplicate stage logic in routes or CLI.
Sandbox runs only inside Docker with --network none and resource limits, using harbor_writer.render_dockerfile() and render_verifier_files(); never re-implement those templates.
Backend error mapping follows architecture.md §10; one active run at a time (409).
```

**Subhasree (Frontend):**
```text
I own: frontend/* only.
The UI talks only to the REST/SSE contract in docs/IMPLEMENTATION.md §5; types in frontend/src/types must match it exactly (v2 fields are additive).
Do not add dependencies to package.json without coordinator approval. No auth/login UI.
Keep mocks (VITE_USE_MOCKS=1) working so the UI can be demoed without the backend.
```
