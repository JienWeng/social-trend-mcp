# Social Trends MCP — repaired local service

All five sources are verified: X topics, TikTok's public preview, YouTube weekly music-video charts, Instagram public Reels samples, and Douyin hot topics. No API keys or paid providers are required for the defaults.

See [current behavior, coverage and test evidence](CURRENT-STATUS.md). The feeds have different scopes: these are not five exhaustive global realtime rankings.

```bash
./setup.sh
./manage-service.sh start
./manage-service.sh status
```

API docs on this host: http://127.0.0.1:8000/docs

Use `./manage-service.sh restart` or `stop` to manage the API. The supervisor handles API crashes and orphan recovery; PostgreSQL data lives in a named Docker volume. `start-api.sh` is also available for foreground debugging.

MCP clients can use `mcp-config.json` or `./start-mcp.sh`; its paths are for this machine. Supported tools: `get_trends`, `get_all_trends`, `exact_search`, `search_trends` (alias), `discover_search`, `list_regions`, `capture_trends`, and `analyze_trends`.

Run `./verification/run_tests.sh` for the regression suite and `.venv/bin/python verification/final_e2e.py` for live checks. The latter performs real scrapes and refreshes stored data.

Upstream: https://github.com/caicai-yao/social-trends-mcp — tested base commit c9f413ad1c8c6b387e8cd1af5f0c709f263ceae2. Local repairs remain in `upstream/`, with a reproducible cumulative patch and tests in `verification/`. Changes are maintained in this repository rather than pushed to the original upstream project.

## Stored trend intelligence

The MCP now exposes `capture_trends` (persist a real observation) and `analyze_trends` (analyze shared history). Latest suite: **104 passed**. Controlled and live checks passed; live Douyin evidence showed rank 29 → 28 → 20 across three observations. See [TREND-ANALYSIS.md](TREND-ANALYSIS.md) for rules, source limits and reproducible checks. Earlier Docker evidence below/above covers collection; that image predates this analysis addition.

## Interfaces and agent documentation

See [supported endpoints and MCP tools](docs/ENDPOINTS.md), [implemented changes](docs/CHANGES.md), and [llms.txt](llms.txt). The running API also serves the guide at `/llms.txt`. Requires Git, uv, Docker, Python 3.12 and Playwright Chromium; setup installs the Python/browser dependencies. Linux may need Playwright system libraries (`.venv/bin/python -m playwright install --with-deps chromium`). PostgreSQL uses loopback port 55433 and the API uses 8000.

The implementation is delivered as `verification/repairs.patch` against the pinned upstream commit plus `verification/regression-tests/`; `setup.sh` reconstructs the working source. Raw scrape pages, browser captures and transient logs are excluded from version control.
