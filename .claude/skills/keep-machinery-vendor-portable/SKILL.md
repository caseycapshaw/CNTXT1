---
name: keep-machinery-vendor-portable
description: Every enforced guarantee lives at a vendor-independent tier; harness surfaces accelerate but never solely carry it, and script failures are declared, never imitated. Use when building or modifying any KB machinery — a script, hook, scheduled job, or enforcement mechanism.
metadata:
  title: Keep Machinery Vendor-Portable
  type: rule
  domain: kb-meta
  trigger: "building or modifying any KB machinery — a script, hook, scheduled job, or enforcement mechanism"
  frequency: always
  tools: []
  owner: "{{NAME}}"
  status: active
  tags: [rule, kb-meta]
  aliases: [Keep Machinery Vendor-Portable, keep-machinery-vendor-portable, portability-rule]
  summary: Every enforced guarantee lives at a vendor-independent tier; harness surfaces accelerate but never solely carry it, and script failures are declared, never imitated.
---


# Skill — Keep Machinery Vendor-Portable

> **When:** building anything enforcement-shaped (lint, caps, rituals, sync, hooks) · **Frequency:** standing
> **Outcome:** the KB survives any single vendor surface disappearing — losing a harness costs latency, never correctness

## The rule

Machinery guarantees live in **three tiers**:

1. **Ritual** — convention-mandated, script-invoked. Any agent with a shell can comply (`lint.sh`, `cap_check.py`, `build-link-map.sh`, the close ritual's record steps).
2. **Producer** — OS-scheduled (launchd on macOS). No AI vendor in the loop (8am plan, 6pm summary, nightly snapshot).
3. **Harness accelerant** — vendor-specific surfaces: Claude Code hooks, skill shims, MCP servers. **Latency and convenience only.**

**A vendor-specific surface may accelerate a guarantee but never solely carry it.** Every enforcement must exist at tier 1 or 2; removing every tier-3 accelerant may cost latency, never correctness. (The SessionStart hook accelerates orientation — but `CLAUDE.md` + `index.md` carry it. A Stop-hook close reminder accelerates the close ritual — but the [[Close a Session]] skill + the 6pm backstop carry it.)

## Corollaries

- **Degradation is declared, never silently skipped.** A session whose harness can't run a mandated script says so explicitly (the `cap_exception:` principle applied to capability itself).
- **A script failure is declared, never imitated.** When a mandated script errors or is unavailable, report that fact — never hand-produce the script's output by model judgment, which keeps the report's *shape* while silently discarding its *determinism*.
- **Scripts stay stdlib-only or vendored** so they run on a stock macOS `python3`/`bash` in any sandbox that syncs the folder.
- **Dry-run by default** for anything that writes: an explicit `--apply`/`--write` flag to act.

## Related

[[SCHEMA]] · [[Maintain Generated Sections]] · [[Close a Session]].
