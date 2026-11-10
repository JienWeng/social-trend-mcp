# Social Trends MCP

Collect public social feeds, save PostgreSQL history and compare what changed. Default sources require no paid API or AI model. Coverage differs by source; see [current status](CURRENT-STATUS.md).

```bash
./setup.sh
./manage-service.sh start
./manage-service.sh status
```

Requires Git, uv, Docker and Python 3.12. Setup installs Python dependencies and Chromium; Linux may also need `.venv/bin/python -m playwright install --with-deps chromium`. PostgreSQL uses loopback port 55433 and a named Docker volume. The API listens on http://127.0.0.1:8000; interactive documentation is at `/docs`.

Use `./manage-service.sh restart` or `stop` to manage the API. The supervisor handles API crashes and orphan recovery; `start-api.sh` is available for foreground debugging.

## Use the data

Run `./start-mcp.sh` from an MCP client; configure its absolute path on your machine (mcp-config.json shows this workspace's path). Nine tools cover live feeds, exact/discovery search, region lookup, persisted capture, historical momentum and checkpoint changes. Default fetch/search tools use the running API's shared cache; `MCP_FETCH_MODE=direct` explicitly enables standalone fetch/search.

Use `capture_trends` to save an observation, `analyze_trends` for sustained movement evidence, and `get_changes` with an ISO-8601 `since` checkpoint for additions, removals, movement and unchanged counts. Save a report's `generated_at` for your next check. These signals describe sampled observations, not future virality.

- [Endpoint and MCP catalog](docs/ENDPOINTS.md): methods, parameters, persistence and source coverage.
- [Trend analysis](TREND-ANALYSIS.md): rules, evidence and checkpoint semantics.
- [Agent guide](llms.txt): also served by `GET /llms.txt`.
- [Implemented changes](docs/CHANGES.md): repairs and optimizations.

## Collection and verification

Defaults: X/Douyin hourly, TikTok/Instagram every six hours, YouTube daily. Optional `SCRAPE_INTERVAL_HOURS` overrides all sources; `SOURCE_INTERVALS_HOURS` JSON overrides specific sources. Health and analysis share the same freshness policy. Unchanged new content reuses stored topic rows while preserving every capture and retrieval timestamp.

Run `./verification/run_tests.sh` for isolated regression checks. `.venv/bin/python verification/monitoring_live.py` checks real capture reuse and REST/MCP checkpoint reports; it performs network requests and persists real snapshots. Latest evidence and limitations are in [current status](CURRENT-STATUS.md).

## Reproduce the implementation

[Original upstream](https://github.com/caicai-yao/social-trends-mcp) is pinned to commit `c9f413ad1c8c6b387e8cd1af5f0c709f263ceae2`. `setup.sh` clones it into ignored `upstream/`, applies `verification/repairs.patch`, and restores `verification/regression-tests/`. Review that patch for application changes. Raw scrape pages, temporary logs, backups and browser captures stay local. Earlier investigation reports are in [docs/archive](docs/archive).
