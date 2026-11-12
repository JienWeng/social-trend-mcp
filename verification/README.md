# Verification

Run from the repository root after setup. Generated results describe one run; they are not guarantees of current source access or factual accuracy.

| Command | Purpose | Side effects |
| --- | --- | --- |
| `./verification/run_tests.sh` | Full regression suite | Resets isolated `social_trends_regression` tables; never use the service database |
| `./check-service.sh --json` | API/MCP readiness and stored evidence | Read-only |
| `.venv/bin/python verification/evidence_live.py` | REST/MCP report parity and unchanged attempt counters | Read-only |
| `.venv/bin/python verification/evidence_audit.py` | Recorded fixture field mapping | Local output only; not factual verification |
| `.venv/bin/python verification/analysis_demo.py` | Controlled movement examples | Local output only |
| `.venv/bin/python verification/analysis_live.py` | Shared stored analysis through MCP/REST | Collects and persists a snapshot |
| `.venv/bin/python verification/monitoring_live.py` | Content reuse and checkpoint reports | Collects and persists snapshots |
| `.venv/bin/python verification/final_e2e.py` | Feeds, search, regions and WebSocket | Collects and persists snapshots |
| `.venv/bin/python verification/creative_reference_demo.py` | Synthetic video inspection/context | Writes labeled library records/assets |
| `.venv/bin/python verification/save_demo_brief.py` | Replay example draft after the synthetic demo | Reads its generated JSON; writes annotations/brief |
| `.venv/bin/python verification/real_reference_test.py` | Licensed-video processing and source captures | Downloads licensed media; writes assets/library/snapshots |
| `.venv/bin/python verification/real_reference_brief.py` | Replay visually reviewed draft after the real-media test | Reads its generated JSON; writes annotations/brief |
| `.venv/bin/python verification/package_repairs.py` | Package changes and verify pristine-base patch application | Updates tracked patch/tests/manifest |

The `check_recovery.py` and `check_orphan_recovery.py` probes deliberately kill service processes. Read them before running; they are not routine readiness checks.

Regression fixtures and concise evidence reports stay tracked. Large historical response dumps and obsolete implementation reports are available in Git history. Most new probe outputs stay ignored. The synthetic and real-reference JSON examples remain because their companion draft scripts read them; regenerate them before replaying on a new database. See [real-media results and attribution](real-testing-report.md).
