#!/usr/bin/env bash
# Harbor verifier. FIXED TEMPLATE rendered by task_factory/harbor_writer.py. Never LLM-authored.
# Contract: ALWAYS writes /logs/verifier/reward.txt and verifier_summary.json, ALWAYS exits 0.
set -uo pipefail

LOG_DIR=/logs/verifier
VERIFIER=/tests/verifier
mkdir -p "$LOG_DIR"

setup_error() {
  python3 "$VERIFIER/compute_reward.py" --setup-error "$1" \
    || echo "0.0" > "$LOG_DIR/reward.txt"
  exit 0
}

export COLUMNS=80 LINES=24 TERM=dumb LC_ALL=C.UTF-8
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$VERIFIER${PYTHONPATH:+:$PYTHONPATH}"

cd /app || setup_error "cannot cd /app"
cp /tests/test_feature_*.py /app/tests/ || setup_error "cannot copy feature tests"
python -c "import click, sys; sys.exit(0 if click.__file__.startswith('/app/src') else 1)" \
  || setup_error "click is not imported from /app/src"

# PYTEST_TARGETS / FAST_MODE are only set by the Stage 1 sandbox. Harbor always runs the full suite.
TARGETS="${PYTEST_TARGETS:-tests}"
# shellcheck disable=SC2086
timeout "${VERIFIER_PYTEST_TIMEOUT:-270}" python -m pytest $TARGETS \
  -p reward_plugin -p no:cacheprovider --continue-on-collection-errors -q \
  > "$LOG_DIR/pytest.log" 2>&1
rc=$?

python3 "$VERIFIER/compute_reward.py" --pytest-exit-code "$rc" \
  || echo "0.0" > "$LOG_DIR/reward.txt"
exit 0
