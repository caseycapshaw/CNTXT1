---
type: concept
updated: 2026-07-02
status: current
tags: [concept, method]
---

# Concept — The Karpathy Method (LLM Knowledge Base / "LLM Wiki")

An LLM-maintained personal wiki that *replaces* RAG at personal scale: you supply
sources and ask questions; the LLM does all the bookkeeping — summarizing,
linking, indexing, and health-checking a persistent collection of markdown files.
See [[AGENTS]] for how this KB operates the method day to day.

> Karpathy's framing: **"Obsidian is the IDE; the LLM is the programmer; the wiki
> is the codebase."** The tedious part of a knowledge base "is not the reading or
> the thinking — it's the bookkeeping," and LLMs don't get bored or forget
> cross-references.

## Origin / lineage
- **Andrej Karpathy** (OpenAI co-founder, ex-Tesla AI director) posted the idea **2026-04-02**; it went viral. Two days later he published the **`llm-wiki.md` gist** — explicitly *"an idea file, designed to be copy-pasted to your own LLM agent"* (Claude Code, Codex, etc.), **not a product or code**. The agent builds the specifics with you.
- He framed it as the next turn of Vannevar Bush's 1945 **Memex** — whose unsolved problem was always *"who does the maintenance."* The LLM is finally a plausible maintainer.
- **Cole Medin** adapted it to **code** (`coleam00/claude-memory-compiler`): the raw material is your own coding sessions, auto-captured via hooks and compiled into a self-evolving per-codebase memory. This starter takes its structure from Medin's framing (the compiler analogy + `concepts/`/`index.md`/`log.md` layout — his separate `connections/` folder was dropped 2026-07-02 as redundant with wikilinks + Related sections) but uses **manual capture, not hooks**.

## The compiler analogy (the mental model)
The reframe is: **knowledge is source code; the LLM is a compiler.**

| Compiler stage | Knowledge-base equivalent |
| :-- | :-- |
| Source code | Raw, unprocessed captures (articles, papers, transcripts, slides) — immutable |
| Compiler | The LLM — reads raw material, summarizes, links, structures |
| Executable / binary | The compiled wiki (concept articles + backlinks) — what you query |
| Index | A hand-navigable map file the LLM keeps current — replaces the vector index |
| Lint / tests | Periodic health checks (gaps, stale facts, broken links, contradictions) |
| Runtime | Answering a question by navigating the wiki via the index |

*Terminology note:* Karpathy's gist labels the operations **ingest / query / lint**; the **"compiler analogy"** is the popularized framing (Medin + secondary writeups) and the one this starter adopts in [[AGENTS]]. Same machinery, two vocabularies.

## Architecture — three layers
1. **Raw sources** — *"the LLM reads from them but never modifies them."* Immutable, append-only, dated. (Here: `raw/`.)
2. **The wiki** — LLM-generated markdown: summaries, concept/entity pages, the index, the log. **"You read it; the LLM writes it."** (Here: `concepts/` + `index.md` + `meta/log.md`.)
3. **The schema** — a config doc (`CLAUDE.md` / `AGENTS.md`) that defines structure, conventions, and workflows. This is *"what makes the LLM a disciplined wiki maintainer rather than a generic chatbot."* (Here: [[AGENTS]].)

## The workflow loop
- **Ingest** — drop a source in raw; the LLM reads it, discusses takeaways with you, writes a summary page, **updates the index**, updates related pages, and appends to the log. *A single source might touch 10–15 wiki pages.*
- **Query** — search the relevant pages via the index and synthesize a **cited** answer. Key trick: **good answers get filed back into the wiki as new pages** — the base compounds.
- **Lint** — periodic audit for contradictions, stale claims, orphan pages, missing cross-references, and gaps that need new research.
- **index.md** — a content catalog (links + one-line summaries) the LLM auto-maintains; **log.md** — chronological, append-only, greppable.

## Why it matters (the case against RAG-at-personal-scale)
- **RAG re-derives knowledge every query.** Upload files → retrieve chunks → answer. Nothing accumulates; a subtle question that needs 5 documents re-finds and re-stitches the fragments *every single time.*
- **The LLM-wiki accumulates.** The model navigates **a knowledge graph it authored itself** — following links it made, reading summaries it wrote. Knowledge is *compiled once* and reused. It's a **persistent, compounding artifact**, not a transient retrieval.
- **Semantics beat cosine similarity at this scale.** The LLM reading a structured `index.md` understands what you're *really* asking; vector search just finds similar words.
- **No embeddings, no vector DB, no infra** — *"the wiki is just a git repo of markdown files."* Plain text → portable, diffable, human-readable, future-proof.
- **The graph is a payoff in itself** — point Obsidian at the folder, open graph view, and every source you add makes the network denser.

## The scale sweet spot
- **Works without RAG at ~100 sources / hundreds of pages** (Karpathy; some writeups cite ~400k words). The entire index fits in a modern context window, so the LLM can check for duplicates and contradictions globally with no retrieval.
- **It does *not* scale to millions of documents.** Practical degradation is reported around **~200k–300k tokens** (despite 1M windows) — the LLM starts missing connections or producing inconsistent pages. RAG/search becomes worth adding around **~2,000+ articles**.
- A young KB is comfortably in the sweet spot — which is *why* you deliberately run **no vector DB** until it grows.

## Pros
- **Compounding** — answers and syntheses are filed back; the base gets *better* over time.
- **Zero retrieval infra** — markdown + an index file; nothing to host, embed, or re-index.
- **Transparent & portable** — git-tracked plaintext; you can read, diff, and audit every fact.
- **Bookkeeping is automated, judgment stays human** — the LLM does the tedious linking/indexing; you decide what's true and what matters.
- **Backlinks surface non-obvious connections** the LLM makes across sources.

## Cons / risks
- **Hallucination propagation (the big one).** Because the LLM *summarizes and compresses* sources into pages, an error can get **baked in as a "fact" and silently propagate across linked pages.** With pure RAG a wrong answer is one wrong answer; here it contaminates the graph. → This is *why the lint step and spot-checking pages against `raw/` are non-negotiable.*
- **Hard scaling ceiling** — degrades past a few hundred pages / ~200–300k tokens; not for large corpora.
- **Maintenance discipline required** — without periodic lint, stale facts and orphan links accumulate; the schema doc ([[AGENTS]]) has to be respected or the LLM drifts into generic-chatbot behavior.
- **Single-LLM dependence** — quality tracks the model and the rigor of the conventions.

## Practices the community converged on
- **Human-in-the-loop:** Karpathy still reads sources, debates takeaways, and makes the include/exclude calls. *The LLM handles logistics, not insight.*
- **Contamination mitigation** (Steph Ango / @kepano, Obsidian co-creator): keep your *clean* vault separate; let agents work in a *messy* vault and only promote distilled, verified artifacts across. (This starter approximates that with the raw → compiled separation + the clean-inbox rule.)
- **It's intentionally abstract & modular** — *"pick what's useful, ignore what isn't."* Domain-specific extensions (task systems, daily notes, auto-capture) are exactly that kind of build-out.

## Sources
- **Primary:** Karpathy, [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) (2026-04-04).
- Cole Medin — [video](https://www.youtube.com/watch?v=7huCP6RkcY4) · [`coleam00/claude-memory-compiler`](https://github.com/coleam00/claude-memory-compiler).
- [VentureBeat coverage](https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an) · MindStudio [compiler analogy](https://www.mindstudio.ai/blog/karpathy-llm-knowledge-base-compiler-analogy).
