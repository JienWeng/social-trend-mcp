> Historical investigation. Current behavior: [current status](../../CURRENT-STATUS.md).

# Repairs and remaining data-access limits

**Superseded by the deeper diagnosis in `CURRENT-STATUS.md`: TikTok now works through its current public endpoint. Instagram suggestions are now opt-in.**

Applied locally on 2026-11-10 to upstream commit c9f413ad1c8c6b387e8cd1af5f0c709f263ceae2. No changes were pushed to GitHub.

## TikTok

The Creative Center endpoint returns HTTP 200 with application error `40101: no permission`. The Discover page contains no usable hashtag listing; the old recursive parser mistakenly harvested generic JSON `name` fields, producing `en`. Countik returns HTTP 403.

The parser now accepts explicit, validated hashtag links rather than arbitrary metadata. API permission errors are checked and retained in the failure message. Search no longer manufactures a matching `Search: ...` item. Empty scrapes are failures. Live retest: zero topics, failed snapshot, with the precise denial reasons visible in REST and WebSocket output.

This fixes incorrect data and false success; it does not restore TikTok data access. An accessible, authorized TikTok data source is still required. No login, proxy subscription, or paid data provider was configured. Changing parsing cannot turn a permission denial into valid trend data.

## Instagram

The old parser selected every URL containing `hashtag`, including site navigation. It also silently returned a static list when all sources failed.

The repaired fallback reads only the publisher's explicit Trending Hashtags article, checks hashtag URL and label agreement, validates names, deduplicates, and ranks the accepted items. Static fallback data and unverified generic parser sources were removed. Live retest: `stayhome`, `likes`, `quotes`, each with source and `third_party_hashtag_suggestions` metadata and a description explaining that freshness and live Instagram popularity are not verified.

This is a cleaner third-party hashtag suggestion feed, not a verified real-time Instagram trend feed. Authenticating the existing Meta path and validating its API contract remain separate work; no Meta credentials were provided.

## WebSocket and service status

The scrape service never called `broadcast_update`. It now emits a `trends_updated` message after a committed scrape snapshot, including platform, snapshot (status/error) and persisted topics. Successful and failed updates are both broadcast. Broadcasts use a snapshot of connected sockets and a five-second send timeout; failed clients are removed.

REST now returns the latest attempt, including failure, instead of silently serving an earlier successful snapshot. Existing old records are retained in history. Topic source metadata and scrape error messages are exposed. Health returns `degraded` when a platform is missing data or its latest scrape failed, while preserving HTTP 200 for process liveness.

The Docker default was reduced to one worker. Socket connections and scheduling are process-local; running multiple workers or replicas still requires a shared event broker and one scheduler owner. Multi-worker deployment was not claimed or tested.

## Verification

Eight automated tests pass, including a real PostgreSQL integration test proving that snapshots are visible to another connection before broadcast. The tests were observed failing against the original code before repairs. Five existing datetime.utcnow deprecation warnings remain.

`verification/check_repairs.py` passes against the restarted live API: ping/pong works, refresh events arrive, and persisted REST topics/snapshot match the events for Instagram and TikTok. Instagram has clean source-labeled suggestions; TikTok has an explicit failure instead of invalid data. Full outputs are in `verification/repair-live-results.json`.

The API remains at http://127.0.0.1:8000/docs on this host. Its overall health is expected to be degraded while TikTok is inaccessible and YouTube has no API key.

## Reproduce

`setup.sh` reapplies `verification/repairs.patch` to the tested upstream revision and copies the regression tests. Already-applied patches are detected; conflicting local edits stop setup. The working source remains in `upstream/`.

For the full test suite, create a dedicated PostgreSQL database named `social_trends_regression`, then run from `upstream/`:

```bash
TEST_DATABASE_URL=postgresql+asyncpg://postgres:local-test-only@127.0.0.1:55432/social_trends_regression ../.venv/bin/pytest -q
```

The integration test resets tables only in this designated test database. Run `.venv/bin/python verification/check_repairs.py` from the workspace root to repeat live refresh and WebSocket checks. This uses real network requests and writes new snapshots to the local service database.
