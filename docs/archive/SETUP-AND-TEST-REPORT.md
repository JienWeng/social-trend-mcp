> Historical investigation. Current behavior: [current status](../../CURRENT-STATUS.md).

# Setup and verification — 2026-11-10 UTC

Update: local repairs have since been applied; see `REPAIR-REPORT.md` for current behavior. The findings below describe the original upstream baseline.

Verdict: the software can run locally with a compatibility workaround, but it does not deliver reliable real-time trends across all four platforms as advertised.

Source: https://github.com/caicai-yao/social-trends-mcp
Tested commit: c9f413ad1c8c6b387e8cd1af5f0c709f263ceae2

## Local setup

The upstream checkout is in `upstream/`, unchanged. Python dependencies are isolated in `.venv/`. PostgreSQL 16 runs in Docker container `social-trends-test-db`, bound to loopback port 55432. Its password is a local test fixture, not a production credential. The REST server binds to loopback port 8000.

Run `./setup.sh` to prepare the environment (requires uv, Git and Docker). Run `./start-api.sh` to start the API when it is not already running. Open http://127.0.0.1:8000/docs on this machine. Use `./start-mcp.sh` for an MCP stdio client; `mcp-config.json` contains this machine's absolute configuration. No client settings were changed automatically. These paths work on this host, not a different desktop.

Upstream's unconstrained `mcp>=1.2.0` installs SDK 2.3.0 and fails during import: `AttributeError: 'Server' object has no attribute 'list_tools'`. Installing `mcp>=1.2,<2` resolved this (tested SDK 1.30.0). The packaged `social-trends-mcp` console command still exits with `coroutine 'main' was never awaited`, because its entry point is an async function. The launcher uses `python upstream/mcp_server.py`, which correctly calls asyncio.run.

## Executed checks

- Source editable installation succeeds; the default dependency set cannot import the MCP server. SDK 1.x workaround verified.
- Real MCP stdio initialization, tool discovery and `list_regions` call pass. Five tools exposed: get_trends, get_all_trends, exact_search, discover_search, list_regions. README's `search_trends` tool does not exist.
- Direct tool calls exercised all-platform trends, exact search, Chinese discovery and region listing. Independent live scraper runs tested all four platforms without credentials.
- REST startup creates PostgreSQL tables and runs the initial scheduled scrape. The six-hour job is registered; waiting six hours was not tested.
- Root, docs, OpenAPI, health, platforms, regions, all trends, single-platform trends and history return HTTP 200. Invalid platform returns 400; zero limit returns 422.
- Manual Twitter refresh returns 200 and increments persisted snapshot count. History returns stored data.
- WebSocket ping returns pong. A completed and persisted refresh produces no WebSocket update within the observation window. Source inspection confirms `broadcast_update` has no callers.

## Data and correctness failures

1. Twitter: 30 topics from trends24.in, with no parsed volumes. This is third-party scraped data; freshness was not independently established. Hashtag URLs contain unescaped `#`, which makes the hashtag a URL fragment instead of a search query value.
2. TikTok: only one item, `en`, from the Discover page. The Creative Center request returned HTTP 200 but no usable results. The fallback incorrectly treats a language value as a topic.
3. YouTube: zero videos from the unauthenticated web fallback, yet its scraper records success. An HTTP 200 and health response do not establish usable trends.
4. Instagram: 22 items from best-hashtags.com, including navigation labels `New Hashtags`, `Best Hashtags`, and `Hashtags Index`; no popularity counts. The final fallback is also a fixed list of evergreen hashtags, without a stale/synthetic marker.
5. Exact search for invented `qzxvnonexistent987` reports a relevant Twitter result titled `Search: qzxvnonexistent987`. This is a generated link, not observed platform evidence. REST Instagram exact search returns no results because that scraper has no search method.
6. REST region `jp` is echoed in the response but the returned stored Twitter topics remain `global`. Region is never passed into the database query or used to filter records.
7. Chinese discovery of `人工智能` runs but expands no related terms with the local graph. LLM-backed multilingual expansion was not tested.
8. WebSocket connections work, but automated trend broadcasts are not wired into the scrape service.

## Limits and next steps

No YouTube, X, Meta or LLM API credentials were supplied. Authenticated provider paths remain unverified. Full upstream Docker Compose/Nginx deployment, four-worker behavior, all 20 regions, long-term refresh reliability and production security were not tested. This setup uses one API worker and a Docker PostgreSQL container. The bundled Docker workers each start a scheduler; production deployment needs a review of duplicate jobs and process-local WebSocket connections.

For meaningful YouTube testing, configure a real API key privately in the workspace root `.env` (the launchers run from this directory) as `YOUTUBE_API_KEY`, then restart the API and MCP processes. Do not copy placeholder tokens from `.env.example`. Code repairs are needed for the other data-quality and reporting issues before trusting these outputs for decisions.

## Evidence and reruns

- `verification/scrapers.json`: complete live scraper output.
- `verification/direct-tools.json`: tool outputs, including the false search match.
- `verification/mcp-protocol.json`: actual MCP initialization, schemas and region call.
- `verification/api-results.json`: REST responses and WebSocket/refresh results.
- `verification/api.log` and `verification/probe-output.log`: runtime logs.
- `verification/installed.txt`: installed dependency versions.

Rerun `.venv/bin/python verification/probe.py` and, with the API running, `.venv/bin/python verification/api_probe.py`. These probes perform real network requests and refresh the test database; results may change over time. Stop the API with Ctrl-C in its terminal and stop the database with `docker stop social-trends-test-db` when finished. Removing that container deletes this test database because no persistent volume was configured.
