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
- **Method:** [[karpathy-method]] · [[open-knowledge-format]] · [[AGENTS]]
- **Indexes:** [[contacts]] → `CONTENT/People/` · [[skills]] → `CONTENT/Skills/`
- _(add your concept groups here: role, product, ops, … one line each)_
- **Live to-dos:** [[Actions]] · **History:** [[log]]

## Initiatives (goal-directed workstreams — one note each in `CONTENT/Initiatives/`)
Bigger outcomes spanning multiple actions over time. Built from [`Initiative TEMPLATE.md`](CONTENT/Initiatives/Initiative%20TEMPLATE.md), run via [[Run an initiative]]; `CONTENT/Initiatives/` is a **structural folder, not an inbox item**. Actions stay inline in each note and aggregate to [[Actions]].

**Live:** _(none yet)_

**Done:** _(closed initiatives stay listed here as records)_

## Concepts (compiled, queryable truth)
- **[[karpathy-method]]** — the architecture this KB is built on: an LLM-maintained "wiki" (raw→compile→index→lint, no RAG at personal scale). Why it works, the scale sweet spot, and the hallucination-propagation risk. The operating rules live in [[AGENTS]].
- **[[open-knowledge-format]]** — Google's OKF v0.1: the open interchange standard for Karpathy-style LLM wikis, how a CNTXT1 vault maps to it (a superset), and how to adopt it at the boundaries (bundle ingest/export) without refactoring internals.
- **[[contacts]]** — the **People index**: usage-context map + grouped tables over the [`CONTENT/People/`](People) folder. Per-person detail lives in each person's own note; this is the *who-for-what* map.
- **[[skills]]** — the **skill index**: grouped tables over the [`CONTENT/Skills/`](CONTENT/Skills) folder. Each recurring "job to be done" is one runbook note filed by type (`DO`/`CHECK`/`FORMAT`/`RULE`); this is the *how-do-I-X* map.

_New concepts get added here, one line each, as you compile them._

## People (one note per person — `CONTENT/People/`)
A note per named person under [`CONTENT/People/`](People) — the **single source of truth** for per-person detail. Built from [`People TEMPLATE.md`](CONTENT/People/People%20TEMPLATE.md). Filed as `Full Name.md`, wikilinked `[[Full Name]]` (nicknames resolve via `aliases:` frontmatter). `CONTENT/People/` is a **structural folder, not an inbox item**.

_Add person notes here as you build the network._

## Skills (one agent-invocable runbook per recurring task — `CONTENT/Skills/`)
Agent-executable runbooks for recurring "jobs to be done", filed as [`CONTENT/Skills/<TYPE>/<Imperative Title>.md`](CONTENT/Skills) where `TYPE` is one of `DO` (performs a recurring task), `CHECK` (verifies/audits something), `FORMAT` (produces/structures an artifact), or `RULE` (a standing convention/policy) — the **single source of truth for the *steps*** of a repeatable task. Built from [`Skill TEMPLATE.md`](CONTENT/Skills/Skill%20TEMPLATE.md). `CONTENT/Skills/` is a **structural folder, not an inbox item**.

Twelve starter skills ship with the kit (KB-meta): [[Add a person to the KB]] · [[Capture a meeting or conversation into the KB]] · [[Run an initiative]] · [[Run the KB health check]] · [[Optimize the knowledge base]] · and more — see [[skills]].

## Raw (source of truth — append-only)
- `CONTENT/raw/2026-01-01-example-capture.md` — **example** showing the dated-capture format (provenance header, a fact, a `[[wikilink]]`, an `#action`). Delete once you have real captures.

## Log
- `SYSTEM/log.md` — chronological record of knowledge updates.

## Related
- `README.md` — operational hub.
- `SYSTEM/Journal.md` — wins & milestones brag doc.

---

_This index is a **pure map** — keep change history in `SYSTEM/log.md`, never here.
If the Quick map ever outgrows the injection budget, tighten it; don't let it spill._

_Last updated: {{DATE}} (initial scaffold)._
