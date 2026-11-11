# Social Trends MCP

Collect public social feeds, save PostgreSQL history and compare what changed. Default sources require no paid API or AI model. Coverage differs by source; see [current status](CURRENT-STATUS.md).

```bash
./setup.sh
./manage-service.sh start
./manage-service.sh status
./check-service.sh
```

Requires Git, uv, Docker and Python 3.12. Setup installs Python dependencies and Chromium; Linux may also need `.venv/bin/python -m playwright install --with-deps chromium`. PostgreSQL uses loopback port 55433 and a named Docker volume. The API listens on http://127.0.0.1:8000; interactive documentation is at `/docs`. On first startup, let initial collection finish before expecting the readiness check to report healthy.

Use `./manage-service.sh restart` or `stop` to manage the API. The supervisor handles API crashes and orphan recovery; `start-api.sh` is available for foreground debugging.

## Use the data

Run `./start-mcp.sh` from an MCP client; configure its absolute path on your machine (mcp-config.json shows this workspace's path). Twenty-two tools cover live feeds, exact/discovery search, region lookup, persisted capture, historical momentum and checkpoint changes. Default fetch/search tools use the running API's shared cache; `MCP_FETCH_MODE=direct` explicitly enables standalone fetch/search.

**Start with `get_report` (no arguments)** for stored freshness, coverage, evidence and next actions; it does not scrape or assign a truth probability. See the [evidence guide](docs/EVIDENCE.md). Use `capture_trends` to save an observation, `analyze_trends` for sustained movement evidence, and `get_changes` with an ISO-8601 `since` checkpoint for additions, removals, movement and unchanged counts. Save a report's `generated_at` for your next check. These signals describe sampled observations, not future virality.

- [Endpoint and MCP catalog](docs/ENDPOINTS.md): methods, parameters, persistence and source coverage.
- [Trend analysis](TREND-ANALYSIS.md): rules, evidence and checkpoint semantics.
- [Agent guide](llms.txt): also served by `GET /llms.txt`.
- [Implemented changes](docs/CHANGES.md): repairs and optimizations.

## Create original video briefs

See [creative-reference workflow](docs/CREATIVE-REFERENCES.md). Save curated references, supply a local video, inspect timestamped frames/OCR/scene/audio evidence, then let your connected AI write and save an original script/storyboard.

```bash
./setup-media.sh
mkdir -p .run/reference-inbox
# Put your authorized reference.mp4 here, then use the MCP workflow:
# add_reference → attach_reference_media → analyze_reference
# → inspect_reference/get_creation_context → save_creative_brief
```

A Reel link alone does not provide video inspection. The backend never downloads source URLs, invents missing speech, verifies audience geography or renders the final video. Source matching, model annotations, supplied counters and generated drafts remain explicitly unverified.

## Collection and verification

Defaults: X/Douyin hourly, TikTok/Instagram every six hours, YouTube daily. Optional `SCRAPE_INTERVAL_HOURS` overrides all sources; `SOURCE_INTERVALS_HOURS` JSON overrides specific sources. Health and analysis share the same freshness policy. Unchanged new content reuses stored topic rows while preserving every capture and retrieval timestamp.

Run `./verification/run_tests.sh` for isolated regression checks. `.venv/bin/python verification/monitoring_live.py` checks real capture reuse and REST/MCP checkpoint reports; it performs network requests and persists real snapshots. Latest evidence and limitations are in [current status](CURRENT-STATUS.md).

## Reproduce the implementation

[Original upstream](https://github.com/caicai-yao/social-trends-mcp) is pinned to commit `c9f413ad1c8c6b387e8cd1af5f0c709f263ceae2`. `setup.sh` clones it into ignored `upstream/`, applies `verification/repairs.patch`, and restores `verification/regression-tests/`. Review that patch for application changes. Raw scrape pages, temporary logs, backups, collection-control state and browser captures stay local. Earlier investigation reports are in [docs/archive](docs/archive).

Source controls now honor Retry-After, pause access-denied/challenge responses and enforce shared attempt budgets. They reduce repeated collection but cannot guarantee that public sources will remain accessible. Use the [evidence guide](docs/EVIDENCE.md) for verification and recovery limits.
