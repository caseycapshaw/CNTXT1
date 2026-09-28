# SYSTEM/bin — KB tooling

One script, one job. Everything runs from any cwd (each script `cd`s to the
vault root itself). The two you'll touch most: `lint.sh` (run it after any
structural change) and `build-link-map.sh` (run it after adding/renaming any
concept, project, person, or skill).

| Script | Job |
| :-- | :-- |
| `regen-all.sh` | Run every generator the kit ships, in order, fail-loud (link map, `.claude` mirrors, index sections, contacts + horizon views, directory + skills indexes, action census if opted in). **Run it before `lint.sh`** — most red is a stale generated view. |
| `lint.sh` | Deterministic KB health check (mechanical checks, numbered in its header; exit 0 = green). Its check-1 variables are the **authoritative** root-exception + structural-folder lists. Stale generated views and word-cap overruns are **WARN** (fix: `regen-all.sh`); `LINT_STRICT=1` FAILs them (CI). Interactive runs use this; scheduled runs use `lint-delta.sh`. |
| `lint-delta.sh` | Scheduled-run wrapper for `lint.sh` — alarms on the finding-count **delta**, not the total (a permanently-red check is an invisible check). State in `SYSTEM/.cache/` (gitignored). |
| `kb-folders.json` / `kb-folders.sh` | **Single source of the numbered content-folder names** (`00 daily` … `05 concepts`) — scripts read the JSON (Python) or source the `.sh` (shell, also carries `extract_aliases`). Rename a folder here first, then in the prose that mirrors it. |
| `audit-project-next-actions.sh` | GTD next-action audit: every `status: active` project must carry ≥1 open `#action` (lint check 10). |
| `audit-area-reviews.sh` | GTD review-cadence audit: every area/horizon's `reviewed:` is within its `review:` window (lint check 12, WARN-only). |
| `cap_check.py` | Script-measured word caps (`cap_config.json`; never by model estimate): registered role digests + `## Now & next` / `## Milestones` sections of projects and areas. Lint check 11. |
| `cap_overflow.py` | Mechanical remedy for an over-cap `## Milestones`: moves the oldest bullets verbatim into `03 Projects/trails/<slug>-trail.md` (areas: `02 Areas/trails/`) and leaves a pointer. Dry-run by default; `--write` applies. |
| `actions.py` | Action census — counts, `#priority` list, per-home totals, **stale** (`➕` stamp > 30d) and **unknown-age** (no stamp) lists. Opt in by adding `<!-- actions:auto:start -->` / `<!-- actions:auto:end -->` to `Actions.md`, then `--write`. |
| `kb_stats.py` | The KB's own telemetry: boot cost, section-cap overruns, action counts, log growth, orphan raw captures, lint time. Stdout report; `--write` appends a trend line to `SYSTEM/stats/` and writes `SYSTEM/kb-stats.md` (generated). |
| `rotate_log.sh` | Keep `SYSTEM/log.md` to the current month; older months move verbatim to `SYSTEM/log/YYYY-MM.md`. Idempotent; `--dry-run` previews. |
| `build-link-map.sh` | Regenerate `SYSTEM/link-map.md` — every `[[target]]` (slugs + `aliases:`, inline or block-list form) → file path; fails on duplicate keys. |
| `validate_frontmatter.py` | Pydantic validation of every note's frontmatter against `SYSTEM/schemas` (run via `uv run`). |
| `build_directory_indexes.py` | Regenerate the per-folder `index.md` tables from note frontmatter, with a `_Generated:` freshness stamp. `--write` applies; default/`--check` reports drift (stamp-insensitive). |
| `build_skills_indexes.py` | Regenerate the per-TYPE `Skills/<TYPE>/<TYPE> Index.md` tables from skill frontmatter. |
| `active-projects.sh` | List every active project + its next open action. |
| `stale-projects.sh` | List active projects overdue for a check-in. |
| `migrate-to-numbered-layout.sh` | One-shot helper for the `Knowledge/…` → numbered-layout move (dry run by default; `--apply` moves, rewrites paths, flips `initiative` → `project`). See `MIGRATING.md`. |
| `aging-actions.sh` | List open `#action` checkboxes older than a threshold — exact age from the `➕` stamp, `~` git-log estimates for unstamped ones (tallied apart as *unknown age*). |
| `rollup-daily-weeks.sh` | Archive past daily notes into weekly folders. |
| `sync-from-upstream.sh` | Preview-first puller of framework files from a fetch-only upstream kit remote. `--reconcile` drains the pending-updates queue: commits you authored (by `git config user.email` or patch-id) are marked applied. |
| `kb-mcp-server.py` | MCP server pointing Claude Desktop at the vault. |
| `excalidraw.py` | Excalidraw diagram helper (see the Create an Excalidraw skill). |
| `backfill-action-dates.sh` | One-time backfill of `#action` created (`➕`) dates from git history; dry-run by default, aborts on squashed history. |

Scripts that touch content folders read the folder names from `kb-folders.json` / `kb-folders.sh` — never hard-code them.

Generated-output conventions for anything these scripts write:
`Skills/RULE/Maintain Generated Sections.md`.
