---
type: do
domain: kb-meta
trigger: "any new item entering the KB — a note about to be created, or an un-triaged inbox item"
frequency: ad-hoc
tools: "Read, Write, Grep, Bash (link-map regen)"
owner: "{{NAME}}"
status: active
version: "1.0"
tags: [do, kb-meta]
aliases: [File a New Note, new-note decision tree, file-a-new-note]
summary: The new-note decision tree — capture to raw first, then one type question per branch (person/org → work via endpoint test → knowledge → procedure → orientation) picks the template; fall-throughs are recorded, never forced.
updated: 2026-09-28
author_type: script
---

> _Generated from `.claude/skills/file-a-new-note/SKILL.md` by `SYSTEM/bin/build_claude_mirrors.py` — edit the canonical file, never this mirror. Generated: 2026-09-28_

# Skill — File a New Note

> **When:** any new item is entering the KB · **Frequency:** ad-hoc ·
> **Outcome:** the item is in its schema-correct home with valid frontmatter, or its capture sits in `raw/` with a recorded fall-through — never a root orphan, never a guessed template.

## When to run this

A new note is about to be created anywhere in the vault, or something un-triaged
is sitting in the root inbox. Skip for machinery the tree doesn't govern: daily
notes (`00 daily/`), generated files (trails, indexes, mirrors, digests),
attachments (→ `attachments/<owning-note-slug>/`), and agent working folders.

## Steps

1. **Capture first.** If the item quotes or summarizes a source (conversation,
   document, email, research, statement), land it verbatim in
   `raw/YYYY-MM-DD-topic.md` — append-only, no frontmatter needed. If it
   contains no durable facts, stop here. Otherwise the raw file becomes the
   citation for whatever the tree creates next.
2. **Walk the type branch — first match wins.**
   a. **A named human?** → `04 People/Full Name.md` from `People TEMPLATE`
      (`type: person`; add `relation:` — relationship to {{NAME}}, side-of-family
      in the value). Deeper treatment: [[Add a Person to the KB]].
   b. **A business/vendor?** → `type: org` note in `04 People/`
      (fields: `org` · `role` · `location` · `found-by: "[[Full Name]]"`).
   c. **Work? Apply the endpoint test.**
      - One action, no note needed → `- [ ] … #action` in its existing home
        note. Not a new file.
      - Completable ever (≈3+ actions or >1 week) → `03 Projects/<kebab-slug>.md`
        from `Project TEMPLATE` (`area:` up-link required; not-now =
        `status: pending`). Run via [[Run a Project]].
      - Never done, maintained to a standard → `02 Areas/<kebab-slug>.md` from
        `Area TEMPLATE`. A physical asset → `02 Areas/Assets/` with `owner:`
        ({{NAME}} | `household` | `"[[Full Name]]"`) and, if it has a vendor,
        `serviced-by: "[[org]]"`.
   d. **Durable knowledge or reference?** → `05 concepts/<kebab-slug>.md`
      (`type: concept`, required one-sentence `description:`); every fact must
      trace to the step-1 raw capture.
   e. **A recurring procedure?** → canonical skill at
      `.claude/skills/<slug>/SKILL.md` per `Skills/Skill TEMPLATE.md`, then the
      mirror chain (template's "Add a skill" block).
   f. **Orientation (goal / vision / purpose)?** → `01 Horizons/` — rare;
      needs {{NAME}}'s word before creating.
3. **No branch fits? Don't force one.** Leave the capture in `raw/`, add an
   `#action` naming the gap on the note that owns your KB systems (or in
   `SYSTEM/log.md`), and tell {{NAME}}. A forced-fit note is worse than a
   recorded fall-through.
4. **Finish the wiring.** Fill the template's frontmatter honestly (no
   fabricated relations — evidence-only), add the note to `index.md` if its
   folder is indexed there, regenerate the link map on any new People/skill
   name (`SYSTEM/bin/build-link-map.sh`), run `SYSTEM/bin/regen-all.sh`, and
   append the `SYSTEM/log.md` line.

## Gotchas / rules

- **First match wins, and person/org outranks work:** a plumber is an org note
  first; the water-heater repair is an `#action` on the house's asset note, not
  a project.
- The tree governs *note creation*, not compilation quality — a concept that
  fails "traces to raw" is a step-1 miss, go back and capture.
- `raw/` is append-only and frontmatter-free by convention; don't "improve" it
  with YAML.
- Unevaluated tools do not get a peer `type: concept` until an adopt/decline
  ruling — park them as a `## Watch` list on the owning project, or tag
  `watchlist` if a concept is the right home.

## Done when

- [ ] Item is in a schema-valid home (Pydantic/lint green) or its fall-through is recorded.
- [ ] Raw citation exists for any compiled facts; index/link-map/log updated.

## Related

[[SCHEMA]] § Data flow + § Conventions (endpoint test, relations frontmatter — the *why*) ·
[[Add a Person to the KB]] · [[Run a Project]] · [[Review an Area]] ·
[[Capture a Meeting or Conversation into the KB]]
