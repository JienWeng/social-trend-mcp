#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker start social-trends-db >/dev/null
ready=false
for _attempt in {1..30}; do
  if docker exec social-trends-db pg_isready -U postgres >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 1
done
if [ "$ready" != true ]; then
  echo 'PostgreSQL did not become ready within 30 seconds' >&2
  exit 1
fi
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://postgres:local-test-only@127.0.0.1:55433/social_trends}"
export APP_ENV=production
exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-graceful-shutdown 15
