---
type: concept
description: Google's OKF v0.1 — the open interchange standard for Karpathy-style LLM wikis, how a CNTXT1 vault maps to it, and how to adopt it at the boundaries.
updated: 2026-07-13
status: current
tags: [concept, method]
---

# Concept — Open Knowledge Format (OKF)

Google's **open standard for the Karpathy LLM wiki**: a v0.1 draft spec
(published in [GoogleCloudPlatform/knowledge-catalog → `okf/`](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf))
that pins down the *minimum* structural rules a markdown knowledge base must
follow so that **any agent can produce, exchange, and consume it** — no SDK, no
registry, no required tooling. "If you can `cat` a file, you can read OKF; if
you can `git clone` a repo, you can ship it." It standardizes exactly two
things: **how files are organized** (bundles + per-directory indexes) and
**what the YAML frontmatter contains** (`type` required; a short recommended
set). Everything else is deliberately left open.

Cole Medin's framing: *"What MCP did for agent-to-tool communication, OKF does
for agent-to-knowledge-base communication."* The Karpathy gist one-shots a
personal wiki, but everyone's wiki comes out structured differently —
different metadata, folders, link styles — so wikis can't be shared between
people's agents. OKF is the thin interoperability layer on top.

## The spec in one table (v0.1)

| Element | Rule |
| :-- | :-- |
| **Bundle** | A directory tree of markdown files — the **unit of distribution** (git repo recommended). Layout is the producer's choice. |
| **Concept** | One unit of knowledge = one `.md` file. Concept ID = path minus `.md` (`tables/users`). Tangible assets *or* abstract ideas. |
| **Frontmatter** | **`type` is the only required field** (free-form string, e.g. `Metric`, `Playbook`; no central registry). Recommended: `title`, `description` (one line), `resource` (canonical URI of the underlying asset), `tags`, `timestamp` (ISO 8601). Extra keys always allowed. |
| **Body** | Plain markdown; favor structure over prose. Conventional headings: `# Schema`, `# Examples`, `# Citations`. |
| **Links** | Standard markdown links; bundle-absolute (`/tables/x.md`) recommended. A link = an untyped relationship; the *kind* lives in surrounding prose. Broken links are legal ("not-yet-written knowledge"). |
| **`index.md`** | Reserved filename, allowed in **any directory** — progressive disclosure (`* [Title](url) - description` bullets, descriptions pulled from frontmatter). |
| **`log.md`** | Reserved, any level — date-grouped history, newest first, `**Update**`/`**Creation**` verb convention. |
| **Citations** | Numbered `# Citations` section at the bottom; may point at URLs or a `references/` subdir mirroring external sources as first-class concepts. |
| **Conformance** | Only 3 hard rules: parseable frontmatter on every non-reserved `.md`, non-empty `type`, reserved files well-formed. Consumers MUST NOT reject unknown types/keys, broken links, or missing indexes — **permissive by design**. |

Non-goals: no fixed type taxonomy, no storage/serving prescriptions, doesn't
replace domain schemas (Avro/OpenAPI — OKF *references* them). The repo's
BigQuery reference agent and Cytoscape `viz.html` visualizer are explicitly
proofs of concept; **the format is the contribution**.

## What it's *for*

- **Exchange** — team wikis every member's second brain reads independently; content creators shipping **prepackaged bundles** you clone and query instead of feeding transcripts in yourself.
- **Production + consumption symmetry** — a standard for how enrichment agents *write* knowledge, not just how consumers read it.
- **Adoption via the spec itself** — SPEC.md works like a skill: paste it into a coding agent to build a new wiki or refactor an existing one (fan out subagents for big KBs).
- The common critique — "it's too simple, there's not much there" — is answered by design: minimal opinionation *is* the point. Even if OKF itself doesn't win, something shaped like it will.

## How a CNTXT1 vault maps to OKF

A vault built on this starter kit (see [[karpathy-method]] / [[AGENTS]]) is
functionally a **superset** of OKF — nearly every OKF idea already exists:

| OKF | CNTXT1 vault |
| :-- | :-- |
| `type` required frontmatter | ✓ `type: concept/initiative` + People/Jobs frontmatter |
| `description` recommended | ✓ one stable sentence on every concept/initiative (enforced by `lint.sh`) |
| `timestamp` recommended | `updated: YYYY-MM-DD` (dialect difference) |
| Root `index.md` with described links | ✓ (Quick map + rich sections) |
| Per-directory `index.md` | Functional equivalent: [[contacts]] indexes `People/`, [[jobs]] indexes `Jobs/` |
| `log.md` | ✓ `meta/log.md` (append-only one-liners vs OKF's newest-first groups — dialect difference) |
| Markdown path links | **Divergent:** Obsidian `[[wikilinks]]` + `meta/link-map.md` |
| Citations / provenance | ✓ stronger: every concept fact must trace to a `raw/` capture |
| Bundle = distribution unit | A private vault ships nothing — conformance matters only for what you *export* or *ingest* |

Strict conformance would require frontmatter on `raw/`/`daily/` files and
portable path links instead of wikilinks. Neither matters internally —
conformance is a property of what you ship, not how you live.

## Recommended posture: adopt at the boundaries

**Don't refactor a working vault's internals to chase conformance** — the
method already implements OKF's load-bearing ideas and exceeds it where the
spec is silent (lint, link-map, raw/compiled separation, Actions). Converting
wikilinks to path links or adding per-folder indexes trades real Obsidian
ergonomics for conformance a private vault doesn't need. Instead:

1. **Inbound:** when someone shares an OKF bundle, ingest it like any source —
   clone, walk its indexes, compile durable facts into `concepts/` with raw
   provenance pointing at the bundle.
2. **Outbound:** anything you export (a shared corpus, a published subset) can
   be made OKF-conformant at export time — map `updated:` → `timestamp`,
   rewrite wikilinks to bundle-relative paths — without touching the vault.
3. **Internal:** the `description:` frontmatter convention (adopted in this
   kit) is the one OKF idea worth carrying inside: it single-sources each
   note's index one-liner and makes any future export trivially conformant.

## Citations

[1] [OKF SPEC.md v0.1 + README](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) — GoogleCloudPlatform/knowledge-catalog.
[2] [Cole Medin, "Finally, an Open Standard for the Karpathy LLM Wiki is HERE"](https://www.youtube.com/watch?v=T33iI6izAKw) (2026-07-02).

## Related

- [[karpathy-method]] — the underlying method OKF standardizes.
- [[AGENTS]] — this kit's schema (where the `description:` rule lives).
