# SCHEMA.md — How this knowledge base works

> Renamed 2026-08-27 from its original `SYSTEM/`-homed "AGENTS" basename so the
> root `AGENTS.md` — the cross-vendor session-instructions standard — could take
> that basename without ambushing historical wikilinks. Wikilink this file as
> `[[SCHEMA]]`.

This knowledge base — rooted at the vault root — is built on the **Karpathy
"knowledge-base-as-compiler" method** (adapted from Andrej Karpathy's LLM
knowledge bases). This file is the project-specific **schema** for that method;
the method *itself* — what it is, why it works, pros/cons — is compiled in
**[[karpathy-method]]**. Read this file first at the start of any session, then
read `index.md`.

_All paths in this file are relative to the vault root, not to this `SYSTEM/` folder._

## The compiler analogy

| Compiler stage | Here | Folder |
| :-- | :-- | :-- |
| Inbox | New, un-triaged notes & dropped files land here first | vault root |
| Source code | Raw, unprocessed captures (slides, conversation notes, articles) — the source of truth | `Knowledge/raw/` |
| Compiler | An LLM (me) processes raw material into structured articles | — |
| Executable / wiki | Compiled, queryable knowledge | `Knowledge/Concepts/` |
| Index | The map the agent starts from | `index.md` |
| Lint / tests | Health checks for gaps, stale data, broken links | see "Health checks" below |
| Log | Record of what changed | `SYSTEM/log.md` |

## Data flow

0. **Inbox = the vault root.** New notes and dropped files start at the **vault root** — the inbox. Anything sitting at the root *other than the pinned anchors* (`README.md`, `index.md`, `Actions.md`, `CLAUDE.md`) is an un-triaged inbox item awaiting filing. A clean root (only the anchors + the structural folders) means the inbox is empty. **Structural folders** (not inbox items): `Knowledge/Concepts/`, `Knowledge/Initiatives/`, `SYSTEM/`, `Knowledge/raw/`, `daily/`, `Knowledge/People/`, `Knowledge/Skills/`, `attachments/`, `docs/` (specs/plans), `Writing/` (optional), `Knowledge/Excalidraw/` (optional).
1. **Triage → `Knowledge/raw/`.** Move each inbox item into `Knowledge/raw/` as dated markdown (`YYYY-MM-DD-topic.md`), lightly edited, with a one-line source/provenance header. This is the source of truth; never delete it.
2. **Compile → `Knowledge/Concepts/`.** Extract durable facts into concept articles. Relationships live inline — `[[wikilinks]]` in prose plus each note's **Related** section (Obsidian's backlinks panel and graph view materialize the reverse direction); a relationship with real substance becomes its own concept.
3. **Index → `index.md`.** Keep the index current so the agent knows where to start without semantic search / RAG.
4. **Log → `SYSTEM/log.md`.** Append a one-line entry for every meaningful update.

## Privacy & content separation (non-negotiable)

This vault is **private by definition**. Every note in it — people, finances,
raw captures, daily notes, initiatives, logs — is personal content, and
**personal content never leaves the vault**. Never copy, commit, push, or
paste any of it into a public or shared repo, an external service, or anything
destined to be published.

The one sanctioned outward path is the **framework itself**: **CNTXT1**, the
public shareable starter kit this vault is an instance of
([caseycapshaw/CNTXT1](https://github.com/caseycapshaw/CNTXT1)), receives
*generic* improvements only — schema, templates, `Knowledge/Skills/` skills,
`SYSTEM/bin/` scripts — each **hand-copied and re-templated** (real values
swapped back to `{{placeholders}}`) via the skill
`Knowledge/Skills/DO/Sync an Improvement to CNTXT1.md`, which ends with a personal-identifier
**grep gate** before anything is committed publicly.

Hard rules:
- **Never push from this vault to the public CNTXT1 repo** — no pushable
  remote, no pushed branch, ever; the private instance and the public
  framework keep independent histories on purpose. A **fetch-only**
  `upstream` remote pointing at the public kit *is* sanctioned (its push URL
  set to `DISABLED` so git physically cannot push): public → private can't
  leak, so that direction is git-automated — pull kit improvements inward
  via `Knowledge/Skills/DO/Pull Framework Updates from CNTXT1.md`. Author generic
  improvements **upstream-first** (in the public kit, through its CI gates)
  when they aren't already implemented privately; the manual re-template
  sync below remains the only outward path.
- **Never automate the outward copy** (no export script, no
  subtree/filter-repo exclude list) — the manual re-template step *is* the
  leak protection; automation drifts stale and leaks.
- **When in doubt whether something is generic or personal, it's personal** —
  it stays in the vault.

## Conventions

- **Backlinks:** use Obsidian-style `[[wikilinks]]` to connect notes. Reference people by `[[Full Name]]` (their `Knowledge/People/` note); nicknames resolve via the note's `aliases:` frontmatter field. A `[[link]]` to a note that doesn't exist yet is fine — it marks something worth writing later. Cite raw captures as path-style wikilinks — `[[Knowledge/raw/YYYY-MM-DD-topic]]` (no `.md`) — so citations hyperlink in Obsidian; backticks are only for filename *patterns*/templates, never for a reference to a real file.
- **People:** every named person = one note in `Knowledge/People/Full Name.md` (Title Case, with spaces) — the single source of truth for per-person detail. Built from `Knowledge/People/People TEMPLATE.md`. `Knowledge/Concepts/contacts.md` is the index (who-for-what map + grouped tables). Don't duplicate per-person prose into concepts — link to the person note. `Knowledge/People/` is a **structural folder, not the inbox**.
- **Skills:** every recurring task = one **canonical** skill at `.claude/skills/<kebab-slug>/SKILL.md` — full content in the standard Agent Skills format (top-level `name:` + `description:`, auto-discovered by Claude Code, Grok Build, and other SKILL.md-standard agents), with the org-schema keys under `metadata:` (`title/type/domain/trigger/frequency/tools/owner/status/tags/aliases/summary/updated`; `title` = the Imperative Title, `type` lowercase ∈ do/check/format/rule, matching the mirror folder `TYPE` ∈ `DO` performs a recurring task · `CHECK` verifies/audits · `FORMAT` produces an artifact · `RULE` standing convention). **Truth direction: the executed surface is canonical; the visible notes are generated mirrors** — `SYSTEM/bin/build_claude_mirrors.py` regenerates `Knowledge/Skills/<TYPE>/<Imperative Title>.md` (banner + `author_type: script`) so wikilinks, the graph, and the per-TYPE indexes keep working; **never edit a mirror** (the lint mirror check reds on drift). Built from `Knowledge/Skills/Skill TEMPLATE.md` (hand-maintained, not mirrored). `Knowledge/Concepts/skills.md` is the index. The skill carries the steps; the matching concept keeps the *why/context*. `Knowledge/Skills/` is a **structural folder, not the inbox**.
- **Concept articles** are evergreen and rewritten in place as understanding improves — they are the compiled truth, not a log. Each opens with YAML frontmatter — `type: concept` · `description:` (one **stable** sentence of essence, not volatile status — it single-sources the note's `index.md` one-liner and keeps exports OKF-aligned, see [[open-knowledge-format]]) · `updated: YYYY-MM-DD` · `status: current` (or `stale`/`superseded`) · `tags: [concept, <domain>]`. **Bump `updated:` on every meaningful rewrite** — it's the mechanical staleness signal (a concept whose `updated:` predates a contradicting fact is findable). Mirrors the frontmatter `Knowledge/People/` and `Knowledge/Skills/` already carry.
- **Initiatives** are goal-directed workstreams — an outcome needing **multiple actions over time** (rule of thumb: 3+ actions or more than a week). Every initiative = one note in `Knowledge/Initiatives/<kebab-slug>.md` (a **structural folder, not the inbox**), built from `Knowledge/Initiatives/Initiative TEMPLATE.md`, with `type: initiative` · `description:` (one stable sentence — same rule as concepts) · `status: active|paused|done` · `started:` · `updated:` frontmatter. Sections: Outcome (definition of done) · Now & next (rewritten in place) · Decisions + Milestones (dated, append-only) · Open questions · Actions (inline `#action` checkboxes — they aggregate to `Actions.md` and group under the initiative automatically) · optional Trail (append-only, one line per working session — the initiative-scoped log; "Now & next" stays the rewritten state so the two never mix) · Related. Live initiatives are listed on the **Initiatives (live)** line of the `index.md` Quick map; every initiative is listed in the index's Initiatives section. A concept that turns out to be goal-shaped converts by `git mv` into `Knowledge/Initiatives/` + frontmatter swap + link-map regen (wikilinks are basename-based, so links don't break). Closing: `status: done`, final milestone, durable knowledge distilled into concepts, then `git mv` the note into **`Knowledge/Initiatives/archive/`** (done initiatives live there; live + paused stay at the top level) + link-map regen — the note is kept forever as the record. Lifecycle skill: `Knowledge/Skills/DO/Run an Initiative.md`.
- **`index.md` is a pure map, not a log.** It opens with a compact **Quick map** skeleton (every concept/initiative/index as a one-liner) so the whole structure fits the session-start injection budget (the optional SessionStart hook inlines `head -c 8000` of `index.md`); rich descriptions follow below. **Change history never lives in `index.md`** — it goes to `SYSTEM/log.md`. If the Quick map outgrows the budget, tighten it — don't let the skeleton spill past the cut.
- **`SYSTEM/link-map.md` resolves wikilinks in one lookup.** A generated table mapping every `[[target]]` (concept slug, People name + `aliases:`, Skill slug + `aliases:`) → its file path — read it instead of grepping. **Regenerate after adding/renaming any concept, person, or skill:** `SYSTEM/bin/build-link-map.sh` (idempotent).
- **Raw notes** are append-only and dated; they preserve the original source.
- **Generated sections** are the always-current mechanism. Any file that machines rewrite splits at a `<!-- generated -->` marker: **hand-maintained config above** (humans edit schedules/annotations), **machine-rewritten content below** with a visible `_Generated: YYYY-MM-DD_` stamp. Generators are small, per-domain, idempotent scripts (one tool, one job); they **pin expected input headers and exit non-zero rather than write partial or silently-wrong output**; a stamp older than its cadence means the job missed — say so, don't guess. Never hand-edit below a marker. Worked examples: the auto-built directory indexes (`SYSTEM/bin/build_directory_indexes.py`) and the optional status-dashboard generator (`SYSTEM/optional/automation/status-gen-example.py`). Full convention: `Knowledge/Skills/RULE/Maintain Generated Sections.md`.
- **Root is the inbox, not a home for permanent files.** Only `README.md`, `index.md`, `Actions.md`, and `CLAUDE.md` live there permanently; everything else at the root is transient and should be triaged into `Knowledge/raw/` (then compiled). Permanent machinery lives in `SYSTEM/`. Structural folders (`Knowledge/Concepts/`, `Knowledge/Initiatives/`, `SYSTEM/`, `Knowledge/raw/`, `daily/`, `Knowledge/People/`, `Knowledge/Skills/`, `attachments/`, `docs/`, `Writing/` [optional], `Knowledge/Excalidraw/` [optional]) are **not inbox items**. *(The structural-folder and root-exception lists are copy-mirrored in prose — `lint.sh` check 1's `structural`/`tooling`/`standing` variables are the **single source of truth**; when adding a top-level folder or root exception, update lint first, then sync the prose copies here and in `CLAUDE.md`.)*
- **Open questions** live at the bottom of the relevant concept article and are mirrored in `index.md`.
- **Actions (to-dos)** are Markdown checkboxes tagged `#action` — `- [ ] … #action` (optional `📅 YYYY-MM-DD` due date) — written **inline in the note they belong to**, next to their context. They're aggregated into one live view at `Actions.md` (a pinned root anchor; Obsidian **Tasks** plugin). Keep *actions* (things you do) distinct from *open questions* (unknowns); when a question's resolution is a task you perform, write it as an `#action`. Check items off in their home note (or the dashboard) — never maintain a duplicate manual to-do list.
- **`#priority` flags a focus action.** Add `#priority` to an action line (`- [ ] … #action #priority`) to mark it important. It's a plain importance flag; no due date required.
- **Two ledgers, two grains:** `SYSTEM/log.md` = *what changed* (append-only changelog, every meaningful update). **`SYSTEM/decisions.md` = *what {{NAME}} ruled*** (index-not-record: date + title + 1–2 sentences + pointer to the fuller record). A decisions line lands **only on {{NAME}}'s explicit ruling-verb** ("decided", "adopted", "that's a decision"…) or their confirmation at a session close — unattended jobs propose, never append. The ledger is non-exhaustive by declaration; per-note `## Decisions` sections remain the records it points at.
- **Authorship & write permission (optional, meaningful when present):** a note may carry `author:` + `author_type: human | assistant | script` in frontmatter — and `author_type` is a **write-permission switch, not credit**. `human` → the body is read-only to machines (propose changes, never edit in place — e.g. a human journal capture); `script` → producer-owned (fix the generator and re-run, never hand-edit — the file-level form of the generated-sections rule); `assistant` → machine-editable per normal rules. **Absence means normal editability — it is not a gap.** Stamp new notes only where ownership matters (agent working data, generated files, verbatim human captures).
- **Session close ritual:** when {{NAME}} says "close", "wrap up", or equivalent, run [[Close a Session]] — one fixed order: threshold feedback pause (one question: "friction, misses, keepers — or 'nothing'"; proceed regardless) → **record** (log line; decisions-ledger check; digest/initiative updates) → **review** (route learnings by scope; schema changes are always proposals). The 6pm automated summary is the backstop for sessions that end without a close, not a replacement.
- **Role digests:** each advisor role keeps one **digest** — current state only, in its working-data area (e.g. a domain-advisor's `current-state.md`, a generated status file, an initiative's "Now & next"). Digests are capped (~2,000 words), **measured by script, never by model estimate** — `SYSTEM/bin/cap_check.py` (config: `SYSTEM/bin/cap_config.json`). A genuine blocker declares a dated `cap_exception:` in frontmatter — declared, never silent. History stays in separate append-only files (journals, trails, session notes) so orientation reads structurally cannot over-read.
- **Interaction contract (how agents report):** commit in one of three forms — "I am doing X now, will report back" / "Ready to do Y — say go" / "I need Z from you — tell me Z" (no status dumps trailing into unowned work). End turns that need {{NAME}}'s word with an explicit "**Need from you now:** …" block — and **nothing needing their word may first surface during or after a close** (a close that reveals a leftover means the prior turn misreported "done"). Rank options by what blocks and what delay costs (checkable facts), never by a causal story. Prefer {{NAME}}'s own phrase over a model-minted compound name.
- **Unattended-session guardrails** (scheduled jobs, CMUX workers, background agents): (1) **scoped rulings** — a ruling {{NAME}} states about named cases ships scoped to those cases; generalizing it into default machinery is a *new proposal for their word*, not a build freedom. (2) **presence gates** — an instruction that names {{NAME}}'s presence ("show me before applying", "confirm with them") reaching a session where they are absent is a **hard stop**, not a reinterpretation surface; prepare up to the gate, state the need, and wait — that the write is reversible does not unlock it.
- **Approval-queue checkbox marks** (any machine→human approval queue): `[ ]` pending · `[x]` approved (machinery may act) · `[-]` rejected — the line stays as its own tombstone, never re-presented · `[~]` snoozed (re-present next run) · `[p]` personal/out-of-scope (terminal, nothing files). Producers only ever flip `[~]` → `[ ]`; they never touch `[x]`, `[-]`, or `[p]`.
- **Vendor portability:** every enforced guarantee lives at a vendor-independent tier (script/ritual or OS-scheduled job); a harness surface (hook, native skill/command discovery) may *accelerate* it but never solely carry it, and **a script failure is declared, never imitated** by model judgment. Full rule: `Knowledge/Skills/RULE/Keep Machinery Vendor-Portable.md`.
- Dates use `YYYY-MM-DD`.
- **Rename/convention-change hygiene (anti-drift):** a rename or convention change isn't done when the primary artifact moves — it's done when **no prose still describes the old world**. Last step of any migration: grep the whole vault (including `Knowledge/Skills/` runbooks, READMEs, and this file) for the old name/pattern and fix every hit; keep old names resolvable via `aliases:`; regenerate the link map. Prefer **referencing** a single source (a script, a generated table) over copying its contents into prose — every copy is a future stale fact. Corollaries (**pointer-over-restatement**): a rule lives in exactly one home — a paraphrase elsewhere is a restatement that drifts, a pointer cannot; a rule that turns out to be stated in two role files or skills gets promoted to this file (one home) with pointers left behind; and **staleness is generated at write time** — the session that edits a rule greps for prose restating it *in the same session*, because that edit is what made the copies stale.

## Health checks (lint) — run on request or automatically via SYSTEM/optional/automation/daily-summary.sh

**Run the mechanical half with `SYSTEM/bin/lint.sh`** (exit 0 = green): it deterministically checks inbox-clean, wikilinks-resolve, index-complete, frontmatter-present, next-action coverage, and digest caps — faster and more reliably than reading every file by hand. It skips TEMPLATE files and ignores `[[links]]` inside inline-code spans. Scheduled runs should use `SYSTEM/bin/lint-delta.sh` (alarms on the finding-count delta, not the total). The **judgment** checks below (stale facts, resolved open questions, whether an `#action` is genuinely still open) aren't scriptable — they remain a manual/LLM pass on top. The optional 6pm `daily-summary.sh` runs `lint.sh` for the mechanical pass (plus `lint-delta.sh` as the scheduled alarm) and has the LLM do only the judgment layer.

- Every fact in a concept article traces back to a `Knowledge/raw/` capture or a conversation.
- No `[[wikilink]]` points to a note that doesn't exist — including `[[Full Name]]` person-links (must resolve to a real `Knowledge/People/` note or registered alias).
- `index.md` lists every concept and initiative file; `Knowledge/Concepts/skills.md` lists every skill in `Knowledge/Skills/`.
- **Inbox is empty:** the vault root holds only `README.md` + `index.md` + `Actions.md` + `CLAUDE.md` (plus the structural folders: `Knowledge/Concepts/`, `Knowledge/Initiatives/`, `SYSTEM/`, `Knowledge/raw/`, `daily/`, `Knowledge/People/`, `Knowledge/Skills/`, `attachments/`, `docs/`, `Writing/` [optional], `Knowledge/Excalidraw/` [optional]). Any other root file is un-triaged — file it into `Knowledge/raw/` and compile. If some automation writes to a fixed root file (a machinery write-target, not an inbox item), register it in `lint.sh`'s `standing` list — triage its *contents*, keep the file.
- Flag stale items and resolved open questions.
- **Actions current:** every `- [ ] … #action` is real and still open; completed ones are checked off (not deleted). `Actions.md` is the single aggregated view.
- **Initiatives current:** every `type: initiative` note with `status: active|paused` appears on the index Quick map's Initiatives line; a live initiative whose `updated:` is weeks old (or whose actions are all checked) probably needs a Now & next rewrite or a close. Every `status: active` initiative carries ≥1 open `#action` (enforced by `SYSTEM/bin/audit-initiative-next-actions.sh`).

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

**Daily-note rollup:** if you adopt daily notes, `SYSTEM/bin/rollup-daily-weeks.sh`
keeps `daily/` tidy — past weeks' `daily/YYYY-MM-DD.md` notes move into folders
named for their week's Monday (`daily/YYYY-MM-DD/`), current-week notes stay
loose. Idempotent; safe to run nightly. Wikilinks resolve by filename, so
moving files breaks nothing.

**Writing pipelines** are another optional layer: an outward-facing publication
(newsletter, blog) gets one subfolder per outlet under `Writing/<Outlet>/`,
with a simple stage flow inside it (e.g. `IDEAS/ → DRAFTS/ → PUBLISH/`, plus a
`RESOURCES/` folder for outlet-specific style notes). `Writing/` is a
structural folder (registered in `lint.sh`); the pipeline's skill lives in
`Knowledge/Skills/` like any other skill.

A ready-to-adopt bundle (macOS + Claude Code) ships in `SYSTEM/optional/automation/` — a
SessionStart loader, a Google Calendar cache + Gmail digest (via the `gws` CLI),
an 8am daily-plan generator, a 6pm lint/recap/git-snapshot job, and the launchd
jobs to schedule them. See `SYSTEM/optional/automation/README.md`.

**Visual diagrams** are another optional layer: `SYSTEM/bin/excalidraw.py` is a
zero-dependency generator that emits native Obsidian-Excalidraw `.excalidraw.md`
files (shapes + bound labels + auto-routing arrows) from a compact Python
node/edge spec — no npm, no browser, no network. Files land in the optional
`Knowledge/Excalidraw/` structural folder. See `Knowledge/Skills/FORMAT/Create an Excalidraw Diagram.md`.

**Multi-agent orchestration (CMUX)** is a further optional *runtime* layer, for
anyone running a terminal multiplexer/agent-orchestration tool (e.g.
[CMUX](https://github.com/disler/learning-cmux-with-agents)) alongside this KB.
The model: two interfaces with a clean division of labour — the **vault stays
memory/state** (durable — initiatives, actions, concepts) and the **orchestration
tool is runtime** (ephemeral — windows/workspaces/panes, spun up and torn down
per task). **State round-trips through the vault, not through the runtime tool**:
whatever gets dispatched, and whatever comes back (decisions, milestones,
follow-up `#action`s), gets written into the relevant `Knowledge/Initiatives/<slug>.md`
note — if it isn't in the vault, it didn't happen. Two granularities of
delegation, each its own runbook: workspace-level (a whole initiative gets its
own repo context and its own agent — `Knowledge/Skills/DO/Delegate an Initiative to a CMUX Workspace.md`) and pane-level (one task fans out into concurrent sub-tasks
sharing a context — `Knowledge/Skills/DO/Spawn Subagent Panes in a CMUX Workspace.md`). Both
skills use the same four-verb control loop (type → submit → read → close),
event-driven coordination (a `DONE: <summary>` sentinel — "notify" from the tool
isn't the same as "done"), and a model policy of a more capable model as
lead/orchestrator with cheaper/faster models as workers. **Launch pane workers
lean** — give each worker few or no MCP servers (e.g. a `--strict-mcp-config`
flag with an empty config, if your agent CLI supports it); a large MCP fleet
injects enough tool schema to crowd out a worker's context after a handful of
file reads, and that same bloat can make an in-process subagent/Task tool
unusable — which is exactly why explicit, lean pane workers are the reliable
path. Entirely optional — skip it if you're not running a multi-agent terminal
tool.

Optionally, give workers a **named identity** instead of a blank agent:
`Knowledge/Agents/` holds one **real Claude Code subagent definition** per role
(a starter set — `research`, `compile`, `lint`, `initiative-worker` — maps
onto this KB's own raw→compile→index→lint verbs and its
initiative-delegation model, not a generic app-build split). Each file is the
same format as a file under `~/.claude/agents/` — YAML frontmatter
(`name`/`description`/`version`/`model`/`tools`/`color`/`status`/`tags`/`updated`, validated
against `AgentFrontmatter` in `SYSTEM/schemas/models.py`) followed by a
plain-English system prompt — so the identical file works two ways:
**symlink it into `~/.claude/agents/`** to make it directly invocable as a
native subagent from any Claude Code session, and/or pass it via your agent
CLI's system-prompt flag when launching a CMUX pane worker (e.g.
`--append-system-prompt <vault>/Knowledge/Agents/<role>.md`, with an
**absolute path** — a worker's cwd may not be your vault). The frontmatter's
`tools:` list keeps a subagent lean (only the tools the role needs), which
sidesteps the MCP-bloat problem above for the native subagent path too.
`SYSTEM/bin/build_directory_indexes.py` regenerates the folder's `index.md`
table straight from every agent's frontmatter.

**Domain-advisor roles** extend the same `Knowledge/Agents/` idea beyond
orchestration: a *standing analyst* over one domain of the KB (finances,
health, a hobby — whatever the vault covers deeply). Each advisor is one role
file built from `Knowledge/Agents/domain-advisor TEMPLATE.md` (scope, data
sources, operating principles, output shape) paired with one on-demand `Knowledge/Skills/`
skill built from `Knowledge/Skills/DO/Run a Domain Review TEMPLATE.md` that loads the role and walks
a review. The role carries the *stance* (what to watch, how to reason about
the domain); the skill carries the *steps*; findings land back in the domain's
concept/initiative notes per the normal compile flow. Entirely optional — add
one when a domain accumulates enough state that ad-hoc questions keep
re-deriving the same analysis.
