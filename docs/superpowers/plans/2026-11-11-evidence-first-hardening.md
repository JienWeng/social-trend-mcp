# Evidence-first hardening implementation plan

> Execute inline with superpowers:executing-plans; verify with test-driven-development and a final independent review.

**Goal:** Make MCP/REST collection safer and give users one clear report explaining what the available evidence supports.

**Approved approach:** User selected MCP/REST evidence reports first. Keep current source coverage; do not add a dashboard, bypass access controls or invent truth probabilities.

**Design:**
- Structured restricted-source errors stop source fallback/retries for HTTP403/429 and browser login/challenge routes. Parse Retry-After seconds/date.
- A per-platform collection controller shares budgets across region/topic-limit keys, serializes actual fetch attempts and applies cooldowns. Default six collection attempts/hour, minimum60sec between uncached attempts, exponential generic-failure cooldown, >=24h access-denial pause. Honor longer Retry-After. Successful cached reads remain possible and retain original fetched_at.
- Persist controller state locally for the single-worker service so restart does not clear pauses. Expose counters, cooldown, next eligible time and budget through read-only status.
- Deferrals do not overwrite stored successful history: capture returns429/persisted=false; genuine attempted failures are recorded.
- Add GET /api/v1/analysis/report and MCP get_report as read-only default entry points. Combine latest data, source/metric validation, momentum and optional checkpoint changes with plain-language next actions and collection state.
- Distinguish structural validation/provenance, observed momentum, source fidelity and factual truth. Last two remain explicitly unverified unless independent evidence is provided; no probability score.
- Add a read-only local check command and usage examples. Verify parser fidelity against recorded raw fixtures independently of trend scoring; report audit denominator and untested sources. Do not claim this fact-checks social captions or news claims.

Tasks:
- [x] Add failing fault-injection tests (429/date,403,challenge,shared budget,cooldown,recovery,persistence,deferral).
- [x] Implement shared source control and integrate scraper/coordinator/API behavior.
- [x] Add evidence-report contract tests; implement report and MCP/REST routes plus local check.
- [x] Run recorded-source fidelity audit, isolated full regression and low-volume live read/capture checks.
- [x] Update docs/llms/reproducible patch, obtain review, commit/push and update existing/open follow-up PR as appropriate.

Limits: one worker, per-platform collection-attempt budgets (not every browser subresource), no external notifications, no multi-day stability claim. Default direct standalone mode cannot provide a distributed quota guarantee.


Rulings: source controls count platform scraper attempts, not browser subresources. Unfinished persisted attempts fail closed for that platform pending operator review. Actual claimed factual truth is not verified or assigned a percentage; recorded fixture checks are a scoped field-mapping audit. A read-only repeatable-read database transaction keeps composed report evidence coherent.

Evidence:139 tests pass. Source-control tests first failed, including review regressions for failed finish writes/restarts and403 Retry-After longer than24h; then passed after repair. Recorded audit108records648fields0mismatches, explicitly excluding factual truth and X/TikTok. Follow-up static review found no concrete blockers.
