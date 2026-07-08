# {{NAME}}'s Knowledge Base — Project Hub

A **memory-first** knowledge base for {{DOMAIN}}. Durable facts compiled into
`concepts/` (relationships inline via `[[wikilinks]]`), sources in `raw/`, mapped by
`index.md`. Built on the Karpathy "knowledge-base-as-compiler" method.

> ### 📌 Start here
> - **[[AGENTS]]** — how this KB works (the method). **Read first.**
> - **[[index]]** — the map (start point after AGENTS).
> - **[[Actions]]** — the single live to-do dashboard (every open `#action`).

---

## Setup flow (first time)

This KB is **two tools working together**:

- **Claude Code** — the agent that *maintains* the base: it captures, compiles, links, and lints, reading `CLAUDE.md` + `meta/AGENTS.md` every session and doing the bookkeeping for you.
- **Obsidian** — how *you* read and navigate it. The vault is plain markdown (any editor works), but Obsidian is the intended "IDE": it renders `[[wikilinks]]`, gives you a backlinks panel and graph view, and — with one plugin — turns `Actions.md` into a live to-do dashboard.

> Karpathy's framing: *"Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase."*

**Steps:**

1. **Install both tools** — [Claude Code](https://claude.com/claude-code) (the agent) and [Obsidian](https://obsidian.md) (free).
2. **Copy & rename** this `kb-starter/` folder to wherever your KB will live (e.g. `~/my-kb`, `~/work-brain`).
3. **Bootstrap with Claude Code.** `cd` into the folder, run `claude`, and say **`follow setup.md`**. It interviews you (~10 min), fills the templated `{{placeholders}}`, and runs one full capture→compile loop so you see the method work once. *(Prefer to do it by hand? `setup.md` has a manual path.)*
4. **Open it as an Obsidian vault.** Obsidian → *Open folder as vault* → pick your renamed folder. Then enable the **Tasks** community plugin (Settings → Community plugins → Browse → search **"Tasks"** → Install → Enable) — this is what makes `Actions.md` aggregate every `#action` into one live view. Without it, the `tasks` query blocks just render as code.
5. **Start the daily habit** (below): drop notes at the root, and periodically ask Claude to *"file the inbox"* and *"run the knowledge health check."*

Full walkthrough — including the no-agent manual path and what you'll have when it's done — is in [`setup.md`](setup.md).

---

## Capture → inbox

The **vault root is the inbox**. Drop new notes/files anywhere at the root; they
get triaged into `raw/` and compiled into `concepts/`. The only permanent root
residents are `README.md`, `index.md`, `Actions.md`, and `CLAUDE.md` — **if you
see anything else loose at the root, it's waiting to be filed** (ask Claude to
"file the inbox" or "run the knowledge health check"). Full method in
[AGENTS.md](meta/AGENTS.md).

## Project memory

| Doc | Use it for |
| :-- | :-- |
| [AGENTS.md](meta/AGENTS.md) · [index.md](index.md) | The knowledge base, structured with the Karpathy compiler method. Read AGENTS.md (how it works) then index.md (the map). Concepts in `concepts/`, sources in `raw/`. |
| [Actions.md](Actions.md) | The single live to-do view — every open `#action` across the KB (needs the Obsidian **Tasks** plugin). |

---

_Last updated: {{DATE}}._

## License

The CNTXT1 starter kit (templates, schema, scripts) is [MIT-licensed](LICENSE) —
free to use, copy, and adapt. Your own knowledge base built from it is yours;
delete this section when you personalize the repo.
