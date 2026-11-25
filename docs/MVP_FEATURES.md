# MVP Features (P0 — Must-Have Before 2 Dec AMA Checkpoint)

Everything listed below is **mandatory** for an automated, Harbor-compliant, judge-ready submission. Do **not** start P1/P2 items from [`goodtohave.md`](./goodtohave.md) until every item here passes end-to-end.

---

## 1. Core Pipeline (CLI — `task_factory/`)
- [ ] **Repo & Commit Lock (`repo_analyzer.py`):**
  - Clone `pallets/click`, checkout pinned 40-char `base_commit` from a stable release tag, verify clean `git status`.
  - Run baseline `pytest` and confirm 100% pass; index all baseline node IDs (`pass_to_pass` pool) and Python `ast` module map.
- [ ] **5-Axis Task Variation Engine (`variation_engine.py`):**
  - Generate **5 substantively different feature blueprints** mapped to 5 distinct axes of `pallets/click` (Parameter/Type, Command/Group Routing, Help/Formatting, Context/EnvVar Resolution, Testing/Shell Integration).
  - Hard scope filter: reject bug-fix tasks, upstream-existing features, external network/credential requirements, and duplicate/similar feature proposals.
- [ ] **Task Synthesizer + Self-Repair (`synthesizer.py`):**
  - Generate `instruction.md` (clear, complete, zero spoilers/test leaks), `solution.patch` (modifying `src/click/...` only), and `test_feature_<slug>.py` (`pytest` tests).
  - Run Stage-1 fast local worktree validator (`base` + feature tests MUST fail; `base` + `solution.patch` + feature & existing tests MUST pass) with up to 3 automated LLM self-repair iterations.
- [ ] **Harbor `0.25.x` Packager (`harbor_writer.py`):**
  - Emit complete Harbor directory (`task.toml`, `instruction.md`, `environment/Dockerfile`, `solution/solve.sh` + `solution.patch`, `tests/test.sh`, `tests/fail_to_pass.json`, `tests/pass_to_pass.json`, `tests/test_feature_*.py`).
  - Enforce Unix `LF` (`\n`) on all `.sh` files and exact Harbor reward formula in `tests/test.sh`.
- [ ] **Automated Harbor Runner (`harbor_runner.py`):**
  - Run official `harbor run -p <task_dir> -a nop -k 1 -o <out_dir> --no-delete -y` $\rightarrow$ assert reward **`0.0`**.
  - Run official `harbor run -p <task_dir> -a oracle -k 1 -o <out_dir> --no-delete -y` $\rightarrow$ assert reward **`1.0`**.
  - Save full trial logs and JSON summary under `artifacts/validation_evidence/`.
- [ ] **Single-Command CLI (`cli.py`):**
  - `python -m task_factory generate --repo pallets/click --commit <sha> --count 5 --out ./artifacts/tasks` runs end-to-end without manual intervention.

---

## 2. Backend & Control Room UI (MVP Scope)
- [ ] **FastAPI + SQLite Wrapper (`backend/`):**
  - Endpoints: `POST /api/runs`, `GET /api/runs/{id}`, `GET /api/runs/{id}/events` (SSE logs), `GET /api/tasks`, `GET /api/tasks/{id}`, `POST /api/tasks/{id}/validate`, `GET /api/tasks/{id}/export`.
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
