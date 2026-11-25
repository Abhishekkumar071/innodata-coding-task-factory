# Innodata Coding Task Factory (Track 1)

Automated **Feature-Development Task Factory** built for the **Innodata AI Hackathon 2026 (Track 1: Coding Task Factory)** using the **Harbor (`0.25.x`)** evaluation framework and **`pallets/click`** as the target open-source repository.

Instead of hand-crafting benchmark tasks, our pipeline analyzes a pinned, clean commit of `pallets/click`, generates **5+ substantively different, realistic feature-development task packages** in strict Harbor format, validates every package automatically via `harbor run` (`nop` = `0.0`, `oracle` = `1.0`) and mutation testing, and exposes everything through both a **reproducible CLI** and a **Control Room Web Dashboard**.

---

## Team & Ownership

| Member | Role | Primary Ownership |
| :--- | :--- | :--- |
| **Abhishek Kumar** *(Leader)* | Architecture, Harbor Infra & Validation | `docs/`, `task_factory/harbor_writer.py`, `harbor_runner.py`, `mutation_tester.py`, `pallets/click` commit pin, CI/Docker, final evidence bundle |
| **Alok Tiwari** | AI Pipeline & Task Variation | `task_factory/repo_analyzer.py`, `variation_engine.py`, `synthesizer.py` (5-axis variation, prompt engineering, self-repair loop) |
| **Mrityunjay Pandey** | Backend Orchestration & Sandbox | `task_factory/cli.py`, Git worktree fast pre-check, `backend/` (FastAPI, SQLite, SSE job streaming) |
| **Subhasree Sahu** | Frontend Control Room | `frontend/` (React + TypeScript + Tailwind dashboard, diff inspector, Harbor validation scorecard) |

---

## Core Compliance Summary (Track 1)

- **Target Repository:** [`pallets/click`](https://github.com/pallets/click) (Python CLI toolkit, `pip install -e .`, `pytest`)
- **Task Interface:** Harbor Framework `harbor==0.25.*` (`task.toml`, `instruction.md`, `environment/Dockerfile`, `solution/solve.sh`, `tests/test.sh`, `tests/fail_to_pass.json`, `tests/pass_to_pass.json`)
- **Task Scope:** Realistic **new feature-development** or **intentional behaviour-change** tasks only (no bug-fix tasks, no features that already exist upstream, no external network/real credentials)
- **Variation Target:** Minimum **5 substantively different tasks** across distinct behavioural axes of `pallets/click`
- **Validation Gate:**
  - `harbor run -p <task_dir> -a nop -k 1 -o <out_dir> --no-delete -y` $\rightarrow$ Reward **`0.0`**
  - `harbor run -p <task_dir> -a oracle -k 1 -o <out_dir> --no-delete -y` $\rightarrow$ Reward **`1.0`**
  - Mutation test (deliberately broken patch) $\rightarrow$ Reward **`< 1.0`**

---

## Documentation Index

> **AI Agents & Contributors:** Read [`AGENTS.md`](./AGENTS.md) first for engineering rules, directory ownership, Git safety, and completion-report standards.

All planning, architecture, interface contracts, and execution plans live inside [`docs/`](./docs/):

1. [**Problem Statement & Scope**](./docs/problem-statement.md) — Official Track 1 goals, starter repo selection rationale, rules, and judging weights.
2. [**System Architecture**](./docs/architecture.md) — End-to-end factory pipeline, 2-stage validation flow, 5-axis variation engine, database, and UI layout.
3. [**Harbor Task Interface Contract**](./docs/TASK_INTERFACE.md) — Exact `harbor==0.25.*` directory layout, `task.toml`, `test.sh` reward formula, and Windows/Docker safety rules.
4. [**MVP Features (P0)**](./docs/MVP_FEATURES.md) — Non-negotiable features required to pass automated judging before the 2 Dec AMA checkpoint.
5. [**Good-to-Have Features (P1/P2)**](./docs/goodtohave.md) — Stretch enhancements (mutation automation, AI solver benchmarking, analytics) after MVP passes.
6. [**Implementation Guide**](./docs/IMPLEMENTATION.md) — Tech stack, repo layout, Day-1 environment setup, module contracts, and API specs.
7. [**Day-Wise Plan & Team Workflow**](./docs/day-wise-plan.md) — 25 Nov – 6 Dec sprint schedule, Git branching (`docs` $\rightarrow$ `main` $\rightarrow$ `dev` $\rightarrow$ `feat/*`), and 9 PM sync rules.
8. [**Technical Explanation (Submission Template)**](./docs/TECHNICAL_EXPLANATION.md) — Living deliverable doc capturing design decisions, declared models/tools, and validation evidence.

---

## Quick Verification Targets (Once Implemented)

```bash
# 1. Verify prerequisites
docker --version
git --version
harbor --version   # Must match 0.25.x

# 2. Generate 5 Harbor task packages from pinned pallets/click commit
python -m task_factory generate --repo pallets/click --count 5 --out ./artifacts/tasks

# 3. Validate a generated task using Harbor CLI
harbor run -p ./artifacts/tasks/<task-id> -a nop -k 1 -o ./artifacts/harbor_runs/nop --no-delete -y
harbor run -p ./artifacts/tasks/<task-id> -a oracle -k 1 -o ./artifacts/harbor_runs/oracle --no-delete -y
```

> **Note:** Detailed setup instructions and pinned commit hashes will be locked in [`docs/IMPLEMENTATION.md`](./docs/IMPLEMENTATION.md) during Day 1 setup.
