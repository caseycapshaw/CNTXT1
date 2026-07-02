# Index — {{NAME}}'s knowledge base

> ### 📌 Start here
> - **[[AGENTS]]** — how this KB works (the method). **Read first.**
> - **[[Actions]]** — the single live to-do dashboard (every open `#action`).

The map. Find what you need without searching everything. Built on the Karpathy
compiler method — see **[[AGENTS]]**.

## Quick map (skeleton — full detail below)
A compact index so the whole structure is graspable at a glance — and so it fits the
session-start injection budget (the optional SessionStart hook inlines `head -c 8000`
of this file; keep the skeleton inside that). Group your concepts here as the base
grows; rich descriptions follow in the sections below.

- **Initiatives (live):** _(none yet — goal-directed workstreams land here)_
- **Method:** [[karpathy-method]] · [[AGENTS]]
- **Indexes:** [[contacts]] → `People/` · [[jobs]] → `Jobs/`
- _(add your concept groups here: role, product, ops, … one line each)_
- **Live to-dos:** [[Actions]] · **History:** [[log]]

## Initiatives (goal-directed workstreams — one note each in `Initiatives/`)
Bigger outcomes spanning multiple actions over time. Built from [`Initiative TEMPLATE.md`](Initiatives/Initiative%20TEMPLATE.md), run via [[Run an initiative]]; `Initiatives/` is a **structural folder, not an inbox item**. Actions stay inline in each note and aggregate to [[Actions]].

**Live:** _(none yet)_

**Done:** _(closed initiatives stay listed here as records)_

## Concepts (compiled, queryable truth)
- **[[karpathy-method]]** — the architecture this KB is built on: an LLM-maintained "wiki" (raw→compile→index→lint, no RAG at personal scale). Why it works, the scale sweet spot, and the hallucination-propagation risk. The operating rules live in [[AGENTS]].
- **[[contacts]]** — the **People index**: usage-context map + grouped tables over the [`People/`](People) folder. Per-person detail lives in each person's own note; this is the *who-for-what* map.
- **[[jobs]]** — the **runbook index**: grouped tables over the [`Jobs/`](Jobs) folder. Each recurring "job to be done" is an agent-executable runbook; this is the *how-do-I-X* map.

_New concepts get added here, one line each, as you compile them._

## People (one note per person — `People/`)
A note per named person under [`People/`](People) — the **single source of truth** for per-person detail. Built from [`People TEMPLATE.md`](People/People%20TEMPLATE.md). Filed as `Full Name.md`, wikilinked `[[Full Name]]` (nicknames resolve via `aliases:` frontmatter). `People/` is a **structural folder, not an inbox item**.

_Add person notes here as you build the network._

## Jobs (one runbook per recurring task — `Jobs/`)
Agent-executable runbooks for recurring "jobs to be done" under [`Jobs/`](Jobs) — the **single source of truth for the *steps*** of a repeatable task. Built from [`Jobs TEMPLATE.md`](Jobs/Jobs%20TEMPLATE.md). `Jobs/` is a **structural folder, not an inbox item**.

Five starter runbooks ship with the kit (KB-meta): [[Add a person to the KB]] · [[Capture a meeting or conversation into the KB]] · [[Run an initiative]] · [[Run the KB health check]] · [[Optimize the knowledge base]].

## Raw (source of truth — append-only)
- `raw/2026-01-01-example-capture.md` — **example** showing the dated-capture format (provenance header, a fact, a `[[wikilink]]`, an `#action`). Delete once you have real captures.

## Log
- `meta/log.md` — chronological record of knowledge updates.

## Related
- `README.md` — operational hub.
- `meta/Journal.md` — wins & milestones brag doc.

---

_This index is a **pure map** — keep change history in `meta/log.md`, never here.
If the Quick map ever outgrows the injection budget, tighten it; don't let it spill._

_Last updated: {{DATE}} (initial scaffold)._
