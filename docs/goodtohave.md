# Good-to-Have & Stretch Features (`goodtohave.md`)

> **Rule:** Strictly **DO NOT** build any P1/P2 item below until every single P0 item in [`MVP_FEATURES.md`](./MVP_FEATURES.md) is implemented, tested, and passing `harbor run` (`nop=0.0`, `oracle=1.0`) for at least 5 tasks.

---

## P1 — High-Impact Judging Boosters (Target: Days 7–9)

1. **Automated Mutation Testing (`task_factory/mutation_tester.py`):**
   - **Why:** The Participant Guide explicitly notes *"Mutation testing (proving tests detect deliberately broken implementations) is strongly recommended."*
   - **How:** For each task's `solution.patch`, generate 2–3 AST/LLM-guided broken variants (e.g., inverted condition, early return, dropped validation check, off-by-one/wrong exception type), run tests, and assert `reward < 1.0`.
   - Display **Mutation Kill Rate** (e.g., `3/3 mutants caught`) in both `validation_evidence/` and the frontend scorecard.

2. **Live AI Coding Agent Evaluation (`Eval Benchmark Mode`):**
   - Run an actual coding agent / LLM solver (not just `nop` and `oracle`) inside Harbor on our 5 generated tasks to compute **Pass@1 / Partial Reward** metrics.
   - Proves the tasks are genuinely solvable yet non-trivial for AI coding systems (adds massive credibility to *Practical Impact & Technical Explanation*).

3. **Semantic Diversity & Novelty Report:**
   - Compute pairwise similarity matrix (TF-IDF / embedding cosine distance + AST file/symbol overlap) across the 5 generated tasks and render a heatmap/chart in the UI proving zero overlap.

4. **One-Click Submission Bundle Exporter:**
   - CLI + UI button that packages `artifacts/tasks/`, `artifacts/validation_evidence/`, summary Markdown/CSV metrics, and `TECHNICAL_EXPLANATION.md` into a clean deliverable directory/archive.

---

## P2 — Nice-to-Have Polish (Only If Ahead of Schedule on Days 9–10)

1. **Optional Second Repo Adapter (`colinhacks/zod` — TypeScript / `vitest`):**
   - *Reminder:* Track 1 rules require choosing **one** starter repo for submission (`pallets/click`). Only explore `zod` internally if proving reusability in a bonus architectural demo, without diluting `pallets/click` evidence!
2. **Difficulty Calibration Scoring:**
   - Automatically classify each generated task as `easy`, `medium`, or `hard` based on files modified, lines changed, API surface depth, and number of interacting components.
3. **Task Quality Scoring (strictly post-MVP):**
   - Score each accepted task on instruction clarity, spec–test consistency coverage, mutation kill rate, and difficulty signals; surface the score in `summary.md` and the UI. Never used as an acceptance gate.
4. **Failure Case Replay Explorer in UI:**
   - Show Stage-1 self-repair history (Attempt 1 error $\rightarrow$ LLM fix $\rightarrow$ Attempt 2 pass) directly inside the UI so judges can see automated reliability in action.
