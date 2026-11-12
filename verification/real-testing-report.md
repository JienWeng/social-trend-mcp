# Real-world test outcome

Tested at 2026-11-11T08:26:06.624778+00:00. This is a real source-file and live-service check, not a claim of viral performance or factual accuracy.

## Real video

[Latte Coffee making.webm](https://commons.wikimedia.org/wiki/File:Latte_Coffee_making.webm) by **Stevenndori289**, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Unmodified original downloaded explicitly as a test fixture; published Commons SHA1 matched. Original video and extracted images stay in ignored local storage and are not committed.

- Uploaded file: 1,549,075 bytes.
- Analysis: 17.7 seconds, 360×640, 30.0 nominal fps.
- Video analysis call: 3.745 seconds on this host (one sample, not throughput benchmark).
- 7 timestamped JPEGs returned through real MCP; 7 image blocks returned in creation context.
- Detected scene changes: 0 at threshold0.35. This does **not** prove no edits or identify exact camera movement.
- Audio present; amplitude measured. Speech transcription was not configured.

Actual extracted samples at0,4.425 and17.5 seconds were inspected. They show tight pitcher/cup/pour framing, white/brown/metal tones, and a wider final cup presentation. No source audio meaning, demographic attributes or audience geography were inferred.

## Useful failure found

OCR emitted short, spurious characters on the footage. In the three inspected frames, these did not constitute reliable designed caption overlays. OCR was explicitly excluded from caption evidence in the creative draft. **Functional extraction passed; OCR output needs quality filtering/review.** No software change was made to conceal this test result.

## Original output

Saved draft **Make the pour the story**, a 20-second 9:16 concept:
- 0–3s: original tight coffee/pitcher opening; new hook “Watch this cup come together.”
- 3–8s: new side-angle pour detail.
- 8–13s: own overhead surface-development shot.
- 13–17s: original finished-detail reveal.
- 17–20s: wider cup presentation in a different setting.

This is a connected-model-authored original example, with cited frames and unreviewed status; no footage, creator likeness, brand or soundtrack is reused. Target MY/en is requested output metadata, not proven local audience/trend evidence. No final video was rendered.

Reference ID: 633d577b91244164b5111fafd1840520. Brief ID: 7e33c1754f544d3396f9970cdb3eb601. Full measured data, timing, annotations and storyboard are in [real-reference-test.json](real-reference-test.json).

## Fresh social-source checks

Exactly one ordinary capture attempt/source, with existing restrictions honored:

| Source | Items returned | State |
| --- | --- | --- |
| twitter | 30 | captured |
| tiktok | 3 | captured |
| youtube | 30 | captured |
| instagram | 8 | captured |
| douyin | 30 | captured |

These retain their documented scope limits (Instagram recommendation sample, TikTok preview, YouTube weekly music chart, X third-party ranking, Douyin China hot list). This does not verify automatic Instagram video downloading; that feature is intentionally absent.

## Verification and reproduction

153 regression tests also passed, recorded in verification/pr-tests.txt. The runtime test uses real MCP calls for add/upload/analyze/inspect/context/annotate/save and fresh captures. It creates a labeled real-reference library record and real source snapshots; no synthetic trend history.

```bash
.venv/bin/python verification/real_reference_test.py
.venv/bin/python verification/real_reference_brief.py
```

The second script replays the example authored after visual inspection; it does not call a new generation model. Re-running creates records and network requests, and may legitimately defer if a source is cooling down.

Remaining unverified: real-model ASR accuracy, continuous-motion/music understanding, representative regional popularity, engagement/viral prediction, originality certification and rendered-video quality.
