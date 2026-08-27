---
type: do
domain: kb-meta
trigger: a framework improvement lands in the public CNTXT1 kit
frequency: ad-hoc
tools: ["git"]
owner: "{{NAME}}"
status: active
tags: [do, kb-meta]
aliases: ["Pull framework updates from CNTXT1", "Pull framework updates", "Pull from upstream CNTXT1", "pull-framework-updates-from-cntxt1"]
summary: Pulls a generic schema/script/runbook/template improvement from the public CNTXT1 starter kit into this vault via git, leaving personal content untouched.
author_type: script
---

> _Generated from `.claude/skills/pull-framework-updates-from-cntxt1/SKILL.md` by `SYSTEM/bin/build_claude_mirrors.py` — edit the canonical file, never this mirror. Generated: 2026-08-27_

# Skill — Pull Framework Updates from CNTXT1

> **When:** the public `CNTXT1` starter kit gains a generic improvement
> (schema, `SYSTEM/bin/` script, runbook, template) this vault should adopt ·
> **Frequency:** ad-hoc, after kit commits · **Tools:** git ·
> **Outcome:** the improvement is applied to this vault via git, with personal
> content in populated files untouched.

## Why this direction is safe (and the other isn't)

Public → private can't leak anything — everything in the kit is already
public. That's why this direction is git-automated while the outward
direction ([[Sync an improvement to CNTXT1]]) stays manual with a grep gate.
**Author generic improvements upstream-first** (in your clone of the public
kit, through its CI gates) whenever they aren't already implemented in your
vault; then this runbook brings them in. Full model: `SYSTEM/SCHEMA.md`
§ Privacy & content separation.

**Precondition:** the `upstream` remote exists and is fetch-only
(`git remote -v` must show `upstream … (fetch)` and `DISABLED (push)`).
One-time setup, from the vault root:

```
git remote add upstream https://github.com/caseycapshaw/CNTXT1.git
git remote set-url --push upstream DISABLED
```

## Steps

1. **Fetch and review** what's new upstream:
   ```
   git fetch upstream
   git log --oneline main..upstream/main
   ```
   (Histories are independent, so `main..upstream/main` lists all upstream
   commits — compare against the last SHA recorded in `SYSTEM/log.md` by the
   previous pull, and pick only the new ones.)
2. **Cherry-pick the wanted commits**, oldest first:
   ```
   git cherry-pick <sha>
   ```
   Files byte-identical across the repos (`SYSTEM/SCHEMA.md`, `SYSTEM/bin/*`,
   most `Knowledge/Skills/`, templates) apply cleanly. Conflicts concentrate in the
   **populated-vs-skeleton files** (`CLAUDE.md`, `index.md`,
   `Knowledge/Concepts/contacts.md`, `Knowledge/Concepts/skills.md`, `README.md`): resolve by
   keeping your vault's personal content and hand-applying only the
   *structural* change the kit commit made. `--strategy-option=ours` is
   usually wrong here — read the conflict.
3. **Skip what doesn't apply.** Kit commits that only touch skeleton content
   your vault has long since replaced (e.g. `setup.md`, README boilerplate)
   can be dropped: `git cherry-pick --skip`.
4. **Post-pull hygiene:** if any concept/person/job was added or renamed,
   `SYSTEM/bin/build-link-map.sh`; then `SYSTEM/bin/lint.sh` must be green.
5. **Update the adopted baseline** so the nightly upstream check stands
   down: write the upstream SHA you just adopted to
   `~/.claude/cache/cntxt1-upstream-adopted`, and delete the auto-generated
   `Upstream kit updates (pending).md` from the vault root if present (the
   6pm daily-summary job also clears it once the baseline is current).
6. **Log it:** one line in `SYSTEM/log.md` — what was pulled and the upstream
   SHA now adopted (the next run diffs from there).

## Gotchas / rules

- **Never make `upstream` pushable, never push your vault anywhere but its
  private origin.** The `DISABLED` push URL is the mechanical guarantee —
  don't "fix" it.
- A cherry-pick that turns out to drag in unwanted skeleton content:
  `git cherry-pick --abort` and hand-apply instead.
- If the same improvement was *also* made in your vault by hand earlier
  (pre-dating the kit commit), the cherry-pick may be empty or conflict
  trivially — `--skip` it and log that the vault already had it.

## Done when

- [ ] Wanted upstream commits applied (cherry-picked or hand-applied), unwanted ones consciously skipped
- [ ] Personal content in populated files untouched
- [ ] Link map regenerated if needed; `lint.sh` green
- [ ] Adopted-baseline cache updated; pending-updates inbox note gone
- [ ] `SYSTEM/log.md` records the pull + the upstream SHA adopted

## Related

[[Sync an improvement to CNTXT1]] (the outward direction — manual on purpose) · [[SCHEMA]] § Privacy & content separation
