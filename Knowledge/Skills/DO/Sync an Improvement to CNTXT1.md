---
type: do
domain: kb-meta
trigger: a generic improvement is ready to share publicly
frequency: ad-hoc
tools: ["Read", "Write", "Edit", "git", "grep"]
owner: "{{NAME}}"
status: active
tags: [do, kb-meta]
aliases: ["Sync an improvement to CNTXT1", "Sync a KB improvement to the shared repo", "Contribute to CNTXT1", "sync-an-improvement-to-cntxt1"]
summary: Lands a generic schema/tooling/template improvement from this private KB into the public CNTXT1 starter kit's own repo, fully re-templated with zero personal content.
author_type: script
---

> _Generated from `.claude/skills/sync-an-improvement-to-cntxt1/SKILL.md` by `SYSTEM/bin/build_claude_mirrors.py` — edit the canonical file, never this mirror. Generated: 2026-08-27_

# Skill — Sync an Improvement to CNTXT1

> **When:** a change to schema/tooling/templates in this private vault is
> worth sharing with the public **CNTXT1** starter kit ·
> **Frequency:** ad-hoc · **Tools:** git, Read/Write/Edit, grep
> **Outcome:** the improvement lands in a CNTXT1 working tree fully
> re-templated, with zero personal content — committed *there*, never in this
> vault's history — then pushed to your public copy and/or PR'd upstream to
> [caseycapshaw/CNTXT1](https://github.com/caseycapshaw/CNTXT1).

## Why this skill exists (the privacy rule)

**Personal content never leaves this vault** — see `SYSTEM/SCHEMA.md` § Privacy
& content separation. This runbook is the *only* sanctioned outward path, and
it is deliberately manual: two independent folders, hand-copy, re-template,
grep gate. No export script, no shared git history, no public remote on this
vault — ever.

## When to run this

Whenever a change made in *this* private vault is generic enough to help
anyone running the CNTXT1 method — a schema tweak in `SYSTEM/SCHEMA.md`, a
new/improved `Knowledge/Skills/` skill, a `SYSTEM/bin/` script fix, a template change.

> **Prefer upstream-first.** If the improvement *isn't already implemented
> in your vault*, don't build it privately and then run this runbook —
> author it directly in your clone of the public kit (through its CI gates)
> and bring it into your vault with [[Pull framework updates from CNTXT1]].
> This runbook is the exception path: improvements discovered while they're
> already implemented in the vault.

**Precondition:** a local working tree of CNTXT1 (e.g. `~/dev/CNTXT1`) with
its **own independent git history** — clone your fork of
[caseycapshaw/CNTXT1](https://github.com/caseycapshaw/CNTXT1) (or the repo
itself if you have push access). It must NOT be a subdirectory, branch, or
remote of this vault.

## Steps

1. **Classify the changed file(s):**
   - **Copy verbatim** (no personal content ever lives here): `setup.md`,
     `SYSTEM/SCHEMA.md`, `SYSTEM/bin/*` scripts, `Knowledge/Concepts/karpathy-method.md`,
     `Knowledge/Skills/Skill TEMPLATE.md`, `Knowledge/People/People TEMPLATE.md`,
     `Knowledge/Initiatives/Initiative TEMPLATE.md`, `SYSTEM/optional/automation/*`
     (already parameterized with `{{VAULT}}` / `{{NAME}}`).
   - **Copy after checking frontmatter:** other `Knowledge/Skills/<TYPE>/*.md`
     skills — the `owner:` field must read `{{NAME}}`, not a real name, in
     the public copy; strip any personal examples from the body.
   - **Copy only the skeleton, re-templated** — never the live rows/content:
     `CLAUDE.md`, `index.md`, `README.md`, `Knowledge/Concepts/contacts.md`,
     `Knowledge/Concepts/skills.md`. Diff for what changed *structurally* (a new
     convention, a new section) and hand-apply just that structural change to
     the kit's own templated version — don't paste this vault's populated
     version over it.
   - **Never copy:** anything in `Knowledge/People/` (except the template), personal
     concepts and initiatives, `Knowledge/raw/`, `daily/`, `Actions.md`, `SYSTEM/log.md`,
     `SYSTEM/Journal.md`, `SYSTEM/link-map.md`, `.claude/`, `.obsidian/`. These
     are personal by definition or specific to this instance.
2. **Apply the change** in the CNTXT1 working tree — write/edit the file
   there directly (don't `cp` blindly; re-templating is part of this step).
3. **Grep gate** — from the CNTXT1 folder, search for your personal
   identifiers before committing:
   ```
   grep -rniE "{{PERSONAL_IDENTIFIERS}}" . --exclude-dir=.git --exclude=LICENSE
   ```
   `{{PERSONAL_IDENTIFIERS}}` is your own `|`-separated list — full name,
   family members, employer, email domains, home IPs, street/project names —
   filled in during setup and **extended whenever a new personal specific
   shows up in this vault**. Any hit is a leak — fix it before proceeding.
4. **Commit inside the CNTXT1 working tree** (its own repo, its own history),
   push to your fork/copy, and — if the improvement is generic enough for
   everyone — open a PR upstream to
   [caseycapshaw/CNTXT1](https://github.com/caseycapshaw/CNTXT1).

## Gotchas / rules

- **Never `git remote add` the public repo to this private vault**, and never
  push a branch of this vault anywhere public — the two must stay two
  independent working trees on purpose.
- The grep-gate identifier list is not exhaustive by construction — treat it
  as a backstop, not a substitute for actually **reading the full diff**
  before committing publicly.
- When in doubt whether something is generic or personal, it's personal — it
  stays in the vault.

## Done when

- [ ] The change is applied in the CNTXT1 working tree, re-templated (no real values, only `{{placeholders}}` where this vault has real content)
- [ ] The grep gate passes clean **and** the full diff has been read
- [ ] Committed and pushed in CNTXT1's own repo (PR'd upstream if broadly useful)

## Related

`SYSTEM/SCHEMA.md` § Privacy & content separation (the rule) · [[karpathy-method]] · [[SCHEMA]]
