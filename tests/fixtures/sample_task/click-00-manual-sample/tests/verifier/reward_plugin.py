"""Records exact pytest node-ID outcomes. Stdlib only. FIXED TEMPLATE."""
import json
import os

_OUT = os.path.join(os.environ.get("VERIFIER_LOG_DIR", "/logs/verifier"), "test_results.json")
_results = {}


def pytest_runtest_logreport(report):
    nodeid = report.nodeid
    if report.failed:                       # failure in setup, call, or teardown
        _results[nodeid] = "failed"
    elif report.skipped:                    # skip / xfail
        _results.setdefault(nodeid, "skipped")
    elif report.when == "call" and report.passed and _results.get(nodeid) != "failed":
        _results[nodeid] = "passed"


def pytest_collectreport(report):
    if report.failed:
        _results["<collection-error>::" + report.nodeid] = "error"


def pytest_sessionfinish(session, exitstatus):
    with open(_OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"exitstatus": int(exitstatus), "results": _results}, fh, indent=1, sort_keys=True)
