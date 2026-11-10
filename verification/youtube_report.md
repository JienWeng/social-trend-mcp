YouTube implementation verification

The obsolete /feed/trending renderer traversal has been replaced with the public
YouTube Charts weekly top music videos page, read by ordinary headless Playwright
Chromium. The browser loads the site's own charts JSON; the scraper captures that
response, with no API replay, login, stealth, CAPTCHA bypass, or paid service.

Live keyless scrape (see youtube_live.json for timestamp and all returned rows):
- global -> US: 100 videos, https://charts.youtube.com/charts/TopVideos/us/weekly
- jp -> JP: 100 videos, https://charts.youtube.com/charts/TopVideos/jp/weekly
- gb -> GB: 100 videos, https://charts.youtube.com/charts/TopVideos/gb/weekly
- All three charts: October 30 through November 5, 2026.

The source covers music videos only. Views are weekly country chart views, not
lifetime/global views. Chart ranks, titles, counts and countries come from the
source response. Missing views remain unlabeled (the shared numeric model uses
zero, paired with views_available=false and view_count=null). Unsupported or
mismatched country/chart responses fail rather than being relabeled. Other
countries have not been live verified. Chromium and Playwright are required.

Keyword search remains YouTube Data API only. Without a key it raises an explicit
limitation; no public keyword-search source is claimed. No real API key was used
for live checks. The existing API path is preserved and tested with HTTP fixtures;
credentials are now in X-Goog-Api-Key headers instead of URLs. API items record
actual mapped country, and missing API views no longer claim '0 views'.

TDD: Initial new regression run failed 7 tests before implementation; the later
missing-API-views regression failed before its fix. Final focused run: 18 passed.
See youtube_tests.txt. compileall and git diff --check passed for the scraper.

The latest full-suite run while other work was active: 62 passed, 3 skipped,
6 failures outside this edit scope (see youtube_full_suite.txt):
- test_correctness.py::test_popularity_does_not_make_unrelated_topic_relevant
- test_correctness.py::test_matching_topic_on_two_platforms_is_not_dropped
- test_instagram_browser.py::test_browser_rejects_country_before_launch
- test_instagram_provider.py::test_instagram_provider_rejects_regional_claim_before_billing
- test_routes_correctness.py::test_region_routes_forward_region_and_reject_invalid
- test_routes_correctness.py::test_exact_search_includes_observed_trends_without_search_method

Reproduce live scrape from checkout root:
PYTHONPATH=upstream .venv/bin/python verification/youtube_live.py

No commits or pushes were made. No central files were edited by this task.
