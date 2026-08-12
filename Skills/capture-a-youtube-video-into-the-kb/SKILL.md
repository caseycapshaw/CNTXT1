---
name: capture-a-youtube-video-into-the-kb
description: Capture a YouTube video's metadata, description links, and transcript digest into raw/ and compile it into the relevant concept(s)/person(s) — use when {{NAME}} shares a YouTube URL to "capture" (e.g. "yt capture this …").
type: skill
domain: kb-meta
tools: yt-dlp (brew), raw/, concepts/, People/
owner: {{NAME}}
status: active
tags: [skill]
aliases: [Capture a YouTube video into the KB, yt capture]
updated: 2026-08-11
---

# Skill — Capture a YouTube video into the KB

> **When:** {{NAME}} shares a YouTube link to capture · **Frequency:** ad-hoc · **Tools:** `yt-dlp`
> **Outcome:** a dated `raw/` capture of the video (metadata + description links + transcript digest), compiled into the concept(s)/person(s) named, indexed and logged. **Every note created must link back to the video and carry the links from its description.**

## When to run this

{{NAME}} drops a YouTube URL and says to capture it — often with a target shape
("as a concept and person", "into initiative X"). If no target shape is given,
default to one `raw/` capture + one concept; add a `People/` note when the
video is really about a person (interview, talk, creator worth tracking).

## Steps

1. **Verify tooling:** `which yt-dlp` — if missing, `brew install yt-dlp`.
2. **Pull metadata + description** (stripping any `&t=` timestamp from the URL is unnecessary — yt-dlp handles it):
   ```sh
   yt-dlp --skip-download --print "%(title)s\n%(channel)s\n%(upload_date)s\n%(duration_string)s\n%(webpage_url)s\n---DESCRIPTION---\n%(description)s" "<URL>"
   ```
3. **Extract the links from the description** — every URL in it. These go into a **Links** section of the raw note and are carried into every compiled note.
4. **Pull the transcript:**
   ```sh
   cd "$(mktemp -d)" && yt-dlp --skip-download --write-auto-subs --sub-langs en --sub-format vtt -o "sub" "<URL>"
   ```
   Read the `.vtt`, and condense it: de-duplicate the rolling caption lines and keep the substance. Do **not** paste the raw VTT into the vault.
5. **Raw capture → `raw/YYYY-MM-DD-<topic>.md`** with a provenance header:
   video title, channel, upload date, duration, **the video URL**, a **Links
   (from description)** section, then the condensed transcript / key points.
6. **Compile** per the requested target shape:
   - **Concept:** new or updated `concepts/<slug>.md` (frontmatter per [[AGENTS]]) distilling the durable ideas — with a **Source** line linking the video and the relevant description links.
   - **Person:** if warranted, run [[Add a person to the KB]] for the speaker/creator (People template, `aliases:`, row in [[contacts]]) — link the video there too.
7. **Wire up:** `index.md` Quick map + section entry for any new concept; regenerate the link map (`meta/bin/build-link-map.sh`) after any new concept/person.
8. **Log:** one line in `meta/log.md`.

## Gotchas / rules

- **Always include the video URL and the description's links in every note created** (raw, concept, person) — that's the point of this runbook; a capture without its sources is unverifiable.
- Auto-subs are rolling/duplicated — condense, never paste raw VTT.
- Don't download the video itself (`--skip-download` everywhere); the KB stores knowledge, not media.
- Timestamped URLs (`&t=…s`) usually mean the sharer cared about that moment — note what's at that timestamp in the raw capture.
- Some videos have no captions; fall back to the description + your own knowledge of the talk, and say so in the provenance header.

## Done when

- [ ] `raw/` capture exists with video URL + description links + condensed transcript
- [ ] Target concept/person notes created or updated, each linking the video
- [ ] `index.md`, link map, and `meta/log.md` updated

## Related

[[Capture a meeting or conversation into the KB]] (the generic capture flow this specializes) · [[Add a person to the KB]] · [[skills]] · [[AGENTS]]
