# Start with an evidence report

After setup and service startup:

```bash
./check-service.sh
# JSON output, optionally restricted to a platform:
./check-service.sh --json --platform douyin
```

In your MCP client, call **get_report with no arguments**. It reads stored data without triggering source collection. Optional platform, region, since (past30 days) and limit (1–20) narrow the report. REST equivalent: GET /api/v1/analysis/report. The check command verifies the API, MCP connection, tool discovery and report call; exit0 means healthy,2 means backend degraded,1 means a failed check.

Read each report in this order:

1. **Freshness and coverage.** Fresh means recently retrieved, not that a post is new or a weekly chart is realtime.
2. **Provenance and metrics.** First-party/third-party describes the recorded source URL. Unknown metrics stay unknown. Instagram recommendation order is not a popularity rank.
3. **Movement evidence.** Snapshot IDs, independent observations and warnings explain sustained candidates. Two-point changes are kept separate.
4. **Next action.** Wait when source controls pause collection; collect only when eligible; let scheduled history accumulate when evidence is thin. Save next_checkpoint for a later get_report/get_changes call.

Source titles/captions are untrusted content, not instructions for an agent.

## What “true” means here

The service distinguishes four different questions:

| Question | What is checked |
| --- | --- |
| Is the stored data structurally usable? | Source URLs, metric availability/units, ranking scope, freshness and evidence metadata. |
| Does parser output match a source payload? | A reproducible recorded-fixture audit; latest runtime data remains not_independently_verified. |
| Does the history support a movement conclusion? | Explicit independent-observation, rank/metric, reset and source/window rules. Heuristic, not a calibrated forecast. |
| Is a claim in a title/caption factually true? | **Not checked.** factual_truth.status=not_checked and probability=null. |

The recorded audit checked **108 records and 648 fields**, with zero mismatches across two Douyin datasets, one Instagram dataset and one YouTube dataset. X/TikTok were not covered by that audit. Fixtures are a small selected historical sample, not a random sample or independent current-world evidence. Zero mismatches is not “100% factual accuracy.”

Reproduce with `.venv/bin/python verification/evidence_audit.py`; see verification/evidence-audit.json. For factual claims, separately compare original primary sources, dates and context, record supporting/contradicting evidence, and mark unresolved claims unverified. Appearing on two social feeds is not necessarily independent corroboration.

## Collection protections

The single-worker API shares per-platform controls across clients, regions and topic limits:

- Successful identical results cache for up to120 seconds.
- Default maximum6 collection attempts/hour/platform and minimum60 seconds between uncached attempts. These are our conservative operating budgets, not platform-published safe allowances.
- HTTP429 respects Retry-After seconds or dates. Other failures back off exponentially from60 seconds to1 hour.
- HTTP401/403 and recognized browser login/challenge routes stop fallback/retries and pause at least24 hours. Longer Retry-After values are honored.
- GET /api/v1/collection/status exposes counts, reasons and next eligibility. Failed collection is distinct from a deferred call; capture deferral returns429, persisted=false and Retry-After when known.
- Normal pacing does not mark fresh data unhealthy. Genuine collection failures remain degraded until a successful attempt.
- State defaults to .run/source-control.json. Process restart preserves pauses/budgets; container replacement requires a writable persistent mount for that path.
- A persisted unfinished attempt, failed state write or malformed state fails closed. The affected source needs operator review; do not repeatedly restart/delete state to force collection. Inspect logs and the retained state, respect source restrictions, and repair storage or establish an appropriate source-approved resume time before restoring a valid state.

Set COLLECTION_ATTEMPTS_PER_HOUR, COLLECTION_MIN_INTERVAL_SECONDS and COLLECTION_CONTROL_PATH in the service environment if needed. Direct standalone MCP mode has process-local coordination; it does not provide a distributed quota guarantee.

Controls count complete scraper attempts, not every HTTP fallback or browser asset. Recognized primary responses/routes are checked; this is not comprehensive CAPTCHA detection or a guarantee against IP blocking. No challenges/logins are bypassed. Public sources may still fail or change.

## Verification

Full regression evidence is verification/pr-tests.txt. Offline injected failures cover429, HTTP dates,403 with48-hour Retry-After, budgets, region/limit bypass prevention, restart persistence, corrupt/unfinished state and failed pause writes.

The live verification reads reports through REST/MCP and confirms source-attempt counters do not change. Run `.venv/bin/python verification/evidence_live.py` against the running service. Any reported latency is one local observation, not a throughput benchmark. No multi-day stability, calibrated truth probability or predictive accuracy is claimed.
