---
name: {kebab-slug}        # the folder name: Skills/<kebab-slug>/SKILL.md
description:              # one sentence: what it does + when to use it
type: skill
domain:                   # dev | kb-meta | ops-comms | (your domain)
tools:                    # CLIs / files / services used
owner: {{NAME}}
status: active            # active | draft
tags: [skill]
aliases: [{Imperative Title}]   # first entry = the human imperative title; more short forms so [[alias]] resolves
updated: {YYYY-MM-DD}
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
{[[concept]] for the why/context · [[Person]]s involved · sibling [[Skill — …]] skills.}

<!--
CONVENTIONS (delete in real skills)
• Filename = Skills/<kebab-slug>/SKILL.md, e.g. "Skills/create-a-pull-request/SKILL.md".
  `name:` = that slug. First alias = the human imperative title, Title Case With Spaces
  ("Create a pull request") — wikilink as [[Create a pull request]]. Skill H1 starts "# Skill — ".
• A Skill is the SINGLE SOURCE OF TRUTH for the *steps* of a recurring task; the matching
  concept note keeps the *why/context/principles* and links here.
• Voice = agent-executable: imperative, tool-specific, no fluff.
• Index every skill in concepts/skills.md.
• Skills/ is a STRUCTURAL folder, not the inbox (like People/, daily/) — each SKILL.md is
  symlinked from .claude/skills/<slug> so it's invocable as a slash-skill
  (`ln -sfn ../../Skills/<slug> .claude/skills/<slug>`).
-->
