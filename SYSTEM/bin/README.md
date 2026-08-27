# SYSTEM/bin — KB tooling

One script, one job. Everything runs from any cwd (each script `cd`s to the
vault root itself). The two you'll touch most: `lint.sh` (run it after any
structural change) and `build-link-map.sh` (run it after adding/renaming any
concept, initiative, person, or skill).

| Script | Job |
| :-- | :-- |
| `lint.sh` | Deterministic KB health check (10 mechanical checks; exit 0 = green). Its check-1 variables are the **authoritative** root-exception + structural-folder lists. Interactive runs use this; scheduled runs use `lint-delta.sh`. |
| `lint-delta.sh` | Scheduled-run wrapper for `lint.sh` — alarms on the finding-count **delta**, not the total (a permanently-red check is an invisible check). State in `SYSTEM/.cache/` (gitignored). |
| `audit-initiative-next-actions.sh` | GTD next-action audit: every `status: active` initiative must carry ≥1 open `#action` (lint check 9). |
| `cap_check.py` | Script-measured digest word caps (`cap_config.json`; never by model estimate). Lint check 10. |
| `build-link-map.sh` | Regenerate `SYSTEM/link-map.md` — every `[[target]]` (slugs + `aliases:`) → file path. |
| `validate_frontmatter.py` | Pydantic validation of every note's frontmatter against `SYSTEM/schemas` (run via `uv run`). |
| `build_directory_indexes.py` | Regenerate the per-folder `index.md` tables from note frontmatter. |
| `build_skills_indexes.py` | Regenerate the per-TYPE `Knowledge/Skills/<TYPE>/<TYPE> Index.md` tables from skill frontmatter. |
| `active-initiatives.sh` | List every active initiative + its next open action. |
| `stale-initiatives.sh` | List active initiatives overdue for a check-in. |
| `aging-actions.sh` | List open `#action` checkboxes older than a threshold. |
| `rollup-daily-weeks.sh` | Archive past daily notes into weekly folders. |
| `sync-from-upstream.sh` | Preview-first puller of framework files from a fetch-only upstream kit remote. |
| `kb-mcp-server.py` | MCP server pointing Claude Desktop at the vault. |
| `excalidraw.py` | Excalidraw diagram helper (see the Create an Excalidraw skill). |
| `backfill-action-dates.sh` | One-time backfill of `#action` created dates — historical, keep for reference. |

Generated-output conventions for anything these scripts write:
`Knowledge/Skills/RULE/Maintain Generated Sections.md`.
