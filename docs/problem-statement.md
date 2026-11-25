# Problem Statement — Track 1: Coding Task Factory

## 1. Challenge Objective

Build an **automated, repeatable Task Factory pipeline** (not hand-crafted tasks) that inspects a supplied open-source software repository at a pinned, clean Git commit and generates **realistic feature-development task packages** suitable for evaluating AI coding systems.

Each generated task package must strictly conform to the **Harbor (`0.25.x`)** framework interface and include clear requirements, a Dockerized starting environment, an oracle reference patch, new feature tests, regression checks, and automated validation evidence.

---

## 2. Permitted Starter Repositories & Our Selection

Track 1 permits choosing **exactly one** of three official repositories (arbitrary repos or projects in Django, Flask, FastAPI, React, Java, or Kotlin are **not permitted**):

| Repository | Language | Domain | Test Runner | Build / Test Commands | Selection Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`pallets/click`** | Python | CLI toolkit | `pytest` | `pip install -e .` and `pytest` | **SELECTED** |
| `colinhacks/zod` | JS / TS | Schema validation | `vitest` | `pnpm install && pnpm build`, `vitest` | Not selected |
| `open-source-parsers/jsoncpp` | C++ | JSON library | `CMake` + `ctest` | C++ compiler, `CMake`, `ctest` | Not selected |

### Why `pallets/click` Is Our Strategic Choice
1. **Native Python Alignment:** Our pipeline is written in Python, enabling exact static analysis via Python's built-in `ast` and `inspect` modules without cross-language parser overhead.
2. **Fast Container & Test Iteration:** `pip install -e .` and `pytest` execute in seconds inside Docker, allowing rapid self-repair and repeated Harbor validation runs.
3. **Deterministic Test Granularity:** `pytest` outputs precise node IDs (`tests/test_xyz.py::test_name`), making SWE-bench-style `tests/fail_to_pass.json` and `tests/pass_to_pass.json` mappings straightforward and reliable.
4. **Rich Feature Surface:** `click` spans decorators, parameter types/validation, command groups & routing, terminal/help formatting, shell completion, environment/context resolution, and `CliRunner` testing utilities — ideal for generating genuinely distinct features.

---

## 3. Hard Scope Rules & Constraints

1. **Feature-Development Only:**
   - Tasks **must** introduce new features or intentional extensions/changes to existing behaviour.
   - **Bug-fix tasks are strictly out of scope.**
   - Generated features **must not already exist** in the selected `base_commit` or upstream history at that commit.
2. **Clean Starting Commit:**
   - Every task must start from a real, recent, stable commit (ideally a release tag) of `pallets/click` where 100% of existing tests pass.
   - The full **40-character commit SHA** must be recorded in `task.toml` under `base_commit`.
   - Tasks cannot start from a dirty or pre-modified repository.
3. **Meaningful Task Variation:**
   - The factory must generate at least **5 substantively different tasks** from `pallets/click`.
   - Tasks must differ in **behaviour, rules, or component interactions** — rewording, renaming flags, or minor cosmetic tweaks do not count as variation.
4. **Strict Harbor `0.25.x` Compliance:**
   - Every task package must follow the Harbor folder layout (`instruction.md`, `solution/`, `tests/`, `environment/Dockerfile`, `task.toml`) plus `tests/fail_to_pass.json` and `tests/pass_to_pass.json`.
   - `instruction.md` is the **only** file visible to the evaluated AI coding agent; it must be clear and self-contained without leaking patch code or test cases.
5. **Security & Environment Boundaries:**
   - Standard security-related feature tasks (e.g., redacting sensitive CLI prompts/values or input constraints) are permitted, but tasks involving exploits, vulnerabilities, malicious code, external network calls, or real credentials are **out of scope**.
   - All models, coding agents, and external tools used to build/run the pipeline must be explicitly declared in technical documentation.

---

## 4. Automated Validation & Grading Contract

Harbor evaluates each task inside an isolated Docker container through two mandatory passes:

| Pass | Command | Expected Behaviour | Expected Reward |
| :--- | :--- | :--- | :---: |
| **Baseline (`nop`)** | `harbor run -p <task_dir> -a nop -k 1 -o <out_dir> --no-delete -y` | Repo left untouched. Existing regression tests pass; new feature tests fail. | **`0.0`** |
| **Oracle (`oracle`)** | `harbor run -p <task_dir> -a oracle -k 1 -o <out_dir> --no-delete -y` | Applies `solution/solve.sh`. All feature tests AND regression tests pass. | **`1.0`** |

### Exact Reward Calculation Rule
- If **any** regression test (`pass_to_pass`) fails $\rightarrow$ Reward = **`0.0`**
- Else if **all** feature tests (`fail_to_pass`) pass $\rightarrow$ Reward = **`1.0`**
- Else $\rightarrow$ Reward = **`passing_feature_tests / total_feature_tests`**
- (`null` reward indicates an environmental or container crash.)

**Mutation Testing (Strongly Recommended):** Beyond `nop` and `oracle`, we will test deliberately broken/incomplete patches against each task's tests to prove the feature tests reject *incorrect* implementations (not only missing ones).

---

## 5. Submission Deliverables & Judging Focus

Submission Deadline: **6 December 2026 · 11:59 PM IST** (AMA Session: **2 December 2026**, Grand Finale: **20 December 2026**).

Required deliverables:
1. **Runnable Source Code:** Clean repo with automated Docker/CLI setup and execution instructions.
2. **Sample Outputs:** Minimum 5 inspectable, Harbor-compliant task packages pinned to `pallets/click`'s `base_commit`.
3. **Validation Evidence:** `nop` (`0.0`) & `oracle` (`1.0`) Harbor logs, execution metrics, mutation test results, failure cases, and documented fixes.
4. **Technical Explanation:** Design decisions, assumptions, reused components, declared models/tools, and task variation strategy.
5. **Walkthrough Demo:** End-to-end video demonstration of the pipeline generating and validating tasks.

Judging focuses on:
- **Implementation & Repeatability** (judged in a standardized Docker environment; automated reliability beats manual fixes)
- **Validity & Validation Evidence** (strict `nop=0.0`, `oracle=1.0`, zero regression leaks, mutation proof)
- **Task Quality & Novelty** (realistic features, crystal-clear `instruction.md`, genuine multi-axis variation)
