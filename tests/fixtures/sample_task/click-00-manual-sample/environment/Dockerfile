# FIXED TEMPLATE rendered by task_factory/harbor_writer.py. Identical for every task.
FROM python:3.11-slim

# less: required by click's echo_via_pager suite (24 failures without it).
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates less \
 && rm -rf /var/lib/apt/lists/*

ARG BASE_COMMIT=cf19179e8e2fd54c601378cec9e0d21bb12b6fb1
WORKDIR /app

# Fetch exactly one commit: no future upstream history inside the image.
RUN git init -q /app \
 && git -C /app remote add origin https://github.com/pallets/click.git \
 && git -C /app fetch -q --depth 1 origin "${BASE_COMMIT}" \
 && git -C /app checkout -q --detach FETCH_HEAD \
 && git -C /app remote remove origin \
 && test "$(git -C /app rev-parse HEAD)" = "${BASE_COMMIT}"

# Editable install + pytest pinned to click's own lockfile at base_commit.
RUN pip install --no-cache-dir -e /app "pytest==9.0.2"
