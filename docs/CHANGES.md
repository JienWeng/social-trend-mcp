# Change summary

The tracked `verification/repairs.patch` contains application changes against pinned upstream. `setup.sh` restores it and the regression tests.

- **Collection:** repaired five public sources, added Douyin, validated actual regions and preserved source URLs, dates and metric units. Paid adapters remain explicit opt-ins.
- **Efficiency:** shared 120-second cache, concurrent-request coalescing, source-specific cadences, canonical content reuse and batched history queries.
- **Reliability:** committed WebSocket updates, supervised API recovery, PostgreSQL named volume and idempotent schema upgrades.
- **Evidence:** persisted captures, checkpoint comparisons and sustained movement rules; failures, missing metrics and limited coverage stay visible.
- **Collection controls:** shared attempt budgets, exponential backoff, Retry-After, access-denial pauses and persistent unfinished-attempt recovery.
- **Creative references:** supplied-video storage, bounded frame/OCR/audio inspection, optional offline transcription, attributed annotations, manual metrics and unreviewed creative briefs.
- **Agent access:** 22 stdio MCP tools, REST/OpenAPI, `llms.txt`, readiness checks and setup/usage instructions.

See [current verification](../CURRENT-STATUS.md), [interface contracts](ENDPOINTS.md) and [agent setup](AGENT-SETUP.md). Git history retains earlier implementation reports and planning notes.
