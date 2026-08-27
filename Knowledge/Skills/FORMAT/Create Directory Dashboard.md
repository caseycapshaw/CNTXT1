---
type: format
domain: kb-meta
trigger: a Knowledge/ folder needs a live, filterable frontmatter table viewable in Obsidian
frequency: ad-hoc
tools: ["Obsidian Bases (core plugin)", "Read", "Write"]
owner: "{{NAME}}"
status: active
tags: [format, kb-meta]
aliases: ["Create a directory dashboard", "Directory dashboard", "Create a Bases dashboard", "create-directory-dashboard"]
summary: Produces an Obsidian Bases `.base` dashboard file that renders a live, filterable frontmatter table for one Knowledge/ folder.
author_type: script
---

> _Generated from `.claude/skills/create-directory-dashboard/SKILL.md` by `SYSTEM/bin/build_claude_mirrors.py` — edit the canonical file, never this mirror. Generated: 2026-08-27_

# Skill — Create Directory Dashboard

> **When:** a `Knowledge/` folder (Concepts, Initiatives, People, Agents, a
> Skills type…) would benefit from a live, sortable frontmatter table inside
> Obsidian · **Frequency:** ad-hoc, once per folder
> **Outcome:** a `<Folder>-Dashboard.base` file in the target folder that
> Obsidian's **Bases** core plugin renders as a filterable table of every
> note's frontmatter — complementing (not replacing) the generated `index.md`.

## When to run this

The generated `index.md` in each folder (from
`SYSTEM/bin/build_directory_indexes.py`) is a static snapshot an *agent* can
read cheaply. A `.base` dashboard is the *human*-facing equivalent: Obsidian
renders it live from current frontmatter, so it never goes stale and supports
interactive sorting/filtering. Add one when you find yourself browsing a
folder in Obsidian and wanting to sort or filter by frontmatter fields.

## Steps

1. **Confirm the plugin.** Bases is a core Obsidian plugin (v1.7+). In
   Obsidian: Settings → Core plugins → enable **Bases**. No community plugin
   needed.
2. **Pick the columns.** Open the folder's schema class in
   `SYSTEM/schemas/base_models.py` (or `models.py` for Agents) and choose the
   fields worth a column. Always lead with `file.name`; then the fields a
   human actually scans — e.g. for Concepts: `type`, `status`, `updated`,
   `tags`, `resource`; for Initiatives: `type`, `status`, `updated`, `tags`;
   for Agents: `description`, `model`, `status`, `tags`.
3. **Write the `.base` file** at `Knowledge/<Folder>/<Folder>-Dashboard.base`.
   The canonical shape — a folder-scoped filter plus one table view — is the
   existing `Knowledge/Concepts/Concepts-Dashboard.base`:

   ```yaml
   filters:
     and:
       - file.inFolder(this.file.folder)
       - file.ext == "md"
   views:
     - type: table
       name: Frontmatter
       order:
         - file.name
         - type
         - status
         - updated
         - tags
         - resource
   ```

   Copy it, rename, and swap the `order:` list for the columns you picked in
   step 2. The `file.inFolder(this.file.folder)` filter is self-relative —
   the file scopes itself to whatever folder it lives in, so no path needs
   hardcoding.
4. **Exclude non-note files if needed.** If the folder holds TEMPLATE files
   or a generated `index.md` you'd rather hide, extend the filter, e.g.:

   ```yaml
       - '!file.name.contains("TEMPLATE")'
       - file.name != "index"
   ```

5. **Verify in Obsidian.** Open the `.base` file — it should render as a
   table with one row per note and your chosen columns populated from
   frontmatter. A blank column usually means a field-name typo (columns are
   frontmatter keys, verbatim).
6. **Book-keep.** `.base` files are config, not notes — they carry no
   frontmatter and are ignored by `validate_frontmatter.py`, the link map,
   and the directory-index generators. Just append one line to
   `SYSTEM/log.md`.

## Related

- `Knowledge/Concepts/Concepts-Dashboard.base` — the reference instance.
- `SYSTEM/bin/build_directory_indexes.py` — the agent-facing static
  counterpart.
- [[karpathy-method]] — why folder-scoped orientation surfaces matter.
