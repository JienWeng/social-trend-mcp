# Stored trend analysis

The MCP now supports evidence-based movement analysis. AI can interpret the returned evidence and explain possible themes; the backend calculates signals from stored observations without calling a paid AI model. These signals identify sampled momentum candidates, not future virality.

## Use it

- MCP `capture_trends`: supply `platform` and optional `region`. Fetches and persists a real snapshot through the running API.
- MCP `analyze_trends`: optional `platform`, `region`, `hours` (1–720, default 48), and `limit` (1–100). Reads shared stored history.
- REST `POST /api/v1/analysis/capture/twitter?region=global`.
- REST `GET /api/v1/analysis/trends?region=global&hours=48&limit=20`.

Start with `./manage-service.sh start`; MCP uses `API_BASE_URL` (default http://127.0.0.1:8000). Existing fetch tools remain direct cached queries; use capture_trends when a query should create historical evidence. Scheduled API collection also persists snapshots, every six hours by default.

## Evidence rules

A rising candidate needs at least three independent observations spanning one hour, with at least 15 minutes between observations. Repeated source editions count once. Rank must improve at every point by at least two positions overall, or a comparable metric must increase at every point by at least 25% overall. These are transparent initial heuristics, not a calibrated forecast.

Results include snapshot IDs, timestamps, ranks, metric units/windows, warnings and an explanation. Confidence is qualitative, not a probability. Raw comparable cumulative counter decreases suppress growth signals even when sampling would omit the reset. Inconsistent net improvement is labeled mixed_movement. New_to_sample means first appearance in this lookback, not newly created on the platform.

Latest failures suppress signals; captures older than 12 hours are stale. Analysis retains at most 500 snapshots per platform and reports truncation. No platform can consume another platform's history allowance.

Instagram recommendation order is never treated as a popularity rank; sampling limits remain. YouTube fallback covers weekly music charts: repeated copies of one weekly edition cannot establish momentum, and three weekly editions require a longer lookback. Heat scores and rolling windows are not cumulative views. Rates describe changes in reported metrics, not new events per hour.

## Verified on November 10, 2026

Full regression suite: **104 passed**, including real isolated PostgreSQL tests. Review regressions first reproduced hidden resets and cross-platform history starvation, then passed after repairs. A second read-only review found no concrete blockers.

The controlled synthetic demonstration correctly classified a 120% rise, stable popularity, decline, counter reset and first sampled appearance. It never writes synthetic data to the service database.

The live MCP test persisted a real X capture and read the same history through REST/MCP. It found one Douyin rising candidate, 后会友期二创大赛, with ranks **29 → 28 → 20** across three observations spanning **2.056 hours**. Its heat score increased only 0.04% overall; the signal came from rank movement. Other sources honestly returned stable, falling, new-to-sample or insufficient-history results. This is a point-in-time observation, not a claim of predictive accuracy.

Reproduce:

```bash
./verification/run_tests.sh
.venv/bin/python verification/analysis_demo.py
.venv/bin/python verification/analysis_live.py
```

The live check makes a real network request and persists a new snapshot. Evidence: verification/analysis-demo.json, verification/analysis-live.json, verification/analysis-tests.txt. The local API has been restarted with this feature; the previously verified Docker image predates it and needs rebuilding to include it.
