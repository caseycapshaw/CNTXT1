# AGENTS.md — How this knowledge base works

This knowledge base — rooted at the vault root — is built on the **Karpathy
"knowledge-base-as-compiler" method** (adapted from Andrej Karpathy's LLM
knowledge bases). This file is the project-specific **schema** for that method;
the method *itself* — what it is, why it works, pros/cons — is compiled in
**[[karpathy-method]]**. Read this file first at the start of any session, then
read `index.md`.

_All paths in this file are relative to the vault root, not to this `meta/` folder._

## The compiler analogy

| Compiler stage | Here | Folder |
| :-- | :-- | :-- |
| Inbox | New, un-triaged notes & dropped files land here first | vault root |
| Source code | Raw, unprocessed captures (slides, conversation notes, articles) — the source of truth | `raw/` |
| Compiler | An LLM (me) processes raw material into structured articles | — |
| Executable / wiki | Compiled, queryable knowledge | `concepts/` |
| Index | The map the agent starts from | `index.md` |
| Lint / tests | Health checks for gaps, stale data, broken links | see "Health checks" below |
| Log | Record of what changed | `meta/log.md` |

## Data flow

0. **Inbox = the vault root.** New notes and dropped files start at the **vault root** — the inbox. Anything sitting at the root *other than the pinned anchors* (`README.md`, `index.md`, `Actions.md`, `CLAUDE.md`) is an un-triaged inbox item awaiting filing. A clean root (only the anchors + the structural folders) means the inbox is empty. **Structural folders** (not inbox items): `concepts/`, `meta/`, `raw/`, `daily/`, `People/`, `Jobs/`, `attachments/`.
1. **Triage → `raw/`.** Move each inbox item into `raw/` as dated markdown (`YYYY-MM-DD-topic.md`), lightly edited, with a one-line source/provenance header. This is the source of truth; never delete it.
2. **Compile → `concepts/`.** Extract durable facts into concept articles. Relationships live inline — `[[wikilinks]]` in prose plus each note's **Related** section (Obsidian's backlinks panel and graph view materialize the reverse direction); a relationship with real substance becomes its own concept.
3. **Index → `index.md`.** Keep the index current so the agent knows where to start without semantic search / RAG.
4. **Log → `meta/log.md`.** Append a one-line entry for every meaningful update.

## Conventions

- **Backlinks:** use Obsidian-style `[[wikilinks]]` to connect notes. Reference people by `[[Full Name]]` (their `People/` note); nicknames resolve via the note's `aliases:` frontmatter field. A `[[link]]` to a note that doesn't exist yet is fine — it marks something worth writing later.
- **People:** every named person = one note in `People/Full Name.md` (Title Case, with spaces) — the single source of truth for per-person detail. Built from `People/People TEMPLATE.md`. `concepts/contacts.md` is the index (who-for-what map + grouped tables). Don't duplicate per-person prose into concepts — link to the person note. `People/` is a **structural folder, not the inbox**.
- **Jobs:** every recurring task = one agent-executable runbook in `Jobs/Imperative Title.md` — the single source of truth for the *steps*. Built from `Jobs/Jobs TEMPLATE.md`. `concepts/jobs.md` is the index. The job carries the steps; the matching concept keeps the *why/context*. `Jobs/` is a **structural folder, not the inbox**.
- **Concept articles** are evergreen and rewritten in place as understanding improves — they are the compiled truth, not a log. Each opens with YAML frontmatter — `type: concept` · `updated: YYYY-MM-DD` · `status: current` (or `stale`/`superseded`) · `tags: [concept, <domain>]`. **Bump `updated:` on every meaningful rewrite** — it's the mechanical staleness signal (a concept whose `updated:` predates a contradicting fact is findable). Mirrors the frontmatter `People/` and `Jobs/` already carry.
- **Initiatives** are goal-directed workstreams — an outcome needing **multiple actions over time** (rule of thumb: 3+ actions or more than a week). An initiative is a **kind of concept, not a separate folder**: it lives in `concepts/<kebab-slug>.md` with `type: initiative` · `status: active|paused|done` · `started:` · `updated:` frontmatter, built from `concepts/Initiative TEMPLATE.md`. Sections: Outcome (definition of done) · Now & next (rewritten in place) · Decisions + Milestones (dated, append-only) · Open questions · Actions (inline `#action` checkboxes — they aggregate to `Actions.md` and group under the initiative automatically) · Related. Live initiatives are listed on the **Initiatives (live)** line of the `index.md` Quick map. Concept↔initiative transitions are **frontmatter-only** (no file moves, links never break). Closing: `status: done`, final milestone, durable knowledge distilled into concepts, note kept forever as the record. Lifecycle runbook: `Jobs/Run an initiative.md`.
- **`index.md` is a pure map, not a log.** It opens with a compact **Quick map** skeleton (every concept/initiative/index as a one-liner) so the whole structure fits the session-start injection budget (the optional SessionStart hook inlines `head -c 8000` of `index.md`); rich descriptions follow below. **Change history never lives in `index.md`** — it goes to `meta/log.md`. If the Quick map outgrows the budget, tighten it — don't let the skeleton spill past the cut.
- **`meta/link-map.md` resolves wikilinks in one lookup.** A generated table mapping every `[[target]]` (concept slug, People name + `aliases:`, Job title + `aliases:`) → its file path — read it instead of grepping. **Regenerate after adding/renaming any concept, person, or job:** `meta/bin/build-link-map.sh` (idempotent).
- **Raw notes** are append-only and dated; they preserve the original source.
- **Root is the inbox, not a home for permanent files.** Only `README.md`, `index.md`, `Actions.md`, and `CLAUDE.md` live there permanently; everything else at the root is transient and should be triaged into `raw/` (then compiled). Permanent machinery lives in `meta/`. Structural folders (`concepts/`, `meta/`, `raw/`, `daily/`, `People/`, `Jobs/`, `attachments/`) are **not inbox items**.
- **Open questions** live at the bottom of the relevant concept article and are mirrored in `index.md`.
- **Actions (to-dos)** are Markdown checkboxes tagged `#action` — `- [ ] … #action` (optional `📅 YYYY-MM-DD` due date) — written **inline in the note they belong to**, next to their context. They're aggregated into one live view at `Actions.md` (a pinned root anchor; Obsidian **Tasks** plugin). Keep *actions* (things you do) distinct from *open questions* (unknowns); when a question's resolution is a task you perform, write it as an `#action`. Check items off in their home note (or the dashboard) — never maintain a duplicate manual to-do list.
- **`#priority` flags a focus action.** Add `#priority` to an action line (`- [ ] … #action #priority`) to mark it important. It's a plain importance flag; no due date required.
- Dates use `YYYY-MM-DD`.

## Health checks (lint) — run on request or automatically via optional/automation/daily-summary.sh

**Run the mechanical half with `meta/bin/lint.sh`** (exit 0 = green): it deterministically checks inbox-clean, wikilinks-resolve, index-complete, and frontmatter-present — faster and more reliably than reading every file by hand. It skips TEMPLATE files and ignores `[[links]]` inside inline-code spans. The **judgment** checks below (stale facts, resolved open questions, whether an `#action` is genuinely still open) aren't scriptable — they remain a manual/LLM pass on top. The optional 6pm `daily-summary.sh` runs `lint.sh` for the mechanical pass and has the LLM do only the judgment layer.

- Every fact in a concept article traces back to a `raw/` capture or a conversation.
- No `[[wikilink]]` points to a note that doesn't exist — including `[[Full Name]]` person-links (must resolve to a real `People/` note or registered alias).
- `index.md` lists every concept file; `concepts/jobs.md` lists every runbook in `Jobs/`.
- **Inbox is empty:** the vault root holds only `README.md` + `index.md` + `Actions.md` + `CLAUDE.md` (plus the structural folders: `concepts/`, `meta/`, `raw/`, `daily/`, `People/`, `Jobs/`, `attachments/`). Any other root file is un-triaged — file it into `raw/` and compile.
- Flag stale items and resolved open questions.
- **Actions current:** every `- [ ] … #action` is real and still open; completed ones are checked off (not deleted). `Actions.md` is the single aggregated view.
- **Initiatives current:** every `type: initiative` note with `status: active|paused` appears on the index Quick map's Initiatives line; a live initiative whose `updated:` is weeks old (or whose actions are all checked) probably needs a Now & next rewrite or a close.

## Scope note (the method's sweet spot)

This design works **without any vector DB / RAG** because the whole index fits in
a context window — good to roughly a few hundred pages. If a base grows past that,
add search; until then, plain markdown + a hand-maintained `index.md` beats
embeddings. See [[karpathy-method]] for the full rationale and the hallucination-
propagation risk (the reason the lint step is non-negotiable).

## Optional extensions

The core method is just **raw → compile → index → log**. Teams layer on extras as
needed — e.g. auto-generated daily planning notes, calendar capture, a SessionStart
hook that inlines the map + inbox. These are deliberately
**not required**; add them once the base habit sticks. *"Pick what's useful, ignore
what isn't."*

A ready-to-adopt bundle (macOS + Claude Code) ships in `optional/automation/` — a
SessionStart loader, a Google Calendar cache + Gmail digest (via the `gws` CLI),
an 8am daily-plan generator, a 6pm lint/recap/git-snapshot job, and the launchd
jobs to schedule them. See `optional/automation/README.md`.
