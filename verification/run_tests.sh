#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "$(docker exec social-trends-db psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='social_trends_regression'")" != 1 ]; then
  docker exec social-trends-db createdb -U postgres social_trends_regression
fi
export TEST_DATABASE_URL='postgresql+asyncpg://postgres:local-test-only@127.0.0.1:55433/social_trends_regression'
exec .venv/bin/pytest upstream -q
