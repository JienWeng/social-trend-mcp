# Social Trends MCP

Public social feeds, PostgreSQL history and evidence reports for AI agents. Supports X, TikTok, YouTube music charts, Instagram Reels samples and Douyin. Default sources need no paid API key.

## Start locally

Requires Git, uv, Docker and Python 3.12. See [installation and MCP configuration](docs/AGENT-SETUP.md) for a fresh machine.

```bash
./setup.sh
./manage-service.sh start
./check-service.sh
```

API: http://127.0.0.1:8000 · [Swagger](http://127.0.0.1:8000/docs). Connect your MCP client to the absolute path of `start-mcp.sh`; keep the API running. Use `./manage-service.sh status|restart|stop` to manage it. Run one worker and keep the service private.

## Use it

Start with **`get_report({})`** for stored coverage, freshness and next actions. `capture_trends` saves observations; `analyze_trends` measures sustained movement; `get_changes` compares against a saved timestamp. These are sampled signals, not virality predictions.

For video briefs, run `./setup-media.sh`, supply an authorized local video, then use `add_reference → attach_reference_media → analyze_reference → get_creation_context → save_creative_brief`. The connected AI interprets frames and writes the draft. Links alone do not download videos; final videos are not rendered.

- [Agent instructions](llms.txt) — also served at `/llms.txt`.
- [Endpoints and 22 MCP tools](docs/ENDPOINTS.md).
- [Evidence, coverage and collection controls](docs/EVIDENCE.md).
- [Trend-analysis rules](TREND-ANALYSIS.md) and [video-reference workflow](docs/CREATIVE-REFERENCES.md).
- [Verification status](CURRENT-STATUS.md) and [change summary](docs/CHANGES.md).

## Development

`./verification/run_tests.sh` runs isolated regression tests. Live checks are listed in [verification](verification/README.md); some collect data and write records.

`setup.sh` reconstructs [upstream](https://github.com/caicai-yao/social-trends-mcp) at `c9f413ad1c8c6b387e8cd1af5f0c709f263ceae2` in ignored `upstream/`, applies `verification/repairs.patch` and restores the regression tests. After source edits, sync `llms.txt` with `upstream/app/llms.txt` and run `.venv/bin/python verification/package_repairs.py` before committing.
