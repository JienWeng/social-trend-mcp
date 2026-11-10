# Supported interfaces

Default local base URL: http://127.0.0.1:8000. REST responses are JSON unless noted. Platform identifiers: `twitter`, `tiktok`, `youtube`, `instagram`, `douyin`.

## HTTP and WebSocket

| Method | Path | Parameters and behavior |
| --- | --- | --- |
| GET | `/` | Service metadata and platform identifiers. |
| GET | `/docs` | Interactive OpenAPI documentation (HTML). |
| GET | `/redoc` | Alternative API documentation (HTML). |
| GET | `/openapi.json` | Machine-readable OpenAPI schema. |
| GET | `/llms.txt` | Plain-text agent guide with interfaces, persistence rules and source limits. |
| GET | `/api/v1/trends` | Latest stored snapshots; `region=global`, `limit=30` (1–100). Does not fetch upstream. |
| GET | `/api/v1/trends/{platform}` | Latest stored snapshot for a platform; same region/limit parameters. |
| GET | `/api/v1/trends/history/{platform}` | Stored history; `region=global`, `hours=72` (1–8760), `limit=12` snapshots (1–100). |
| GET | `/api/v1/search/exact` | Required `q` (1–200 characters); `region=global`, optional comma-separated `platforms`. Fetches observed feeds; does not persist them. |
| GET | `/api/v1/search/discover` | Required `q`; `region=global`, `min_relevance=10` (0–100). Keyword expansion and relevance scoring over observed feeds; does not persist them. |
| POST | `/api/v1/refresh` | Queues persisted collection; optional `platform`, `region=global`. Returns 202 before collection completes. |
| GET | `/api/v1/regions` | Region catalog. Availability varies by platform. |
| GET | `/api/v1/platforms` | Platforms and supported region combinations. |
| GET | `/api/v1/health` | Healthy/degraded collection state, freshness and per-platform statistics. HTTP 200 can contain degraded status. |
| GET | `/api/v1/analysis/trends` | Stored momentum signals; optional `platform`, `region=global`, `hours=48` (1–720), `limit=20` topics/platform (1–100). |
| POST | `/api/v1/analysis/capture/{platform}` | Fetches and persists a snapshot; `region=global`. 200 captured, 202 capture already running (not persisted by this call), 502 failed capture recorded. |
| WebSocket | `/ws/trends` | Persisted collection updates after database commit. Send text `ping` to receive `pong`. In-process broadcast: run one worker. |

Invalid platform/region combinations return 400; parameter validation failures return 422. Empty results or a source failure do not establish that a topic is absent from the entire platform. Search responses include per-platform coverage.

## MCP (stdio)

Launch `./start-mcp.sh` after setup. There is no HTTP MCP endpoint. Paths in mcp-config.json are an example for this workspace; configure the script's absolute path on another machine.

| Tool | Arguments | Behavior |
| --- | --- | --- |
| `get_trends` | Required `platform`; `region=global`, `limit=20` (1–50). | Direct feed fetch with 30-minute cache; does not persist. |
| `get_all_trends` | `region=global`, `limit=10` (1–50). | Direct fetch/cache across available sources; reports coverage. Does not persist. |
| `exact_search` | Required `query`; optional `region`, `platforms` array. | Exact matches in observed feeds, not full-platform search. Does not persist. |
| `search_trends` | Same as exact_search. | Alias for exact_search. |
| `discover_search` | Required `query`; optional `region`, `min_relevance` (default 10). | Related observed topics from keyword expansion and relevance scoring. Does not persist. |
| `list_regions` | None. | Region catalog; check platform-specific availability. |
| `capture_trends` | Required `platform`; `region=global`. | Calls the REST capture endpoint, saving shared PostgreSQL history. |
| `analyze_trends` | Optional `platform`, `region=global`, `hours=48` (1–720), `limit=20` (1–100). | Calls shared stored-history analysis; evidence, warnings and qualitative confidence. |

Capture/analysis tools require the running API at `API_BASE_URL`, default http://127.0.0.1:8000. Other MCP tools query sources directly.

## Source coverage

- X: third-party trends24 rankings, not official firehose; unavailable volumes are unknown.
- TikTok: limited official public preview. Global currently maps to US. Generic fallbacks cannot establish country rankings.
- YouTube: keyless fallback is weekly music-video charts; global maps to US. Broader API-backed behavior requires a key.
- Instagram: public logged-out Reels recommendation sample, global only; not an Instagram-wide trends ranking or own-account analytics.
- Douyin: public China hot-topic list; accepts global/cn and reports actual source region cn. Heat scores are not views.

Use the live platform/region catalog rather than assuming every region works everywhere. Public endpoints may change or block collection. Optional paid adapters are explicit opt-ins. Analysis rules and evidence are documented in [TREND-ANALYSIS.md](../TREND-ANALYSIS.md).
