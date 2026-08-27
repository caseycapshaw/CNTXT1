---
type: concept
description: The skills index — the how-do-I-X map and grouped tables over the Knowledge/Skills/ folder.
updated: 2026-08-20
status: current
tags: [concept, index]
---

# Concept — Skills (skill index)

**The index to the [`Knowledge/Skills/`](../Skills) folder.** A **Skill** is a reusable, agent-executable runbook for a recurring "job to be done" — the **single source of truth for the *steps*** of a repeatable task, filed at `Knowledge/Skills/<TYPE>/<Imperative Title>.md` where `TYPE` ∈ `DO` (performs a recurring task) · `CHECK` (verifies/audits something) · `FORMAT` (produces/structures an artifact) · `RULE` (a standing convention/policy). The matching **concept** keeps the *why/context/principles* and links here. This page is the map.

> **How to use this**
> - **Each recurring task = one skill**, filed as `Knowledge/Skills/<TYPE>/<Imperative Title>.md`, wikilinked `[[Imperative Title]]` (old kebab slugs stay registered as `aliases:`).
> - **Add a skill:** copy `Knowledge/Skills/Skill TEMPLATE.md` → `Knowledge/Skills/<TYPE>/<Imperative Title>.md`, set the frontmatter (`type:` matching the folder, `trigger:`, `summary:`), fill `When / Steps / Gotchas / Done-when / Related`, regen the link map, add a row here.
> - **Naming:** kebab-case slug; the old-style imperative title (`Imperative Title`) becomes the first alias so existing `[[Imperative Title]]` links keep resolving.
> - `Knowledge/Skills/` is a **structural folder, not the inbox**.
> - **Steps live in the skill; context lives in the concept** — skills link to their concept for the deeper why.

---

## 📚 KB-meta
Skills for maintaining the knowledge base itself — always useful, ship with the starter.

| Skill | Trigger | Notes |
| :-- | :-- | :-- |
| [[Add a person to the KB]] | a new person appears | copy People template → note → index in [[contacts]] |
| [[Close a Session]] | "{{NAME}} says close / wrap up" | single-door session close: one feedback question → record (log, decisions, digests) → review (route learnings by scope) |
| [[Capture a meeting or conversation into the KB]] | new durable knowledge | inbox→`Knowledge/raw/`→compile→`index.md`→`SYSTEM/log.md` |
| [[Capture a YouTube video into the KB]] | a YouTube link worth keeping | `yt-dlp` metadata + transcript digest → `Knowledge/raw/` → compile; every note links the video + its description links |
| [[Run an initiative]] | an outcome needs multiple actions over time | one note per initiative in `Knowledge/Initiatives/` (`type: initiative` + lifecycle); start / keep current / close |
| [[Run the KB health check]] | lint (on request or automated at 6pm) | inbox clean · links resolve · index complete · actions current |
| [[Optimize the knowledge base]] | monthly / when the KB feels bloated | efficiency pass: injection budget · index-as-map · frontmatter staleness · link-map · lint |
| [[Audit the KB System]] | quarterly, or after a major structural change | the wide audit: 4 parallel auditors (structure/UX · interlinking · consistency · connected systems) → ranked report + phased fix plan; recurring findings promoted to lint checks |
| [[Audit state freshness]] | monthly with the optimize pass, or when the index Quick map feels behind reality | the judgment layer of lint: verify every state-shaped claim on the always-loaded surfaces against its source note; replace drifted state in place |
| [[Sync an improvement to CNTXT1]] | a generic change is already implemented privately and worth sharing | the ONLY outward path — manual copy + re-template + grep gate; the exception path — prefer authoring upstream-first (`AGENTS.md` § Privacy) |
| [[Pull framework updates from CNTXT1]] | a kit improvement should land in your vault | git cherry-pick from the fetch-only `upstream` remote — the safe inbound direction |
| [[Maintain Generated Sections]] | any file a script rewrites, a new data feed, or an "always current" requirement | RULE — hand config above a `<!-- generated -->` marker, machine content below with a stamp; generators fail loud; never hand-edit below the line |
| [[Keep Machinery Vendor-Portable]] | building or modifying lint, caps, rituals, hooks, or scheduled jobs | RULE — every enforced guarantee lives at a vendor-independent tier; harnesses accelerate, never solely carry; script failures are declared, never imitated |
| [[Create an Excalidraw diagram]] | need a diagram / visual in the vault *(optional)* | zero-dep `SYSTEM/bin/excalidraw.py` (spec→file) or Mermaid by hand; text ids ≤8 chars or the mirror breaks |
| [[Create Directory Dashboard]] | a Knowledge/ folder needs a live frontmatter table in Obsidian *(optional)* | one `.base` file per folder (Obsidian Bases); self-relative filter, columns = schema fields; human counterpart to the generated `index.md` |
| [[Delegate an initiative to a CMUX workspace]] | an initiative is ready to run in its own repo context *(optional, needs CMUX)* | workspace-level delegation; state round-trips through `Knowledge/Initiatives/<slug>.md`, not the runtime tool |
| [[Spawn subagent panes in a CMUX workspace]] | one task fans out into concurrent sub-tasks *(optional, needs CMUX)* | pane-level fan-out; four-verb loop (send/send-key/read-screen/close-surface) + `DONE:` sentinel |

## 🛠️ Dev
_(add skills for your recurring dev tasks)_

| Skill | Trigger | Notes |
| :-- | :-- | :-- |
| _(add rows here)_ | — | — |

## 🤝 Ops & comms
_(add skills for recurring communications and operations tasks)_

| Skill | Trigger | Notes |
| :-- | :-- | :-- |
| _(add rows here)_ | — | — |

---

## Adding & maintaining skills
- A skill earns a note when the task **recurs** and has **non-obvious steps or a gotcha** worth not re-deriving. One-offs stay as actions/notes.
- **Domain reviews:** when a domain (finances, health, …) accumulates enough state, pair a standing role (`Knowledge/Agents/domain-advisor TEMPLATE.md`) with a review skill built from `Knowledge/Skills/DO/Run a Domain Review TEMPLATE.md` — see `SYSTEM/SCHEMA.md` § Optional extensions.
- Keep steps **executable** — name the exact tool / CLI / file. If a skill's "why" grows, push it into the concept and keep the skill lean.

## Related
[[contacts]] (the People index — sibling system) · [[SCHEMA]] (the method + structural-folder rules) · [[karpathy-method]]
