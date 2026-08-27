---
name: capture-a-meeting-or-conversation-into-the-kb
description: Turns a meeting, conversation, or document into a dated Knowledge/raw/ capture compiled into Knowledge/Concepts/. Use when a meeting, conversation, or document produces durable knowledge.
metadata:
  title: Capture a Meeting or Conversation into the KB
  type: do
  domain: kb-meta
  trigger: a meeting, conversation, or document produces durable knowledge
  frequency: ad-hoc
  tools: ["Write", "Edit", "Read"]
  owner: "{{NAME}}"
  status: active
  tags: [do, kb-meta]
  aliases: ["Capture a meeting or conversation into the KB", "capture-a-meeting-or-conversation-into-the-kb"]
  summary: Turns a meeting, conversation, or document into a dated Knowledge/raw/ capture compiled into Knowledge/Concepts/.
---


# Skill — Capture a meeting or conversation into the KB

> **When:** a meeting, conversation, or document produces facts worth keeping
> **Outcome:** raw capture in `Knowledge/raw/` → compiled concept in `Knowledge/Concepts/` → indexed + logged

## When to run this
After any meeting, reading session, or conversation where you learned something durable: decisions made, people's roles clarified, a system explained, a priority shifted. If you'd have to re-derive it next time, write it down.

## Steps
1. **Triage.** If the raw content is already at the vault root (inbox), you're ready. If it's in notes or memory, draft it now.
2. **Raw capture.** Move or write the content to `Knowledge/raw/YYYY-MM-DD-topic.md` (today's date; topic = one or two descriptive words). Add a one-line provenance header at the top: `_Source: <meeting name / conversation / document>, YYYY-MM-DD._`
3. **Quote-anchor gate (before compiling — code, not vibes).** Every commitment, decision, or claim you extract from a transcript or meeting notes must carry a **verbatim quote** that literally appears in the source. Verify each anchor mechanically — `grep -F` the quote against the raw capture (normalize only whitespace and curly/straight quotes, identically on both sides). **No anchor, no proposal** — an extraction that can't be anchored is dropped, and the drop is noted in the raw capture. Tune asymmetrically: recall-tuned for *{{NAME}}'s own* commitments (missing one costs them), precision-tuned for what *others* owe them (a fabricated waiting-for pollutes the KB; self-plan narration by the other party never qualifies). Skip this step when the source is already a compiled document, not a transcript.
4. **Compile.** Extract the durable facts into the right concept article(s) in `Knowledge/Concepts/`. Ask: which concept does this fact belong to? If no concept exists yet, create one.
   - Wikilink liberally: `[[person]]`, `[[concept]]`, `[[workstream]]`.
   - If a real to-do surfaced, write it inline as `- [ ] … #action`.
   - If a new person appeared, run [[Add a person to the KB]].
5. **Index.** In `index.md`, add the raw note to the Raw section and the new/updated concept(s) to the Concepts section (one-line summary each). Update the "last updated" line.
6. **Log.** Append one line to `SYSTEM/log.md`: `- YYYY-MM-DD — <what was captured> → compiled into [[concept]]`.

## Gotchas / rules
- `Knowledge/raw/` is append-only. Never delete or rewrite a raw note — add a correction note dated later if needed.
- Compile the facts, not the conversation. Raw notes are the transcript; concept notes are the extracted truth.
- One raw note can feed multiple concepts; one concept can draw from multiple raw notes.
- A fact in a concept must be traceable to a raw note. If you're writing something you just know, create a raw stub first.

## Done when
- [ ] Raw note exists in `Knowledge/raw/YYYY-MM-DD-topic.md` with a provenance header.
- [ ] Durable facts compiled into one or more `Knowledge/Concepts/` articles.
- [ ] New/updated concepts listed in `index.md`.
- [ ] One-line entry in `SYSTEM/log.md`.

## Related
[[karpathy-method]] · [[SCHEMA]] · [[Add a person to the KB]] · [[Run the KB health check]]
