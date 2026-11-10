#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d upstream/.git ]; then
  git clone https://github.com/caicai-yao/social-trends-mcp.git upstream
  git -C upstream checkout c9f413ad1c8c6b387e8cd1af5f0c709f263ceae2
fi
if git -C upstream apply --check ../verification/repairs.patch 2>/dev/null; then
  git -C upstream apply ../verification/repairs.patch
elif ! git -C upstream apply --reverse --check ../verification/repairs.patch 2>/dev/null; then
  echo 'Repair patch conflicts with local edits; inspect upstream before continuing.' >&2
  exit 1
fi
mkdir -p upstream/tests
cp -R verification/regression-tests/. upstream/tests/
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e './upstream[browser,dev]' 'mcp[cli]>=1.2,<2'
.venv/bin/python -m playwright install chromium
if ! docker container inspect social-trends-db >/dev/null 2>&1; then
  docker volume create social-trends-pgdata >/dev/null
  docker run -d --name social-trends-db -e POSTGRES_PASSWORD=local-test-only -e POSTGRES_DB=social_trends -p 127.0.0.1:55433:5432 -v social-trends-pgdata:/var/lib/postgresql/data --restart unless-stopped postgres:16-alpine
else
  docker start social-trends-db
fi
