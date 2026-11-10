# Verified current state — November 10, 2026

The local single-worker service collects all five keyless default sources and exposes REST, WebSocket and nine stdio MCP tools. Public endpoints can change; these feeds are not exhaustive global realtime rankings.

## Coverage

| Source | Verified default collection | Scope |
| --- | --- | --- |
| X | 30 topics | Third-party trends24 ranking; unknown volumes remain unknown. |
| TikTok | 3 tags | Limited official public preview; global maps to US. US/GB/JP/SG were tested. |
| YouTube | 30 entries | Weekly music-video charts via ordinary Chromium; global maps to US. US/GB/JP tested; direct larger requests returned 100. |
| Instagram | 8 Reels | Logged-out public recommendation sample, global only; no login or automatic paid fallback. |
| Douyin | 30 topics | Official public China hot list; global/cn map to cn. Direct requests returned 50. Heat scores are not views. |

See [endpoint catalog](docs/ENDPOINTS.md) and [Instagram details](INSTAGRAM-SETUP.md). No login/challenge bypass is implemented.

## Current improvements

- One API collection cache coalesces concurrent identical fetches for up to 120 seconds. REST search, live feeds, persisted captures and default MCP fetch/search share it. Failed results are not cached.
- Default cadence is hourly X/Douyin, six-hourly TikTok/Instagram and daily YouTube; global/per-source overrides are supported. Health and analysis mark retrievals stale after twice the applicable interval.
- Scheduled collection honors enabled platforms and configured regions; saved captures honor max_topics. Snapshot requested regions and actual source regions stay separate.
- Every capture retains its ID and timing. Identical new source-aware content reuses canonical topic rows; metadata/edition changes remain distinct. Existing historical duplicates are not rewritten or deleted.
- History loads snapshots/topics in two queries rather than one query per snapshot. Latest/history/analysis/WebSocket/capture responses resolve reused content.
- Checkpoint reports show sample additions/removals, rank/comparable metric changes and unchanged counts, with evidence and separate sustained momentum. Baselines exclude data fetched or completed after the checkpoint.
- Search covers observed feeds and reports coverage. No fabricated matches or popularity-only unrelated results.
- WebSocket updates follow commit. Single-instance supervisor, API crash/orphan recovery, named-volume PostgreSQL and idempotent schema upgrades remain supported.

## Verification

Latest suite: **120 passed**, including isolated PostgreSQL, cache/single-flight behavior, failure retries, configuration/cadence, content reuse, source-edition separation, batched history, change reports, counter resets and checkpoint availability. Tests use social_trends_regression, not the service database.

Focused evidence:

- `verification/pr-tests.txt`: latest full suite.
- `verification/monitoring-live.json`: real unchanged-content capture reuse, preserved retrieval time and matching REST/MCP checkpoint reports.
- `verification/analysis-demo.json`, `analysis-live.json`: controlled and earlier real momentum evidence. The earlier Douyin rank 29 → 28 → 20 candidate is a dated observation, not a prediction.
- `verification/final-e2e.json`: earlier five-source, regional, search and committed WebSocket checks.
- `verification/recovery.json`, `orphan-recovery.json`: actual process recovery.
- `verification/patch-validation.json`: cumulative patch applies to pristine pinned upstream, including all new source files.

Review reproduced and fixed the post-checkpoint baseline bug; follow-up static review found no concrete blockers. No synthetic service history, paid provider accounts or paid subscriptions were created.

## Operation and limits

Use README for setup/service commands, docs/ENDPOINTS.md for interface contracts and TREND-ANALYSIS.md for interpretation. Older reports are archived rather than maintained as competing setup guides.

The running local API includes these optimizations. Previously verified Docker collection-image evidence predates analysis/llms.txt/monitoring changes: rebuild to include them. Public HTTPS and multiple replicas remain unverified. Cache/locks/WebSocket are process-local; run one worker. Canonical content snapshots are protected by references and must not be deleted while referenced; automatic retention deletion is intentionally absent.

No cross-platform semantic clustering, watchlist notifications or predictive accuracy claim is included. The useful output is an evidence-based report of what changed in the feeds actually observed.
