---
name: review-an-area
description: 'Run one area''s cadenced review — check the standard, walk its projects, spawn/retire work, bump reviewed:. Use when {{NAME}} asks to review an area or audit-area-reviews.sh flags one overdue.'
metadata:
  title: Review an Area
  type: do
  domain: kb-meta
  trigger: "{{NAME}} asks to review an area, or audit-area-reviews.sh flags one overdue"
  frequency: "per area cadence (weekly / monthly / quarterly)"
  tools: "Read, Edit, Bash"
  owner: "{{NAME}}"
  status: active
  version: "1.0"
  tags: [do, kb-meta, gtd]
  aliases: [review-an-area, Review area]
  summary: Run one area's cadenced review — check the standard, walk its projects, spawn/retire work, bump reviewed:.
  updated: 2026-09-28
---


# Skill — Review an area

> **When:** an area's `review:` cadence comes due (`SYSTEM/bin/audit-area-reviews.sh`
> flags it) or {{NAME}} asks · **Outcome:** the area re-grounded against its
> Standard, its projects pruned/spawned, `reviewed:` bumped
> **Why:** GTD's hinge — H2 is where projects are created and retired.
> Areas don't owe next actions (projects do); they owe a recent, honest look.

## Steps

1. **Open the area note** (`02 Areas/<slug>.md` or `02 Areas/Assets/<slug>.md`).
   Read `## Standard` and the current state sections.
2. **Walk its children.** The live view is the backlinks on `area:` —
   mechanical fallback:
   ```bash
   rg -l 'area: "\[\[<slug>\]\]"' "03 Projects" "02 Areas"
   ```
   (sub-areas + live projects up-linking this area).
3. **Judge against the Standard:**
   - Anything slipping that needs a new `#action` or a new project
     ([[Run a Project]])?
   - Any live project under this area dead or stalled → close, pause, or
     re-scope it?
   - Any `status: pending` project whose trigger has fired → promote to
     active (the Someday/Maybe pass)?
   - Does this area's `serves:` still point at the right `type: goal` note
     (or horizon)? Retarget rather than accumulating stale whole-horizon
     links.
4. **Make the edits in the owning notes** — actions inline where they
   belong, never a side list.
5. **Bump the area's `reviewed:`** to today (and `updated:` if the note
   meaningfully changed). If `serves:` changed, regen the downward lists:
   `uv run python SYSTEM/bin/build_horizon_serves.py --write`. Append a
   one-line entry to `SYSTEM/log.md`.
6. **Verify:** `SYSTEM/bin/audit-area-reviews.sh` shows the area PASS.

## Gotchas / rules

- **Don't invent busywork.** A quiet area that meets its Standard just gets
  `reviewed:` bumped — that's a legitimate review outcome.
- **Horizon notes review the same way** (`[[goals]]` quarterly — walk its goal
  notes; vision/purpose yearly) — same audit, same bump; content changes there
  are bigger conversations.
- A review that finds the *Standard itself* wrong rewrites the Standard —
  that's a meaningful change; bump `updated:` and log it.

## Done when

- [ ] Standard checked honestly; slippage turned into actions/projects in their owning notes.
- [ ] Dead projects closed/paused; fired pending triggers promoted.
- [ ] `reviewed:` bumped; log line appended; audit shows PASS.

## Related

[[gtd]] (the H2 hinge) · [[Run a Project]] · [[Run the KB health check]] ·
`SYSTEM/bin/audit-area-reviews.sh`
