# Instagram without a paid API

Direct browser scraping is implemented, enabled by default, and verified live on 2026-11-10. It opens Instagram's ordinary logged-out Reels page with local Chromium and reads the page's embedded JSON records. It uses no SocialCrawl, Meta API key, Instagram account, saved cookies, paid proxy, CAPTCHA solver, or stealth patch.

## Verified results

The local scraper fetched eight Reel records in about 4.6 seconds on the first direct run. Subsequent startup, manual-refresh and MCP runs also returned eight records. Captions, authors, Reel URLs, publication times, likes and comments were available. View counts were not supplied by this page and remain null; likes are labeled as likes. Results differ between runs because this is a recommendation feed.

The live end-to-end check passed: browser scraping -> PostgreSQL -> REST responses and matching committed WebSocket update -> an independent live MCP `get_trends` call. Evidence is in `verification/instagram-browser-live.json` and `verification/instagram-no-api-e2e.json`. The current tests are 86 passed in the complete latest suite, with no warnings. Tests cover fixture parsing, duplicate and navigation rejection, null metrics, default browser selection and no paid fallback. The public browser regression tests failed before implementation.

This is a sample of the public Reels recommendation feed, not an exhaustive global chart or a measurement of topic growth. No country ranking is claimed. Only `region=global` is accepted. The scraper reads one page and does not attempt to page through login restrictions. If Instagram serves a login, challenge or empty page, it reports a failure. Accessibility may differ by host/IP and change over time; repeated success here does not guarantee access from every deployment.

## Run

The current workspace is already configured. See `CURRENT-STATUS.md` for the authoritative combined report. `setup.sh` installs the Python browser extra and Chromium. The running service now uses the direct browser scraper.

```bash
./setup.sh
./manage-service.sh start
```

Do not start a second API process if one is already running. API docs are at http://127.0.0.1:8000/docs on this machine. Inspect results at http://127.0.0.1:8000/api/v1/trends/instagram, or use MCP `get_trends` with `platform=instagram`, `region=global`.

The default is `INSTAGRAM_SOURCE=browser`; no `.env` is required for Instagram. An existing SocialCrawl key alone no longer enables provider usage. `INSTAGRAM_SOURCE=socialcrawl` must be selected explicitly to use that separate metered adapter. There is no automatic fallback from browser scraping to SocialCrawl. Suggestions are also opt-in and labeled separately.

For manual source installation:

```bash
uv pip install --python .venv/bin/python -e './upstream[browser,dev]'
.venv/bin/python -m playwright install chromium
```

On a Linux host missing browser system libraries, use `python -m playwright install --with-deps chromium` in the environment that runs the service. The Dockerfile now includes this installation and a browser path readable by its app user; the complete Docker image was subsequently built and its five live feeds verified.

## Checks

```bash
.venv/bin/python verification/verify_instagram.py --live
.venv/bin/python verification/check_no_api_instagram.py
TEST_DATABASE_URL=postgresql+asyncpg://postgres:local-test-only@127.0.0.1:55433/social_trends_regression .venv/bin/pytest upstream -q
```

`--live` uses the configured source, which is the local browser by default. Without `--live`, the older verification helper replays the recorded SocialCrawl demo and makes no network request. `check_no_api_instagram.py` is the current end-to-end check. It performs a real scrape and writes a snapshot to the test service database. Tests use a separate dedicated regression database.

## Cost and runtime

There are no third-party API charges for browser mode. It uses this machine's CPU, RAM, bandwidth and disk for Chromium. The scheduler refreshes every six hours by default and also scrapes once at startup. MCP caches results for 30 minutes within its process. Use one API worker; shared scheduling and cross-worker WebSocket distribution still need work before multi-worker deployment.

The cumulative patch, fixture captures and tests are saved in `verification/`, and setup restores them to the tested upstream revision. No code was pushed to GitHub.
