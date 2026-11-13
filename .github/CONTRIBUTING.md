# Contributing to CNTXT1

CNTXT1 is a **public template** for building a *private* personal knowledge
base. That split is the whole design, so one rule dominates every review:

> **This repo ships a framework — never content.** Nothing personal or
> instance-specific lands here: no real names, people notes, raw captures,
> daily notes, projects, logs, addresses, emails, IPs, or filled-in
> `{{placeholders}}`. The rulebook is `SYSTEM/SCHEMA.md` § *Privacy & content
> separation*.

## What makes a good PR

Generic improvements to the method or its machinery:

- Schema clarifications in `SYSTEM/SCHEMA.md`
- New or sharper `Skills/` skills (with `owner: {{NAME}}`, indexed in
  `05 concepts/skills.md`)
- `SYSTEM/bin/` tooling fixes (`lint.sh`, `build-link-map.sh`,
  `kb-mcp-server.py`)
- Template and setup-flow improvements (`setup.md`, the TEMPLATE files)
- Automation additions under `SYSTEM/optional/`

## Before you open a PR

1. **If your change was born in your own vault, re-template it** — swap your
   real values back to `{{placeholders}}`. The skill you already have for
   this is `Skills/DO/Sync an Improvement to CNTXT1.md`; run your own grep gate
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
5. Review the staged diff against the *Review checklist* below (or have an
   agent with no other context do it) and fix anything short of PASS.

## What CI enforces

- **`PR gate`** (deterministic, blocking, runs on every PR and every push to
  `main`; its job `gate` is the required check): instance-content folders hold
  only their shipped templates/examples, placeholders stay intact, no PII or
  credential patterns, skills indexed in `05 concepts/skills.md` **and** in
  their `<TYPE> Index.md`, link map + generated directory/skills indexes
  byte-identical to a fresh regen, frontmatter valid against the
  `SYSTEM/schemas/` Pydantic models, KB lint green. It holds no secrets.
- **`Identifier sweep`** (maintainer only, after merge): on every push to
  `main` the maintainer's private identifier list is grepped against the
  tree by `.github/scripts/identifier-sweep.sh`. It never runs on a pull
  request, and its public log shows only how many files matched (run it
  locally to see which). The `gate` job self-tests the script with synthetic
  patterns on every PR.

Judgment is not in CI: every change is reviewed against the checklist below
before it is pushed (see *Review checklist*).

A privacy finding always blocks. If you're unsure whether something counts as
personal — it does; keep it in your vault and send the generic version here.

## Review checklist

Apply this to the staged diff before anything is pushed, as a reviewing agent
or a person. The kit's sync runbook (`Skills/DO/Sync an Improvement to
CNTXT1.md`) has a fresh subagent run it and waits on the verdict; a
maintainer reviews someone else's pull request the same way.

CNTXT1 is a **public** template for private personal knowledge bases. It ships
a framework (schema, templates, runbooks, scripts) and must contain **zero**
personal or instance-specific content. Read `SYSTEM/SCHEMA.md` § *Privacy &
content separation* first. Then check the diff for, in priority order:

1. **Privacy (blocking):** any content that looks personal or
   instance-specific rather than framework-generic — real names,
   family/household details, employers, addresses, emails, IPs, device/host
   names, populated content under `00 daily/`, `01 Horizons/`, `02 Areas/`,
   `03 Projects/`, `04 People/`, `raw/`, `attachments/`, an `owner:` field
   with a real name, placeholders (`{{NAME}}`, `{{PERSONAL_IDENTIFIERS}}`,
   etc.) replaced with real values, or personal specifics leaking through
   examples. The deterministic gate catches known patterns; the review
   catches what patterns miss. When in doubt, it's personal: flag it.
2. **Schema consistency:** the change conforms to `SYSTEM/SCHEMA.md`. Skills
   are edited in canonical `.claude/skills/<slug>/SKILL.md` with
   `owner: {{NAME}}`, their `Skills/<TYPE>/` mirror regenerated and indexed
   in `05 concepts/skills.md`; concepts carry frontmatter
   (type/description/updated/status/tags); projects carry an `area:` up-link,
   areas a review cadence; the link map is regenerated when link targets
   change; `index.md` stays a pure map (no change history); the root gains no
   new permanent files; wikilinks resolve; dates are `YYYY-MM-DD`.
3. **Doc coherence:** `setup.md`, `README.md`, `CLAUDE.md` and `AGENTS.md`
   still tell the same story (counts, paths, folder tables, phase
   instructions).

Return a verdict that starts with `VERDICT: PASS`, `VERDICT: PRIVACY BLOCK` or
`VERDICT: ISSUES`, then the findings, each anchored to a file and line. For a
privacy finding quote the smallest identifying snippet possible; do not
amplify personal data. Be concise and actionable. Nothing is pushed until the
verdict is PASS.

## For maintainers: the repo settings this CI assumes

The workflows are only half of the protection; two GitHub settings carry the
rest. A maintainer of a copy that runs the identifier sweep applies both
(and puts their own handle in `.github/CODEOWNERS` and their own slug in
`.github/workflows/identifier-sweep.yml`):

- **Environment `maintainer-secrets`** holds the secret `PERSONAL_IDENTIFIERS`
  (your private list joined with `|`). Deployment branches: selected, one
  rule, `main`. No required reviewer: the branch rule is the lock, so a
  pull-request run or a dispatch from another branch never gets the secret.
- **Branch protection on `main`:** require the `gate` status check; require a
  pull request before merging with **0** required approvals, **code-owner
  review required**, and stale approvals dismissed on a new push. Pull
  requests that touch nothing under `.github/` merge on a green `gate`;
  changes under `.github/` need the code owner. The owner merges their own
  `.github/` changes, and Dependabot's, with the admin bypass after reading
  the diff, pinned to the commit that was read:
  `gh pr merge <n> --admin --match-head-commit <reviewed SHA>`. Anyone with
  write access can push onto an open pull request branch after it was read.

Three traps when setting this up or changing it later:

- **Branch rule, not tag rule.** The environment's deployment rule must be of
  type *branch* (`main`); branch and tag rules are separate lists.
- **Old runs can be re-run.** Runs on the default branch can be re-run for 30
  days with the workflow version they started with. If an older workflow used
  an environment behind a required reviewer, don't just remove that reviewer:
  use a fresh environment name, or delete those old runs first.
- **Retire credentials at the source.** When CI stops using a token, revoke it
  where it was issued, not only the GitHub secret.

## License of contributions

By submitting a pull request you agree that your contribution is licensed
under the [MIT License](../LICENSE), the same as the rest of the project
(the standard "inbound = outbound" rule).

## Adding framework files under the numbered content folders

`00 daily/`, `01 Horizons/`, `02 Areas/`, `03 Projects/`, `04 People/`,
`05 concepts/`, `raw/`, `attachments/`, `excalidraw/` (and the generated `Skills/` /
`Agents/` mirrors) are **user territory** — `.gitignore` ignores every user note
there so people using the repo directly can never commit personal content by
accident; negation patterns keep the shipped scaffolding (templates, generated
indexes, `.gitkeep` placeholders, example/stub notes) tracked. If your contribution
adds a NEW framework file those patterns would ignore (a new shipped concept, a new
skill/agent mirror), add a matching `!` negation where it is a template/scaffold, or
stage it with `git add -f <path>`. The whole-tree gate `.github/scripts/pr-gate.sh`
(`check_only`) is the enforcement: keep its allowed-file lists in step.
Skill/agent content changes go in the canonical `.claude/skills/` / `.claude/agents/`
files — the visible mirrors are generated (`uv run python
SYSTEM/bin/build_claude_mirrors.py`); CI reds if they drift.
