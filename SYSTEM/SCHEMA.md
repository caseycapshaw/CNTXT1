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
| Source code | Raw, unprocessed captures (slides, conversation notes, articles) — the source of truth | `raw/` |
| Compiler | An LLM (me) processes raw material into structured articles | — |
| Executable / wiki | Compiled, queryable knowledge | `05 concepts/` |
| Index | The map the agent starts from | `index.md` |
| Lint / tests | Health checks for gaps, stale data, broken links | see "Health checks" below |
| Log | Record of what changed | `SYSTEM/log.md` |
| Work stack (GTD) | actions → Projects (H1) → Areas (H2) → Horizons (H3–5), chained by frontmatter up-links | `Actions.md` · `03 Projects/` · `02 Areas/` · `01 Horizons/` |

## Data flow

0. **Inbox = the vault root.** New notes and dropped files start at the **vault root** — the inbox. Anything sitting at the root *other than the pinned anchors* (`README.md`, `index.md`, `Actions.md`, `CLAUDE.md`, `AGENTS.md`) is an un-triaged inbox item awaiting filing. A clean root (only the anchors + the structural folders) means the inbox is empty. **Structural folders** (not inbox items): `00 daily/`, `01 Horizons/`, `02 Areas/`, `03 Projects/`, `04 People/`, `05 concepts/`, `raw/`, `Skills/`, `Agents/`, `attachments/`, `excalidraw/`, `docs/`, `SYSTEM/`. Authoritative exception list: `SYSTEM/bin/lint.sh` check 1; folder *names* single-source in `SYSTEM/bin/kb-folders.json`.
1. **Triage → `raw/`.** Move each inbox item into `raw/` as dated markdown (`YYYY-MM-DD-topic.md`), lightly edited, with a one-line source/provenance header. This is the source of truth; never delete it.
2. **Route → the right compiled home.** First match wins (`Skills/DO/File a New Note.md`): person/org → `04 People/` · completable work → `03 Projects/` · ongoing responsibility → `02 Areas/` · procedure → `.claude/skills/` · orientation → `01 Horizons/` · otherwise durable knowledge → `05 concepts/`. Relationships live inline — `[[wikilinks]]` plus each note's **Related** section (Obsidian's backlinks panel and graph view materialize the reverse direction); a relationship with real substance becomes its own concept.
3. **Index → `index.md`.** Keep the index current so the agent knows where to start without semantic search / RAG.
4. **Log → `SYSTEM/log.md`.** Append a one-line entry for every meaningful update.

## Privacy & content separation (non-negotiable)

This vault is **private by definition**. Every note in it — people, finances,
raw captures, daily notes, projects, logs — is personal content, and the
hard, non-negotiable line is **publication**: personal content never gets
posted to a public website, committed or pushed to a public or shared repo,
or otherwise put anywhere a public or shared audience could find it.

**Third-party LLM/tool API calls are not "publication."** Sending vault
content to your agent itself, a headless `claude -p` job, or a third-party
model/tool you have evaluated, as part of normal KB automation, does not
require a case-by-case privacy ruling — ordinary judgment applies (send only
what a call needs; prefer non-sensitive material when there's a choice). The
concern this rule guards against is public/shared exposure, not private
request/response calls to a service provider. Keep this stricter than that
for **search/share tools that post a query to a public platform**: a query can
surface in someone else's results, an API call can't — disable those before
working in the vault.

**Secret hygiene.** Agents never print credential or config stores — `.env`
files, app config databases, `/etc/credstore`, `~/.config/*` secrets,
password-manager item values. Inspect by **key name or length/prefix only**
(`jq 'keys'`, `wc -c`, `${v:0:6}`). Secrets move **machine-to-machine** (ssh
into a variable/file, never stdout) or via a **password manager CLI**; human
entry uses a **hidden prompt on the target host** (`read -rs`) — never through
chat. A leak into any session output (transcript, log, terminal scrollback) is
treated as exposure: rotate the secret. (Why: a subagent that "just looked" at
a config file with `sed` printed live API keys into its transcript, forcing a
rotation — the harm is in the printing, not the intent.)

The one sanctioned outward path to a **public** audience is the **framework
itself**: **CNTXT1**, the public shareable starter kit this vault is an instance of
([caseycapshaw/CNTXT1](https://github.com/caseycapshaw/CNTXT1)), receives
*generic* improvements only — schema, templates, `Skills/` skills,
`SYSTEM/bin/` scripts — each **hand-copied and re-templated** (real values
swapped back to `{{placeholders}}`) via the skill
`Skills/DO/Sync an Improvement to CNTXT1.md`, which ends with a personal-identifier
**grep gate** before anything is committed publicly.

Hard rules:
- **Never push from this vault to the public CNTXT1 repo** — no pushable
  remote, no pushed branch, ever; the private instance and the public
  framework keep independent histories on purpose. A **fetch-only**
  `upstream` remote pointing at the public kit *is* sanctioned (its push URL
  set to `DISABLED` so git physically cannot push): public → private can't
  leak, so that direction is git-automated — pull kit improvements inward
  via `Skills/DO/Pull Framework Updates from CNTXT1.md`. Author generic
  improvements **upstream-first** (in the public kit, through its CI gates)
  when they aren't already implemented privately; the manual re-template
  sync below remains the only outward path.
- **Never automate the outward copy** (no export script, no
  subtree/filter-repo exclude list) — the manual re-template step *is* the
  leak protection; automation drifts stale and leaks.
- **When in doubt whether something is generic or personal, it's personal** —
  it stays in the vault.

## Conventions

- **Backlinks:** use Obsidian-style `[[wikilinks]]` to connect notes. Reference people by `[[Full Name]]` (their `04 People/` note); nicknames resolve via the note's `aliases:` frontmatter field. A `[[link]]` to a note that doesn't exist yet is fine — it marks something worth writing later. Cite raw captures as path-style wikilinks — `[[raw/YYYY-MM-DD-topic]]` (no `.md`) — so citations hyperlink in Obsidian; backticks are only for filename *patterns*/templates, never for a reference to a real file.
- **People:** every named person = one note in `04 People/Full Name.md` (Title Case, with spaces) — the single source of truth for per-person detail. Built from `04 People/People TEMPLATE.md`. `05 concepts/contacts.md` is the index (who-for-what map + grouped tables). Don't duplicate per-person prose into concepts — link to the person note. Businesses and vendors are **`type: org` notes in the same folder** (see *Relations frontmatter*). `04 People/` is a **structural folder, not the inbox**.
- **Skills:** every recurring task = one **canonical** skill at `.claude/skills/<kebab-slug>/SKILL.md` — full content in the standard Agent Skills format (top-level `name:` + `description:`, auto-discovered by Claude Code, Grok Build, and other SKILL.md-standard agents), with the org-schema keys under `metadata:` (`title/type/domain/trigger/frequency/tools/owner/status/tags/aliases/summary/updated`; `title` = the Imperative Title, `type` lowercase ∈ do/check/format/rule, matching the mirror folder `TYPE` ∈ `DO` performs a recurring task · `CHECK` verifies/audits · `FORMAT` produces an artifact · `RULE` standing convention). **Truth direction: the executed surface is canonical; the visible notes are generated mirrors** — `SYSTEM/bin/build_claude_mirrors.py` regenerates `Skills/<TYPE>/<Imperative Title>.md` (banner + `author_type: script`) so wikilinks, the graph, and the per-TYPE indexes keep working; **never edit a mirror** (the lint mirror check reds on drift). Built from `Skills/Skill TEMPLATE.md` (hand-maintained, not mirrored). `05 concepts/skills.md` is the index. The skill carries the steps; the matching concept keeps the *why/context*. `Skills/` is a **structural folder, not the inbox**.
- **Concept articles** are evergreen and rewritten in place as understanding improves — they are the compiled truth, not a log. Each opens with YAML frontmatter — `type: concept` · `description:` (one **stable** sentence of essence, not volatile status — it single-sources the note's `index.md` one-liner and keeps exports OKF-aligned, see [[open-knowledge-format]]) · `updated: YYYY-MM-DD` · `status: current` (or `stale`/`superseded`) · `tags: [concept, <domain>]`. **Bump `updated:` on every meaningful rewrite** — it's the mechanical staleness signal (a concept whose `updated:` predates a contradicting fact is findable). Mirrors the frontmatter `04 People/` and `Skills/` already carry.
- **Projects (GTD H1)** are goal-directed workstreams — an outcome needing **multiple actions over time** (rule of thumb: 3+ actions or more than a week) with a **genuine endpoint**. The classification rule is the **endpoint test**: completable ever = project; maintained-to-a-standard, never "done" = area (below). Every project = one note in `03 Projects/<kebab-slug>.md` (a **structural folder, not the inbox**), built from `03 Projects/Project TEMPLATE.md`, with `type: project` · `description:` (one stable sentence — same rule as concepts) · `status: pending|active|paused|done` (`pending` = **the Someday/Maybe bucket**: opened, waiting on a trigger; exempt from the next-action audit like `paused`) · `started:` · `updated:` · **`area:` (required up-link — the `02 Areas/` note this project serves, `"[[<slug>]]"`; schema-enforced on live projects)** · optional **`serves:`** (→ a `type: goal` note or a horizon; does not replace `area:`). Sections: Outcome (definition of done) · Now & next (rewritten in place) · Decisions + Milestones (dated, append-only) · Open questions · Actions (inline `#action` checkboxes — they aggregate to `Actions.md` and group under the project automatically) · optional `## Trail` (append-only, one line per working session, written at the session close; "Now & next" stays the rewritten state so the two never mix) · Related. Live projects are listed on the **Projects (live)** line of the `index.md` Quick map; every project is listed in the index's Projects section. A concept that turns out to be goal-shaped converts by `git mv` into `03 Projects/` + frontmatter swap + link-map regen (wikilinks are basename-based, so links don't break) — the same mechanic converts project↔area when the endpoint test says a note is filed wrong. Closing: `status: done`, final milestone, durable knowledge distilled into `05 concepts/`/areas, then `git mv` the note into **`03 Projects/archive/`** (done projects live there; live + paused stay at the top level) + link-map regen — the note is kept forever as the record. Lifecycle skill: `Skills/DO/Run a Project.md`. Every active project must carry ≥1 open `#action` (`SYSTEM/bin/audit-project-next-actions.sh`, lint check 10).
- **Areas (GTD H2)** are ongoing responsibilities — never "done", maintained to a standard. One note each in `02 Areas/<kebab-slug>.md`; **`02 Areas/` is flat except `02 Areas/Assets/`**, the subfolder holding asset sub-areas (a vehicle, a boat, the house). Built from `02 Areas/Area TEMPLATE.md`, with `type: area` · `description:` · `status: current` · `updated:` · **`review: weekly|monthly|quarterly` + `reviewed: YYYY-MM-DD`** (the review cadence — audited by `SYSTEM/bin/audit-area-reviews.sh`, lint check 12, WARN-only) · sub-areas carry `area:` (parent up-link, e.g. `"[[assets]]"`) · areas may carry `serves:` (→ a `type: goal` note under `01 Horizons/Goals/`, or a horizon note). Body = the compiled truth (facts trace to `raw/`, same as concepts — an area note IS the single source of truth for its thing) plus a **`## Standard`** section: what "maintained" means, the bar a review checks. Areas do **not** owe next actions — they owe a recent review; **reviewing an area is where its projects get created and retired** (runbook: `Skills/DO/Review an Area.md`). **Graduated-folder policy:** an area whose work accumulates self-contained elements (a pipeline, working artifacts) graduates to a matching lowercase subfolder `02 Areas/<slug>/` beside its note — the same note-plus-working-folder pattern as `Agents/<role>.md` + `Agents/<role>/`. The area note stays flat at `02 Areas/<slug>.md` (schema-checked like any area); the folder holds working files exempt from note rules. Distinct from `02 Areas/Assets/` (capitalized), which is a *grouping* folder of schema-checked sub-area notes, not working data.
- **Horizons (GTD H3–H5)** are the orientation notes above areas. H3 is nested: `01 Horizons/Goals/index.md` (the door, `aliases: [goals]`, reviewed quarterly) plus one `type: goal` note per 1–2 year outcome in `01 Horizons/Goals/` (`horizon: "[[goals]]"`, `order:`, no review cadence of its own; built from `Goal TEMPLATE.md`). H4 `01 Horizons/vision.md` and H5 `01 Horizons/purpose-principles.md` stay one note each (`type: horizon` + `level:`, yearly review). **The chain is up-links only:** projects declare `area:` (required); areas and projects may declare `serves:` at a specific goal (or a horizon); goal notes up-link `horizon: "[[goals]]"`; downward views are generated by `SYSTEM/bin/build_horizon_serves.py` (markdown below `<!-- generated -->`, lint check 14) — never hand-maintained lists. Method background: `05 concepts/gtd.md`.
- **Relations frontmatter:** compiled entities carry their cross-document relationships as typed frontmatter fields, extending the GTD up-link pattern beyond the work stack. Asset sub-areas declare `owner:` (the owner's name | `household` | `"[[Full Name]]"`) and optionally `serviced-by: "[[org]]"`; person notes declare `relation:` (the relationship **to you**, side-of-family in the value when it matters); businesses/vendors are **`type: org` notes living in `04 People/`** beside the people (fields: `org` · `role` · `location` · `found-by: "[[Full Name]]"` — who brought the relationship in). **Up-links only:** an org never lists its clients, a person never lists what they own — inverse views are grepped or generated, never hand-maintained. Enforcement: Pydantic (`SYSTEM/schemas/`, lint check 9). Retrieval contract: seek relationships by **`rg` over frontmatter first**, then trace into prose.
- **`index.md` is a pure map, not a log.** It opens with a compact **Quick map** skeleton (every concept/project/area/index as a one-liner) so the whole structure fits the session-start injection budget. `SYSTEM/bin/build_boot_bundle.sh` (the session-start boot bundle) inlines that skeleton via awk (everything up to the first H2 that is not `## Quick map`); lint check 8 measures the same cut against 8000 bytes, and lint check 18 fails ISO dates / status words in the skeleton so it cannot become a dashboard again. One-liners single-source from stable `description:` fields. **Change history never lives in `index.md`** — it goes to `SYSTEM/log.md`. If the Quick map outgrows the budget, tighten it — don't let the skeleton spill past the cut. The `## Projects`, `## Concepts` and `## Areas` sections generate from each note's frontmatter (`build_index_projects.py` + `build_index_lists.py`, lint checks 15/15a); the Quick map and the Horizons/People/Skills lists stay hand-curated.
- **`SYSTEM/link-map.md` resolves wikilinks in one lookup.** A generated table mapping every `[[target]]` (concept slug, project/area/goal slug, People name + `aliases:`, Skill slug + aliases) → its file path — read it instead of grepping. **Regenerate after adding/renaming any note that is a link target:** `SYSTEM/bin/build-link-map.sh` (idempotent; fails on duplicate keys).
- **Raw notes** are append-only and dated; they preserve the original source.
- **Generated sections** are the always-current mechanism. Any file that machines rewrite splits at a `<!-- generated -->` marker: **hand-maintained config above** (humans edit schedules/annotations), **machine-rewritten content below** with a visible `_Generated: YYYY-MM-DD_` stamp. Generators are small, per-domain, idempotent scripts (one tool, one job); they **pin expected input headers and exit non-zero rather than write partial or silently-wrong output**; a stamp older than its cadence means the job missed — say so, don't guess. Never hand-edit below a marker. Worked examples: the auto-built directory indexes (`SYSTEM/bin/build_directory_indexes.py`), the index Projects/Concepts/Areas sections, the horizon serving lists, and the optional status-dashboard generator (`SYSTEM/optional/automation/status-gen-example.py`). Full convention: `Skills/RULE/Maintain Generated Sections.md`.
- **Attachments are stored with their content — by ownership, not location.** Every binary/document lives in `attachments/<owning-note-slug>/…` where the slug names the concept/project/area/skill/person note that owns it (e.g. `attachments/family-car/` ↔ `02 Areas/Assets/family-car.md`); nested subfolders under the owner are fine. No loose files at the `attachments/` top level; the owning note references its files inline. `lint.sh` enforces this mechanically (check 6).
- **Root is the inbox, not a home for permanent files.** Only `README.md`, `index.md`, `Actions.md`, `CLAUDE.md`, and `AGENTS.md` live there permanently (plus the kit's own `setup.md`, `LICENSE`, `MIGRATING.md`, `CHANGELOG.md` and `pyproject.toml`/`uv.lock`); everything else at the root is transient and should be triaged into `raw/` (then compiled). Permanent machinery lives in `SYSTEM/`. Structural folders (`00 daily/`, `01 Horizons/`, `02 Areas/`, `03 Projects/`, `04 People/`, `05 concepts/`, `raw/`, `Skills/`, `Agents/`, `attachments/`, `excalidraw/`, `docs/`, `SYSTEM/`) are **not inbox items**. *(The structural-folder list is copy-mirrored in prose — `lint.sh` check 1's `structural`/`template_extras`/`tooling`/`standing` variables are the **single source of truth**; when adding a top-level folder or root exception, update lint first, then sync the prose copies here and in `AGENTS.md`.)*
- **Open questions** live at the bottom of the relevant concept, project, or area note — not as a separate index section.
- **Actions (to-dos)** are Markdown checkboxes tagged `#action` — `- [ ] … #action` (optional `📅 YYYY-MM-DD` due date) — written **inline in the note they belong to**, next to their context. They're aggregated into one live view at `Actions.md` (a pinned root anchor; Obsidian **Tasks** plugin). Keep *actions* (things you do) distinct from *open questions* (unknowns); when a question's resolution is a task you perform, write it as an `#action`. Check items off in their home note (or the dashboard) — never maintain a duplicate manual to-do list.
- **`#priority` flags a focus action.** Add `#priority` to an action line (`- [ ] … #action #priority`) to mark it important. It's a plain importance flag; no due date required.
- **Three ledgers, three grains:** `SYSTEM/log.md` = *what changed* (append-only changelog, every meaningful update). **`SYSTEM/decisions.md` = *what {{NAME}} ruled*** (index-not-record: date + title + 1–2 sentences + pointer to the fuller record). A decisions line lands **only on {{NAME}}'s explicit ruling-verb** ("decided", "adopted", "that's a decision"…) or their confirmation at a session close — unattended jobs propose, never append. The ledger is non-exhaustive by declaration; per-note `## Decisions` sections remain the records it points at. **`SYSTEM/skill-impact.md` = *how the skills evolved*** (third ledger): one line per proposed change to a canonical skill, `ADOPTED|REJECTED|PARKED` + reason + pointer, written at the session close (step 3 of [[Close a Session]]) — rejections are recorded on purpose so they are never re-proposed; an ADOPTED line bumps the skill's `metadata.version`. Unattended jobs may write `PARKED` only. Three ledgers, three grains.
- **`#auto` marks machine-written actions.** Any job or agent that appends an action on its own must add `#auto` (`- [ ] … #action #auto`) — a job that omits it is a bug. `#auto` lines are queues worked in their home note; the action census (`SYSTEM/bin/actions.py`) excludes them from "stale" unless they are also `#priority`. Human-written actions never carry it. Optionally stamp a created date (`➕ YYYY-MM-DD`) so aging can be measured; the census reports actions with **no** stamp as their own *unknown-age* count rather than folding them into "not stale".
- **Orientation caps + trails.** A project's or area's `## Now & next` is an orientation surface — **≤500 words**, rewritten state, never a diary; `## Milestones` ≤400 words. Measured by script (`SYSTEM/bin/cap_check.py`, `sections` in `cap_config.json`; lint check 11), never by model estimate; a dated `cap_exception:` declares a WARN. Over cap → move history **verbatim** into the note's trail sibling `03 Projects/trails/<slug>-trail.md` / `02 Areas/trails/<slug>-trail.md` (`type: trail`, `of: "[[slug]]"`, append-only, newest entries stay in the note) and rewrite the section from what is still true; `SYSTEM/bin/cap_overflow.py --write` does the `## Milestones` half mechanically (oldest bullets out, trail pointer left; dry-run default) — `## Now & next` overflow is prose, always a rewrite. Durable reference that isn't state (design notes, loan facts) moves to its own `## Design` / `## Reference` section, not the trail. Trails are link-map targets (`[[<slug>-trail]]`), not index entries, not schema-validated.
- **Action census (optional).** `SYSTEM/bin/actions.py --write` rewrites a generated block in `Actions.md` — open / `#priority` / `#auto` counts, per-home table, **stale** (created stamp `➕ YYYY-MM-DD` older than 30 days) and **unknown-age** lists — between the marker lines `<!-- actions:auto:start -->` and `<!-- actions:auto:end -->`, which you add to `Actions.md` to opt in. `SYSTEM/bin/aging-actions.sh` is the terminal view; `backfill-action-dates.sh` stamps undated actions once. Nothing bulk-adds dates silently.
- **Boot bundle (the KB kernel's boot sequence).** `SYSTEM/bin/build_boot_bundle.sh` generates one ≤6k-token orientation bundle for the start of every agent session, identical on every machine: **HOST** (which machine this is + the scheduled jobs living there) · **VAULT** pointer · **TODAY** (plan-note pointer + calendar from the cache, never live) · **MAP** (the `index.md` Quick-map skeleton only — everything up to the first H2 that is not `## Quick map`) · **INBOX** (un-triaged root items) · **PRIORITY** (open `#action #priority` lines with their home note) · **LOG TAIL** (last 5 `SYSTEM/log.md` lines) · **KB STATS** (the last `kb_stats.py` digest line). The SessionStart hook (`SYSTEM/optional/automation/sessionstart-hook.sh`, registered in `.claude/settings.json`) emits it; if the script is missing or fails the hook falls back to its older inline loader, never to nothing. Because the bundle inlines the map, an agent does **not** re-read `index.md` at session start and reads this schema **on demand** (when a task touches conventions, structure, or compilation) rather than by reflex. `build_boot_bundle.sh --size` reports bytes + ≈tokens and exits non-zero over `BUDGET_BYTES` (default 24000); `kb_stats.py` records that as the boot-cost gauge. Vault-generic and configured only by env vars with neutral defaults: `KB_LAUNCHD_PREFIX` (macOS launchd label prefix to list as this machine's jobs, default `com.example.`), `KB_TIMER_PREFIX` (Linux systemd timer prefix, default `kb-`), `KB_PEERS` (space-separated `~/.ssh/config` Host names to list as reachable peers — nothing is read from ssh config unless listed), `CAL_CACHE`, `BUDGET_BYTES`. Lint checks 8 and 18 keep the Quick map inside the injection budget and free of status/dates. Not a required piece of the method — a harness without hooks can run the script by hand.
- **Log rotation (optional).** `SYSTEM/log.md` is the live log for the current month; `SYSTEM/bin/rotate_log.sh` (idempotent — run it from a nightly job) moves every `- YYYY-MM-DD` entry from earlier months verbatim into `SYSTEM/log/YYYY-MM.md`. Appenders never change; readers search both. A log that can't be read whole is a log that gets skipped.
- **Inline human protection (`> [!human]`).** A note whose body is otherwise machine-editable but carries pockets of raw human-typed text — a daily note's `## Notes` section is the paradigm case, alongside automated sweeps in the same file — wraps that text in an Obsidian callout, `> [!human]`. This is the inline counterpart of the `author_type: human` rule below: **content inside a `[!human]` callout is read-only to machines.** Automated sweeps and AI sessions may *integrate around it* (append a strikethrough + completion link, add a reply, file a pointer) but must never edit, shorten, or delete the quoted text itself. Applies wherever human and machine text share a note.
- **Authorship & write permission (optional, meaningful when present):** a note may carry `author:` + `author_type: human | assistant | script` in frontmatter — and `author_type` is a **write-permission switch, not credit**. `human` → the body is read-only to machines (propose changes, never edit in place — e.g. a human journal capture); `script` → producer-owned (fix the generator and re-run, never hand-edit — the file-level form of the generated-sections rule); `assistant` → machine-editable per normal rules. **Absence means normal editability — it is not a gap.** Stamp new notes only where ownership matters (agent working data, generated files, verbatim human captures).
- **Session close ritual:** when {{NAME}} says "close", "wrap up", or equivalent, run [[Close a Session]] — one fixed order: threshold feedback pause (one question: "friction, misses, keepers — or 'nothing'"; proceed regardless) → **record** (log line; decisions-ledger check; digest/project updates) → **review** (route learnings by scope; schema changes are always proposals). The 6pm automated summary is the backstop for sessions that end without a close, not a replacement.
- **Role digests:** each advisor role keeps one **digest** — current state only, in its working-data area (e.g. a domain-advisor's `current-state.md`, a generated status file, a project's "Now & next"). Digests are capped (~2,000 words), **measured by script, never by model estimate** — `SYSTEM/bin/cap_check.py` (config: `SYSTEM/bin/cap_config.json`). A genuine blocker declares a dated `cap_exception:` in frontmatter — declared, never silent. History stays in separate append-only files (journals, trails, session notes) so orientation reads structurally cannot over-read.
- **Interaction contract (how agents report):** commit in one of three forms — "I am doing X now, will report back" / "Ready to do Y — say go" / "I need Z from you — tell me Z" (no status dumps trailing into unowned work). End turns that need {{NAME}}'s word with an explicit "**Need from you now:** …" block — and **nothing needing their word may first surface during or after a close** (a close that reveals a leftover means the prior turn misreported "done"). Rank options by what blocks and what delay costs (checkable facts), never by a causal story. Prefer {{NAME}}'s own phrase over a model-minted compound name.
- **Unattended-session guardrails** (scheduled jobs, CMUX workers, background agents): (1) **scoped rulings** — a ruling {{NAME}} states about named cases ships scoped to those cases; generalizing it into default machinery is a *new proposal for their word*, not a build freedom. (2) **presence gates** — an instruction that names {{NAME}}'s presence ("show me before applying", "confirm with them") reaching a session where they are absent is a **hard stop**, not a reinterpretation surface; prepare up to the gate, state the need, and wait — that the write is reversible does not unlock it.
- **Approval-queue checkbox marks** (any machine→human approval queue): `[ ]` pending · `[x]` approved (machinery may act) · `[-]` rejected — the line stays as its own tombstone, never re-presented · `[~]` snoozed (re-present next run) · `[p]` personal/out-of-scope (terminal, nothing files). Producers only ever flip `[~]` → `[ ]`; they never touch `[x]`, `[-]`, or `[p]`.
- **Vendor portability:** every enforced guarantee lives at a vendor-independent tier (script/ritual or OS-scheduled job); a harness surface (hook, native skill/command discovery) may *accelerate* it but never solely carry it, and **a script failure is declared, never imitated** by model judgment. Project hooks are registered in `.claude/settings.json` and point at `SYSTEM/optional/automation/` scripts. Full rule: `Skills/RULE/Keep Machinery Vendor-Portable.md`.
- Dates use `YYYY-MM-DD`.
- **Rename/convention-change hygiene (anti-drift):** a rename or convention change isn't done when the primary artifact moves — it's done when **no prose still describes the old world**. Last step of any migration: grep the whole vault (including `Skills/` runbooks, READMEs, and this file) for the old name/pattern and fix every hit; keep old names resolvable via `aliases:`; regenerate the link map. Prefer **referencing** a single source (a script, a generated table) over copying its contents into prose — every copy is a future stale fact. Corollaries (**pointer-over-restatement**): a rule lives in exactly one home — a paraphrase elsewhere is a restatement that drifts, a pointer cannot; a rule that turns out to be stated in two role files or skills gets promoted to this file (one home) with pointers left behind; and **staleness is generated at write time** — the session that edits a rule greps for prose restating it *in the same session*, because that edit is what made the copies stale.

## Health checks (lint) — run on request or automatically via SYSTEM/optional/automation/daily-summary.sh

**Run the mechanical half with `SYSTEM/bin/lint.sh`** (exit 0 = green): it deterministically checks inbox-clean, wikilinks-resolve, index-complete, frontmatter-present, next-action coverage, and digest caps — faster and more reliably than reading every file by hand. It skips TEMPLATE files and ignores `[[links]]` inside inline-code spans. Scheduled runs should use `SYSTEM/bin/lint-delta.sh` (alarms on the finding-count delta, not the total). The **judgment** checks below (stale facts, resolved open questions, whether an `#action` is genuinely still open) aren't scriptable — they remain a manual/LLM pass on top. The optional 6pm `daily-summary.sh` runs `lint.sh` for the mechanical pass (plus `lint-delta.sh` as the scheduled alarm) and has the LLM do only the judgment layer.

**Regenerate before you check.** Most red is a stale generated view, not a decision — run `SYSTEM/bin/regen-all.sh` first (every generator the kit ships, in order, fail-loud). Policy: **stale generated views and word-cap overruns are WARN, not FAIL, under plain `lint.sh`** — a mechanical remedy exists (`regen-all.sh`; `cap_overflow.py --write` for Milestones overflow), so it is not a human decision. `LINT_STRICT=1` FAILs them again (the gate a scheduled maintainer runs *after* regen). Everything else — broken links, missing frontmatter, schema violations, a next-action gap — still FAILs plainly: a human's call.

- Every fact in a concept article traces back to a `raw/` capture or a conversation.
- No `[[wikilink]]` points to a note that doesn't exist — including `[[Full Name]]` person-links (must resolve to a real `04 People/` note or registered alias).
- `index.md` lists every concept, project, area, horizon and goal note; `05 concepts/skills.md` lists every skill in `Skills/`.
- **Inbox is empty:** the vault root holds only `README.md` + `index.md` + `Actions.md` + `CLAUDE.md` (plus the structural folders: `00 daily/`, `01 Horizons/`, `02 Areas/`, `03 Projects/`, `04 People/`, `05 concepts/`, `raw/`, `Skills/`, `Agents/`, `attachments/`, `excalidraw/`, `docs/`, `SYSTEM/`). Any other root file is un-triaged — file it into `raw/` and compile. If some automation writes to a fixed root file (a machinery write-target, not an inbox item), register it in `lint.sh`'s `standing` list — triage its *contents*, keep the file.
- Flag stale items and resolved open questions.
- **Actions current:** every `- [ ] … #action` is real and still open; completed ones are checked off (not deleted). `Actions.md` is the single aggregated view.
- **Projects current:** every `type: project` note with `status: active|paused` appears on the index Quick map's Projects line; a live project whose `updated:` is weeks old (or whose actions are all checked) probably needs a Now & next rewrite or a close. Every `status: active` project carries ≥1 open `#action` (lint check 10, `SYSTEM/bin/audit-project-next-actions.sh`) and an `area:` up-link (schema-enforced).
- **Areas/Horizons reviewed:** every area and horizon note's `reviewed:` is within its `review:` cadence window (lint check 12, WARN-only — `SYSTEM/bin/audit-area-reviews.sh`); overdue means run `Skills/DO/Review an Area.md`.

**The gardener (optional add-on)** is a nightly autonomous maintainer: unattended on its own schedule, it runs `regen-all.sh`, fixes what lint can fix mechanically, compiles unambiguous `raw/` captures, commits, and writes one digest to the day's `00 daily/` note. Start in **propose-mode** and auto-apply only once you have reviewed its output — and even then never past the same hard walls any session respects: `raw/` stays append-only, `> [!human]` text and `SYSTEM/decisions.md` stay yours alone. Its changes are logged through the digest + commits (not a per-edit `SYSTEM/log.md` line); revert like any commit. It ships as an opt-in add-on: `SYSTEM/optional/gardener/` (isolated git worktree, checkpoint + merge-back, code-enforced guardrails, systemd unit shipped in propose-mode — see its README and `SYSTEM/optional/cloud-core/README.md`); nothing in the core method depends on it.

## Scope note (the method's sweet spot)

This design works **without any vector DB / RAG** because the whole index fits in
a context window — good to roughly a few hundred pages. If a base grows past that,
add search; until then, plain markdown + a hand-maintained `index.md` beats
embeddings. See [[karpathy-method]] for the full rationale and the hallucination-
propagation risk (the reason the lint step is non-negotiable).

## Optional extensions

The core method is just **raw → compile → index → log**. Teams layer on extras as
needed — e.g. auto-generated daily planning notes, calendar capture, a SessionStart
hook that inlines the map + inbox (registered in `.claude/settings.json`; disable
from `/hooks` if you don't want it). These are deliberately
**not required**; add them once the base habit sticks. *"Pick what's useful, ignore
what isn't."*

**Daily-note rollup:** if you adopt daily notes, `SYSTEM/bin/rollup-daily-weeks.sh`
keeps `00 daily/` tidy — past weeks' `00 daily/YYYY-MM-DD.md` notes move into folders
named for their week's Monday (`00 daily/YYYY-MM-DD/`), current-week notes stay
loose. Idempotent; safe to run nightly. Wikilinks resolve by filename, so
moving files breaks nothing.

**Pipelines and working folders** are another optional layer: an area whose work
accumulates self-contained artifacts (a publication pipeline, a data lake) graduates
to a lowercase working folder beside its note — `02 Areas/<slug>.md` +
`02 Areas/<slug>/` (see *Areas* above); the pipeline's skill lives in `Skills/`
like any other skill.

A ready-to-adopt bundle (macOS + Claude Code / Grok) ships in `SYSTEM/optional/automation/` — a
SessionStart loader, a Google Calendar cache + Gmail digest (via the `gws` CLI),
an 8am daily-plan generator, a 6pm lint/recap/git-snapshot job, and the launchd
jobs to schedule them. **Project-level hooks** (SessionStart loader, close-ritual
Stop reminder, porting-candidate nudge) are registered in `.claude/settings.json`
and point at those scripts — trust the folder on first session (`/hooks` to
inspect). Launchd jobs stay opt-in. See `SYSTEM/optional/automation/README.md`.

**Visual diagrams** are another optional layer: `SYSTEM/bin/excalidraw.py` is a
zero-dependency generator that emits native Obsidian-Excalidraw `.excalidraw.md`
files (shapes + bound labels + auto-routing arrows) from a compact Python
node/edge spec — no npm, no browser, no network. Files land in the optional
`excalidraw/` structural folder. See `Skills/FORMAT/Create an Excalidraw Diagram.md`.

**Multi-agent orchestration (CMUX)** is a further optional *runtime* layer, for
anyone running a terminal multiplexer/agent-orchestration tool (e.g.
[CMUX](https://github.com/disler/learning-cmux-with-agents)) alongside this KB.
The model: two interfaces with a clean division of labour — the **vault stays
memory/state** (durable — projects, actions, concepts) and the **orchestration
tool is runtime** (ephemeral — windows/workspaces/panes, spun up and torn down
per task). **State round-trips through the vault, not through the runtime tool**:
whatever gets dispatched, and whatever comes back (decisions, milestones,
follow-up `#action`s), gets written into the relevant `03 Projects/<slug>.md`
note — if it isn't in the vault, it didn't happen. Two granularities of
delegation, each its own runbook: workspace-level (a whole project gets its
own repo context and its own agent — `Skills/DO/Delegate a Project to a CMUX Workspace.md`) and pane-level (one task fans out into concurrent sub-tasks
sharing a context — `Skills/DO/Spawn Subagent Panes in a CMUX Workspace.md`). Both
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

Optionally, give workers a **named identity** instead of a blank agent.
**Agent Roles (one contract, three doors — adopted 2026-08-27):** every role is
one canonical identity contract in `.claude/agents/<role>.md` (a starter set —
`research`, `compile`, `lint`, `project-worker` — maps onto this KB's own
raw→compile→index→lint verbs and its project-delegation model). Top-level
frontmatter carries the **harness-enforced** fields — `name:`, `description:`,
**`tools:`** (least-privilege list per role) and **`model:`** (workers
`haiku`/`sonnet`, advisors `inherit`) — with the org keys (`kind: advisor |
worker | classifier`, `version`, `status`, `updated`, …) under `metadata:`.
Claude Code and Grok Build auto-discover these as native subagents. Three
invocation doors, same contract: **dialogic** — an advisor's DO skill opens by
reading and adopting the canonical role file in the main loop (full
conversation; `tools:` does not bind this path — session permissions and the
contract's own guardrails do); **delegated** — Task-tool subagent in an
isolated context (`tools:`/`model:` harness-enforced; the lean list also
sidesteps the MCP-bloat problem above); **external** — pass the **generated
mirror** `Agents/<role>.md` via your agent CLI's system-prompt flag
(e.g. `--append-system-prompt <vault>/Agents/<role>.md`, absolute
path — a worker's cwd may not be your vault). Description policy by kind:
advisors open "Explicit invocation only" (so they never fire uninvited);
workers/classifiers say "Use when delegating <X>" so orchestration may route
to them. `SYSTEM/bin/build_directory_indexes.py` regenerates the folder's
`index.md` table straight from every mirror's frontmatter.

**Domain-advisor roles** extend the same `Agents/` idea beyond
orchestration: a *standing analyst* over one domain of the KB (finances,
health, a hobby — whatever the vault covers deeply). Each advisor is one role
file built from `Agents/domain-advisor TEMPLATE.md` (scope, data
sources, operating principles, output shape) paired with one on-demand `Skills/`
skill built from `Skills/DO/Run a Domain Review TEMPLATE.md` that loads the role and walks
a review. The role carries the *stance* (what to watch, how to reason about
the domain); the skill carries the *steps*; findings land back in the domain's
concept/project notes per the normal compile flow. Entirely optional — add
one when a domain accumulates enough state that ad-hoc questions keep
re-deriving the same analysis.
