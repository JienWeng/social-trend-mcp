# Verified current state — November 11, 2026

The local single-worker service collects all five keyless default sources and exposes REST, WebSocket and 22 stdio MCP tools. Public endpoints can change; these feeds are not exhaustive global realtime rankings.

## Coverage

| Source | Verified default collection | Scope |
| --- | --- | --- |
| X | 30 topics | Third-party trends24 ranking; unknown volumes remain unknown. |
| TikTok | 3 tags | Limited official public preview; global maps to US. US/GB/JP/SG were tested. |
| YouTube | 30 entries | Weekly music-video charts via ordinary Chromium; global maps to US. US/GB/JP tested; direct larger requests returned 100. |
| Instagram | 8 Reels | Logged-out public recommendation sample, global only; no login or automatic paid fallback. |
| Douyin | 30 topics | Official public China hot list; global/cn map to cn. Direct requests returned 50. Heat scores are not views. |

See [endpoint catalog](docs/ENDPOINTS.md). No login/challenge bypass is implemented.

## Current improvements

- One API collection cache coalesces concurrent identical fetches for up to 120 seconds. REST search, live feeds, persisted captures and default MCP fetch/search share it. Failed results are not cached.
- Default cadence is hourly X/Douyin, six-hourly TikTok/Instagram and daily YouTube; global/per-source overrides are supported. Health and analysis mark retrievals stale after twice the applicable interval.
- Scheduled collection honors enabled platforms and configured regions; saved captures honor max_topics. Snapshot requested regions and actual source regions stay separate.
- Every capture retains its ID and timing. Identical new source-aware content reuses canonical topic rows; metadata/edition changes remain distinct. Existing historical duplicates are not rewritten or deleted.
- History loads snapshots/topics in two queries rather than one query per snapshot. Latest/history/analysis/WebSocket/capture responses resolve reused content.
- Checkpoint reports show sample additions/removals, rank/comparable metric changes and unchanged counts, with evidence and separate sustained momentum. Baselines exclude data fetched or completed after the checkpoint.
- Search covers observed feeds and reports coverage. No fabricated matches or popularity-only unrelated results.
- WebSocket updates follow commit. Single-instance supervisor, API crash/orphan recovery, named-volume PostgreSQL and idempotent schema upgrades remain supported.

## Evidence-first usability and collection controls

Start with MCP get_report({}) or GET /api/v1/analysis/report. This read-only report combines stored freshness/coverage, source/metric checks, momentum, checkpoint changes and next actions. ./check-service.sh verifies API/MCP readiness without collecting.

Source controls share budgets across region/limit/client keys: default6 collection attempts/hour/platform, minimum60sec uncached interval, exponential failure cooldown, Retry-After handling and >=24h access-denial/challenge pause. Longer Retry-After values are honored. Deferrals do not create failure snapshots. Persistent unfinished attempts or bad state require operator review; failed pause writes cannot silently clear a restriction on restart.

Field-fidelity audit: **108 historical records,648 field checks,zero mismatches** across Douyin/Instagram/YouTube fixtures; X/TikTok were not audited. Latest runtime extraction remains not_independently_verified. Factual truth is explicitly not_checked, probability=null. See [evidence guide](docs/EVIDENCE.md); these results are not a factual-accuracy rate.

## Creative reference workflow

The backend now stores curated reference metadata, explicitly supplied immutable videos, timestamped frame/OCR/scene/audio evidence, attributed annotations, optional supplied metric observations and original creative briefs. Source links are not downloaded. Call add_reference → attach_reference_media → analyze_reference → inspect_reference/get_creation_context → save_creative_brief. See [creative-reference guide](docs/CREATIVE-REFERENCES.md).

The connected multimodal AI inspects JPEG image blocks and generates the script/storyboard; there is no hidden backend LLM call or final-video renderer. Missing speech/OCR remains explicit. Target market/labels, source-media matching, supplied counters, client annotations and originality remain unverified.

A real MCP protocol demonstration uploaded a clearly labeled synthetic4-second clip, extracted6 frames, found the known2-second scene change, returned frame images/context and saved an original20-second unreviewed storyboard after actual frame inspection. This does not analyze an Instagram clip or establish organic trends. Optional offline ASR was not tested against a real speech model.

## Verification

Latest suite: **153 passed**, including isolated PostgreSQL, cache/single-flight behavior, failure retries, configuration/cadence, content reuse, source-edition separation, batched history, change reports, counter resets and checkpoint availability. Tests use social_trends_regression, not the service database.

Focused evidence:

- `verification/creative-reference-demo.json`: synthetic-media MCP lifecycle and saved original example draft; source video files stay ignored.
- `verification/creative_reference_demo.py`, `save_demo_brief.py`: reproduce the synthetic reference and replay the example draft.

- `verification/evidence-audit.json`: selected recorded-field fidelity audit and its explicit limits.
- `verification/evidence-live.json`: live read-only REST/MCP report, unchanged source-attempt counters and saved-state checks.

- `verification/pr-tests.txt`: latest full suite.
- `verification/monitoring-live.json`: real unchanged-content capture reuse, preserved retrieval time and matching REST/MCP checkpoint reports.
- `verification/recovery.json`, `orphan-recovery.json`: actual process recovery.
- `verification/patch-validation.json`: cumulative patch applies to pristine pinned upstream, including all new source files.

Review reproduced and fixed the post-checkpoint baseline bug and, in this round, failed pause-write recovery and longer403 Retry-After. Follow-up static review found no concrete blockers. No synthetic trend history, paid provider accounts or paid subscriptions were created. The reference library contains explicitly labeled synthetic demo records, separate from trend snapshots.

## Operation and limits

Use README for setup/service commands, docs/ENDPOINTS.md for interface contracts and TREND-ANALYSIS.md for interpretation. Historical reports remain in Git history; [verification commands](verification/README.md) describe the maintained checks.

The running local API includes these optimizations. Previously verified Docker collection-image evidence predates analysis/llms.txt/monitoring changes: rebuild to include them. Public HTTPS and multiple replicas remain unverified. Cache/locks/WebSocket are process-local; run one worker. Collection controls count scraper attempts, not each browser asset, and do not guarantee continued access or absence of IP blocking. State needs persistent writable storage to survive container replacement. Canonical content snapshots are protected by references and must not be deleted while referenced; automatic retention deletion is intentionally absent.

No cross-platform semantic clustering, watchlist notifications or predictive accuracy claim is included. Media inspection is bounded local single-user processing, not a hostile multi-user upload sandbox. Back up reference asset storage as well as PostgreSQL. The useful output is an evidence-based report of what changed in the feeds actually observed.
