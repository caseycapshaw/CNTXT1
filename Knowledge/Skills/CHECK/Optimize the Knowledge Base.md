---
type: check
domain: kb-meta
trigger: "monthly, when the KB feels slow/bloated to navigate, or when {{NAME}} asks for a Claude+KB performance / organization step-back"
frequency: monthly
tools: "bash (wc/awk/grep/rg), ssh <other-machine> (if you run more than one), SYSTEM/bin/lint.sh, SYSTEM/bin/build-link-map.sh, SYSTEM/bin/cap_check.py"
owner: "{{NAME}}"
status: active
version: "1.0"
tags: [check, kb-meta]
aliases: [Optimize the knowledge base, Optimize the KB, KB efficiency pass, Tune the knowledge base, KB kernel pass, optimize-the-knowledge-base]
summary: Profile the KB like an OS (boot cost, paging, scheduler, log, GC, hook parity), record the gauges, then cut only what a number justifies.
updated: 2026-09-28
author_type: script
---

> _Generated from `.claude/skills/optimize-the-knowledge-base/SKILL.md` by `SYSTEM/bin/build_claude_mirrors.py` — edit the canonical file, never this mirror. Generated: 2026-09-28_

# Skill — Optimize the knowledge base

> **When:** monthly, whenever the KB feels slow/bloated, or when {{NAME}} asks for a step-back on Claude+KB performance/organization · **Frequency:** monthly / ad-hoc · **Tools:** `bash`, `ssh` to the other machine, `SYSTEM/bin/lint.sh`, `SYSTEM/bin/build-link-map.sh`, `SYSTEM/bin/cap_check.py`
> **Outcome:** a dated gauge table (the "before"), a ranked set of cuts each traceable to a gauge, and — if the cuts are more than an evening — an initiative. Distinct from [[Run the KB health check]] (correctness) and [[Audit the KB System]] (architecture); this is **performance and organization**, measured.

## The lens

Treat Claude+KB as an **operating system for information work**. The filesystem
(schema, up-links, lint, link map) is usually fine; what degrades is the
**kernel** — and each kernel part has a gauge:

| OS part | KB surface | Gauge |
| :-- | :-- | :-- |
| Boot sequence | SessionStart hook + "read at start" files | tokens loaded before the first word of work; is the map loaded twice? |
| Hardware detection | hook output | does the session know which machine it's on? |
| Memory paging | Now & next vs. Milestones/Trail in the same file | bytes per section of the biggest notes |
| Process scheduler | open `#action` lines | count · age · per-home · machine-made share |
| Syslog | `SYSTEM/log.md` | size, lines/month |
| Garbage collection | `Knowledge/raw/` captures never compiled | orphan count (zero inbound links) |
| Telemetry | none unless built | is any of this measured automatically? |

**Measure before changing.** Every cut in step 5 must point at a row in the
table from steps 1–4.

## Steps

1. **Boot cost — what every session pays.** Bytes ÷ 4 ≈ tokens.
   ```bash
   cd <vault>
   for f in AGENTS.md SYSTEM/SCHEMA.md index.md Actions.md SYSTEM/link-map.md SYSTEM/log.md SYSTEM/decisions.md; do
     printf "%-24s %7d bytes ~%5d tok %4d lines\n" "$f" $(wc -c <"$f") $(( $(wc -c <"$f")/4 )) $(wc -l <"$f"); done
   head -c 8000 index.md | grep -c '^## '        # Quick-map skeleton inside the injection window?
   ```
   Add up what `AGENTS.md` tells a session to read *plus* what the hook injects.
   Double-loading (hook injects the index head **and** the session is told to
   read `index.md`) is the classic leak.

2. **Hook parity + machine identity — on EVERY machine that opens the vault.**
   A second machine can share the vault path yet run different hooks (or none).
   ```bash
   hostname; ls ~/.claude/hooks/; python3 -c "import json;print(json.load(open('$HOME/.claude/settings.json')).get('hooks',{}).get('SessionStart'))"
   ssh <other-machine> 'hostname; ls ~/.claude/hooks/'
   ```
   Different hooks per machine, or a hook that never announces `hostname`,
   is a finding. (Single-machine setups: skip the `ssh` line.)

3. **Paging — where the bytes live inside the big notes.**
   ```bash
   find "Knowledge/Initiatives" "Knowledge/Concepts" -maxdepth 2 -name "*.md" -exec wc -c {} + | sort -rn | head -8
   awk '/^## /{if(h)printf "%7d  %s\n",n,h;h=$0;n=0;next}{n+=length($0)+1}END{printf "%7d  %s\n",n,h}' "Knowledge/Initiatives/<biggest>.md" | sort -rn | head
   grep -h '^updated:' Knowledge/Concepts/*.md | awk '{print substr($2,1,7)}' | sort | uniq -c   # concept freshness by month
   ```
   A `## Now & next` or `## Milestones` measured in tens of KB is history
   living in a hot file. Check `SYSTEM/bin/cap_check.py` covers it; if not,
   that's the cut.

4. **Scheduler, syslog, GC — the counts.**
   ```bash
   grep -rcE '^\s*- \[ \] .*#action' --include='*.md' . | grep -v ':0$' | sort -t: -k2 -rn | head -12   # open actions by home
   grep -rhoE '^\s*- \[ \] .*#action' --include='*.md' . | wc -l                                        # total
   grep -oE '^- [0-9]{4}-[0-9]{2}' SYSTEM/log.md | sort | uniq -c                                            # log lines / month
   for r in Knowledge/raw/20*.md; do b=$(basename "$r" .md); grep -rqlF "raw/$b" --include='*.md' --exclude-dir=raw --exclude-dir=SYSTEM . || echo "$b"; done | wc -l   # orphan raw
   ( time bash SYSTEM/bin/lint.sh >/dev/null ) 2>&1 | grep real
   ```
   Look for **action inflation from automation** (one machine-fed note
   holding a large share of all open actions) — machine-made actions
   dilute the human next-action signal and want their own tag/queue.

5. **Write the gauge table, then rank the cuts by leverage.** Save the
   numbers as a dated `Knowledge/raw/YYYY-MM-DD-kb-performance-assessment.md` (or append to
   the existing initiative's Baseline table). Rank: per-session costs (boot)
   beat per-open costs (note bloat) beat per-month costs (log, GC). Give
   credit for what is already good — the gauges that are fine are part of
   the picture.

6. **Cut only what a number justifies — or open an initiative.** One-evening
   fixes (tighten the Quick map, rotate the log, add a lint WARN) go now;
   anything structural (new hook, new generated section, cap extension)
   becomes `#action`s in a dedicated initiative note. Regenerate
   `SYSTEM/bin/build-link-map.sh`; `SYSTEM/bin/lint.sh` must be green.

7. **Judgment pass lint can't do:** resolved open questions, actions that
   should be checked off, dated items now overdue, `index.md` entries that
   duplicate a note's Now & next (the [[Audit state freshness]] symptom).

8. **Document + log.** Convention changes → `SYSTEM/SCHEMA.md` + `AGENTS.md`.
   One line in `SYSTEM/log.md`. Re-measure next run and put the delta in the
   log line — the point of the table is the trend.

## Gotchas / rules
- **Measure first, then cut** — every change traces to a gauge row.
- **Count tokens, not lines** — `wc -l` hides a 16KB paragraph; bytes ÷ 4 doesn't.
- **Every machine, every time** — the machine you're on is not necessarily the one {{NAME}} uses most; verify with `hostname` before any machine-specific action.
- **Bare `grep`/`rg` may be Claude Code shell wrappers** — for benchmarks use full paths (`/usr/bin/grep`, `/opt/homebrew/bin/rg`); `rg` skips `.claude/` unless `--hidden` .
- **`index.md` is a map, never a log** — narrative status creeping into it is duplicated state that will go stale.
- **The injection cap is invisible** — nothing errors when the Quick map outgrows `head -c 8000`; the tail silently never reaches the LLM.
- **Don't hand-edit generated artifacts** — link map, mirrors, serves lists, any `<!-- generated -->` block ([[maintain-generated-sections]]).
- **Efficiency ≠ correctness** — a green health check doesn't mean the KB is lean; that's why this job is separate.

## Done when
- [ ] Gauge table captured (boot cost, hook parity, biggest sections, actions, log, orphan raw, lint time) and saved dated in `Knowledge/raw/`.
- [ ] Cuts ranked by leverage; each points at a gauge.
- [ ] One-evening cuts applied; structural ones filed as `#action`s in an initiative note.
- [ ] `SYSTEM/link-map.md` regenerated; `SYSTEM/bin/lint.sh` green.
- [ ] `SYSTEM/log.md` entry with the delta vs. the last run.

## Related
- [[Run the KB health check]] (correctness sibling) · [[Audit the KB System]] (architecture sibling) · [[Audit state freshness]] (duplicated-state symptom) · [[keep-machinery-vendor-portable]] (script-measured, never model-estimated) · [[karpathy-method]] · [[SCHEMA]]
