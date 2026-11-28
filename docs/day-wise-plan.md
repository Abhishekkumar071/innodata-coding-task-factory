# Day-Wise Plan & Team Workflow — v2 (re-baselined 27 Nov 2026)

**Submission deadline:** Sun 6 Dec 2026 · 11:55 PM IST (team target: **submitted by 18:00 IST**)
**AMA:** 2 Dec · **Screening:** 7–14 Dec · **Mentor Connect:** 15 Dec · **Finalist Demo Day:** 20 Dec · **Grand Finale:** 23 Dec

> **Why re-baselined:** As of 27 Nov the repo contains docs and a frontend UI shell only. No `task_factory/`, `backend/`, `pyproject.toml`, `.gitattributes`, or pinned commit exists yet, so **Gate 1 (26 Nov) was missed**. This plan compresses the remaining work into 10 days with explicit handoffs and stubs so nobody waits on anybody. Architecture: [`architecture.md`](./architecture.md). Contracts: [`IMPLEMENTATION.md`](./IMPLEMENTATION.md) §4–5, [`TASK_INTERFACE.md`](./TASK_INTERFACE.md).

---

## 1. Milestones & Gates

| Milestone | Due | Gate (pass/fail check, run by Abhishek) |
| :--- | :--- | :--- |
| **M1 — Foundations & Contracts** | Sat 28 Nov, 23:00 | **Gate 1:** `pip install -e ".[dev]"`, `ruff`, `pytest` green in CI; SHA pinned; hand-made sample task gives `nop=0.0` / `oracle=1.0` in **Harbor** *and* in the **Stage 1 sandbox** with identical `verifier_summary.json`; `baseline.json` produced |
| **M2 — Core MVP Pipeline (P0)** | Tue 1 Dec, 23:00 | **Gate 2:** `python -m task_factory generate --count 5` (and one UI click) produces ≥ 3 tasks passing Harbor `nop=0.0` / `oracle=1.0`; evidence summary written; UI shows live run; `dev → main` merged |
| **M3 — 5-Axis Variation & Mutation (P1)** | Thu 3 Dec, 23:00 | **Gate 3:** ≥ 5 accepted tasks covering all 5 axes; ≥ 2/3 mutants killed per task; `doctor`, `validate --tasks`, `generate --replay` all pass **without an API key** |
| **M4 — Submission Harvest & Demo** | Sun 6 Dec, 18:00 | **Gate 4:** 10–15 curated packages in `artifacts/tasks/`, full evidence, `TECHNICAL_EXPLANATION.md`, deck, video, fresh-clone verification, tag `v1.0-submission` |

---

## 2. Daily Rhythm (every day)

| Time (IST) | What | Who |
| :--- | :--- | :--- |
| 10:00 | Async stand-up in chat: *yesterday merged / today's target (from this plan) / blockers* | All |
| 13:00 | Handoff checkpoint: any stub/interface promised "by 13:00" is pushed | Owner of the handoff |
| 20:00 | **PR cut-off** into `dev` (small PRs; one module per PR) | All |
| 21:00 | 15-min sync: gate status, blockers, re-assignments | All |
| 22:00 | Integration smoke on `dev`: `ruff check . && pytest` + one `generate --replay` (from M2 onwards) | Abhishek |

**Blocker rule:** if you are blocked > 1 hour on someone else's module, code against the stub signature in `IMPLEMENTATION.md` §4.4 and post in chat. Never edit their file.

---

## 3. Day-by-Day Plan

### Fri 27 Nov — M1 · "Contracts & skeletons"

| Member | Build | Files | Done when |
| :--- | :--- | :--- | :--- |
| **Abhishek** | (1) **Decision D1**: pick LLM provider + model. (2) Pin click: choose stable tag, record SHA, verify baseline in a `python:3.11-slim` container. (3) Scaffold PR **by 18:00**: `pyproject.toml`, `.gitignore`, `.gitattributes` (+ `git add --renormalize .`), `.env.example`, `task_factory/__init__.py`, `config.py`, `schemas.py`, `errors.py`, `tests/conftest.py`. (4) CI: ruff + pytest + frontend build. (5) Start Harbor verification items 1–4 (`harbor task init`). | root files, `task_factory/{config,schemas,errors}.py`, `.github/workflows/ci.yml` | Scaffold merged to `dev`; CI green; SHA + D1 announced in chat; schemas frozen |
| **Alok** | `llm_client.py`: single provider, `complete_json()` with Pydantic validation + 3 retries + jittered backoff, record/replay cache (`sha256` key), `FakeLLM`. Draft `prompts/ideate_v1.md` (axis table, guard rules, output schema). | `task_factory/llm_client.py`, `task_factory/prompts/`, `tests/test_llm_client.py` | Unit tests green (FakeLLM, stable cache key, replay-miss raises `LLMError`); one live call recorded locally (not committed) |
| **Mrityunjay** | `__main__.py` + `cli.py` skeleton (`doctor`, `analyze`, `generate`, `validate`, `mutate`, `report`; argparse; `--help`). `pipeline.py` stub: `run_pipeline()` emitting fixture `RunEvent`s to `events.jsonl`. Backend skeleton: app factory, CORS, `/api/health`, error-handler mapping `errors.py` → HTTP, SQLite WAL session. | `task_factory/{__main__,cli,pipeline}.py`, `backend/*`, `tests/test_cli.py`, `tests/test_backend_health.py` | `python -m task_factory --help` works; `uvicorn backend.main:app` serves `/api/health`; tests green |
| **Subhasree** | Align `src/types` with v2 **additive** contract (`RunEvent.seq/level/data`, nullable `task_id`, stages `run`/`baseline`/`package`, `TaskSummary.run_id/target_files/status`, `RunSummary` additions). Add mock layer (`VITE_USE_MOCKS=1`) with fixture JSON exactly matching IMPLEMENTATION §5. | `frontend/src/types/*`, `frontend/src/services/*`, `frontend/src/mocks/*` | `npm run build` + `npm run lint` green; all pages render from mocks |

**Handoffs:** Abhishek → all: `schemas.py` + `errors.py` + SHA by **18:00**.

---

### Sat 28 Nov — M1 due · Gate 1 · "One task, proven twice"

| Member | Build | Files | Done when |
| :--- | :--- | :--- | :--- |
| **Abhishek** | `templates/harbor/*` exactly per TASK_INTERFACE §2. `harbor_writer.py`: `write_text_lf`, `render_dockerfile`, `render_verifier_files`, `write_task_package`, `validate_package` (all §4 checks). Unit tests incl. `compute_reward.py` cases (ok/partial/crash/missing/fast-mode). Hand-craft `tests/fixtures/sample_task` (`click-00-manual-sample`) and run Harbor `nop`/`oracle` on WSL2. Close §15 verification items → update `[VERIFY]` markers. | `task_factory/harbor_writer.py`, `task_factory/templates/harbor/`, `tests/test_harbor_writer.py`, `tests/fixtures/sample_task/`, `docs/TASK_INTERFACE.md` | Harbor gives `0.0` / `1.0` on the sample; verification results announced |
| **Alok** | `repo_analyzer.py`: `ensure_mirror()` (`core.autocrlf=false`, SHA + clean check → `RepoStateError`), `analyze_repo()` (AST `SymbolInfo` map, test file index), upstream `CHANGES.md` feature index (`artifacts/upstream/CHANGES.md`, `.cache/` fallback). | `task_factory/repo_analyzer.py`, `tests/test_repo_analyzer.py` | Tests on a temp git repo green; `python -m task_factory analyze` (with Mrityunjay's CLI) prints symbol counts for the pinned SHA |
| **Mrityunjay** | `sandbox_precheck.py`: `ensure_sandbox_image()` from `render_dockerfile()`, worktree manager (lock, prune, Windows retry), `verify_in_worktree()` (base + oracle runs, `--network none`, CPU/RAM/PID limits, fast/full mode), `collect_baseline()` (3 runs → stable set). | `task_factory/sandbox_precheck.py`, `tests/test_sandbox_precheck.py` (`@pytest.mark.docker`) | Sample task: sandbox summaries equal Harbor's; `baseline.json` written with pass count + exclusions |
| **Subhasree** | Task Inspector: `react-diff-viewer-continued` for `solution.patch`, feature test code view, `fail_to_pass` / `pass_to_pass` lists, **logs tab** using `GET /api/tasks/{id}/logs/{evidence}` (mocked). | `frontend/src/features/task-inspector/*` | Build/lint green; inspector shows all 6 views from mocks |

**Handoffs:** Abhishek → Mrityunjay: `render_dockerfile()` + `render_verifier_files()` (stub acceptable) by **13:00**.
**Gate 1 check (23:00):** see §1.

---

### Sun 29 Nov — M2 · "Pipeline spine"

| Member | Build | Files | Done when |
| :--- | :--- | :--- | :--- |
| **Abhishek** | `harbor_runner.validate_task()`: unique `-o` dirs, parse Harbor job layout (from Gate 1 findings), acceptance from `verifier_summary.json` (ADR-11), evidence copy, semaphore + warm-first run, timeouts. Unit tests on a **recorded** Harbor output fixture. | `task_factory/harbor_runner.py`, `tests/test_harbor_runner.py`, `tests/fixtures/harbor_output/` | `validate_task(sample_task)` returns 2 accepted `ValidationOutcome`s; evidence folders populated |
| **Alok** | `variation_engine.propose_blueprints()` v1: 5 axes, `count + 2` proposals, scope (bug-fix language), novelty (AST symbols/docstrings), upstream (`CHANGES.md`) guards, basic Jaccard diversity. Record one live run. | `task_factory/variation_engine.py`, `task_factory/prompts/`, `tests/test_variation_engine.py` | FakeLLM tests cover each guard rejecting; 7 live blueprints → ≥ 5 accepted across 5 axes; fixture JSON shared |
| **Mrityunjay** | `pipeline.run_pipeline()` real wiring: analyze → baseline → ideate → synthesize (Alok's stub) → package → harbor; per-task `state.json` checkpoints; `--resume`; `generate` + `validate` CLI wired. | `task_factory/pipeline.py`, `task_factory/cli.py`, `tests/test_pipeline.py` | Pipeline test with FakeLLM + stubbed sandbox/harbor passes; resume skips completed stages |
| **Subhasree** | Pipeline Runner on real `POST /api/runs` + SSE (fallback to mocks until routes land): stepper incl. `baseline` and `package`, live log panel with `level` colouring, reconnect banner. | `frontend/src/features/pipeline/*` | Works against mocks and against Mrityunjay's local backend when available |

**Handoffs:** Alok → Mrityunjay: blueprint fixture JSON by **13:00**. Alok → all: `synthesize_task()` stub with final signature by **13:00**.

---

### Mon 30 Nov — M2 · "First AI-generated task through Harbor"

| Member | Build | Files | Done when |
| :--- | :--- | :--- | :--- |
| **Abhishek** | Pair with Mrityunjay to integrate writer + runner in the pipeline; push the **first AI-generated task** through Harbor; fix template edge cases; `write_evidence_summary()` (`summary.json`, `summary.md`, `environment.json`). | `harbor_writer.py`, `harbor_runner.py`, `tests/` | ≥ 1 generated task accepted by Harbor; `summary.md` renders the evidence table |
| **Alok** | `synthesizer.synthesize_task()` v1: prompts with exact file contents; whole-file edits → `CandidateFiles`; instruction template sections; feature tests (lazy imports); f2p collected via sandbox; self-repair ≤ 3 using `VerifierSummary` + truncated log; **anti-weakening** (f2p count & assertion count never drop); **spec–test consistency** (AST-extracted literals must appear in instruction). | `task_factory/synthesizer.py`, `task_factory/prompts/`, `tests/test_synthesizer.py` | FakeLLM tests: repair loop, weakening rejected, consistency failure triggers repair; ≥ 1 live task passes Stage 1 |
| **Mrityunjay** | Backend routes per IMPLEMENTATION §5: runs (+ `409`), SSE (`id: seq`, `Last-Event-ID`, `: ping`, terminal `run` event), tasks (`?run_id=`), task detail, validate, export, logs; `service.py` single worker thread; DB writer. | `backend/*`, `tests/test_backend_*.py` | `TestClient` tests: status codes, 409, SSE framing, path-traversal rejection |
| **Subhasree** | Variations Table (axis, title, target files, difficulty, repairs, status, `nop`/`oracle` badges) + Inspector on live API; **Validate** and **Export** buttons; "pending" vs "crashed" (`reward=null` with a validation present) distinguished. | `frontend/src/features/variations/*`, `task-inspector/*` | Works on live backend with the sample task + first generated task |

---

### Tue 1 Dec — M2 due · Gate 2 · "Integration day"

| Member | Build | Done when |
| :--- | :--- | :--- |
| **Abhishek** | 10:00 run `generate --count 5` end-to-end on WSL2; triage every failure to its owner by 13:00; re-run at 18:00; after Gate 2, merge `dev → main`. | Gate 2 passed; failure list posted with owners |
| **Alok** | Prompt tuning on failing tasks (most common: unspecified literals, vacuous tests, oversized patches). Target ≥ 3/5 pass Stage 1 within 3 repairs. | ≥ 3 tasks accepted in the 18:00 run |
| **Mrityunjay** | Hardening: container kill on timeout, worktree cleanup, run-level failure events, resume tested by killing a run mid-way. | Kill-and-resume demo works; no orphan containers (`docker ps -a` clean) |
| **Subhasree** | UI end-to-end on the live run; error states (backend down, run failed, 409 run active); first rough screen recording of the flow. | Live run fully observable from UI |

---

### Wed 2 Dec — M3 · AMA · "Prove the tests bite"

| Member | Build | Files | Done when |
| :--- | :--- | :--- | :--- |
| **Abhishek** | Attend AMA; log every clarification in `TASK_INTERFACE.md`/`problem-statement.md`. `mutation_tester.run_mutations()`: AST operators on **added** lines, sandbox screening, Harbor confirmation on a temp copy, kill-rate + meaningful-kill metrics. | `task_factory/mutation_tester.py`, `tests/test_mutation_tester.py`, docs | ≥ 2/3 mutants killed on every accepted task so far |
| **Alok** | Full diversity guard (Jaccard + LLM "same feature?" judge) → `diversity.json`; apply AMA feedback to prompts; difficulty calibration rule. | `variation_engine.py`, `synthesizer.py` | `diversity.json` shows all pairs below threshold |
| **Mrityunjay** | `/api/tasks/{id}/mutate` + mutation fields in DB; `mutate` CLI; complete `doctor` (Docker, Harbor version, Python, disk, LF/BOM scan of `artifacts/tasks/**`) and `validate --tasks` (judge path B). | `cli.py`, `pipeline.py`, `backend/*` | `doctor` and `validate --tasks` run with no API key |
| **Subhasree** | Mutation scorecard (killed/total + meaningful kills), axis-coverage badges, run history (`GET /api/runs`). | `frontend/src/features/*` | Scorecard renders real mutation outcomes |

---

### Thu 3 Dec — M3 due · Gate 3 · "Scale & reproducibility"

| Member | Build | Done when |
| :--- | :--- | :--- |
| **Abhishek** | `docker-compose.yml` judge path (path-parity mount); fresh-clone test on Linux/WSL; run mutations on all accepted tasks. | Judge paths A + B pass from a fresh clone |
| **Alok** | Batch generation of ~15 candidates with `LLM_MODE=record`; ensure every axis has ≥ 2 accepted tasks; tag prompt versions. | ≥ 10 accepted tasks, all 5 axes ≥ 2 |
| **Mrityunjay** | `generate --replay` reproduces packages **byte-identically** from the cache (diff check); raise unit-test coverage on pipeline/backend error paths. | Replay diff is empty |
| **Subhasree** | Evidence summary view (per-task reward matrix + kill rates); responsive/demo polish. | Demo-ready UI on real data |

**Gate 3 check (23:00):** see §1. Code is **feature-complete** after Gate 3; only fixes from here.

---

### Fri 4 Dec — M4 · "Evidence harvest"

| Member | Build | Done when |
| :--- | :--- | :--- |
| **Abhishek** | Final recorded run → curate 10–15 tasks into `artifacts/tasks/`; `validate` + `mutate` all; regenerate evidence bundle; commit `artifacts/llm_cache/` of the final run; merge `dev → main` as `rc1`. | `summary.md` complete; all shipped tasks green |
| **Alok** | Manual quality review of every `instruction.md` (clarity, completeness, no leaks); write the failure-case section from `events.jsonl` (real failures + fixes). | Review checklist signed off per task |
| **Mrityunjay** | Fresh clone on a clean machine/VM: run judge paths A–D exactly as README says; fix any setup gap. | README commands verified verbatim |
| **Subhasree** | UI on final data; screenshots for deck; rehearse UI walkthrough. | Screenshot set ready |

---

### Sat 5 Dec — "Freeze & document"

**12:00 code freeze** (only fixes for a failing judge path, approved by Abhishek).

| Member | Build | Done when |
| :--- | :--- | :--- |
| **Abhishek** | Complete `TECHNICAL_EXPLANATION.md` (pinned SHA/tag, metrics table from `summary.md`, models/tools declared, ADRs, assumptions); final README; own the 11-slide deck. | Docs complete, no `[TO BE RECORDED]` left |
| **Alok** | Deck slides: variation strategy, AI pipeline, guards, failure cases; model declaration table. | Slides delivered to Abhishek by 16:00 |
| **Mrityunjay** | Record CLI + Harbor segments of the walkthrough video (doctor → generate → validate → evidence). | Raw CLI footage ready by 17:00 |
| **Subhasree** | Record UI segment; edit the full walkthrough video. | Video draft shared by 22:00 |

---

### Sun 6 Dec — "Submit"

| Time | Activity | Owner |
| :--- | :--- | :--- |
| 10:00 | Final QA checklist (§5) split across members | All |
| 13:00 | Fix window for QA findings (docs/evidence only) | Owners |
| 15:00 | Final `dev → main`, tag `v1.0-submission` | Abhishek |
| 16:00 | Deck PDF + video upload + repo link verified in incognito | Abhishek + Subhasree |
| **18:00** | **Submit on Hack2skill dashboard** (5 h buffer before 23:55) | Abhishek |

---

## 4. Cut Lines (if behind schedule, drop in this order)

1. LLM "same feature?" judge (keep Jaccard diversity only).
2. Mutation confirmation in Harbor (keep sandbox mutation results as evidence).
3. UI mutation scorecard / run history.
4. Curated set size 15 → 10 → 5 (never below 5; never below 1 per axis).
5. Fast mode in Stage 1 (always run full suite).

**Never cut:** Harbor `nop`/`oracle` evidence, LF/leak guards, `validate --tasks` judge path, `TECHNICAL_EXPLANATION.md`, video.

---

## 5. Submission QA Checklist (Sun 6 Dec)

- [ ] Fresh clone → `pip install -e ".[dev]"` → `doctor` → `validate --tasks artifacts/tasks` all green (no API key).
- [ ] Every package: 10 required files + 1 feature test, `task.toml` `base_commit` = pinned SHA, no `\r`/BOM, `.sh` executable in git.
- [ ] `artifacts/validation_evidence/summary.md` matches `TECHNICAL_EXPLANATION.md` §6 numbers.
- [ ] ≥ 5 tasks, all 5 axes covered, no bug-fix tasks, no network/credentials in tests.
- [ ] Models/tools declared (incl. coding assistants used during development).
- [ ] No `.env`, keys, `_tmp_*`, `.cache/`, or `*.db` committed.
- [ ] Deck (11 slides) + video link + repo link open in incognito.

---

## 6. Git Workflow

- **Branches:** `docs` → `main` (docs PRs) · `main` (stable, no direct pushes) · `dev` (daily integration) · `feat/<member>-<topic>` cut from `dev`.
- **PR checklist:** owned files only · matches contracts · `ruff check .` + `pytest` (or `npm run build` + lint) green · tests for new logic · no secrets/CRLF/BOM · description lists exact test commands and what is stubbed.
- **Merge `dev → main`:** only at Gate 2, Gate 3, `rc1` (4 Dec), and `v1.0-submission` (6 Dec).
