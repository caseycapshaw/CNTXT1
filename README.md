# {{NAME}}'s Knowledge Base — Project Hub

A **memory-first** knowledge base for {{DOMAIN}}. Durable facts compiled into
`Knowledge/Concepts/` (relationships inline via `[[wikilinks]]`), sources in `Knowledge/raw/`, mapped by
`index.md`. Built on the Karpathy "knowledge-base-as-compiler" method.

> ### 📌 Start here
> - **[[SCHEMA]]** — how this KB works (the method). **Read first.**
> - **[[index]]** — the map (start point after AGENTS).
> - **[[Actions]]** — the single live to-do dashboard (every open `#action`).

---

## Setup flow (first time)

This KB is **two tools working together**:

- **Claude Code** — the agent that *maintains* the base: it captures, compiles, links, and lints, reading `AGENTS.md` (via `CLAUDE.md`) + `SYSTEM/SCHEMA.md` every session and doing the bookkeeping for you.
- **Obsidian** — how *you* read and navigate it. The vault is plain markdown (any editor works), but Obsidian is the intended "IDE": it renders `[[wikilinks]]`, gives you a backlinks panel and graph view, and — with one plugin — turns `Actions.md` into a live to-do dashboard.

> Karpathy's framing: *"Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase."*

**Steps:**

1. **Install both tools** — [Claude Code](https://claude.com/claude-code) (the agent) and [Obsidian](https://obsidian.md) (free).
2. **Get the repo — two modes:**
   - **Clone mode (simplest):** `git clone` this design repo and use it directly. Your
     personal content lives in `Knowledge/` (plus `daily/` and `attachments/`), which
     git **ignores by default** — nothing personal can be committed by accident, and
     `git pull` brings framework updates any time without conflicts.
   - **Instance-repo mode (own history):** copy the folder into your own private repo
     and add this repo as a **fetch-only** `upstream` (push URL disabled) — pull
     framework updates inward with the shipped skill `Pull Framework Updates from
     CNTXT1`. This is how the maintainer's own instance runs.
3. **Bootstrap with Claude Code.** `cd` into the folder, run `claude`, and say **`follow setup.md`**. It interviews you (~10 min), fills the templated `{{placeholders}}`, and runs one full capture→compile loop so you see the method work once. *(Prefer to do it by hand? `setup.md` has a manual path.)*
4. **Open it as an Obsidian vault.** Obsidian → *Open folder as vault* → pick your renamed folder. Then enable the **Tasks** community plugin (Settings → Community plugins → Browse → search **"Tasks"** → Install → Enable) — this is what makes `Actions.md` aggregate every `#action` into one live view. Without it, the `tasks` query blocks just render as code.
5. **Start the daily habit** (below): drop notes at the root, and periodically ask Claude to *"file the inbox"* and *"run the knowledge health check."*

Full walkthrough — including the no-agent manual path and what you'll have when it's done — is in [`setup.md`](setup.md).

---

## Capture → inbox

The **vault root is the inbox**. Drop new notes/files anywhere at the root; they
get triaged into `Knowledge/raw/` and compiled into `Knowledge/Concepts/`. The only permanent root
residents are `README.md`, `index.md`, `Actions.md`, `CLAUDE.md`, and `AGENTS.md` — **if you
see anything else loose at the root, it's waiting to be filed** (ask Claude to
"file the inbox" or "run the knowledge health check"). Full method in
[AGENTS.md](SYSTEM/SCHEMA.md).

## Project memory

| Doc | Use it for |
| :-- | :-- |
| [AGENTS.md](SYSTEM/SCHEMA.md) · [index.md](index.md) | The knowledge base, structured with the Karpathy compiler method. Read AGENTS.md (how it works) then index.md (the map). Concepts in `Knowledge/Concepts/`, sources in `Knowledge/raw/`. |
| [Actions.md](Actions.md) | The single live to-do view — every open `#action` across the KB (needs the Obsidian **Tasks** plugin). |

---

## Staying in sync with the kit (your instance is *not* a fork)

Your KB is a **private instance generated from this kit**, with its own
independent git history — deliberately not a GitHub fork. Forks of a public
repo can't be made private, and shared history would put your personal
content one mistyped `git push` (or one PR from the wrong branch) away from
being published. With independent histories, **no single command can leak**.

The two sync directions have opposite risk profiles, so they use opposite
tooling:

**Kit → instance (safe — automate it).** Everything in this repo is already
public, so pulling it into your private vault can't leak anything. One-time
setup, from your vault root:

```
git remote add upstream https://github.com/caseycapshaw/CNTXT1.git
git remote set-url --push upstream DISABLED   # git physically cannot push
```

Then adopt any kit improvement with `git fetch upstream` +
`git cherry-pick <sha>`. Files that stay byte-identical across instances
(`SYSTEM/SCHEMA.md`, `SYSTEM/bin/*`, most `Knowledge/Skills/`, templates) apply cleanly;
files your instance has populated (`index.md`, `AGENTS.md`, the concept
indexes) occasionally need a small manual merge. Step-by-step skill:
[`Knowledge/Skills/DO/Pull Framework Updates from CNTXT1.md`](Knowledge/Skills/DO/Pull Framework Updates from CNTXT1.md).

**Instance → kit (dangerous — stays manual).** Personal content never leaves
your vault, so this direction is a deliberate, hand-operated path:
re-template to `{{placeholders}}`, run the identifier grep gate, and go
through this repo's CI (privacy gate + review). Skill:
[`Knowledge/Skills/DO/Sync an Improvement to CNTXT1.md`](Knowledge/Skills/DO/Sync an Improvement to CNTXT1.md).

**Rule of thumb: author upstream-first.** When you're about to build
something generic — a lint check, a runbook, a template improvement — build
it *here* (PRs welcome, see Contributing) and pull it into your vault via
the safe direction. That keeps every framework enhancement maintained in
exactly one place; the manual outward sync is only for improvements you
discover after they're already implemented privately.

---

_Last updated: {{DATE}}._

## License

The CNTXT1 starter kit (templates, schema, scripts) is [MIT-licensed](LICENSE) —
free to use, copy, and adapt. Your own knowledge base built from it is yours;
delete this section when you personalize the repo.

## Contributing

Generic improvements to the framework are welcome — see
[.github/CONTRIBUTING.md](.github/CONTRIBUTING.md). One rule dominates: this
repo ships a framework, never personal content.
