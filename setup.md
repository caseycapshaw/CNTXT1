# setup.md — Bootstrap your knowledge base

This folder is a **starter kit** for a personal, LLM-maintained knowledge base
(KB) built on the Karpathy "knowledge-base-as-compiler" method. It ships with the
schema and conventions but **no personal content** — you fill that in.

This file does double duty: it's a readable walkthrough for *you*, and it's a
script for *Claude*. The fastest path is to let Claude run it.

---

## ▶ How to set up (the easy way)

1. Copy this whole `kb-starter/` folder to wherever you want your KB to live, and
   rename it (e.g. `~/my-kb`, `~/work-brain`).
2. Open it in **Claude Code** (`cd` into the folder, run `claude`).
3. Say: **`follow setup.md`**

Claude will interview you, fill in the templated files, run one full
capture→compile loop so you see the method work once, walk you through setting
up **Obsidian** (vault + Tasks plugin), and offer each **optional automation**
individually — you choose what runs on your machine. Takes ~15 minutes.

> Prefer to do it by hand? Skip to **[Manual setup](#manual-setup)** at the bottom.

---

## 📋 Instructions to Claude (the agent reads from here)

You are bootstrapping a brand-new knowledge base for the user in the current
folder. Work **conversationally and one step at a time** — this is also their
first lesson in how the KB works, so narrate lightly as you go. Do not dump all
questions at once.

**First, read these so you operate the way this KB expects:**
- `meta/AGENTS.md` — the schema (compiler analogy, data flow, conventions, health checks).
- `CLAUDE.md` — the project instructions (note the `{{placeholders}}` you'll fill).
- `concepts/karpathy-method.md` — why this design works (so you can explain it).

### Phase 1 — Interview

Ask the user, a few at a time (skip anything that doesn't apply):

1. **Name** — how the KB should address them.
2. **Role / title** and **org / team**.
3. **Who they report to / key people** (3–5 names + one-line roles) — these become their first `People/` notes and seed `concepts/contacts.md`.
4. **The domain this KB is *about*** — the role, project, system, or transition they're building memory around. Get them to say it in a sentence.
5. **What they're ramping on right now** — current priorities, the things they keep having to re-learn. This seeds the first concepts and actions.

Keep it light. You're collecting enough to personalize the scaffolding, not writing a biography.

### Phase 2 — Fill the templates

In `CLAUDE.md`, replace the placeholders from the interview:
- `{{NAME}}`, `{{ROLE}}`, `{{ORG}}`.
- `{{REPORTS_TO}}` → e.g. `, reporting to <Name>` — or delete it entirely if not relevant.
- `{{CONTEXT_SHORTCUTS}}` → leave just the method shortcut for now; add concept shortcuts as they get created.

Then update the header lines of `index.md` and `README.md` to name the user and
their domain (replace the `{{...}}` placeholders there too).

Two placeholders live outside `CLAUDE.md`:
- `owner: {{NAME}}` in each `Jobs/*.md` runbook → the user's name.
- `{{PERSONAL_IDENTIFIERS}}` in `Jobs/Sync an improvement to CNTXT1.md` → a
  `|`-separated grep pattern of the user's personal identifiers (full name,
  family members, employer, email domain — from the interview). **State the
  privacy rule out loud while doing this:** this vault is private; personal
  content never leaves it; only re-templated framework improvements flow out,
  through that runbook's grep gate (`meta/AGENTS.md` § Privacy & content
  separation).

### Phase 3 — Run one real loop (the important part)

Don't leave them with empty folders. Do one full pass so the method is demonstrated:

1. **Capture.** Pick the richest thing from the interview (often "what they're ramping on" or the people list). Brain-dump it with the user into a dated raw note: `raw/YYYY-MM-DD-<topic>.md` (use today's date), with a one-line provenance header (e.g. `_Source: setup interview, <date>._`).
2. **Compile.** Extract the durable facts into a concept article in `concepts/` (e.g. `concepts/the-role.md` or `concepts/<system>.md`). Use `[[wikilinks]]`. If a real to-do surfaced, write it inline as `- [ ] … #action`.
3. **Seed People/.** For each key person from Phase 1, create `People/<Full Name>.md` from `People/People TEMPLATE.md` and add a row to `concepts/contacts.md`. Even stubs (name + role + one-liner) are better than nothing — they can flesh them out later.
4. **Index.** Add the new concept (and the raw note) to `index.md` with a one-line summary. Confirm the People section reflects the new person notes.
5. **Log.** Append one line to `meta/log.md` (start it with today's date).

Show the user the before/after so they connect the steps to the files.

### Phase 4 — Set up Obsidian (the reading layer)

The KB works from any editor, but Obsidian is the intended "IDE" — it renders
`[[wikilinks]]`, backlinks, the graph, and (with one plugin) the live Actions
dashboard. You can't click for the user, so narrate each step and **verify by
asking what they see**:

1. **Install check.** Ask if Obsidian is installed. If not: [obsidian.md](https://obsidian.md)
   (free), or `brew install --cask obsidian` on macOS with Homebrew. Wait for them.
2. **Open the vault.** Obsidian → *Open folder as vault* → pick this KB folder.
   If prompted about trust, they authored this vault — trusting it is fine.
3. **Enable the Tasks plugin.** Settings → *Community plugins* → *Turn on
   community plugins* → Browse → search **"Tasks"** (by Clare Macrae) →
   Install → Enable.
4. **Verify.** Have them open `Actions.md`: the query blocks should render as a
   (possibly empty) live task list, **not** as fenced code. If they still see
   code fences, the plugin isn't enabled — revisit step 3.
5. Optional niceties to mention, not push: pin `index.md` and `Actions.md` as
   tabs; try graph view once a few concepts exist.

### Phase 5 — Optional automation (ask per option — never install unprompted)

The `meta/optional/automation/` bundle (macOS + Claude Code) makes the KB feel
alive day to day. **Present each option with one line on what it does and what
it requires, and ask yes/no per option** — the user chooses; skipping all of
them is a fine answer (the core loop needs none of this). Full install detail:
`meta/optional/automation/README.md`.

| # | Option | What it does | Requires |
| :-- | :-- | :-- | :-- |
| 1 | **Session loader** (SessionStart hook) | injects the map + inbox + today's context into every Claude Code session in the vault | nothing external |
| 2 | **Google Calendar context** | today's events cached for the session loader + daily plan | `gws` CLI authenticated (see below) |
| 3 | **8am daily plan** (launchd) | writes `daily/YYYY-MM-DD.md`: schedule + live `#action` query + priorities | headless `claude -p` working; calendar/Gmail optional |
| 4 | **Gmail digest in the daily plan** | a grouped "From the inbox" section from the last 2 days of email (read-only) | `gws`; **privacy note: mail headers/snippets land in daily notes** — say this out loud |
| 5 | **6pm summary + git snapshot** (launchd) | evening lint, "what we did today" recap, then a nightly commit (+push if a remote exists) | git repo; remote optional |
| 6 | **Claude Desktop MCP server** | lets the Claude Desktop chat app read the vault (index/read/search/actions) and capture new facts to `raw/` — the "prioritize the KB" rule rides into every chat as server instructions | Claude Desktop + `python3` (stdlib only) |

For whichever they accept:

1. **`gws` first if 2 or 4 chosen:** `brew install googleworkspace-cli` — warn
   that the plain `gws` Homebrew formula is an **unrelated** git tool with a
   conflicting binary name. Then `gws auth setup` (needs `gcloud`:
   `brew install --cask google-cloud-sdk`) and `gws auth login` — the user does
   the interactive OAuth steps in the browser; verify with `gws auth status`.
2. **Copy + configure the accepted scripts** per the README: into
   `~/.claude/hooks/`, set the CONFIG block (`VAULT`, `NAME`) in each.
3. **Register the SessionStart hook** (option 1) in `~/.claude/settings.json`.
4. **Install the launchd plists** (options 3/5): copy to `~/Library/LaunchAgents/`,
   personalize the `Label` and paths, `launchctl load` them.
5. **Register the MCP server** (option 6): personalize the `INSTRUCTIONS`
   block in `meta/bin/kb-mcp-server.py` (`{{NAME}}`, `{{SCOPE}}` — one phrase
   for what the KB covers), then add it to
   `~/Library/Application Support/Claude/claude_desktop_config.json` under
   `mcpServers` (the config snippet is in the script's docstring). Restart
   Claude Desktop and verify the `cntxt-kb` tools appear.
6. **Test immediately** — don't wait for the schedule: `daily-plan.sh --force`
   and `daily-summary.sh` by hand; show the user the generated note.
7. **Record what was enabled** in `meta/log.md` (one line listing the options).

Non-macOS: the scripts and hook port; launchd doesn't — offer cron/systemd
equivalents but don't set them up unless asked.

### Phase 6 — Clean up & hand off

1. Offer to delete the **example files** now that real ones exist:
   - `raw/2026-01-01-example-capture.md` (clearly-labeled example).
   - Keep `concepts/karpathy-method.md` — it explains the method; suggest they keep it.
2. Remove any remaining `{{placeholders}}` and the placeholder note at the top of `CLAUDE.md`.
3. Run the **health checks** from `meta/AGENTS.md` once and report a clean bill (no broken wikilinks, index lists every file, inbox clean).
4. Tell them the everyday loop in one breath: *drop notes at the root → ask me to "file the inbox" → I triage to `raw/`, compile to `concepts/`, update `index.md`, log it.* And that they can ask you to **"run the knowledge health check"** anytime.

That's it — stop here and let them start using it.

---

## What you'll have when it's done

```
your-kb/
├── CLAUDE.md         ← personalized; Claude reads it every session
├── index.md          ← the map, seeded with your first concept
├── Actions.md        ← live #action dashboard
├── README.md         ← your hub
├── meta/
│   ├── AGENTS.md     ← the schema (how it works)
│   ├── log.md        ← changelog, one line per update
│   ├── Journal.md    ← wins & milestones brag doc
│   ├── link-map.md   ← generated [[wikilink]] → path index
│   └── bin/          ← lint.sh + build-link-map.sh + kb-mcp-server.py (KB tooling)
│   └── optional/     ← opt-in automation bundle (offered during setup, Phase 5)
├── raw/              ← your first dated capture
├── concepts/         ← karpathy-method + contacts + jobs + your first concept (all carry frontmatter)
├── Initiatives/      ← one note per goal-directed workstream (+ its template)
├── People/           ← one note per person (single source of truth for per-person detail)
└── Jobs/             ← agent-executable runbooks for recurring tasks (7 KB-meta ones ship)
```

## The daily habit

- **Capture anything** by dropping a note at the root (the inbox) — or just talking to Claude.
- Periodically say **"file the inbox"** → raw → concept → index → log.
- Ask questions; good answers get **filed back** as new concepts, so the base compounds.
- Run **"the knowledge health check"** every week or two.

Read `concepts/karpathy-method.md` once — it explains *why* this beats throwing
files at a chatbot, and the one real risk (a wrong fact can propagate, which is
why the health check matters).

## Optional: automation (macOS + Claude Code)

Setup **Phase 5** offers these one by one — nothing installs without an explicit
yes. Once the basic habit sticks, `meta/optional/automation/` adds the machinery that makes
the base feel alive: a **SessionStart hook** that inlines your map + inbox + today's
calendar into every Claude Code session, an **8am daily-plan generator** that writes
a `daily/YYYY-MM-DD.md` note (schedule + a "From the inbox" Gmail digest + live
`#action` query + priorities — calendar and Gmail via the [`gws`](https://github.com/googleworkspace/cli)
CLI, read-only), and a **6pm end-of-day job** that runs the KB health check, appends
a "What we did today" recap, and commits a nightly git snapshot — so the lint and
the backup run automatically every evening. There's also a **Claude Desktop MCP
server** (`meta/bin/kb-mcp-server.py`, stdlib-only python) that gives the chat
app read access to the vault plus capture-to-`raw/` — registration snippet in
the script's docstring.
Not required to start — see `meta/optional/automation/README.md` when you're ready.

---

## Manual setup

If you'd rather not use the agent:

1. Copy & rename the folder; open it in your editor.
2. In `CLAUDE.md`, `index.md`, and `README.md`, replace every `{{placeholder}}` with your details (delete `{{REPORTS_TO}}` / `{{CONTEXT_SHORTCUTS}}` if unused).
3. Delete `raw/2026-01-01-example-capture.md`. Keep `concepts/karpathy-method.md`.
4. Write your first real capture in `raw/YYYY-MM-DD-topic.md`, compile a concept into `concepts/`, add both to `index.md`, and log a line in `meta/log.md`.
5. (Optional, for the `Actions.md` dashboard) install the Obsidian **Tasks** plugin and point Obsidian at the folder.
6. (Optional) adopt any of the automation pieces by hand — `meta/optional/automation/README.md` is the full walkthrough.

The conventions you're following are all in `meta/AGENTS.md`.
