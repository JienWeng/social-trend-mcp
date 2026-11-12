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
| GET | `/api/v1/feeds/{platform}` | Shared live/cache feed; `region=global`, `limit=30` (1–100). Does not persist. Successful results cached up to 120 seconds; failures are not cached. |
| GET | `/api/v1/trends` | Latest stored snapshots; `region=global`, `limit=30` (1–100). Does not fetch upstream. |
| GET | `/api/v1/trends/{platform}` | Latest stored snapshot for a platform; same region/limit parameters. |
| GET | `/api/v1/trends/history/{platform}` | Stored history; `region=global`, `hours=72` (1–8760), `limit=12` snapshots (1–100). |
| GET | `/api/v1/search/exact` | Required `q` (1–200 characters); `region=global`, optional comma-separated `platforms`. Fetches observed feeds; does not persist them. |
| GET | `/api/v1/search/discover` | Required `q`; `region=global`, `min_relevance=10` (0–100). Keyword expansion and relevance scoring over observed feeds; does not persist them. |
| POST | `/api/v1/refresh` | Queues persisted collection; optional `platform`, `region=global`. Returns 202 before collection completes. |
| GET | `/api/v1/regions` | Region catalog. Availability varies by platform. |
| GET | `/api/v1/platforms` | Platforms and supported region combinations. |
| GET | `/api/v1/collection/status` | Shared per-platform attempt budgets, cooldown reasons, counters and next eligibility. Does not collect. |
| GET | `/api/v1/health` | Healthy/degraded collection state, freshness and per-platform statistics. HTTP 200 can contain degraded status. |
| GET | `/api/v1/analysis/report` | Start here: read-only evidence report. Optional `platform`, `region=global`, `since` (past30 days; default24h ago), `limit=5` (1–20). Stored data, provenance/metric checks, movement, changes and next actions. No truth probability or scrape. |
| GET | `/api/v1/analysis/trends` | Stored momentum signals; optional `platform`, `region=global`, `hours=48` (1–720), `limit=20` topics/platform (1–100). |
| GET | `/api/v1/analysis/changes` | Required `since` ISO-8601 checkpoint within past 30 days; optional `platform`, `region=global`, `limit=20` (1–100 per section). Added/removed/changed sample topics, unchanged count, snapshot evidence and separate momentum. No scrape. |
| POST | `/api/v1/analysis/capture/{platform}` | Fetches and persists a snapshot; `region=global`. 200 captured, 202 capture already running (not persisted by this call), 502 failed capture recorded; 429 source collection deferred (persisted=false, optional Retry-After). |
| WebSocket | `/ws/trends` | Persisted collection updates after database commit. Send text `ping` to receive `pong`. In-process broadcast: run one worker. |

Invalid platform/region combinations return 400; parameter validation failures return 422. Empty results or a source failure do not establish that a topic is absent from the entire platform. Search responses include per-platform coverage.

## MCP (stdio)

Launch `./start-mcp.sh` after setup. There is no HTTP MCP endpoint. Paths in mcp-config.json are an example for this workspace; configure the script's absolute path on another machine.

| Tool | Arguments | Behavior |
| --- | --- | --- |
| `get_report` | No required arguments; optional `platform`, `region=global`, `since`, `limit=5` (1–20). | Read-only stored evidence, source coverage, metric availability, momentum, changes, collection controls and next actions. Start here. |
| `get_trends` | Required `platform`; `region=global`, `limit=20` (1–50). | Shared API feed fetch/cache (up to 120 seconds); does not persist. |
| `get_all_trends` | `region=global`, `limit=10` (1–50). | Shared API fetch/cache across available sources; reports coverage. Does not persist. |
| `exact_search` | Required `query`; optional `region`, `platforms` array. | Exact matches in observed feeds, not full-platform search. Does not persist. |
| `search_trends` | Same as exact_search. | Alias for exact_search. |
| `discover_search` | Required `query`; optional `region`, `min_relevance` (default 10). | Related observed topics from keyword expansion and relevance scoring. Does not persist. |
| `list_regions` | None. | Region catalog; check platform-specific availability. |
| `get_changes` | Required `since` ISO-8601; optional `platform`, `region=global`, `limit=20` (1–100). | Compare current stored sample with last successful data fetched and completed at/before checkpoint; returns evidence and separate sustained momentum. |
| `capture_trends` | Required `platform`; `region=global`. | Calls the REST capture endpoint, saving shared PostgreSQL history. |
| `analyze_trends` | Optional `platform`, `region=global`, `hours=48` (1–720), `limit=20` (1–100). | Calls shared stored-history analysis; evidence, warnings and qualitative confidence. |

Fetch/search/capture/analysis/change-report tools use the running API at `API_BASE_URL`, default http://127.0.0.1:8000, sharing one collection cache and in-flight requests. `MCP_FETCH_MODE=direct` explicitly enables standalone fetch/search (process-local cache); capture/analysis/changes still require the API. `list_regions` is local.

## Source coverage

- X: third-party trends24 rankings, not official firehose; unavailable volumes are unknown.
- TikTok: limited official public preview. Global currently maps to US. Generic fallbacks cannot establish country rankings.
- YouTube: keyless fallback is weekly music-video charts; global maps to US. Broader API-backed behavior requires a key.
- Instagram: public logged-out Reels recommendation sample, global only; not an Instagram-wide trends ranking or own-account analytics.
- Douyin: public China hot-topic list; accepts global/cn and reports actual source region cn. Heat scores are not views.

Use the live platform/region catalog rather than assuming every region works everywhere. Public endpoints may change or block collection. Optional paid adapters are explicit opt-ins. Analysis rules and evidence are documented in [TREND-ANALYSIS.md](../TREND-ANALYSIS.md).

## Collection and storage policy

Defaults: X/Douyin hourly; TikTok/Instagram every six hours; YouTube daily. `SCRAPE_INTERVAL_HOURS` overrides all sources; `SOURCE_INTERVALS_HOURS` JSON overrides specific sources and takes precedence. Freshness is twice the applicable interval in health, latest trends, analysis and change reports. Scheduling honors enabled platforms and configured regions; saved captures honor configured max_topics (clamped to 1–100).

Captures retain separate IDs/timestamps. New identical source-aware payloads reuse earlier topic rows via content_snapshot_id; content_reused identifies this and fetched_at retains the actual retrieval time. Legacy rows remain readable. Referenced canonical snapshots must not be deleted; no automatic retention deletion is configured. Existing historical duplicates are retained.

Collection protections and the difference between field fidelity and factual truth are documented in [EVIDENCE.md](EVIDENCE.md). Use `./check-service.sh` for a read-only readiness check.


## Creative reference library and briefs

These interfaces inspect explicitly supplied local media. Source links remain metadata and are not downloaded. See [creative-reference guide](CREATIVE-REFERENCES.md) for the workflow, schemas and limits.

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/api/v1/references` | Create curated metadata; source URL, country/language/niche/audience labels are declared/unverified. |
| GET | `/api/v1/references` | List metadata summaries; optional platform/niche/target_country/language, limit1–50. |
| GET | `/api/v1/references/{reference_id}` | Full saved metadata, analysis, transcript and attributed annotations. |
| PUT | `/api/v1/references/{reference_id}/media` | Stream raw binary upload; default100MiB, immutable media identity. |
| POST | `/api/v1/references/{reference_id}/analyze` | Bounded local FFprobe/FFmpeg/OCR and optional offline ASR. |
| GET | `/api/v1/references/{reference_id}/frames/{frame_id}` | Hash-checked JPEG frame. |
| PUT | `/api/v1/references/{reference_id}/transcript` | Explicit timed transcript, user-supplied/unverified. |
| POST | `/api/v1/references/{reference_id}/annotations` | Append observed/inferred client claims with validated source times/evidence. |
| POST | `/api/v1/references/{reference_id}/metrics` | Record supplied counters/time; no platform fetch/verification. |
| GET | `/api/v1/references/{reference_id}/performance` | Counter history/deltas with reset/source-change warnings. |
| POST | `/api/v1/creation/context` | Evidence and schema for the connected AI to create an original draft; backend generation_performed=false. |
| POST | `/api/v1/creation/briefs` | Save a client-generated, unreviewed original script/storyboard with cited frame evidence. |
| GET | `/api/v1/creation/briefs` | List saved drafts, limit1–20. |
| GET | `/api/v1/creation/briefs/{brief_id}` | Retrieve one draft. |

Library failures:400/422 invalid metadata/media/evidence,404 missing records/frames,409 immutable media or concurrent operation,413 size limit,503 missing processing tools,504 timeout. All creation/reference JSON bodies are limited to2MiB.

Twelve additional MCP tools (22 total): `add_reference`, `list_references`, `attach_reference_media`, `analyze_reference`, `inspect_reference`, `set_reference_transcript`, `annotate_reference`, `record_reference_metrics`, `get_reference_performance`, `get_creation_context`, `save_creative_brief`, `list_creative_briefs`. inspect_reference returns up to7 JPEG image blocks; get_creation_context caps images at8 across references. All use the backend; local media imports are restricted to REFERENCE_INBOX_DIR.
