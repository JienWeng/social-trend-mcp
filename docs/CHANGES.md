# Implemented changes

This repository reconstructs a repaired version of caicai-yao/social-trends-mcp at commit c9f413ad1c8c6b387e8cd1af5f0c709f263ceae2. Source changes are reviewable in verification/repairs.patch; regression tests live in verification/regression-tests/. setup.sh applies both to the ignored upstream/ checkout.

## Collection and truthful coverage

- Restored five keyless default sources: X third-party rankings, TikTok official public preview, YouTube weekly music-video charts, Instagram public Reels recommendation samples, and official public Douyin hot topics.
- Added Douyin enum, scraper, configuration seeding and idempotent database initialization for existing installations.
- Separated requested snapshot region from the actual source region. Unsupported combinations fail clearly; generic TikTok fallbacks cannot manufacture country attribution.
- Preserved source URLs, chart periods/source timestamps, Unicode and metric units. Missing views remain unknown; heat scores and likes are not presented as views.
- Kept paid Instagram adapters explicit opt-ins; no automatic paid fallback.
- Bounded source attempts/timeouts and prevented duplicate concurrent captures.

## Persistence, search and realtime delivery

- Stored collection outcomes, topics and region-specific history in PostgreSQL.
- Made exact search and discovery operate on observed feeds with per-platform coverage. Removed fabricated search results and unrelated popularity-only matches.
- Broadcast WebSocket updates after commit, with snapshot/topic payloads, safe connection iteration and send timeouts.
- Added freshness and degraded health reporting. Failed sources do not populate successful fetch caches.
- Added a local supervisor with single-instance locking, API crash restart and verified orphan reconciliation. PostgreSQL uses a named Docker volume.
- Repaired Chromium container dependencies, settings parsing, UTC handling and single-worker Docker configuration.

## Stored trend analysis

- Added shared REST/MCP capture and analysis. capture_trends persists real observations; analyze_trends reads shared history. Existing fetch/search tools remain non-persisting queries.
- Added minimum independent evidence, rank and metric comparisons, source/window compatibility checks, stale/failed-data suppression, and explicit uncertainty.
- Added stable, falling, new_to_sample, mixed_movement, insufficient_history and insufficient_evidence signals.
- Guarded against counter resets hidden by downsampling and against high capture volume starving another platform's history.
- Returned snapshot-linked evidence, warnings, qualitative confidence and per-platform truncation flags. No paid LLM call or forecast is involved.

## Documentation and validation

- Added the complete endpoint/MCP catalog, coverage limits, setup/service commands and analysis guide.
- Added repository llms.txt and a matching GET /llms.txt plain-text API route.
- Verified isolated PostgreSQL regression tests, controlled synthetic analysis without production writes, and real REST/MCP persistence and analysis.
- Earlier live checks covered all five sources, regional history/search, committed WebSocket delivery, process recovery and the collection Docker image.
- The previously built Docker image predates analysis and llms.txt; rebuild from reconstructed upstream/ to deploy those additions. Public HTTPS, multiple replicas and predictive accuracy have not been validated.

See CURRENT-STATUS.md and TREND-ANALYSIS.md for dated evidence. Public sources can change; Instagram remains a recommendation sample, YouTube fallback remains weekly music only, and no source set guarantees exhaustive platform-wide trend discovery.
