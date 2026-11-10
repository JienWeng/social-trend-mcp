# Social trend correctness and reliability implementation plan

Goal: eliminate misleading search/regions, restore useful free sources, and provide recoverable local operation with observable freshness.

Architecture: preserve existing async scrapers and PostgreSQL snapshots. Add snapshot region with backward-compatible migration and strict regional queries. Keep browser sources explicitly labeled samples/charts and never claim inaccessible data.

- [x] X: test invented keyword, search real scraped trends only, URL-encode queries, attach source metadata.
- [x] Regions: test per-region success/failure/history isolation. Add snapshot region and startup migration; validate region/platform pairs at REST/MCP boundaries and refresh into requested region.
- [x] YouTube: independently diagnose current public charts/pages; add test-first parser and verified no-key source if accessible. Preserve truthful source/category/window labels.
- [x] Douyin: independently investigate public hot list. Add scraper/tests only if usable data exists, then integrate enum/registry/API/MCP with PostgreSQL enum migration.
- [x] Search: unify REST exact search with observed trends; validate empty queries, invalid platforms, relevance limits; expose partial errors.
- [x] Reliability: add stale state and retained history, single-instance supervisor guard, per-region scrape lock, bounded browser startup; handle orderly cancellation.
- [x] Operations: local process supervisor with restart and persistent DB volume; verify restart/recovery and scheduler triggering without pretending multi-day testing.
- [x] Verification: full tests, clean schema and existing schema migrations, live sources, REST region/filter/search/history/refresh, WebSocket, MCP, restart test. Save cumulative patch and authoritative current report.
