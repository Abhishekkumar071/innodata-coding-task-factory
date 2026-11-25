# Day-Wise Plan & Team Workflow (25 Nov – 6 Dec 2026)

**Submission Deadline:** 6 December 2026 · 11:55 PM IST  
**AMA Session Checkpoint:** 2 December 2026  
**Evaluation & Screening:** 7–14 December 2026  
**Mentor Connect:** 15 December 2026  
**Finalist Demo Day:** 20 December 2026  
**Grand Finale:** 23 December 2026

---

## 1. Daily Team & Git Workflow

### Branching Rules
- **`docs`** $\rightarrow$ PR into **`main`** (Documentation foundation — Day 1).
- **`main`** $\rightarrow$ Always stable, demo-ready milestones. **Direct pushes prohibited.**
- **`dev`** $\rightarrow$ Daily integration branch (created from `main` after docs PR merges).
- **Feature Branches** (branched from `dev`, merged via PR daily):
  - `feat/abhishek-<topic>`
  - `feat/mrityunjay-<topic>`
  - `feat/alok-<topic>`
  - `feat/subhasree-<topic>`

### PR Merge Checklist
1. Code touches only your owned directories (or contract changes were agreed beforehand).
2. `ruff check` + `pytest` (or `npm run build` for `frontend/`) passes locally.
3. No `.env`, API keys, or giant temporary clones committed (`_tmp_*` stays ignored).
4. Short PR description explaining what works and how you tested it.

### Daily 9:00 PM Sync (15 Minutes Strict)
Each member shares exactly 3 points:
1. **Merged today:** Which PR / module is done.
2. **Building tomorrow:** Next concrete deliverable.
3. **Blocker:** Any schema mismatch, Harbor Docker error, or LLM issue (resolve immediately on call).

---

## 2. 12-Day Execution Roadmap

### Phase 1: Foundation & Contracts (25–26 Nov)

| Day | Abhishek (Leader/Harbor) | Alok (AI/Variation) | Mrityunjay (Backend/Sandbox) | Subhasree (Frontend) |
| :--- | :--- | :--- | :--- | :--- |
| **Day 1 (25 Nov)** | Finalize & PR `docs/`; verify `harbor==0.25.*` (`harbor task init`); pin `pallets/click` stable commit & verify baseline `pytest` | Inspect `click` codebase modules & `CHANGES.rst`; design `ast` module/symbol extractor script | Set up `pyproject.toml` + FastAPI hello-world + SQLite DB schema (`runs`, `tasks`, `validations`) | Initialize `frontend/` (Vite + React + TS + Tailwind + Diff viewer lib); create layout with mock JSON |
| **Day 2 (26 Nov)** | Lock `task_factory/schemas.py`, `config.py`, `.gitattributes`; build `harbor_writer.py` & verify 1 manual dummy task passes `harbor run` (`nop=0`, `oracle=1`) | Complete `repo_analyzer.py` + 5-axis prompt prototypes; generate 1 raw `click` feature prototype via CLI | Build `sandbox_precheck.py` (isolated Git worktree + `pytest` runner + nodeid collector) & `cli.py` skeleton | Build Pipeline Runner screen + 5-Task Variation Table with mock states |

**Gate 1 (26 Nov Night):** A manually created `pallets/click` sample task successfully runs `harbor run -a nop` (`0.0`) and `harbor run -a oracle` (`1.0`).

---

### Phase 2: End-to-End MVP Pipeline (27–29 Nov)

| Day | Abhishek | Alok | Mrityunjay | Subhasree |
| :--- | :--- | :--- | :--- | :--- |
| **Day 3 (27 Nov)** | Build `harbor_runner.py` to automate `nop` & `oracle` execution, parse `/logs/verifier/reward.txt`, and archive logs | Implement `variation_engine.py` (5 orthogonal axes + bug-fix filter + upstream symbol check + pairwise dedup) | Connect `cli.py` pipeline (`analyze → ideate → synthesize → precheck`); add FastAPI `/runs` & `/tasks` routes | Build Task Inspector tabs (`instruction.md`, `task.toml`, diff viewer for `solution.patch` & feature tests) |
| **Day 4 (28 Nov)** | Test `harbor_writer.py` on Alok's first AI-generated task; fix any Dockerfile, `test.sh`, or `fail_to_pass` edge cases | Implement `synthesizer.py` using file-edit $\rightarrow$ `git diff` strategy + deterministic `pytest --collect-only` + Stage-1 self-repair (up to 3 retries) | Add SSE `/runs/{id}/events` live streaming logs + task zip exporter + DB persistence | Connect frontend to live FastAPI endpoints + SSE pipeline log stream |
| **Day 5 (29 Nov)** | End-to-end integration run on `pallets/click` for **3 tasks**; verify zero test leaks in `instruction.md` & Dockerfiles | Tune prompts & self-repair on failing tasks to hit >80% first-run/repaired Stage-1 pass rate | Stabilize job background execution, error recovery, and worktree cleanup | Connect Harbor Reward Matrix badges (`nop=0.0` / `oracle=1.0`) & raw trial log viewer |

**Gate 2 (29 Nov Night — Core MVP Ready):** One command (and one UI click) generates multiple `click` tasks and validates them end-to-end with Harbor `nop=0.0` and `oracle=1.0`. Merge `dev` $\rightarrow$ `main`!

---

### Phase 3: 5-Task Variation, Mutation Testing & AMA (30 Nov – 2 Dec)

| Day | Abhishek | Alok | Mrityunjay | Subhasree |
| :--- | :--- | :--- | :--- | :--- |
| **Day 6 (30 Nov)** | Implement `mutation_tester.py` (2–3 broken mutants per task) & prove `reward < 1.0` | Run full **5-axis generation** (`count=5`) and tighten variation rules so all 5 tasks touch distinct behaviours | Add `/tasks/{id}/validate` and `/tasks/{id}/mutate` API endpoints + store mutation metrics in SQLite | Add Mutation Scorecard & Diversity/Axis coverage badges in UI |
| **Day 7 (1 Dec)** | Build standardized `docker-compose.yml` / Judge Dockerfile and test pipeline execution inside clean container | Fix prompt edge cases, eliminate flaky tests, document failure cases & improvements | Add comprehensive unit tests (`tests/`) for Git worktrees, API routes, and CLI | Polish UI responsiveness, error banners, and task export button |
| **Day 8 (2 Dec — AMA)** | Attend AMA Session; verify any clarifications against `TASK_INTERFACE.md`; patch adapter if needed | Refine variation & requirement clarity based on AMA feedback | Harden pipeline timeouts, disk cleanup, and retry logic | Prepare UI screens cleanly for demo walkthrough |

**Gate 3 (2 Dec Night — Feature Freeze for Core):** Full 5-task batch runs cleanly, passes Harbor `nop=0.0` & `oracle=1.0`, and kills broken mutants.

---

### Phase 4: Evidence Collection, Solver Eval & Submission Polish (3–6 Dec)

| Day | All-Hands Focus |
| :--- | :--- |
| **Day 9 (3 Dec)** | **Fresh Pipeline Run & Evidence Harvest:** Generate 5–8 clean Harbor tasks from `pallets/click`, run Harbor `nop` + `oracle` + mutation tests on all, and archive verified outputs under `artifacts/tasks/` and `artifacts/validation_evidence/`. *(Stretch if smooth: run 1 external AI solver inside Harbor to record Pass@1 benchmark evidence!)* |
| **Day 10 (4 Dec)** | **Clean-Environment Verification:** Run full setup from scratch following `README.md` inside Docker/fresh clone. Fix any missing dependency, path issue, or flaky test. Merge final stable code `dev` $\rightarrow$ `main`. |
| **Day 11 (5 Dec)** | **Final Freeze & Docs:** Complete `docs/TECHNICAL_EXPLANATION.md` (with exact metrics, models declared, failure cases & fixes), verify all 5 submission deliverables, and record the **end-to-end Walkthrough Video Demo** (CLI + Harbor runs + UI dashboard). |
| **Day 12 (6 Dec)** | **Final QA & Submit (Before 6 PM IST buffer for 11:55 PM deadline):** Verify all repo files, sample outputs, validation logs, technical PDF/markdown, presentation deck, and video link on Hack2skill Participant Dashboard. |
