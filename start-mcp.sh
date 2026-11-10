#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec .venv/bin/python upstream/mcp_server.py
