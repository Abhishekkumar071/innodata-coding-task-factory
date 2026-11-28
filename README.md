# Innodata Coding Task Factory (Track 1)

Automated **feature-development task factory** for the **Innodata AI Hackathon 2026 — Track 1: Coding Task Factory**. It analyzes a pinned, clean commit of **[`pallets/click`](https://github.com/pallets/click)**, generates **5+ substantively different** feature-development tasks in strict **Harbor `0.25.x`** format, and proves every package automatically: Harbor `nop` → `0.0`, Harbor `oracle` → `1.0`, deliberately broken mutants → `< 1.0`. Everything is driven by a reproducible CLI, with a Control Room web UI for live inspection.

> **Project status (27 Nov 2026):** Architecture and contracts finalized (v2). Implementation in progress per [`docs/day-wise-plan.md`](./docs/day-wise-plan.md). Commands below marked *(planned)* land by the milestone shown.

---

## How It Works

```text
pallets/click @ base_commit
  → Analyze (AST map, upstream feature index) → Baseline (stable pass_to_pass, 3 runs in Docker)
  → Ideate (5 orthogonal axes + scope/novelty/diversity guards)
  → Synthesize (instruction.md + whole-file edits → git diff + feature tests)
  → Stage 1 sandbox (same image + same test.sh as Harbor; self-repair ≤ 3)
  → Package (fixed Harbor templates + leak/scope validation)
  → Stage 2 Harbor (nop = 0.0, oracle = 1.0) → Mutation testing → Evidence bundle
```

Details: [`docs/architecture.md`](./docs/architecture.md).

---

## Team & Ownership

| Member | Role | Owns |
| :--- | :--- | :--- |
| **Abhishek Kumar** *(Leader)* | Architecture, contracts, Harbor infra, validation, DevOps | `docs/`, root config, `task_factory/{config,schemas,errors,harbor_writer,harbor_runner,mutation_tester}.py`, Harbor templates, `artifacts/` |
| **Alok Tiwari** | AI pipeline & task variation | `task_factory/{llm_client,repo_analyzer,variation_engine,synthesizer}.py`, `task_factory/prompts/` |
| **Mrityunjay Pandey** | Orchestration, sandbox, CLI, backend | `task_factory/{cli,pipeline,sandbox_precheck}.py`, `backend/` |
| **Subhasree Sahu** | Control Room UI | `frontend/` |

AI coding agents and contributors: read [`AGENTS.md`](./AGENTS.md) first (rules, ownership, session preamble).

---

## Track 1 Compliance Summary

- **Target repo:** `pallets/click` only, pinned at one 40-char `base_commit` where 100% of baseline tests pass.
- **Scope:** new features or intentional behaviour changes only — no bug fixes, no features already present upstream, no network or real credentials.
- **Variation:** ≥ 5 tasks across 5 axes — `parameter-validation`, `command-routing`, `formatting-termui`, `context-envvar`, `testing-completion`.
- **Package:** `task.toml`, `instruction.md`, `environment/Dockerfile`, `solution/solve.sh`, `tests/test.sh`, `tests/fail_to_pass.json`, `tests/pass_to_pass.json` (+ `solution.patch`, feature test, verifier scripts) — see [`docs/TASK_INTERFACE.md`](./docs/TASK_INTERFACE.md).
- **Validation gate:** `harbor run -a nop` → `0.0`, `harbor run -a oracle` → `1.0`, mutants → `< 1.0`, with logs in `artifacts/validation_evidence/`.

---

## Quickstart

### Prerequisites
Docker (daemon running), Git, Python 3.11+, Harbor `0.25.x` (`pipx install "harbor==0.25.*"`). Windows users run Harbor evidence on **WSL2**.

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cp .env.example .env                                  # LLM key only needed for path D
```

### Judge paths
| Path | Command | API key | Available |
| :--- | :--- | :---: | :--- |
| A. Environment check | `python -m task_factory doctor` | No | *(planned, M3 — 3 Dec)* |
| B. Validate shipped tasks | `python -m task_factory validate --tasks artifacts/tasks` | No | *(planned, M3)* |
| C. Replay generation | `python -m task_factory generate --replay --out _tmp_replay` | No | *(planned, M3)* |
| D. Fresh generation | `python -m task_factory generate --count 5 --out artifacts/tasks` | Yes | *(planned, M2 — 1 Dec)* |

Validate one package directly with Harbor:
```bash
harbor run -p artifacts/tasks/<task_id> -a nop    -k 1 -o artifacts/harbor_runs/manual/<task_id>/harbor_nop    --no-delete -y
harbor run -p artifacts/tasks/<task_id> -a oracle -k 1 -o artifacts/harbor_runs/manual/<task_id>/harbor_oracle --no-delete -y
```

### Control Room *(planned, M2)*
```bash
uvicorn backend.main:app --port 8000
cd frontend && npm install && npm run dev            # http://localhost:5173
```

---

## Repository Layout

```text
task_factory/   Core pipeline + CLI (python -m task_factory)
backend/        FastAPI + SQLite + SSE wrapper around task_factory
frontend/       React + Vite + TypeScript + Tailwind Control Room
tests/          Unit & integration tests for the factory itself
artifacts/      Curated Harbor task packages, validation evidence, recorded LLM I/O
docs/           Architecture, contracts, plans, submission write-up
```

---

## Documentation Index

1. [Problem Statement & Scope](./docs/problem-statement.md) — official Track 1 rules and deliverables.
2. [System Architecture](./docs/architecture.md) — v2 design, ADRs, threat model, concurrency, reproducibility, risks.
3. [Harbor Task Interface Contract](./docs/TASK_INTERFACE.md) — package layout, fixed templates, reward rule, acceptance.
4. [Implementation Guide](./docs/IMPLEMENTATION.md) — stack, ownership, schemas, signatures, config, API, testing.
5. [MVP Features (P0)](./docs/MVP_FEATURES.md) and [Good-to-Have (P1/P2)](./docs/goodtohave.md).
6. [Day-Wise Plan](./docs/day-wise-plan.md) — 27 Nov – 6 Dec per-member schedule, gates, cut lines, QA checklist.
7. [Technical Explanation](./docs/TECHNICAL_EXPLANATION.md) — living submission document.

---

## Key Dates

AMA **2 Dec** · Submission **6 Dec 2026, 11:55 PM IST** (team target 18:00) · Screening 7–14 Dec · Demo Day 20 Dec · Finale 23 Dec.
