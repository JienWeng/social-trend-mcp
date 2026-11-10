# Useful Trend Monitoring Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce duplicate collection/storage and turn stored captures into useful change reports.

**Architecture:** One process-local fetch coordinator coalesces concurrent requests and caches successful public results briefly. Persisted captures remain distinct observations, but identical source-aware payloads may reference an earlier snapshot's content. REST/MCP use shared change-report logic; the API remains single-worker.

**Tech Stack:** FastAPI, MCP stdio, PostgreSQL/SQLAlchemy async, APScheduler, pytest.

User requested planning and resolution after the audit; proceed with these implementation choices without another approval round.

- [x] Shared collection: add app/fetching.py coordinator with bounded cache, per-source/region/topic-limit keys and single-flight behavior. Route REST/MCP/saved captures through it. Test reuse, failure retry, concurrent callers and key isolation.
- [x] Consistent policy: add app/policy.py for source-specific intervals and freshness. Default X/Douyin hourly, TikTok/Instagram six-hourly, YouTube daily (weekly edition dedup remains). Honor global interval override and per-platform overrides. Scheduler retains startup collection and configuration enable/region behavior. Pass configured max_topics to persisted scrapers.
- [x] Storage/query optimization: add nullable content_snapshot_id/content_hash migration; reference identical source-aware successful content without deleting captures. Resolve referenced content in latest/history/analysis/capture; history batch loads in two queries. Test repeated content preserves timestamps, changed source edition remains distinct and legacy rows remain readable.
- [x] Useful report: add GET /api/v1/analysis/changes and MCP get_changes with since timestamp, optional platform/region/limit. Compare latest current capture to last successful baseline at/before since: added, removed, rank/metric movement, unchanged counts, snapshot evidence and no-baseline/failed/stale states. Include stored momentum evidence; do not call disappearance a platform-wide decline.
- [x] Documentation: endpoint/MCP/llms guides match; archive historical reports, retain authoritative README/current status/analysis. Update reproducible patch and tests.
- [x] Verify full isolated regression suite, controlled change reports and live route/persistence checks; update PR #1 with tests and remaining limitations.

Storage design keeps canonical content snapshots and all observation snapshots. No automatic retention deletion is introduced: referenced content must remain. Short cache reuse is explicitly recorded and cannot produce independent evidence at the 15-minute analysis spacing.


Rulings: default MCP fetch/search route through the API to share cache across stdio client processes; explicit direct mode preserves standalone access. Use both retrieval and completion times to select checkpoint baselines, so cached recaptures cannot rewrite what was available at the checkpoint. Canonical references optimize new captures only; no destructive rewrite/retention of existing history.

Evidence: new tests first failed for missing coordinator/policy, thirteen history queries, absent content references, absent change interface, Instagram unchanged misclassification and post-checkpoint baselines. Final regression count120; live monitoring covers persisted real content reuse and REST/MCP agreement. Follow-up static review found no concrete blockers.
