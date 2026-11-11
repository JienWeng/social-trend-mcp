# Curated videos → evidence → original creative briefs

This layer gives an MCP-connected AI actual video evidence, instead of asking it to guess the style from a Reel caption. It runs locally with PostgreSQL, FFmpeg/FFprobe and optional Tesseract OCR. The connected model interprets supplied images and writes the creative draft; the backend does not make a hidden paid LLM call.

## Quick start

```bash
./setup.sh
./setup-media.sh
./manage-service.sh start
mkdir -p .run/reference-inbox
# Put a video you can legitimately use here:
cp /path/to/your-video.mp4 .run/reference-inbox/reference.mp4
```

setup-media.sh installs FFmpeg/FFprobe and Tesseract on Debian/Ubuntu when administrator access is available. Other systems should install equivalent packages. The Dockerfile includes them; rebuild to deploy this feature.

In your MCP client:

1. **add_reference** — title, platform, optional source_url, target_country, language, niche, audience and notes. Labels are operator declarations, not verified audience geography. Put a caption/creator context in notes if useful.
2. **attach_reference_media** — returned reference_id and path `reference.mp4`. Paths resolve inside REFERENCE_INBOX_DIR; source links are not downloaded.
3. **analyze_reference** — reference_id. Measures the supplied local video.
4. **inspect_reference** — reference_id. Returns timestamped JPEG image blocks and measured/unknown fields. A multimodal client can inspect the images.
5. **get_creation_context** — supply reference_ids, goal, niche, language and optional target_country/audience/duration_seconds/target_aspect_ratio. It returns reference evidence, images, constraints and the schema for an original draft.
6. Ask your connected AI to write that draft, then call **save_creative_brief**. Use **list_creative_briefs** to retrieve saved scripts/storyboards.

Example creation request:

```json
{
  "reference_ids": ["REFERENCE_ID_FROM_ADD_REFERENCE"],
  "goal": "Create an original 20-second desk-reset video using the references' broad caption and editing techniques",
  "niche": "productivity",
  "language": "en",
  "target_country": "MY",
  "audience": "English-speaking office workers",
  "duration_seconds": 20,
  "target_aspect_ratio": "9:16"
}
```

Do not paste the placeholder ID unchanged. The model should inspect returned frames before describing visual style, cite real frame IDs/source intervals, and mark inferred intent and unknown audio explicitly.

## What inspection provides

- Immutable supplied-file SHA256, duration, encoded dimensions/fps and codec metadata.
- Up to seven sampled JPEG frames; timestamps are approximate requested seek positions, not verified exact frame PTS. Sampling can miss motion, transitions or events between frames.
- Estimated scene-change timestamps using a declared threshold. Motion/flashes can create false cuts; this is not a definitive shot list.
- On-screen text from Tesseract when available, with boxes and engine scores; OCR remains machine-extracted/unverified.
- Audio presence and signal-amplitude measurements. These do not recognize speech, genre, emotion, beats or music identity.
- Optional offline speech transcription if explicitly configured; otherwise speech status is not_configured, not an invented transcript.
- Source URL and declared audience labels. Uploaded media is **not independently verified to match its declared URL/creator**.

An AI can store **annotate_reference** entries as observed or inferred, citing a frame/time or existing transcript/scene/audio evidence. These stay attributed client claims, separate from measured fields. The server validates IDs and intervals, not semantic truth.

**set_reference_transcript** stores explicitly supplied timed words as user_supplied_unverified. Do not invent missing speech from a caption.

## Performance observations

**record_reference_metrics** accepts supplied views/likes/comments/shares and optional observed_at/source_url. It never fetches platform counters. Unknown values stay null. **get_reference_performance** returns observations/deltas and reset/source-change warnings. These data are labeled user_supplied_unverified; they do not establish representative national popularity or an emerging trend.

This permits a curated reference set to accumulate observations while retaining provenance. It does not turn manual observations into platform-verified analytics.

## What a saved brief contains

Target/goal, concept, opening hook, ordered timed storyboard/shot list, new spoken/on-screen text, editing notes, source frame evidence and unknowns. Source-video intervals are separate from the new storyboard's timings. The draft is client-submitted, with a declared generator and unreviewed status. Originality is requested, not independently certified.

Use broad creative techniques as inspiration. Do not reuse source footage, exact scripts, branding, creator identity or distinctive assets. There is **no final-video rendering/generation engine** in this layer.

## REST equivalents

Swagger: http://127.0.0.1:8000/docs — [full catalog](ENDPOINTS.md).

```bash
# Create a reference:
curl -X POST http://127.0.0.1:8000/api/v1/references \
  -H 'Content-Type: application/json' \
  -d '{"title":"My reference","platform":"uploaded","language":"en","niche":"productivity"}'

# Substitute its real ID:
curl -X PUT http://127.0.0.1:8000/api/v1/references/REFERENCE_ID/media \
  -H 'Content-Type: application/octet-stream' --data-binary @/path/to/video.mp4
curl -X POST http://127.0.0.1:8000/api/v1/references/REFERENCE_ID/analyze
```

## Limits and storage

Default100MiB uploads,180-second input duration, at most3840 pixels per dimension/3840×2160 pixels and120 nominal fps. Accepts ftyp MP4/MOV and EBML WebM/Matroska containers with supported video streams. Decoder input protocols/formats are allowlisted; no shell is used. Decoder/filter threads are bounded, output pipes have a live2MiB cap, jobs/subprocesses time out, and analysis concurrency is one (uploads two). These controls are not a hostile multi-user sandbox; this service remains local/single-user with no public authentication layer.

Media is immutable after upload. Create a new reference for another file; analyzed ready references are idempotent. Files/frames live under REFERENCE_STORAGE_DIR (default .run/references), while metadata/drafts live in PostgreSQL. Back up both; neither assets nor inbox files are committed. Source/trend history is separate from the library. No automatic library deletion or final rendering is provided.

AI context text is bounded and marks truncation; full saved detail remains available through REST. Image blocks are capped (seven for inspection, eight across creation references). Selected frames are passed to your connected AI client; that client's processing may be remote.

## Optional local speech recognition

```bash
uv pip install --python .venv/bin/python -e './upstream[transcription]'
```

Set REFERENCE_ASR_MODEL_PATH to an already-installed complete CTranslate2 faster-whisper model directory containing tokenizer.json; the service does not download models. Restart the API. OCR language defaults to eng; configure REFERENCE_OCR_LANGUAGE and install matching Tesseract language data for others. ASR is optional and was not validated against a real speech model in this session; missing/failed status remains explicit. For longer CPU transcription, adjust REFERENCE_PROCESS_TIMEOUT consciously (default90 seconds for the whole analysis).

## Verified example

The regression suite exercises actual FFmpeg/OCR on a generated four-second red/blue clip with known text, one scene change and a synthetic tone. This is **not an Instagram reference or organic performance evidence**.

```bash
.venv/bin/python verification/creative_reference_demo.py
.venv/bin/python verification/save_demo_brief.py
```

The first script persists a clearly labeled synthetic reference and verifies the real MCP upload/analysis/image/context flow. The second replays an original example draft authored after actual frame inspection; it does not invoke a fresh generation model. See verification/creative-reference-demo.json for the saved example, evidence and unreviewed draft. These scripts write library records/files, not synthetic trend snapshots.
