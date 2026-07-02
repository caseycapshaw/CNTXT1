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

Claude will interview you, fill in the templated files, and run one full
capture→compile loop with you so you see the method work once. Takes ~10 minutes.

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

### Phase 3 — Run one real loop (the important part)

Don't leave them with empty folders. Do one full pass so the method is demonstrated:

1. **Capture.** Pick the richest thing from the interview (often "what they're ramping on" or the people list). Brain-dump it with the user into a dated raw note: `raw/YYYY-MM-DD-<topic>.md` (use today's date), with a one-line provenance header (e.g. `_Source: setup interview, <date>._`).
2. **Compile.** Extract the durable facts into a concept article in `concepts/` (e.g. `concepts/the-role.md` or `concepts/<system>.md`). Use `[[wikilinks]]`. If a real to-do surfaced, write it inline as `- [ ] … #action`.
3. **Seed People/.** For each key person from Phase 1, create `People/<Full Name>.md` from `People/People TEMPLATE.md` and add a row to `concepts/contacts.md`. Even stubs (name + role + one-liner) are better than nothing — they can flesh them out later.
4. **Index.** Add the new concept (and the raw note) to `index.md` with a one-line summary. Confirm the People section reflects the new person notes.
5. **Log.** Append one line to `meta/log.md` (start it with today's date).

Show the user the before/after so they connect the steps to the files.

### Phase 4 — Clean up & hand off

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
│   └── bin/          ← lint.sh + build-link-map.sh (KB tooling)
├── raw/              ← your first dated capture
├── concepts/         ← karpathy-method + contacts + jobs + your first concept (all carry frontmatter)
├── People/           ← one note per person (single source of truth for per-person detail)
└── Jobs/             ← agent-executable runbooks for recurring tasks (5 KB-meta ones ship)
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

Once the basic habit sticks, `optional/automation/` adds the machinery that makes
the base feel alive: a **SessionStart hook** that inlines your map + inbox + today's
calendar into every Claude Code session, an **8am daily-plan generator** that writes
a `daily/YYYY-MM-DD.md` note (schedule + a "From the inbox" Gmail digest + live
`#action` query + priorities — calendar and Gmail via the [`gws`](https://github.com/googleworkspace/cli)
CLI, read-only), and a **6pm end-of-day job** that runs the KB health check, appends
a "What we did today" recap, and commits a nightly git snapshot — so the lint and
the backup run automatically every evening.
Not required to start — see `optional/automation/README.md` when you're ready.

---

## Manual setup

If you'd rather not use the agent:

1. Copy & rename the folder; open it in your editor.
2. In `CLAUDE.md`, `index.md`, and `README.md`, replace every `{{placeholder}}` with your details (delete `{{REPORTS_TO}}` / `{{CONTEXT_SHORTCUTS}}` if unused).
3. Delete `raw/2026-01-01-example-capture.md`. Keep `concepts/karpathy-method.md`.
4. Write your first real capture in `raw/YYYY-MM-DD-topic.md`, compile a concept into `concepts/`, add both to `index.md`, and log a line in `meta/log.md`.
5. (Optional, for the `Actions.md` dashboard) install the Obsidian **Tasks** plugin and point Obsidian at the folder.

The conventions you're following are all in `meta/AGENTS.md`.
