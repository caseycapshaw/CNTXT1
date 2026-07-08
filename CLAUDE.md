# CLAUDE.md — {{NAME}}'s Knowledge Base

> **Placeholders in `{{double braces}}` are filled in during setup.** Open this
> folder in Claude Code and say *"follow setup.md"* — Claude will interview you
> and replace them. Until then, this file still reads fine.

**Who:** {{NAME}}, {{ROLE}} at {{ORG}}{{REPORTS_TO}}.

**What this folder is:** A personal, LLM-maintained knowledge base — your project
memory — built on the **Karpathy "knowledge-base-as-compiler" method**. The
schema (how the KB works) is `meta/AGENTS.md`. The map of all content is
`index.md`. The method itself — what it is and why it works — is compiled in
`concepts/karpathy-method.md`.

---

## Start of every session

1. Read `meta/AGENTS.md` — the schema (how the KB works).
2. Read `index.md` — the map (where everything lives).
3. Check `Actions.md` for open to-dos if the task involves execution.

---

## Folder structure

| Folder / file | Purpose |
| :-- | :-- |
| `raw/YYYY-MM-DD-topic.md` | Append-only source captures — **never delete** |
| `concepts/` | Compiled, queryable truth (evergreen, rewritten in place) |
| `Initiatives/<kebab-slug>.md` | One note per goal-directed workstream (`type: initiative`, lifecycle `status:`); built from `Initiatives/Initiative TEMPLATE.md`, run via `Jobs/Run an initiative.md`. **Structural folder — not the inbox.** |
| `index.md` | The map — keep current after every change |
| `meta/AGENTS.md` | KB schema and operating rules |
| `meta/log.md` | Append-only changelog — one line per meaningful update |
| `meta/link-map.md` | Generated `[[wikilink]]` → file-path index (one-lookup link resolution). Rebuild: `meta/bin/build-link-map.sh` |
| `meta/bin/` | KB tooling — `lint.sh` (mechanical health check), `build-link-map.sh` (regenerate the link map) |
| `meta/Journal.md` | Wins & milestones brag doc — use for perf reviews |
| `Actions.md` | Live to-do dashboard (pinned root anchor) |
| `People/Full Name.md` | One note per person — single source of truth for per-person detail; built from `People/People TEMPLATE.md`, indexed by `concepts/contacts.md`. **Structural folder — not the inbox.** |
| `Jobs/Imperative Title.md` | One runbook per recurring "job to be done" — single source of truth for the *steps*; built from `Jobs/Jobs TEMPLATE.md`, indexed by `concepts/jobs.md`. **Structural folder — not the inbox.** |

---

## Conventions (must follow)

- **Wikilinks:** use `[[note-name]]` (Obsidian-style) to cross-reference concepts. Reference people by `[[Full Name]]` (their `People/` note); nicknames resolve via the note's `aliases:` frontmatter field. Relationships live inline (wikilinks + each note's Related section) — a relationship with real substance becomes its own concept; there is no separate connections folder.
- **People:** every named person = one note in `People/` (the single source of truth for per-person detail), built from `People/People TEMPLATE.md`. `concepts/contacts.md` is the **index** (who-for-what map). Don't duplicate per-person prose into concepts — link to the note.
- **Jobs:** every recurring task = one agent-executable runbook in `Jobs/` (the single source of truth for the *steps*), built from `Jobs/Jobs TEMPLATE.md`. `concepts/jobs.md` is the **index**. Steps live in the job; the *why/context* stays in the matching concept.
- **Actions:** inline `- [ ] … #action` checkboxes in their home note. Add `#priority` to flag focus items. Check off in the home note — never maintain a separate list. `Actions.md` aggregates them automatically (Obsidian Tasks plugin).
- **Raw notes:** append-only, dated (`YYYY-MM-DD-topic.md`). Never delete or rewrite.
- **Concept articles:** evergreen — rewrite in place as understanding improves. Each carries YAML frontmatter (`type: concept` · `updated: YYYY-MM-DD` · `status: current` · `tags: [concept, <domain>]`); **bump `updated:` whenever you meaningfully rewrite one** so staleness is mechanical.
- **Initiatives:** a goal-directed workstream (multiple actions over time) = one note in `Initiatives/` with `type: initiative` frontmatter and lifecycle `status: active|paused|done`. Live ones sit on the index Quick map's Initiatives line; actions stay inline in the initiative note. Concept↔initiative conversions are a `git mv` + frontmatter swap + link-map regen. Runbook: `Jobs/Run an initiative.md`.
- **Wikilink resolution:** `meta/link-map.md` maps every `[[target]]` (concept slug, People name+alias, Job title+alias) → its file path. Use it instead of grepping; regenerate with `meta/bin/build-link-map.sh` after adding/renaming any of those.
- **Index is a pure map:** `index.md` opens with a **Quick map** skeleton (every concept/initiative/index, one line) so the structure fits the session-start injection; rich descriptions follow below. Change history lives in `meta/log.md`, **never** in `index.md`.
- **Dates:** always `YYYY-MM-DD`.
- **Log:** append a one-line entry to `meta/log.md` after every meaningful KB update.

---

## Inbox rule

**The vault root is the inbox.** The only permanent files at the root are
`README.md`, `index.md`, `Actions.md`, and `CLAUDE.md`. Anything else at the root
is un-triaged — file it into `raw/` (then compile into `concepts/` if durable).
`concepts/`, `Initiatives/`, `meta/`, `raw/`, `daily/`, `People/`, `Jobs/`, and `attachments/` are **structural folders — not inbox items**.

---

## Privacy rule (non-negotiable)

Everything in this vault is private: **personal content never leaves the
vault** — never copy it into public or shared repos, external services, or
anything destined to be published. The only sanctioned outward path is
*generic framework improvements* (schema, templates, runbooks, scripts)
flowing to the public **CNTXT1** starter kit via
`Jobs/Sync an improvement to CNTXT1.md` — always re-templated to
`{{placeholders}}`, always through its grep gate. Never add the public repo
as a git remote of this vault. Full rules: `meta/AGENTS.md` § Privacy &
content separation. When in doubt, it's personal — it stays here.

---

## Data flow

New note → root inbox → `raw/YYYY-MM-DD-topic.md` → compile facts into
`concepts/` → update `index.md` → append `meta/log.md`. Relationships live
inline: `[[wikilinks]]` + Related sections; substantial ones become concepts.

---

## Health checks (run on request, or automatically at 6pm if you've installed the optional daily-summary job)

- Root inbox clean: only the four anchors + structural folders (`concepts/`, `Initiatives/`, `meta/`, `raw/`, `daily/`, `People/`, `Jobs/`, `attachments/`).
- No `[[wikilink]]` points to a non-existent note (including `[[Full Name]]` person-links → a real `People/` note or registered alias).
- Every concept and initiative listed in `index.md`; every `Jobs/` runbook listed in `concepts/jobs.md`.
- Every fact in a concept traces to a `raw/` capture.
- All open `#action` checkboxes are real and still open; completed ones are checked, not deleted.

---

## Context shortcuts

- **The method:** `concepts/karpathy-method.md`
{{CONTEXT_SHORTCUTS}}
