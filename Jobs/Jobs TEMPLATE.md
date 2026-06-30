---
type: job
domain:                   # dev | kb-meta | ops-comms | (your domain)
trigger:                  # the cue that starts this job (one line)
frequency:                # per-PR | weekly | ad-hoc | per-new-hire | …
tools:                    # CLIs / files / services used
owner: {{NAME}}
status: active            # active | draft
tags: [job]
aliases: []               # short forms so [[alias]] resolves
---

# Job — {Imperative Title}

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
{[[concept]] for the why/context · [[Person]]s involved · sibling [[Job — …]] runbooks.}

<!--
CONVENTIONS (delete in real jobs)
• Filename = imperative verb-first, Title Case With Spaces → "Create a pull request.md".
  Wikilink as [[Create a pull request]]. Job-note titles inside start with "Job — ".
• A Job is the SINGLE SOURCE OF TRUTH for the *steps* of a recurring task; the matching
  concept note keeps the *why/context/principles* and links here.
• Voice = agent-executable: imperative, tool-specific, no fluff.
• Index every job in concepts/jobs.md.
• Jobs/ is a STRUCTURAL folder, not the inbox (like People/, daily/).
-->
