---
type: job
domain: kb-meta
trigger: periodic efficiency review (monthly), or when the KB feels slow/bloated to navigate
frequency: monthly / ad-hoc
tools: bash (wc/grep/head), meta/bin/lint.sh, meta/bin/build-link-map.sh
owner: {{NAME}}
status: active
tags: [job, kb-meta]
aliases: [Optimize the KB, KB efficiency pass, Tune the knowledge base]
---

# Job — Optimize the knowledge base

> **When:** monthly, or whenever the KB feels slow/bloated to navigate · **Frequency:** monthly / ad-hoc · **Tools:** `bash`, `meta/bin/lint.sh`, `meta/bin/build-link-map.sh`
> **Outcome:** the KB stays *fast for the LLM* (lean injected map, resolvable links) and *accurate* (fresh frontmatter, green lint). Distinct from [[Run the KB health check]], which checks **correctness**; this checks **efficiency/structure**.

## When to run this
A KB grows every session, and growth quietly degrades what the LLM pays for: the **session-start context** (if you use the optional SessionStart hook, it inlines `head -c 8000` of `index.md` — outgrow that and the tail is silently dropped) and **link/lookup cost**. Run this monthly, or any time the map feels bloated, a concept has ballooned, or `index.md` has started accreting a changelog. **Measure before changing** — don't optimize on a hunch.

## Steps

1. **Measure the cost surface first.**
   ```bash
   cd <vault>
   wc -l CLAUDE.md meta/AGENTS.md index.md Actions.md      # session-load files
   wc -l concepts/*.md | sort -rn | head                   # biggest concepts (prune/split candidates)
   wc -l raw/*.md      | sort -rn | head                   # biggest raw captures
   ```

2. **Check the injection budget** (if you run the SessionStart hook). The whole Quick-map skeleton must land inside the injected window, or startup context is partial.
   ```bash
   head -c 8000 index.md | grep -c '## Concepts'           # expect 1 (skeleton + heading both inside budget)
   ```
   If it no longer fits: **tighten the Quick map** (shorter glosses) first; only raise `head -c 8000` in the hook as a last resort (bigger injection = more tokens every session).

3. **Keep `index.md` a pure map.** No changelog, no dated narrative — those belong in `meta/log.md`.
   ```bash
   grep -nE '^_(Prior|Last updated|Status)' index.md       # expect no changelog blocks (a single _Last updated_ footer is fine)
   ```
   Move any narrative history to `meta/log.md`. Keep the Raw listing condensed (grouped one-liners, not a paragraph per file).

4. **Audit concept frontmatter + staleness.** Every concept carries `type/updated/status/tags`; `updated:` is the staleness signal.
   ```bash
   for f in concepts/*.md; do [ "$(head -1 "$f")" = "---" ] || echo "NO FM: $f"; done
   grep -H '^updated:' concepts/*.md | sort -t: -k3         # oldest first — eyeball for outdated truth
   ```
   For any concept whose `updated:` predates work that changed its truth: rewrite in place + bump `updated:`, or set `status: stale`/`superseded`.

5. **Refresh the link-map.**
   ```bash
   ./meta/bin/build-link-map.sh        # overwrites meta/link-map.md
   ```

6. **Run the mechanical lint — must be green**, then do the judgment pass it can't.
   ```bash
   ./meta/bin/lint.sh                  # inbox · wikilinks · index · frontmatter
   ```
   Judgment layer: resolved open questions, `#action`s that should be checked off, dated items now overdue.

7. **Large-file review.** For any concept much longer than its peers (step 1): decide whether it's genuinely dense reference (fine) or is carrying `raw/`-capture detail that should be pruned back to the source. Concepts are the *compiled* layer; long-tail detail lives in `raw/`.

8. **Document + log.** If you changed a *convention* (not just content), update `meta/AGENTS.md` + `CLAUDE.md`. Append a one-line `meta/log.md` entry.

## Gotchas / rules
- **Measure first, then cut** — every change should trace to a number from step 1–2.
- **`index.md` is a map, never a log** — the most common regression is changelog narrative creeping back into the index. Step 3 catches it.
- **The injection cap is invisible** — nothing errors when the map outgrows it; the tail just silently never reaches the LLM. Step 2 is the only signal.
- **`updated:` only helps if you bump it** — stamping frontmatter once and never maintaining it makes staleness *look* solved while rotting.
- **Don't hand-edit generated artifacts** — `meta/link-map.md` is built by its script.
- **Efficiency ≠ correctness** — a green [[Run the KB health check]] doesn't mean the KB is lean; that's why this job is separate.

## Done when
- [ ] Step 1–2 numbers captured; Quick-map skeleton fits the injection budget.
- [ ] `index.md` is a pure map; Raw listing condensed.
- [ ] All concepts have frontmatter; stale ones rewritten or marked.
- [ ] `meta/link-map.md` regenerated; `meta/bin/lint.sh` exits green.
- [ ] Any new convention documented; `meta/log.md` entry appended.

## Related
- [[Run the KB health check]] (sibling — correctness lint vs. this efficiency pass) · [[karpathy-method]] (the architecture being optimized) · [[AGENTS]] (the conventions this enforces)
