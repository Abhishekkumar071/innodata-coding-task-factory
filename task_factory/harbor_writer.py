"""Harbor 0.25.x package renderer and validator (docs/TASK_INTERFACE.md).

Fixed templates (ADR-05) live in ``task_factory/templates/harbor/`` and are rendered with
regex-validated values only. ``validate_package()`` enforces every check of
TASK_INTERFACE §4 and raises ``LeakageDetected`` or ``ScopeViolation`` with all issues.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tomllib
import uuid
from importlib import resources
from pathlib import Path, PurePosixPath

from task_factory.config import get_settings
from task_factory.errors import ConfigError, LeakageDetected, ScopeViolation
from task_factory.schemas import (
    ALL_AXES,
    FEATURE_TEST_PATTERN,
    SHA_PATTERN,
    TASK_ID_MAX_LENGTH,
    TASK_ID_PATTERN,
    SynthesizedTask,
)

logger = logging.getLogger("task_factory.harbor_writer")

DIFFICULTIES = ("easy", "medium", "hard")
F2P_MIN, F2P_MAX = 3, 10
MAX_PATCH_CHANGED_LINES = 400
VERBATIM_MIN_CHARS = 40
GIT_APPLY_TIMEOUT_SEC = 60

# Package-relative path -> template file name (static, no placeholders).
_STATIC_FILES: dict[str, str] = {
    "solution/solve.sh": "solve.sh",
    "tests/test.sh": "test.sh",
    "tests/verifier/reward_plugin.py": "reward_plugin.py",
    "tests/verifier/compute_reward.py": "compute_reward.py",
}
REQUIRED_FILES: tuple[str, ...] = (
    "task.toml",
    "instruction.md",
    "environment/Dockerfile",
    "solution/solve.sh",
    "solution/solution.patch",
    "tests/test.sh",
    "tests/fail_to_pass.json",
    "tests/pass_to_pass.json",
    "tests/verifier/reward_plugin.py",
    "tests/verifier/compute_reward.py",
)
EXECUTABLE_FILES = ("solution/solve.sh", "tests/test.sh")

INSTRUCTION_SECTIONS: dict[str, tuple[str, ...]] = {
    "Goal": ("goal",),
    "Required behaviour": ("required behaviour", "required behavior"),
    "Public API": ("public api",),
    "Errors": ("errors",),
    "Examples": ("examples",),
    "Non-goals": ("non-goals", "non goals"),
    "Compatibility": ("compatibility",),
}
INSTRUCTION_BANNED_TOKENS = (
    "test_feature",
    "fail_to_pass",
    "pass_to_pass",
    "::test_",
    "@@",
    "+++ ",
    "--- a/",
    "diff --git",
)
# Matched against added patch lines (ScopeViolation, anti-reward-hacking; architecture §11 T5).
PATCH_DENY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (label, re.compile(rx))
    for label, rx in (
        ("/logs", r"/logs"),
        ("reward", r"reward"),
        ("subprocess", r"\bsubprocess\b"),
        ("socket", r"\bsocket\b"),
        ("os.system", r"\bos\.system\b"),
        ("urllib", r"\burllib\b"),
        ("requests", r"\brequests\b"),
        ("http.client", r"\bhttp\.client\b"),
        ("import pytest", r"\bimport\s+pytest\b|\bfrom\s+pytest\b"),
        ("sys.modules", r"\bsys\.modules\b"),
        ("conftest", r"conftest"),
    )
)
_SIGNATURE_PREFIXES = ("def ", "async def ", "class ", "@")
_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z_]+\}\}")
_DIFF_HEADER_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)$")
_RENAME_PREFIXES = ("rename from ", "rename to ", "copy from ", "copy to ")


# --------------------------------------------------------------------------------------
# Writing helpers
# --------------------------------------------------------------------------------------


def normalize_lf(text: str) -> str:
    """Strip a leading BOM and convert CRLF/CR to LF."""
    if text.startswith("﻿"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n")


def write_text_lf(path: Path, text: str) -> None:
    """Write ``text`` as UTF-8 (no BOM) with LF endings and a trailing newline."""
    text = normalize_lf(text)
    if text and not text.endswith("\n"):
        text += "\n"
    data = text.encode("utf-8")
    if b"\r" in data:  # pragma: no cover - defensive, normalize_lf removes all CRs
        raise ScopeViolation(f"refusing to write CR bytes to {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _make_executable(path: Path) -> None:
    if os.name != "nt":
        path.chmod(0o755)


# --------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------


def _load_template(name: str) -> str:
    # Normalize defensively: a Windows checkout without .gitattributes would add CRLF.
    raw = resources.files("task_factory").joinpath("templates", "harbor", name).read_text("utf-8")
    return normalize_lf(raw)


def _render(name: str, values: dict[str, str]) -> str:
    text = _load_template(name)
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    leftover = _PLACEHOLDER_RE.findall(text)
    if leftover:  # pragma: no cover - template/renderer mismatch
        raise ConfigError(f"unrendered placeholders in {name}: {sorted(set(leftover))}")
    return text


def _require_sha(base_commit: str) -> str:
    if not re.fullmatch(SHA_PATTERN, base_commit or ""):
        raise ConfigError("base_commit must be a 40-character lowercase hex SHA")
    return base_commit


def _require_task_id(task_id: str) -> str:
    if len(task_id) > TASK_ID_MAX_LENGTH or not re.fullmatch(TASK_ID_PATTERN, task_id):
        raise ConfigError(f"invalid task_id {task_id!r} (expected {TASK_ID_PATTERN}, ≤ 64 chars)")
    return task_id


def render_dockerfile(base_commit: str, *, pytest_pin: str | None = None) -> str:
    """Render the environment Dockerfile (also used for the Stage 1 sandbox image)."""
    pin = pytest_pin or get_settings().pytest_pin
    if not re.fullmatch(r"\d+(\.\d+){1,2}", pin):
        raise ConfigError(f"invalid pytest pin {pin!r}")
    return _render("Dockerfile", {"BASE_COMMIT": _require_sha(base_commit), "PYTEST_PIN": pin})


def render_task_toml(task_id: str, *, axis: str, difficulty: str, base_commit: str) -> str:
    if axis not in ALL_AXES:
        raise ConfigError(f"invalid axis {axis!r}")
    if difficulty not in DIFFICULTIES:
        raise ConfigError(f"invalid difficulty {difficulty!r}")
    return _render(
        "task.toml",
        {
            "TASK_ID": _require_task_id(task_id),
            "AXIS": axis,
            "DIFFICULTY": difficulty,
            "BASE_COMMIT": _require_sha(base_commit),
        },
    )


def render_solve_sh() -> str:
    return _load_template("solve.sh")


def render_verifier_files() -> dict[str, str]:
    """Return verifier files keyed by path relative to the package ``tests/`` dir.

    Keys: ``test.sh``, ``verifier/reward_plugin.py``, ``verifier/compute_reward.py``.
    The Stage 1 sandbox mounts exactly these files at ``/tests``.
    """
    return {
        pkg_path.removeprefix("tests/"): _load_template(template)
        for pkg_path, template in _STATIC_FILES.items()
        if pkg_path.startswith("tests/")
    }


def _json_list(items: list[str]) -> str:
    return json.dumps(sorted(set(items)), indent=2) + "\n"


# --------------------------------------------------------------------------------------
# Package writing
# --------------------------------------------------------------------------------------


def write_task_package(
    task: SynthesizedTask,
    out_dir: Path,
    *,
    base_commit: str | None = None,
    overwrite: bool = False,
) -> Path:
    """Write ``out_dir/<task_id>/``, validate it, and return its path.

    The package is staged in a temporary sibling directory and only moved into place after
    ``validate_package()`` passes, so a rejected task never lands in ``out_dir``.
    """
    task_id = _require_task_id(task.blueprint.task_id)
    sha = _require_sha(base_commit or get_settings().click_base_commit)
    target = out_dir / task_id
    if target.exists() and not overwrite:
        raise ConfigError(f"task package already exists: {target}")

    files: dict[str, str] = {
        "task.toml": render_task_toml(
            task_id,
            axis=task.blueprint.axis,
            difficulty=task.blueprint.difficulty,
            base_commit=sha,
        ),
        "instruction.md": task.instruction_md,
        "environment/Dockerfile": render_dockerfile(sha),
        "solution/solve.sh": render_solve_sh(),
        "solution/solution.patch": task.solution_patch,
        "tests/fail_to_pass.json": _json_list(task.fail_to_pass),
        "tests/pass_to_pass.json": _json_list(task.pass_to_pass),
        task.feature_test_filename: task.feature_test_code,
    }
    for rel, content in render_verifier_files().items():
        files[f"tests/{rel}"] = content

    out_dir.mkdir(parents=True, exist_ok=True)
    staging_root = out_dir / f".staging-{uuid.uuid4().hex[:12]}"
    staged = staging_root / task_id
    try:
        for rel, content in files.items():
            path = staged / rel
            write_text_lf(path, content)
            if rel in EXECUTABLE_FILES:
                _make_executable(path)
        validate_package(staged, base_commit=sha, pass_to_pass=task.pass_to_pass)
        if target.exists():
            shutil.rmtree(target)
        staged.rename(target)
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)

    logger.info("wrote task package %s", target)
    return target


# --------------------------------------------------------------------------------------
# Validation (TASK_INTERFACE §4)
# --------------------------------------------------------------------------------------


def _read_text_checked(path: Path, rel: str, scope: list[str]) -> str | None:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        scope.append(f"{rel}: has a UTF-8 BOM")
    if b"\r" in data:
        scope.append(f"{rel}: contains CR (\\r) bytes; LF line endings required")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        scope.append(f"{rel}: is not valid UTF-8")
        return None


def _patch_paths_and_added_lines(patch: str) -> tuple[set[str], list[str], int, list[str]]:
    """Return (touched paths, added lines, changed-line count, structural issues)."""
    paths: set[str] = set()
    added: list[str] = []
    changed = 0
    issues: list[str] = []
    in_hunk = False
    for line in patch.split("\n"):
        header = _DIFF_HEADER_RE.match(line)
        if header:
            in_hunk = False
            paths.update({header.group(1), header.group(2)})
            continue
        if line.startswith("GIT binary patch") or line.startswith("Binary files"):
            issues.append("solution.patch: binary patches are not allowed")
        elif not in_hunk and line.startswith(_RENAME_PREFIXES):
            paths.add(line.split(" ", 2)[2])
        elif not in_hunk and (line.startswith("--- ") or line.startswith("+++ ")):
            target = line[4:].strip()
            if target != "/dev/null":
                paths.add(target[2:] if target[:2] in ("a/", "b/") else target)
        elif line.startswith("@@"):
            in_hunk = True
        elif in_hunk and line.startswith("+"):
            added.append(line[1:])
            changed += 1
        elif in_hunk and line.startswith("-"):
            changed += 1
    if not paths:
        issues.append("solution.patch: no file headers found (not a git diff)")
    return paths, added, changed, issues


def _is_allowed_patch_path(path: str) -> bool:
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or "\\" in path:
        return False
    return (
        len(pure.parts) >= 3
        and pure.parts[0] == "src"
        and pure.parts[1] == "click"
        and pure.name != "conftest.py"
    )


def _git_apply_check(repo: Path, patch_path: Path) -> str | None:
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(Path(repo).resolve()),
                "apply",
                "--check",
                "--whitespace=nowarn",
                str(Path(patch_path).resolve()),
            ],
            capture_output=True,
            text=True,
            timeout=GIT_APPLY_TIMEOUT_SEC,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"solution.patch: git apply --check could not run ({exc.__class__.__name__})"
    if proc.returncode != 0:
        return f"solution.patch: does not apply cleanly: {proc.stderr.strip()[:500]}"
    return None


def _instruction_headings(text: str) -> list[str]:
    return [
        m.group(1).strip().lower()
        for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, flags=re.MULTILINE)
    ]


def validate_package(
    task_dir: Path,
    *,
    base_commit: str | None = None,
    pass_to_pass: list[str] | None = None,
    apply_check_repo: Path | None = None,
) -> None:
    """Enforce TASK_INTERFACE §4. Raises ``LeakageDetected`` or ``ScopeViolation``.

    ``pass_to_pass`` (the run baseline) and ``apply_check_repo`` (a clean checkout at
    ``base_commit`` for ``git apply --check``) enable their checks when given.
    """
    task_dir = Path(task_dir)
    expected_sha = base_commit or get_settings().click_base_commit
    scope: list[str] = []
    leaks: list[str] = []

    if not task_dir.is_dir():
        raise ScopeViolation(f"task package directory not found: {task_dir}")

    # 1. Layout: required files, exactly one feature module, nothing else.
    present = {p.relative_to(task_dir).as_posix() for p in task_dir.rglob("*") if p.is_file()}
    for rel in REQUIRED_FILES:
        if rel not in present:
            scope.append(f"missing required file: {rel}")
    feature_files = sorted(
        rel
        for rel in present
        if rel.startswith("tests/") and PurePosixPath(rel).name.startswith("test_feature_")
    )
    if len(feature_files) != 1:
        scope.append(f"expected exactly one tests/test_feature_*.py, found {len(feature_files)}")
    for rel in feature_files:
        if not re.fullmatch(FEATURE_TEST_PATTERN, rel):
            scope.append(f"feature test path must match {FEATURE_TEST_PATTERN}: {rel}")
    unexpected = sorted(present - set(REQUIRED_FILES) - set(feature_files))
    for rel in unexpected:
        scope.append(f"unexpected file in package: {rel}")

    # 2. Encoding of every file.
    texts: dict[str, str] = {}
    for rel in sorted(present):
        text = _read_text_checked(task_dir / rel, rel, scope)
        if text is not None:
            texts[rel] = text

    # 3. task.toml identity.
    meta: dict = {}
    if "task.toml" in texts:
        try:
            meta = tomllib.loads(texts["task.toml"]).get("metadata", {})
        except tomllib.TOMLDecodeError as exc:
            scope.append(f"task.toml: invalid TOML ({exc})")
    task_id = str(meta.get("task_id", ""))
    meta_ok = False
    if meta:
        id_ok = len(task_id) <= TASK_ID_MAX_LENGTH and bool(re.fullmatch(TASK_ID_PATTERN, task_id))
        if not id_ok:
            scope.append(f"task.toml: invalid task_id {task_id!r}")
        if task_dir.name != task_id:
            scope.append(f"directory name {task_dir.name!r} != task.toml task_id {task_id!r}")
        if meta.get("base_commit") != expected_sha:
            scope.append("task.toml: base_commit does not match the pinned click_base_commit")
        axis_ok = meta.get("axis") in ALL_AXES
        if not axis_ok:
            scope.append(f"task.toml: invalid axis {meta.get('axis')!r}")
        difficulty_ok = meta.get("difficulty") in DIFFICULTIES
        if not difficulty_ok:
            scope.append(f"task.toml: invalid difficulty {meta.get('difficulty')!r}")
        meta_ok = id_ok and axis_ok and difficulty_ok

    # 4. Fixed templates must be byte-identical to a fresh render (no drift / hand edits).
    expected: dict[str, str] = {
        rel: _load_template(name) for rel, name in _STATIC_FILES.items()
    }
    try:
        expected["environment/Dockerfile"] = render_dockerfile(expected_sha)
        if meta_ok:
            expected["task.toml"] = render_task_toml(
                task_id,
                axis=str(meta.get("axis")),
                difficulty=str(meta.get("difficulty")),
                base_commit=expected_sha,
            )
    except ConfigError as exc:
        scope.append(f"cannot render templates for drift check: {exc}")
    for rel, want in expected.items():
        if rel in texts and texts[rel] != want:
            scope.append(f"{rel}: differs from the fixed template (template drift)")

    # 5. Dockerfile isolation.
    dockerfile = texts.get("environment/Dockerfile", "")
    if re.search(r"^\s*(COPY|ADD)\b", dockerfile, flags=re.IGNORECASE | re.MULTILINE):
        leaks.append("environment/Dockerfile: COPY/ADD is not allowed")
    if re.search(r"\b(solution|tests)\b", dockerfile, flags=re.IGNORECASE):
        leaks.append("environment/Dockerfile: must not reference solution/ or tests/")

    # 6. solution.patch scope.
    added_lines: list[str] = []
    patch = texts.get("solution/solution.patch")
    if patch is not None:
        if not patch.strip():
            scope.append("solution.patch: is empty")
        else:
            paths, added_lines, changed, issues = _patch_paths_and_added_lines(patch)
            scope.extend(issues)
            for path in sorted(paths):
                if not _is_allowed_patch_path(path):
                    scope.append(f"solution.patch: touches disallowed path {path!r}")
            if changed > MAX_PATCH_CHANGED_LINES:
                scope.append(
                    f"solution.patch: {changed} changed lines > {MAX_PATCH_CHANGED_LINES}"
                )
            for label, rx in PATCH_DENY_PATTERNS:
                if any(rx.search(line) for line in added_lines):
                    scope.append(f"solution.patch: added code contains denied token {label!r}")
            if apply_check_repo is not None and "solution/solution.patch" in present:
                problem = _git_apply_check(apply_check_repo, task_dir / "solution/solution.patch")
                if problem:
                    scope.append(problem)

    # 7. fail_to_pass / pass_to_pass.
    feature_rel = feature_files[0] if len(feature_files) == 1 else None
    lists: dict[str, list[str]] = {}
    for rel in ("tests/fail_to_pass.json", "tests/pass_to_pass.json"):
        if rel not in texts:
            continue
        try:
            value = json.loads(texts[rel])
        except json.JSONDecodeError as exc:
            scope.append(f"{rel}: invalid JSON ({exc.msg})")
            continue
        if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
            scope.append(f"{rel}: must be a JSON array of non-empty strings")
            continue
        if len(set(value)) != len(value):
            scope.append(f"{rel}: contains duplicate node IDs")
        if value != sorted(value):
            scope.append(f"{rel}: node IDs must be sorted")
        lists[rel] = value
    f2p = lists.get("tests/fail_to_pass.json")
    p2p = lists.get("tests/pass_to_pass.json")
    if f2p is not None:
        if not F2P_MIN <= len(f2p) <= F2P_MAX:
            scope.append(f"fail_to_pass.json: {len(f2p)} IDs, expected {F2P_MIN}-{F2P_MAX}")
        if feature_rel:
            outside = [n for n in f2p if not n.startswith(feature_rel + "::")]
            if outside:
                scope.append(f"fail_to_pass.json: IDs outside {feature_rel}: {outside[:3]}")
    if p2p is not None:
        if not p2p:
            scope.append("pass_to_pass.json: is empty")
        if feature_rel and any(n.startswith(feature_rel + "::") for n in p2p):
            scope.append("pass_to_pass.json: must not contain feature test IDs")
        if pass_to_pass is not None and p2p != sorted(set(pass_to_pass)):
            scope.append("pass_to_pass.json: does not equal the run baseline")

    # 8. instruction.md: leaks and required sections.
    instruction = texts.get("instruction.md")
    if instruction is not None:
        lowered = instruction.lower()
        for token in INSTRUCTION_BANNED_TOKENS:
            if token in lowered:
                leaks.append(f"instruction.md: contains banned token {token!r}")
        for line in added_lines:
            stripped = line.strip()
            if len(stripped) <= VERBATIM_MIN_CHARS or stripped.startswith(_SIGNATURE_PREFIXES):
                continue
            if stripped in instruction:
                leaks.append(f"instruction.md: copies patch code verbatim: {stripped[:60]!r}")
        headings = _instruction_headings(instruction)
        for section, aliases in INSTRUCTION_SECTIONS.items():
            if not any(h.startswith(alias) for h in headings for alias in aliases):
                scope.append(f"instruction.md: missing required section heading {section!r}")

    if leaks:
        raise LeakageDetected(f"task package {task_dir.name} leaks content", issues=leaks + scope)
    if scope:
        raise ScopeViolation(f"task package {task_dir.name} is invalid", issues=scope)


__all__ = [
    "REQUIRED_FILES",
    "normalize_lf",
    "render_dockerfile",
    "render_solve_sh",
    "render_task_toml",
    "render_verifier_files",
    "validate_package",
    "write_task_package",
    "write_text_lf",
]
