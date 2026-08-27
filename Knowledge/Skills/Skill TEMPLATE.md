---
type: do                  # do | check | format | rule — must match the folder (DO/CHECK/FORMAT/RULE)
domain:                   # dev | kb-meta | ops-comms | (your domain)
trigger:                  # the cue that fires this skill, in one clause
frequency:                # ad-hoc | daily | weekly | monthly | once | …
tools: []                 # CLIs / files / services used, as a list
owner: "{{NAME}}"
status: active            # active | draft | superseded
tags: [do]                # first tag = the type; add the domain
aliases: ["{Imperative Title}"]   # short forms so [[alias]] resolves
summary:                  # one sentence: what it does — feeds the generated <TYPE> Index.md row
---

# Skill — {Imperative Title}

> **When:** {the trigger cue} · **Frequency:** {…} · **Tools:** {…}
> **Outcome:** {what "done" looks like — and where the output lands}

## When to run this
{The cue + preconditions. 1–3 lines. If there's a decision ("which path am I in?"), state it here.}

## Steps
{Imperative and executable — written so an agent OR you can follow them. Name the exact
tool / CLI command / file path. Number them; nest sub-steps where there's a branch.}
1. …
2. …

## Gotchas / rules
{The non-obvious constraints that make this job fail if missed — the reason this runbook exists.}
- …

## Done when
- [ ] {acceptance checks — what proves the job is actually complete}

## Related
{[[concept]] for the why/context · [[Person]]s involved · sibling [[Skill]]s.}

<!--
CONVENTIONS (delete in real skills)
• Filename = Knowledge/Skills/<TYPE>/<Imperative Title>.md, Title Case With Spaces —
  e.g. "Knowledge/Skills/DO/Create a Pull Request.md". Wikilink as [[Create a Pull Request]].
  Skill H1 starts "# Skill — ".
• TYPE taxonomy: DO = performs a recurring task · CHECK = verifies/audits something ·
  FORMAT = produces/structures an artifact · RULE = a standing convention/policy.
  The frontmatter `type:` (lowercase) must match the folder.
• A Skill is the SINGLE SOURCE OF TRUTH for the *steps* of a recurring task; the matching
  concept note keeps the *why/context/principles* and links here.
• Voice = agent-executable: imperative, tool-specific, no fluff.
• `summary:` is what index tables show — one stable sentence, no trailing "use when …".
• CANONICAL HOME (standard Claude/Grok configuration, 2026-08-27): author the skill
  at .claude/skills/<kebab-slug>/SKILL.md — top-level `name:` + `description:` (the
  "Use when…" trigger text), then this template's org-schema keys indented under
  `metadata:` plus `metadata.title:` (the Imperative Title). Claude Code, Grok
  Build, and other SKILL.md-standard agents auto-discover it there.
• The visible Knowledge/Skills/<TYPE>/<Imperative Title>.md note is a GENERATED
  MIRROR — never write it by hand. After adding/renaming a skill run:
  uv run python SYSTEM/bin/build_claude_mirrors.py && uv run python
  SYSTEM/bin/build_skills_indexes.py && SYSTEM/bin/build-link-map.sh
• Index every skill in Knowledge/Concepts/skills.md.
• Knowledge/Skills/ is a STRUCTURAL folder, not the inbox (like Knowledge/People/, daily/).
-->
