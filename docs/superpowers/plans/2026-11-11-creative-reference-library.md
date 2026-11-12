# Creative reference library implementation plan

> Execute inline using superpowers:executing-plans, TDD and final independent review.

**Goal:** Turn curated, accessible video references into timestamped evidence that an MCP-connected AI can use to create original video briefs.

**User authorization:** User approved the proposed curated-library + actual video inspection workflow and requested immediate implementation.

**Architecture:** PostgreSQL stores reference metadata, immutable media identity, measured analysis, attributed annotations and creative briefs. Videos/frames stay in an ignored local storage directory. FFprobe/FFmpeg measure duration, frame samples, scene-change estimates and audio properties; optional Tesseract OCR and explicitly configured offline ASR report unavailable honestly. MCP returns frame image blocks so the connected multimodal model, rather than a hidden paid backend model, can interpret visual style. Source links alone are not analyzed videos.

**Boundaries:** No automatic social-video downloading, login/challenge bypass, geolocation inference, paid LLM calls or final-video rendering. Country/language/niche/audience labels are operator declarations, not verified audience geography. Model annotations and generated creative briefs remain attributed/unverified. Measured observations are kept separate.

Tasks:
- [x] Library models/schema and validated create/list/detail REST contracts. Store source URL, niche/language/target-country labels; no URL fetch.
- [x] Stream bounded MP4/WebM uploads into immutable reference media; local MCP imports restricted to configured inbox. Prevent traversal/overwrite and limit duration/dimensions/fps, concurrent jobs and subprocess time. Local container/protocol allowlists; no shell.
- [x] FFprobe/FFmpeg frame extraction, estimated scene changes, audio properties, optional OCR/offline transcription. Timestamp every observation and expose frame routes. Mark absent tools/model/transcript explicitly.
- [x] Validated user transcript segments and client-model annotations referencing actual timestamps/frame IDs; no promotion into measured truth.
- [x] MCP tools for library operations, media attach/analyze/inspect and creation context with bounded image blocks. Context supplies target/goal, evidence, unknowns and an original-brief output schema.
- [x] Persist generated briefs (concept, hook, timed script/storyboard, shot/edit notes and verified reference IDs) with model-origin label; list/detail endpoints. Creation is performed by the connected AI, not a deterministic template pretending to watch a video.
- [x] Tests: raw upload bounds, unsafe formats/paths, parser measurements on generated synthetic video, missing-tool reporting, validation and isolated PostgreSQL REST/MCP lifecycle.
- [x] Install/document media prerequisites; update setup/container, llms/endpoint/user guides, reproducible patch and tests. Verify end-to-end on clearly labeled synthetic media; inspect actual extracted frames and save an example original brief. Review and deliver PR update.

File map: app/models/references.py; app/reference_schemas.py; app/services/reference_media.py, reference_library.py, reference_speech.py; app/routers/references.py; app/mcp_references.py; tests/test_reference_*.py; docs/CREATIVE-REFERENCES.md.


Rulings: supplied performance observations are optional/manual and unverified, not scraped/verified analytics. Contexts bound transcript/OCR/annotation/history text with persistent truncation flags. Draft generation is performed by the connected AI; saved provenance is client-submitted with declared generator, not a server authenticity claim.

Evidence:153 tests passed, including real synthetic FFmpeg/OCR and isolated PostgreSQL lifecycle/concurrency. Real MCP demonstration persisted a labeled synthetic reference and returned6 frame images; connected assistant inspected red/blue frames and saved an original20-second script/storyboard. Review reproduced output buffering, decoder-thread placement and annotation race failures before fixes; follow-up found no concrete blockers. Optional offline ASR requires supplied model files and was not validated with a real model.
