---
type: concept
description: The runbook index — the how-do-I-X map and grouped tables over the Jobs/ folder.
updated: {{DATE}}
status: current
tags: [concept, index]
---

# Concept — Jobs (runbook index)

**The index to the [`Jobs/`](../Jobs) folder.** A **Job** is a reusable runbook for a recurring "job to be done" — the **single source of truth for the *steps*** of a repeatable task, written agent-executable (imperative, tool-specific) so an agent or you can run it. The matching **concept** keeps the *why/context/principles* and links here. This page is the map.

> **How to use this**
> - **Each recurring task = one runbook**, filed as `Jobs/Imperative Title.md`, wikilinked `[[Imperative Title]]`.
> - **Add a job:** copy `Jobs/Jobs TEMPLATE.md` → `Jobs/<Imperative Title>.md`, fill `When / Steps / Gotchas / Done-when / Related`, add a row here.
> - **Naming:** imperative verb-first, Title Case (`Create a pull request`, not "Creating…").
> - `Jobs/` is a **structural folder, not the inbox**.
> - **Steps live in the job; context lives in the concept** — jobs link to their concept for the deeper why.

---

## 📚 KB-meta
Jobs for maintaining the knowledge base itself — always useful, ship with the starter.

| Job | Trigger | Notes |
| :-- | :-- | :-- |
| [[Add a person to the KB]] | a new person appears | copy People template → note → index in [[contacts]] |
| [[Capture a meeting or conversation into the KB]] | new durable knowledge | inbox→`raw/`→compile→`index.md`→`meta/log.md` |
| [[Run an initiative]] | an outcome needs multiple actions over time | one note per initiative in `Initiatives/` (`type: initiative` + lifecycle); start / keep current / close |
| [[Run the KB health check]] | lint (on request or automated at 6pm) | inbox clean · links resolve · index complete · actions current |
| [[Optimize the knowledge base]] | monthly / when the KB feels bloated | efficiency pass: injection budget · index-as-map · frontmatter staleness · link-map · lint |
| [[Sync an improvement to CNTXT1]] | a generic schema/tooling/template change is worth sharing | the ONLY outward path — manual copy + re-template + grep gate; personal content never leaves the vault (`AGENTS.md` § Privacy) |
| [[Create an Excalidraw diagram]] | need a diagram / visual in the vault *(optional)* | zero-dep `meta/bin/excalidraw.py` (spec→file) or Mermaid by hand; text ids ≤8 chars or the mirror breaks |
| [[Delegate an initiative to a CMUX workspace]] | an initiative is ready to run in its own repo context *(optional, needs CMUX)* | workspace-level delegation; state round-trips through `Initiatives/<slug>.md`, not the runtime tool |
| [[Spawn subagent panes in a CMUX workspace]] | one task fans out into concurrent sub-tasks *(optional, needs CMUX)* | pane-level fan-out; four-verb loop (send/send-key/read-screen/close-surface) + `DONE:` sentinel |

## 🛠️ Dev
_(add job runbooks for your recurring dev tasks)_

| Job | Trigger | Notes |
| :-- | :-- | :-- |
| _(add rows here)_ | — | — |

## 🤝 Ops & comms
_(add job runbooks for recurring communications and operations tasks)_

| Job | Trigger | Notes |
| :-- | :-- | :-- |
| _(add rows here)_ | — | — |

---

## Adding & maintaining jobs
- A job earns a note when the task **recurs** and has **non-obvious steps or a gotcha** worth not re-deriving. One-offs stay as actions/notes.
- Keep steps **executable** — name the exact tool / CLI / file. If a job's "why" grows, push it into the concept and keep the job lean.

## Related
[[contacts]] (the People index — sibling system) · [[AGENTS]] (the method + structural-folder rules) · [[karpathy-method]]
