---
type: job
domain: kb-meta
trigger: a meeting, conversation, or document produces durable knowledge
frequency: ad-hoc
tools: Write, Edit, Read
owner: {{NAME}}
status: active
tags: [job]
---

# Job — Capture a meeting or conversation into the KB

> **When:** a meeting, conversation, or document produces facts worth keeping
> **Outcome:** raw capture in `raw/` → compiled concept in `concepts/` → indexed + logged

## When to run this
After any meeting, reading session, or conversation where you learned something durable: decisions made, people's roles clarified, a system explained, a priority shifted. If you'd have to re-derive it next time, write it down.

## Steps
1. **Triage.** If the raw content is already at the vault root (inbox), you're ready. If it's in notes or memory, draft it now.
2. **Raw capture.** Move or write the content to `raw/YYYY-MM-DD-topic.md` (today's date; topic = one or two descriptive words). Add a one-line provenance header at the top: `_Source: <meeting name / conversation / document>, YYYY-MM-DD._`
3. **Compile.** Extract the durable facts into the right concept article(s) in `concepts/`. Ask: which concept does this fact belong to? If no concept exists yet, create one.
   - Wikilink liberally: `[[person]]`, `[[concept]]`, `[[workstream]]`.
   - If a real to-do surfaced, write it inline as `- [ ] … #action`.
   - If a new person appeared, run [[Add a person to the KB]].
4. **Index.** In `index.md`, add the raw note to the Raw section and the new/updated concept(s) to the Concepts section (one-line summary each). Update the "last updated" line.
5. **Log.** Append one line to `meta/log.md`: `- YYYY-MM-DD — <what was captured> → compiled into [[concept]]`.

## Gotchas / rules
- `raw/` is append-only. Never delete or rewrite a raw note — add a correction note dated later if needed.
- Compile the facts, not the conversation. Raw notes are the transcript; concept notes are the extracted truth.
- One raw note can feed multiple concepts; one concept can draw from multiple raw notes.
- A fact in a concept must be traceable to a raw note. If you're writing something you just know, create a raw stub first.

## Done when
- [ ] Raw note exists in `raw/YYYY-MM-DD-topic.md` with a provenance header.
- [ ] Durable facts compiled into one or more `concepts/` articles.
- [ ] New/updated concepts listed in `index.md`.
- [ ] One-line entry in `meta/log.md`.

## Related
[[karpathy-method]] · [[AGENTS]] · [[Add a person to the KB]] · [[Run the KB health check]]
