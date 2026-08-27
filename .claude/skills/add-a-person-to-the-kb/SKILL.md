---
name: add-a-person-to-the-kb
description: Creates a Knowledge/People/ note (and indexes it in Knowledge/Concepts/contacts.md) for a new person relevant to your work. Use when a new person appears who is relevant to your work.
metadata:
  title: Add a Person to the KB
  type: do
  domain: kb-meta
  trigger: a new person appears who is relevant to your work
  frequency: ad-hoc
  tools: ["Read", "Write", "Edit"]
  owner: "{{NAME}}"
  status: active
  tags: [do, kb-meta]
  aliases: ["Add a person to the KB", "add-a-person-to-the-kb"]
  summary: Creates a Knowledge/People/ note (and indexes it in Knowledge/Concepts/contacts.md) for a new person relevant to your work.
---


# Skill — Add a person to the KB

> **When:** a new person enters the picture — a collaborator, stakeholder, or contact
> **Outcome:** a note in `Knowledge/People/` + a row in `Knowledge/Concepts/contacts.md`

## When to run this
Any named person who will recur in your work: a new colleague, a counterpart on another team, someone you just met in a meeting, or a person referenced repeatedly in raw captures.

## Steps
1. Copy `Knowledge/People/People TEMPLATE.md` to `Knowledge/People/<Full Name>.md` (Title Case, with spaces).
2. Fill in the frontmatter: `status`, `org`, `team`, `role`, `reports-to`, `location`, `aliases` (nicknames + short forms).
3. Fill in the body sections: Relationship to me, Personal, Notes (one dated entry), Related.
4. In `Knowledge/Concepts/contacts.md`, add a row to the relevant table (or the go-to map if they're a primary contact). Format: `| [[Full Name]] | Role | Usage context |`.
5. If you added an alias, verify the `[[alias]]` wikilink resolves (Obsidian or a quick grep).
6. Append one line to `SYSTEM/log.md`: `- YYYY-MM-DD — Added [[Full Name]] to Knowledge/People/`.

## Gotchas / rules
- Filename must be `Full Name.md` (Title Case, spaces) — this is what `[[Full Name]]` resolves to.
- Aliases go in frontmatter `aliases:`, not as separate files. A bare first name shared by two people should NOT be aliased.
- Keep per-person detail in the note, not in `Knowledge/Concepts/contacts.md`. The contacts page is an index, not a biography.
- Don't add a person just because they're mentioned once. One-off names stay in the raw note.

## Done when
- [ ] `Knowledge/People/<Full Name>.md` exists and is filled in.
- [ ] A row in `Knowledge/Concepts/contacts.md` links to the note.
- [ ] `SYSTEM/log.md` updated.

## Related
[[contacts]] (the index) · [[Capture a meeting or conversation into the KB]] · [[SCHEMA]]
