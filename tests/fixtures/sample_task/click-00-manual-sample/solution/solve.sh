#!/usr/bin/env bash
# Oracle entrypoint. FIXED TEMPLATE rendered by task_factory/harbor_writer.py.
set -euo pipefail
cd /app
git apply --whitespace=nowarn /solution/solution.patch
