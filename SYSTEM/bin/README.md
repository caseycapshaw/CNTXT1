# SYSTEM/bin — KB tooling

One script, one job. Everything runs from any cwd (each script `cd`s to the
vault root itself). The two you'll touch most: `lint.sh` (run it after any
structural change) and `build-link-map.sh` (run it after adding/renaming any
concept, initiative, person, or skill).

| Script | Job |
| :-- | :-- |
| `regen-all.sh` | Run every generator the kit ships, in order, fail-loud (link map, `.claude` mirrors, directory + skills indexes, action census if opted in). **Run it before `lint.sh`** — most red is a stale generated view. |
| `lint.sh` | Deterministic KB health check (10 mechanical checks; exit 0 = green). Its check-1 variables are the **authoritative** root-exception + structural-folder lists. Stale generated views and word-cap overruns are **WARN** (fix: `regen-all.sh`); `LINT_STRICT=1` FAILs them (CI). Interactive runs use this; scheduled runs use `lint-delta.sh`. |
| `lint-delta.sh` | Scheduled-run wrapper for `lint.sh` — alarms on the finding-count **delta**, not the total (a permanently-red check is an invisible check). State in `SYSTEM/.cache/` (gitignored). |
| `audit-initiative-next-actions.sh` | GTD next-action audit: every `status: active` initiative must carry ≥1 open `#action` (lint check 9). |
| `cap_check.py` | Script-measured word caps (`cap_config.json`; never by model estimate): registered role digests + `## Now & next` / `## Milestones` sections of initiatives. Lint check 10. |
| `cap_overflow.py` | Mechanical remedy for an over-cap `## Milestones`: moves the oldest bullets verbatim into `Knowledge/Initiatives/trails/<slug>-trail.md` and leaves a pointer. Dry-run by default; `--write` applies. |
| `actions.py` | Action census — counts, `#priority` list, per-home totals, **stale** (`➕` stamp > 30d) and **unknown-age** (no stamp) lists. Opt in by adding `<!-- actions:auto:start -->` / `<!-- actions:auto:end -->` to `Actions.md`, then `--write`. |
| `kb_stats.py` | The KB's own telemetry: boot cost, section-cap overruns, action counts, log growth, orphan raw captures, lint time. Stdout report; `--write` appends a trend line to `SYSTEM/stats/` and writes `SYSTEM/kb-stats.md` (generated). |
| `rotate_log.sh` | Keep `SYSTEM/log.md` to the current month; older months move verbatim to `SYSTEM/log/YYYY-MM.md`. Idempotent; `--dry-run` previews. |
| `build-link-map.sh` | Regenerate `SYSTEM/link-map.md` — every `[[target]]` (slugs + `aliases:`, inline or block-list form) → file path; fails on duplicate keys. |
| `validate_frontmatter.py` | Pydantic validation of every note's frontmatter against `SYSTEM/schemas` (run via `uv run`). |
| `build_directory_indexes.py` | Regenerate the per-folder `index.md` tables from note frontmatter. |
| `build_skills_indexes.py` | Regenerate the per-TYPE `Knowledge/Skills/<TYPE>/<TYPE> Index.md` tables from skill frontmatter. |
| `active-initiatives.sh` | List every active initiative + its next open action. |
| `stale-initiatives.sh` | List active initiatives overdue for a check-in. |
| `aging-actions.sh` | List open `#action` checkboxes older than a threshold — exact age from the `➕` stamp, `~` git-log estimates for unstamped ones (tallied apart as *unknown age*). |
| `rollup-daily-weeks.sh` | Archive past daily notes into weekly folders. |
| `sync-from-upstream.sh` | Preview-first puller of framework files from a fetch-only upstream kit remote. `--reconcile` drains the pending-updates queue: commits you authored (by `git config user.email` or patch-id) are marked applied. |
| `kb-mcp-server.py` | MCP server pointing Claude Desktop at the vault. |
| `excalidraw.py` | Excalidraw diagram helper (see the Create an Excalidraw skill). |
| `backfill-action-dates.sh` | One-time backfill of `#action` created (`➕`) dates from git history; dry-run by default, aborts on squashed history. |

Scripts that touch content folders define the folder names in a `CONFIG` block at the top (default: the starter's `Knowledge/…` layout) — edit there if your instance renames them.

Generated-output conventions for anything these scripts write:
`Knowledge/Skills/RULE/Maintain Generated Sections.md`.
