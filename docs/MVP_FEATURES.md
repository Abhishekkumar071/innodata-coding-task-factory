# MVP Features (P0 — Must-Have Before 2 Dec AMA Checkpoint)

Everything listed below is **mandatory** for an automated, Harbor-compliant, judge-ready submission. Do **not** start P1/P2 items from [`goodtohave.md`](./goodtohave.md) until every item here passes end-to-end.

---

## 1. Core Pipeline (CLI — `task_factory/`)
- [ ] **Repo & Commit Lock (`repo_analyzer.py`):**
  - Clone `pallets/click`, checkout pinned 40-char `base_commit` from a stable release tag, verify clean `git status`.
  - Build Python `ast` module/symbol map and upstream `CHANGES.rst` feature index.
  - Baseline (`sandbox_precheck.collect_baseline()`): run the suite 3× **inside the Linux sandbox**; `pass_to_pass` = stable passes; exclusions recorded in `baseline.json`.
- [ ] **5-Axis Task Variation Engine (`variation_engine.py`):**
  - Generate **5 substantively different feature blueprints** mapped to 5 distinct axes of `pallets/click` (Parameter/Type, Command/Group Routing, Help/Formatting, Context/EnvVar Resolution, Testing/Shell Integration).
  - Hard scope filter: reject bug-fix tasks, upstream-existing features, external network/credential requirements, and duplicate/similar feature proposals.
- [ ] **Task Synthesizer + Self-Repair (`synthesizer.py`):**
  - Generate `instruction.md` (clear, complete, zero spoilers/test leaks), `solution.patch` (modifying `src/click/...` only), and `test_feature_<slug>.py` (`pytest` tests).
  - Run Stage-1 sandbox validator (worktree mounted into the Harbor image, same `test.sh`, `--network none`): `base` → all feature tests fail and regressions pass; `base + solution.patch` → reward `1.0`; up to 3 automated LLM self-repair iterations.
  - Spec–test consistency check and anti-weakening guard (see `architecture.md` §11).
- [ ] **Harbor `0.25.x` Packager (`harbor_writer.py`):**
  - Emit complete Harbor directory (`task.toml`, `instruction.md`, `environment/Dockerfile`, `solution/solve.sh` + `solution.patch`, `tests/test.sh`, `tests/fail_to_pass.json`, `tests/pass_to_pass.json`, `tests/test_feature_*.py`).
  - Render only fixed templates (`TASK_INTERFACE.md` §2); write every file via `write_text_lf` (LF, no BOM); run `validate_package()` (leak/scope checklist) before Harbor.
- [ ] **Automated Harbor Runner (`harbor_runner.py`):**
  - Run official `harbor run -p <task_dir> -a nop -k 1 -o <out_dir> --no-delete -y` $\rightarrow$ assert reward **`0.0`**.
  - Run official `harbor run -p <task_dir> -a oracle -k 1 -o <out_dir> --no-delete -y` $\rightarrow$ assert reward **`1.0`**.
  - Save full trial logs and JSON summary under `artifacts/validation_evidence/`.
- [ ] **Single-Command CLI (`cli.py`):**
  - `python -m task_factory generate --repo pallets/click --commit <sha> --count 5 --out ./artifacts/tasks` runs end-to-end without manual intervention, via `pipeline.run_pipeline()`, with checkpointing and `--resume <run_id>`.
  - Key-less judge commands: `doctor` and `validate --tasks artifacts/tasks` (no LLM key needed).
  - LLM record/replay (`LLM_MODE=record|replay`, `generate --replay`) so the final run is reproducible without an API key.

---

## 2. Backend & Control Room UI (MVP Scope)
- [ ] **FastAPI + SQLite Wrapper (`backend/`):**
  - Endpoints: `GET /api/health`, `POST /api/runs` (`409` if a run is active), `GET /api/runs`, `GET /api/runs/{id}`, `GET /api/runs/{id}/events` (SSE with `seq` + `Last-Event-ID`), `GET /api/tasks?run_id=`, `GET /api/tasks/{id}`, `POST /api/tasks/{id}/validate`, `GET /api/tasks/{id}/logs/{evidence}`, `GET /api/tasks/{id}/export` — exact payloads in `IMPLEMENTATION.md` §5.
- [ ] **React Control Room UI (`frontend/`):**
  - Trigger a run and view live pipeline stage progress (`Analyze → Ideate → Synthesize → Fast Check → Harbor Validate`).
  - **5-Task Variation Table:** shows axis, title, target module(s), difficulty, repair count, and `nop` / `oracle` reward badges (`0.0` / `1.0`).
  - **Task Inspector:** tabs for `instruction.md`, `task.toml`, diff viewer (`solution.patch` & `test_feature_*.py`), `fail_to_pass.json` / `pass_to_pass.json`, and raw Harbor trial logs.
  - **No Authentication / Login Page:** Keep UI immediately accessible for live judging & video walkthrough.

---

## 3. Deliverable Readiness (MVP Bar)
- [ ] **5+ Verified Harbor Task Packages** committed under `artifacts/tasks/` (all passing `nop=0.0` and `oracle=1.0`).
- [ ] **Automated CI (`pytest` + frontend build)** green on PRs into `dev`/`main`.
- [ ] **Reproducible Docker / Setup Instructions** verified on a clean environment.
