"""Computes the Harbor reward from exact node-ID outcomes. Stdlib only. FIXED TEMPLATE."""
import argparse
import json
import os
from pathlib import Path

# Overridable only so the factory's own unit tests can run this file outside a container.
LOG_DIR = Path(os.environ.get("VERIFIER_LOG_DIR", "/logs/verifier"))
TESTS_DIR = Path(os.environ.get("VERIFIER_TESTS_DIR", "/tests"))
MAX_LISTED = 50


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pytest-exit-code", type=int, default=None)
    ap.add_argument("--setup-error", default=None)
    args = ap.parse_args()

    f2p = _load(TESTS_DIR / "fail_to_pass.json")
    p2p = _load(TESTS_DIR / "pass_to_pass.json")
    fast_mode = os.environ.get("FAST_MODE") == "1"
    errors, results = [], {}

    if args.setup_error:
        errors.append("setup: " + args.setup_error)
    results_file = LOG_DIR / "test_results.json"
    if results_file.exists():
        results = _load(results_file)["results"]
    elif not args.setup_error:
        errors.append("test_results.json missing (pytest did not finish)")
    if args.pytest_exit_code not in (None, 0, 1):   # 0=all passed, 1=some failed; else crash/timeout
        errors.append("pytest exit code %s" % args.pytest_exit_code)
    if not f2p:
        errors.append("fail_to_pass.json is empty")
    if fast_mode:                                   # Stage 1 fast mode: only grade what ran
        p2p = [n for n in p2p if n in results]

    f2p_passed = [n for n in f2p if results.get(n) == "passed"]
    f2p_not_passed = [n for n in f2p if results.get(n) != "passed"]
    p2p_not_passed = [n for n in p2p if results.get(n) != "passed"]

    status = "error" if errors else "ok"
    if status == "error" or p2p_not_passed:
        reward = 0.0
    elif len(f2p_passed) == len(f2p):
        reward = 1.0
    else:
        reward = round(len(f2p_passed) / len(f2p), 4)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "reward.txt").write_text("%s\n" % reward, encoding="utf-8")
    summary = {
        "schema_version": 1,
        "status": status,
        "reward": reward,
        "errors": errors,
        "fast_mode": fast_mode,
        "pytest_exit_code": args.pytest_exit_code,
        "f2p_total": len(f2p),
        "f2p_passed": len(f2p_passed),
        "p2p_total": len(p2p),
        "p2p_passed": len(p2p) - len(p2p_not_passed),
        "f2p_not_passed": f2p_not_passed[:MAX_LISTED],
        "p2p_not_passed": p2p_not_passed[:MAX_LISTED],
    }
    (LOG_DIR / "verifier_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
