# AGENTS.md — {{NAME}}'s Knowledge Base (cross-vendor session instructions)

> **Placeholders in `{{double braces}}` are filled in during setup.** Open this
> folder in Claude Code and say *"follow setup.md"* — Claude will interview you
> and replace them. Until then, this file still reads fine.

**Who:** {{NAME}}, {{ROLE}} at {{ORG}}{{REPORTS_TO}}.

**What this folder is:** A personal, LLM-maintained knowledge base — your project
memory — built on the **Karpathy "knowledge-base-as-compiler" method**. The
schema (how the KB works) is `SYSTEM/SCHEMA.md`. The map of all content is
`index.md`. The method itself — what it is and why it works — is compiled in
`05 concepts/karpathy-method.md`.

---

## Start of every session

1. The SessionStart hook has already inlined the **boot bundle**
   (`SYSTEM/bin/build_boot_bundle.sh`): which machine you are on, the `index.md`
   Quick map, the inbox, open `#priority` actions, today's plan + calendar, and the
   log tail. **Don't re-read `index.md` at start** — open it only to navigate to a
   section. If no bundle appeared (hook not trusted/installed), run the builder
   yourself: `SYSTEM/bin/build_boot_bundle.sh`.
2. Read `SYSTEM/SCHEMA.md` when the task touches conventions, structure, or
   compilation (schema changes, new note types, compile passes) — not by reflex.
3. Check `Actions.md` for open to-dos if the task involves execution.

## Where a new fact goes

Capture first → `raw/YYYY-MM-DD-topic.md` (if it quotes a source). Then **first
match wins** — full tree: `Skills/DO/File a New Note.md`.

- named human / vendor? → `04 People/` (person | org)
- completable work? → `03 Projects/` (or one `#action` in an existing note)
- never-done responsibility? → `02 Areas/` (a physical thing → `02 Areas/Assets/`)
- how do I do X again? → `.claude/skills/` (edit the canonical, never the `Skills/` mirror)
- orientation (1–5 yr)? → `01 Horizons/`
- otherwise compiled truth → `05 concepts/` (method, standing fact, or watchlist — say which in `tags:`)

Never a new file: today's scribble → `00 daily/` · a binary → `attachments/<owning-slug>/` ·
role knowledge → `Agents/<role>/` · pipeline artifacts → `02 Areas/<slug>/`.

## Multi-model rules (Claude, Grok, and any other agent reading this)

This file is the cross-vendor entry (`CLAUDE.md` just imports it). The canonical
agent machinery — skills, roles, commands, and project hooks — lives in `.claude/`
and is auto-discovered by Claude Code, Grok Build, and other SKILL.md-standard
agents. Hook *scripts* stay in `SYSTEM/optional/automation/`; `.claude/settings.json`
only registers them. Usage: `README.md` § Agent machinery.
Non-negotiables for every model:

- **One model is the KB's maintainer** (default: Claude Code). Other models are
  readers/executors — run skills, answer from the KB — but schema changes,
  compilation, and index maintenance route through the maintainer unless
  {{NAME}} re-rules.
- **Privacy overrides tooling:** before working in this vault, disable any
  outbound search/share tools your runtime auto-enables (ones that post a
  query to a public platform) — the same public-exposure risk the
  § Privacy rule below guards against.
- Follow the same schema (`SYSTEM/SCHEMA.md`), wikilink conventions, and lint
  discipline regardless of vendor; the visible `Skills/` and `Agents/*.md`
  notes are **generated mirrors** — edit their `.claude/` canonicals only.

---

## Folder structure

| Folder / file | Purpose |
| :-- | :-- |
| `raw/YYYY-MM-DD-topic.md` | Append-only source captures — **never delete** |
| `05 concepts/` | Compiled, queryable truth (evergreen, rewritten in place) |
| `03 Projects/` | GTD H1 — finite workstreams (`type: project`, `status: pending\|active\|paused\|done`; required `area:` up-link). Built from `Project TEMPLATE.md`; done → `archive/`. **Structural — not the inbox.** |
| `02 Areas/` | GTD H2 — ongoing responsibilities (`type: area`, `review:` cadence + `## Standard`). Flat except `Assets/` (physical things) and graduated working folders. Built from `Area TEMPLATE.md`. |
| `01 Horizons/` | GTD H3–H5 — `Goals/` (one `type: goal` note per 1–2 yr outcome) · `vision.md` · `purpose-principles.md`. |
| `04 People/Full Name.md` | One note per person or `type: org` — single source of truth for per-person detail; built from `People TEMPLATE.md`, indexed by `05 concepts/contacts.md`. |
| `index.md` | The map — keep current after every change |
| `SYSTEM/` | Machinery home: `SCHEMA.md` (law) · `log.md` · `decisions.md` · `skill-impact.md` · `link-map.md` (generated) · `Journal.md` (wins log) · `bin/` (tooling: `lint.sh`, `regen-all.sh`, generators, audits) |
| `Actions.md` | Live to-do dashboard (pinned root anchor) |
| `.claude/` | **Canonical** agent machinery (cross-vendor): `skills/`, `agents/`, `commands/`, project **hooks** in `settings.json` (scripts live in `SYSTEM/optional/automation/`). |
| `Skills/<TYPE>/` · `Agents/*.md` | **Generated mirrors** of the `.claude/` canonicals (`DO` performs a task · `CHECK` audits · `FORMAT` produces an artifact · `RULE` standing convention). Working data: `Agents/<role>/`. Never edit a mirror. |
| `attachments/<slug>/` | Binaries, owned by the note of that slug |
| `00 daily/` | Day notes — not compiled truth |
| `excalidraw/` | *(optional)* Diagrams embedded in their owning note — `Skills/FORMAT/Create an Excalidraw Diagram.md` |
| `docs/` | *(optional)* Scratch space for specs/plans (tool-owned, not KB content) |

Folder names live in one place — `SYSTEM/bin/kb-folders.json` (mirrored for
shell in `kb-folders.sh`); every script reads them from there.

---

## Conventions (must follow)

Law: `SYSTEM/SCHEMA.md` § Conventions. Operating subset:

- **Wikilinks:** `[[note-name]]`. Reference people by `[[Full Name]]` (their `04 People/` note); nicknames resolve via `aliases:`. Resolve via `SYSTEM/link-map.md` (regenerate after add/rename: `SYSTEM/bin/build-link-map.sh`). Relationships live inline (wikilinks + Related sections).
- **GTD endpoint test:** completable ever = project; maintained-to-a-standard = area. **Up-links only** (`area:` / `serves:` / `horizon:`); downward views are generated, never hand-maintained. Skills: `Skills/DO/Run a Project.md` · `Skills/DO/Review an Area.md`.
- **Relations frontmatter:** asset sub-areas carry `owner:` (+ optional `serviced-by:`), people carry `relation:`, vendors are `type: org` notes in `04 People/`. Up-links only.
- **Actions:** inline `- [ ] … #action` in the home note; `#priority` = focus. Machine-written lines must carry `#auto` (a job that omits it is a bug). Check off in the home note. Census: `Actions.md`.
- **Raw notes:** append-only, dated (`YYYY-MM-DD-topic.md`). Never delete or rewrite.
- **Concept articles:** evergreen — rewrite in place. Frontmatter: `type: concept` · `description:` (one *stable* sentence — single-sources the index one-liner) · `updated:` (bump on every meaningful rewrite) · `status: current` · `tags:`.
- **Projects / Areas:** orientation sections are script-capped (`## Now & next` ≤500 words, `## Milestones` ≤400); overflow history moves verbatim to `trails/<slug>-trail.md`. Every active project carries ≥1 open `#action`; every area carries a recent `reviewed:`.
- **Mirrors:** edit `.claude/skills/<slug>/SKILL.md` / `.claude/agents/<role>.md`, never the `Skills/` or `Agents/*.md` mirror; regenerate with `SYSTEM/bin/build_claude_mirrors.py`.
- **Index is a pure map:** `index.md` opens with a **Quick map** skeleton (one stable line per concept/project/area) that fits the session-start injection budget. Change history lives in `SYSTEM/log.md`, **never** in `index.md`.
- **Human text in mixed notes:** wrap in `> [!human]` — machines integrate around it, never edit the quoted text.
- **Secret hygiene:** never print credential/config stores (`.env`, `~/.config/*` secrets, password-manager values) — inspect by key name or length only; a leak into session output means rotate.
- **Three ledgers:** `SYSTEM/log.md` (what changed — append after every meaningful update) · `SYSTEM/decisions.md` (what {{NAME}} ruled — only on their explicit word) · `SYSTEM/skill-impact.md` (how skills evolved).
- **Dates:** always `YYYY-MM-DD`.
- **Search:** prefer `rg` (ripgrep) over `grep`; note `rg` skips hidden dirs — add `--hidden` when the target might be in `.claude/`.

---

## Inbox rule

**The vault root is the inbox.** The only permanent files at the root are
`README.md`, `index.md`, `Actions.md`, `CLAUDE.md`, and this `AGENTS.md`
(plus the kit's `setup.md`, `LICENSE`, `MIGRATING.md`, `CHANGELOG.md`, and Python
tooling `pyproject.toml`/`uv.lock`). Anything else at the root is un-triaged —
file it into `raw/` (then compile into `05 concepts/` if durable). The
structural folders (`00 daily/`, `01 Horizons/`, `02 Areas/`, `03 Projects/`,
`04 People/`, `05 concepts/`, `raw/`, `Skills/`, `Agents/`, `attachments/`,
`excalidraw/`, `docs/`, `SYSTEM/`) are **not inbox items**. Authoritative list:
`SYSTEM/bin/lint.sh` check 1.

---

## Privacy rule (non-negotiable)

Everything in this vault is private: the non-negotiable line is
**publication** — personal content never gets posted to a public website or
committed/pushed to a public or shared repo. The only sanctioned outward path
to a public audience is *generic framework improvements* (schema, templates,
skills, scripts) flowing to the public **CNTXT1** starter kit via
`Skills/DO/Sync an Improvement to CNTXT1.md` — always re-templated to
`{{placeholders}}`, always through its grep gate. Never push from this
vault to the public repo — the only sanctioned remote for it is a
**fetch-only** `upstream` (push URL `DISABLED`) used to pull framework
updates *inward* (`Skills/DO/Pull Framework Updates from CNTXT1.md`); author
generic improvements upstream-first when possible. **Third-party LLM/tool API
calls are not publication** — ordinary judgment applies, no case-by-case
ruling required. **Never print secrets** (see Conventions). Full rules:
`SYSTEM/SCHEMA.md` § Privacy & content separation. When in doubt, it's
personal — it stays here.

---

## Data flow

New note → root inbox → `raw/YYYY-MM-DD-topic.md` → route to its home per
*Where a new fact goes* (compile durable facts into `05 concepts/`) → update
`index.md` → append `SYSTEM/log.md`. Relationships live inline: `[[wikilinks]]` +
Related sections; substantial ones become concepts.

---

## Health checks

Run `SYSTEM/bin/regen-all.sh` then `SYSTEM/bin/lint.sh` (exit 0 = green). Stale
generated views and word-cap overruns **WARN** (a mechanical remedy exists);
`LINT_STRICT=1` FAILs them (the CI gate); anything else (broken links, schema
violations, an active project with no next action) FAILs plainly. Judgment checks
(stale facts, resolved questions, actions still open) stay a manual/LLM pass.
Full policy + the optional nightly gardener: `SYSTEM/SCHEMA.md` § Health checks.

---

## Context shortcuts

- **The method:** `05 concepts/karpathy-method.md`
{{CONTEXT_SHORTCUTS}}
