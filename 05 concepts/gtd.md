---
type: concept
description: David Allen's Getting Things Done — the five-step workflow, the six Horizons of Focus, and the project-vs-area distinction built into this KB's 03 Projects / 02 Areas / 01 Horizons stack.
updated: 2026-09-28
status: current
tags: [concept, method]
---

# Concept — GTD (Getting Things Done)

David Allen's methodology for stress-free productivity. This KB adopts its
structure because a single "initiative" bucket **conflates two GTD levels** —
finite projects and ongoing areas — and the two need different mechanics (one
ends, one is maintained). The kit therefore builds the H1–H5 stack into the
layout: `03 Projects/` · `02 Areas/` · `01 Horizons/`.

## The five-step workflow

**Capture → Clarify → Organize → Reflect → Engage.** Clarify is the decision
point: is it actionable? If yes — what's the very next action, and does it need
a project? If no — trash, reference, or defer (Someday/Maybe). (The 2001
edition named these Collect/Process/Organize/Review/Do.)

KB mapping: Capture = root inbox → `raw/`; Clarify + Organize = compile into
`05 concepts/` / `03 Projects/` / `02 Areas/` + inline `#action`s (the endpoint
test does Clarify's project-or-not call); Reflect = the lint audits (project
next-action, area review cadence); Engage = the day's plan / `Actions.md`.

## The six Horizons of Focus

Priorities cascade **top-down**; Allen advises building the system
**bottom-up** (get control at the runway first).

| Level | Name | Altitude | Content | KB home |
| :-- | :-- | :-- | :-- | :-- |
| Ground | Calendar / Next Actions | runway | the concrete moves | inline `#action`s → `Actions.md` |
| H1 | Projects | 10,000 ft | finite multi-step outcomes (most people: 30–100) | `03 Projects/` |
| H2 | Areas of Focus & Accountability | 20,000 ft | ongoing roles/"hats", no endpoint (typically 4–7) | `02 Areas/` |
| H3 | Goals | 30,000 ft | 1–2 year objectives | `01 Horizons/Goals/` |
| H4 | Vision | 40,000 ft | 3–5 year picture | `01 Horizons/vision.md` |
| H5 | Purpose & Principles | 50,000 ft | the why; values | `01 Horizons/purpose-principles.md` |

## The core distinction: project vs area

- **Project (H1):** any desired outcome requiring more than one action step,
  **finite and completable** — official materials bound it at roughly
  completable-within-12-months. It ends.
- **Area (H2):** an ongoing role or responsibility — health, family, finances, a
  team — with **no endpoint**. It is maintained to a standard, never "done."
- The hinge: **H2 is where projects are created and retired.** Reviewing an
  area surfaces the new projects it needs and prunes the dead ones.

**How the KB makes the distinction structural:** `03 Projects/` holds finite work
classified by the **endpoint test** (completable ever = project;
`status: pending` = Someday/Maybe); `02 Areas/` holds the perpetual
responsibilities, plus `02 Areas/Assets/` sub-areas for physical things
(e.g. a `family-car` or `house` note) — a car is a *thing* you maintain, so it is an
area, not a project. Areas carry a `## Standard` and a `review:` / `reviewed:`
cadence instead of a done state. The chain is frontmatter **up-links only**
(`area:` / `serves:` / `horizon:`); downward views are generated, never
hand-maintained. The concepts folder is the don't-force-everything remainder —
knowledge notes that are neither.

## The Weekly Review

Allen's **"critical success factor"** — 11 steps, three phases:

1. **Get Clear** — collect loose inputs, process IN to zero, mind-sweep.
2. **Get Current** — review next actions, calendar, Waiting For, and **every
   project one by one, ensuring each has at least one current next action**
   (the mechanism that keeps the project list alive).
3. **Get Creative** — review Someday/Maybe; promote newly-active items to
   Projects, delete stale ones.

KB mapping: Get Current runs mechanically — every active project must carry an
open `#action` (`audit-project-next-actions.sh`, lint check 10) and every
area/horizon a fresh-enough review (`audit-area-reviews.sh`, check 12,
WARN-only); Get Creative = the `status: pending` pass inside [[Review an Area]].
The judgment layers stay with the health check.

## Known gaps in this note

Contexts (@calls, @computer), the standalone Waiting For list, the 43-folder
tickler, and the two-minute rule are deliberately **not** modeled here rather
than asserted from memory. PARA-style adaptations exist (Forte's Projects / Areas /
Resources / Archives); the kit's stack differs on purpose — a project need not
serve a goal (`area:` is required, `serves:` optional), and the concepts folder
replaces "Resources".

## Related

[[karpathy-method]] (the compile loop is GTD's Capture → Clarify in knowledge
form) · [[Run a Project]] · [[Review an Area]] · [[first-principles-thinking]] ·
[[SCHEMA]] § Conventions (Projects / Areas / Horizons)
