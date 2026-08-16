# SYSTEM/bin — KB tooling

One script, one job. Everything runs from any cwd (each script `cd`s to the
vault root itself). The two you'll touch most: `lint.sh` (run it after any
structural change) and `build-link-map.sh` (run it after adding/renaming any
concept, initiative, person, or skill).

| Script | Job |
| :-- | :-- |
| `lint.sh` | Deterministic KB health check (exit 0 = green). Its check-1 variables are the **authoritative** root-exception + structural-folder lists. |
| `build-link-map.sh` | Regenerate `SYSTEM/link-map.md` — every `[[target]]` (slugs + `aliases:`) → file path. |
| `validate_frontmatter.py` | Pydantic validation of every note's frontmatter against `SYSTEM/schemas` (run via `uv run`). |
| `build_directory_indexes.py` | Regenerate the per-folder `index.md` tables from note frontmatter. |
| `build_skills_indexes.py` | Regenerate the per-TYPE `CONTENT/Skills/<TYPE>/<TYPE> Index.md` tables from skill frontmatter. |
| `active-initiatives.sh` | List every active initiative + its next open action. |
| `stale-initiatives.sh` | List active initiatives overdue for a check-in. |
| `aging-actions.sh` | List open `#action` checkboxes older than a threshold. |
| `rollup-daily-weeks.sh` | Archive past daily notes into weekly folders. |
| `sync-from-upstream.sh` | Preview-first puller of framework files from a fetch-only upstream kit remote. |
| `kb-mcp-server.py` | MCP server pointing Claude Desktop at the vault. |
| `excalidraw.py` | Excalidraw diagram helper (see the Create an Excalidraw skill). |
| `backfill-action-dates.sh` | One-time backfill of `#action` created dates — historical, keep for reference. |

Generated-output conventions for anything these scripts write:
`CONTENT/Skills/RULE/Maintain Generated Sections.md`.
