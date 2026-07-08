# Contributing to CNTXT1

CNTXT1 is a **public template** for building a *private* personal knowledge
base. That split is the whole design, so one rule dominates every review:

> **This repo ships a framework — never content.** Nothing personal or
> instance-specific lands here: no real names, people notes, raw captures,
> daily notes, initiatives, logs, addresses, emails, IPs, or filled-in
> `{{placeholders}}`. The rulebook is `meta/AGENTS.md` § *Privacy & content
> separation*.

## What makes a good PR

Generic improvements to the method or its machinery:

- Schema clarifications in `meta/AGENTS.md`
- New or sharper `Jobs/` runbooks (with `owner: {{NAME}}`, indexed in
  `concepts/jobs.md`)
- `meta/bin/` tooling fixes (`lint.sh`, `build-link-map.sh`,
  `kb-mcp-server.py`)
- Template and setup-flow improvements (`setup.md`, the TEMPLATE files)
- Automation additions under `meta/optional/`

## Before you open a PR

1. **If your change was born in your own vault, re-template it** — swap your
   real values back to `{{placeholders}}`. The runbook you already have for
   this is `Jobs/Sync an improvement to CNTXT1.md`; run your own grep gate
   before pushing anything public.
2. Run the checks CI will run:
   ```
   ./meta/bin/lint.sh
   ./.github/scripts/pr-gate.sh
   ```
3. If you added or renamed a concept, person-template, or job: regenerate the
   link map (`./meta/bin/build-link-map.sh`) and commit it.

## What CI enforces

Every PR runs two layers:

- **`PR gate`** (deterministic, blocking): instance-content folders hold only
  their shipped templates/examples, placeholders stay intact, no PII or
  credential patterns, jobs indexed, link map current, KB lint green.
- **`Claude review`** (judgment layer): an automated reviewer checks that the
  change is framework-generic rather than personal, conforms to the schema in
  `meta/AGENTS.md`, and keeps the docs coherent. It runs automatically on
  same-repo PRs; for fork PRs a maintainer triggers it after a first look.

A privacy finding always blocks. If you're unsure whether something counts as
personal — it does; keep it in your vault and send the generic version here.
