# Verified current state — 2026-11-10

The identified local failures are repaired. All five sources are currently collecting data without paid provider credentials, and `/api/v1/health` reports `healthy`. This report supersedes the earlier setup, repair and provider-only reports.

## Working feeds and their actual coverage

- **X/Twitter:** 30 topics per default scrape from trends24.in, with source metadata. This is a third-party ranking. Volumes are unknown; no fabricated post counts are shown. Search matches observed current topics instead of manufacturing a `Search: ...` item. Hashtag/search URLs are encoded correctly.
- **TikTok:** three ranked hashtags from TikTok One's current official public preview. View/post metrics, actual source country and seven-day window are preserved. US, UK, Japan and Singapore were tested. `global` maps explicitly to US. Generic Discover/Countik fallbacks cannot be relabeled as country-specific results.
- **YouTube:** 30 entries by default from official weekly top **music-video** charts, read with ordinary Chromium. The underlying chart returned 100 videos when requested directly with a larger scraper limit. US, Japan and UK were tested. The tested chart covered October 30–November 5, 2026. These are country/week music-chart views, not lifetime views or all-category realtime trends. Exact/discovery search covers the observed chart; the separate native keyword-search method still requires a YouTube key.
- **Instagram:** eight Reels from the ordinary logged-out public Reels page, rendered by local Chromium. Captions, authors, URLs, publication times, likes and comments are extracted. Missing views stay unknown and likes are labeled as likes. This is a recommendation sample, not a representative or exhaustive global ranking. No Instagram login, saved session, SocialCrawl, paid proxy or API key is needed. Browser mode is the default and never silently falls back to a paid provider.
- **Douyin (抖音):** 30 hot topics per default scrape, from official public hot-list endpoints; direct source tests returned 50 with a higher limit. `cn` and `global` select mainland China. Heat scores and source timestamps are preserved; heat is not labeled as views.

Public/undocumented source interfaces can change or become unavailable. Real failures are exposed rather than replaced with fake trends. No bypass of logins or challenges is implemented. Broader chart/sample coverage and multi-worker operation are outside the verified local scope.

## Correctness repairs

Snapshots now store the **requested region** independently of each topic's actual source region. Latest queries, history and refreshes are isolated by region. A Japan request with no stored Japan snapshot returns a missing state, not mislabeled global data. Unsupported platform/region pairs and unknown regions/platforms are rejected. Instagram accepts global only; Douyin accepts global/cn; mainland China TikTok requests direct callers toward Douyin.

Search operates concurrently on observed feeds, reports per-platform coverage/failures, validates blank queries and limits, and includes feeds without a native search API. An unrelated popular topic cannot qualify merely through a popularity bonus. Matching topics from different platforms are preserved instead of deduplicated across platforms. REST and MCP use the same collection behavior. The README-advertised `search_trends` MCP name is now a supported alias of exact search.

Manual refresh responds HTTP 202. Completed snapshots trigger WebSocket `trends_updated` messages only after commit; payloads match persisted REST data. Failures are also visible. Duplicate in-flight scrapes of the same platform/region are skipped. Source chains and browser attempts are not repeatedly retried after exhaustion.

Freshness metadata reports missing, fresh, stale or unavailable. Its age measures the last retrieval, not the age of an original post or chart period; those source timestamps/windows remain separate metadata. Health degrades when a required source fails, is missing, or its last retrieval exceeds twice the configured interval. All five are healthy at final verification.

The schema upgrade is idempotent for clean and existing PostgreSQL databases: it adds snapshot regions, the Douyin enum value and the needed index, and seeds Douyin in pre-existing platform configurations without altering explicit disabled settings. UTC timestamps are explicit and the test suite no longer emits the previous datetime deprecation warnings. Compose-only `.env` variables no longer break settings parsing.

## Local operation and recovery

The API is running at http://127.0.0.1:8000/docs under a single-instance supervisor. PostgreSQL uses the named Docker volume `social-trends-pgdata` and container `social-trends-db`, bound to loopback port 55433. The earlier database was dumped, restored to the named-volume database, and left intact in the old container; the backup is under `.run/backups/`. No existing snapshots were discarded.

```bash
./setup.sh
./manage-service.sh start
./manage-service.sh status
./manage-service.sh restart
./manage-service.sh stop
```

Setup installs the compatible MCP SDK, Playwright/Chromium, cumulative source patch and regression files. Start waits up to 30 seconds for PostgreSQL readiness. The supervisor restarts a crashed API, guards against duplicate supervisors, and verifies/reconciles a recorded orphan before launching another API. Stop leaves the persistent database intact. Logs are `.run/api.log` and `.run/supervisor.log`.

A real API SIGKILL test recovered in **4.09 seconds**, preserving stored snapshots. A supervisor SIGKILL/orphan test recovered in **1.59 seconds** and removed the original orphan. These demonstrate recovery on this running host, not host-boot integration or a multi-day uptime guarantee. The six-hour scheduler was checked at startup and with an accelerated real interval/shutdown test; six hours of wall-clock waiting was not claimed.

The Docker image `social-trends-local:verified` was built successfully. A bootstrap failure exposed a missing `libatomic1`; that dependency is now installed before Playwright. The built image ran as its app user with Gunicorn/one worker against a fresh isolated database and collected all five live feeds, with healthy status. The temporary test container was stopped afterward. Full Nginx/public HTTPS deployment and multi-replica pub/sub were not tested or claimed.

## Verification and evidence

- **86 tests passed, no warnings**, including real PostgreSQL tests, migrations, search, regional isolation, source schemas, null metrics, paid-fallback prevention, source-chain bounds, duplicate refresh protection, real scheduler triggering/shutdown and orphan safety.
- `verification/final-e2e.json`: five live feeds, JP/CN regional refreshes/history, negative and positive search, validated errors, persisted WebSocket messages and live MCP calls.
- `verification/all-repairs-tests.log`: latest complete suite output.
- `verification/recovery.json`, `verification/orphan-recovery.json`: actual process recovery results.
- `verification/docker-runtime.json`: all five source counts and health from the built container with a fresh isolated database.
- `verification/patch-validation.json`: cumulative patch applies to a pristine copy of upstream commit `c9f413ad1c8c6b387e8cd1af5f0c709f263ceae2`, including newly added source modules.
- `verification/douyin/` and `verification/youtube_live.json`: direct source investigations, timestamps, full coverage and source limitations.

```bash
./verification/run_tests.sh
.venv/bin/python verification/final_e2e.py
```

The suite uses a separate `social_trends_regression` database and never resets the service database. End-to-end checks do make real network requests and write new service snapshots. Recovery scripts intentionally terminate only verified local service processes; they are diagnostic checks, not normal startup commands.

Working source is under `upstream/`. The cumulative patch and complete regression-file snapshot are in `verification/`; the root setup script restores them reproducibly. Two independent source implementation tasks and two read-only integrated reviews were used. The three review findings were reproduced and fixed; the second review found no remaining blockers for this local single-worker scope. At that verification stage no commits, pushes or PRs had been created. No provider accounts or paid subscriptions were created.

## Stored trend intelligence

The MCP now exposes `capture_trends` (persist a real observation) and `analyze_trends` (analyze shared history). Latest suite: **104 passed**. Controlled and live checks passed; live Douyin evidence showed rank 29 → 28 → 20 across three observations. See [TREND-ANALYSIS.md](TREND-ANALYSIS.md) for rules, source limits and reproducible checks. Earlier Docker evidence below/above covers collection; that image predates this analysis addition.

## PR documentation addition

Added [endpoint and MCP catalog](docs/ENDPOINTS.md), [change summary](docs/CHANGES.md), repository [llms.txt](llms.txt) and a matching `GET /llms.txt` route. Latest full regression run: **105 passed** (`verification/pr-tests.txt`). The guide endpoint was reproduced as missing (404), implemented, and verified.
