# Index — {{NAME}}'s knowledge base

> ### 📌 Start here
> - **[[SCHEMA]]** — how this KB works (the method). **Read first.**
> - **[[Actions]]** — the single live to-do dashboard (every open `#action`).

The map. Find what you need without searching everything. Built on the Karpathy
compiler method — see **[[SCHEMA]]**.

## Quick map (skeleton — full detail below)
A compact index so the whole structure is graspable at a glance — and so it fits the
session-start injection budget (the boot bundle / SessionStart hook inlines everything
up to the next H2; keep it inside 8000 bytes). One-liners are stable `description:`
essence, not live status — that lives in each note + the generated Projects section below.

- **Projects (live):** _(none yet — finite, goal-directed workstreams land here)_
- **Areas:** _(none yet — ongoing responsibilities land here)_
- **Horizons:** [[goals]] (H3) · [[vision]] (H4) · [[purpose-principles]] (H5)
- **Method:** [[karpathy-method]] · [[gtd]] · [[open-knowledge-format]] · [[SCHEMA]]
- **Thinking:** [[first-principles-thinking]] (DARE; `/dare`)
- **Indexes:** [[contacts]] → `04 People/` · [[skills]] → `Skills/`
- _(add your concept groups here: role, product, ops, … one line each)_
- **Live to-dos:** [[Actions]] · **History:** [[log]] · [[decisions]]

## Horizons (H3–H5 — `01 Horizons/`)
Orientation above the areas: [[goals]] (1–2 year outcomes, one note each in `01 Horizons/Goals/`, built from [`Goal TEMPLATE.md`](01%20Horizons/Goals/Goal%20TEMPLATE.md)) · [[vision]] (3–5 years) · [[purpose-principles]] (the why). Chained to areas and projects by frontmatter up-links only — the downward views are generated. Method: [[gtd]].

## Projects (goal-directed workstreams — one note each in `03 Projects/`)
Finite outcomes with a genuine endpoint (the endpoint test), spanning multiple actions over time. Built from [`Project TEMPLATE.md`](03%20Projects/Project%20TEMPLATE.md), run via [[Run a Project]]; `03 Projects/` is a **structural folder, not an inbox item**. Actions stay inline in each note and aggregate to [[Actions]].

<!-- projects:auto:start -->
_Generated 2026-09-28 by `SYSTEM/bin/build_index_projects.py` from each note's frontmatter + first paragraph of Now & next — do not hand-edit between the markers. Live/done ordered by `updated:`._

**Pending** (opened but not yet actively worked — waiting on a trigger):
- _none_

**Live:**
- _none_

**Done** (archived in `03 Projects/archive/`):
- _none_
<!-- projects:auto:end -->

## Areas (ongoing responsibilities — one note each in `02 Areas/`)
Standing responsibilities maintained to a standard, never "done" — each carries a `## Standard` and a review cadence. Built from [`Area TEMPLATE.md`](02%20Areas/Area%20TEMPLATE.md); physical things live in `02 Areas/Assets/`.

<!-- areas:auto:start -->
_Generated 2026-09-28 by `SYSTEM/bin/build_index_lists.py` from each note's `description:` frontmatter — do not hand-edit between the markers. To change an entry, edit that area note's `description:` and regenerate (SYSTEM/bin/regen-all.sh)._

<!-- areas:auto:end -->

## Concepts (compiled, queryable truth)
<!-- concepts:auto:start -->
_Generated 2026-09-28 by `SYSTEM/bin/build_index_lists.py` from each note's `description:` frontmatter — do not hand-edit between the markers. To change an entry, edit that concept note's `description:` and regenerate (SYSTEM/bin/regen-all.sh)._

- **[[contacts]]** — The People index — the who-for-what map and grouped tables over the 04 People/ folder.
- **[[first-principles-thinking]]** — First-principles thinking and the DARE framework (Decompose, Audit, Recombine, Experiment) — reasoning from essentials instead of inherited assumptions, with AIM-structured prompts that force an AI off the conventional-wisdom average.
- **[[gtd]]** — David Allen's Getting Things Done — the five-step workflow, the six Horizons of Focus, and the project-vs-area distinction built into this KB's 03 Projects / 02 Areas / 01 Horizons stack.
- **[[karpathy-method]]** — The LLM-maintained wiki architecture this KB is built on — raw→compile→index→lint, replacing RAG at personal scale.
- **[[open-knowledge-format]]** — Google's OKF v0.1 — the open interchange standard for Karpathy-style LLM wikis, how a CNTXT1 vault maps to it, and how to adopt it at the boundaries.
- **[[skills]]** — The skills index — the how-do-I-X map and grouped tables over the Skills/ folder.
<!-- concepts:auto:end -->

_New concepts appear here automatically from their `description:` frontmatter — edit the note, then regenerate._

## People (one note per person or vendor — `04 People/`)
A note per named person or business under [`04 People/`](04%20People) — the **single source of truth** for per-person detail. Built from [`People TEMPLATE.md`](04%20People/People%20TEMPLATE.md). Filed as `Full Name.md`, wikilinked `[[Full Name]]` (nicknames resolve via `aliases:` frontmatter). Indexed by [[contacts]]. `04 People/` is a **structural folder, not an inbox item**.

_Add person notes here as you build the network._

## Skills (one agent-invocable runbook per recurring task — `Skills/`)
Agent-executable runbooks for recurring "jobs to be done": canonical at `.claude/skills/<slug>/SKILL.md` (the **single source of truth for the *steps***, auto-discovered by Claude Code and Grok Build), mirrored by `SYSTEM/bin/build_claude_mirrors.py` into [`Skills/<TYPE>/`](Skills) (`DO` = performs a task · `CHECK` = verifies/audits · `FORMAT` = produces an artifact · `RULE` = standing convention) for Obsidian reading and wikilinks. Built from [`Skill TEMPLATE.md`](Skills/Skill%20TEMPLATE.md). `Skills/` is a **structural folder, not an inbox item**.

Starter skills ship with the kit (KB-meta): [[Run a Project]] · [[Add a person to the KB]] · [[Capture a meeting or conversation into the KB]] · [[Run the KB health check]] · [[Optimize the knowledge base]] · and more — see [[skills]].

## Raw (source of truth — append-only)
- [[raw/2026-01-01-example-capture]] — **example** showing the dated-capture format (provenance header, a fact, a `[[wikilink]]`, an `#action`). Delete once you have real captures.

## Log
- `SYSTEM/log.md` — chronological record of knowledge updates.

## Related
- `README.md` — operational hub.
- `SYSTEM/Journal.md` — wins & milestones brag doc.

---

_This index is a **pure map** — keep change history in `SYSTEM/log.md`, never here.
If the Quick map ever outgrows the injection budget, tighten it; don't let it spill._
