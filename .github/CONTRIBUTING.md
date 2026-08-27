# Contributing to CNTXT1

CNTXT1 is a **public template** for building a *private* personal knowledge
base. That split is the whole design, so one rule dominates every review:

> **This repo ships a framework — never content.** Nothing personal or
> instance-specific lands here: no real names, people notes, raw captures,
> daily notes, initiatives, logs, addresses, emails, IPs, or filled-in
> `{{placeholders}}`. The rulebook is `SYSTEM/SCHEMA.md` § *Privacy & content
> separation*.

## What makes a good PR

Generic improvements to the method or its machinery:

- Schema clarifications in `SYSTEM/SCHEMA.md`
- New or sharper `Knowledge/Skills/` skills (with `owner: {{NAME}}`, indexed in
  `Knowledge/Concepts/skills.md`)
- `SYSTEM/bin/` tooling fixes (`lint.sh`, `build-link-map.sh`,
  `kb-mcp-server.py`)
- Template and setup-flow improvements (`setup.md`, the TEMPLATE files)
- Automation additions under `SYSTEM/optional/`

## Before you open a PR

1. **If your change was born in your own vault, re-template it** — swap your
   real values back to `{{placeholders}}`. The skill you already have for
   this is `Knowledge/Skills/DO/Sync an Improvement to CNTXT1.md`; run your own grep gate
   before pushing anything public.
2. Run the checks CI will run:
   ```
   ./SYSTEM/bin/lint.sh
   ./.github/scripts/pr-gate.sh
   ```
3. If you added or renamed a concept, person-template, agent, or skill:
   regenerate the link map and the generated indexes, and commit them:
   ```
   ./SYSTEM/bin/build-link-map.sh
   uv run python SYSTEM/bin/build_directory_indexes.py
   uv run python SYSTEM/bin/build_skills_indexes.py
   ```
4. New/changed frontmatter must validate against the Pydantic schemas in
   `SYSTEM/schemas/` (`uv run python SYSTEM/bin/validate_frontmatter.py`).

## What CI enforces

Every PR runs two layers:

- **`PR gate`** (deterministic, blocking): instance-content folders hold only
  their shipped templates/examples, placeholders stay intact, no PII or
  credential patterns, skills indexed in `Knowledge/Concepts/skills.md` **and**
  in their `<TYPE> Index.md`, link map + generated directory/skills indexes
  byte-identical to a fresh regen, frontmatter valid against the
  `SYSTEM/schemas/` Pydantic models, KB lint green.
- **`Claude review`** (judgment layer): an automated reviewer checks that the
  change is framework-generic rather than personal, conforms to the schema in
  `SYSTEM/SCHEMA.md`, and keeps the docs coherent. It runs automatically on
  same-repo PRs; for fork PRs a maintainer triggers it after a first look.

A privacy finding always blocks. If you're unsure whether something counts as
personal — it does; keep it in your vault and send the generic version here.

## License of contributions

By submitting a pull request you agree that your contribution is licensed
under the [MIT License](../LICENSE), the same as the rest of the project
(the standard "inbound = outbound" rule).

## Adding framework files under `Knowledge/` (or `daily/`, `attachments/`)

Those paths are **user territory** — `.gitignore` ignores everything new there so
people using the repo directly can never commit personal content by accident. The
shipped skeleton (templates, indexes, generated `Knowledge/Skills`/`Knowledge/Agents`
mirrors) predates the rule and stays tracked. If your contribution adds a NEW
framework file under those paths, stage it explicitly with `git add -f <path>`.
Skill/agent content changes go in the canonical `.claude/skills/` / `.claude/agents/`
files — the visible mirrors are generated (`uv run python
SYSTEM/bin/build_claude_mirrors.py`); CI reds if they drift.
