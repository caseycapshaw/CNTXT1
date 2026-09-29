---
type: person
status: active            # active | exec | dormant | departing | tbc
org:                      # company / org / department
team:
role:
relation:                 # relationship to {{NAME}} — spouse · "brother-in-law — {{spouse}}'s brother" · friend · … (side of family in the value when it matters)
reports-to:               # plain name (wikilink in the body)
location:
tags: [person]
aliases: []               # nicknames / short forms so [[alias]] resolves
---

# {Full Name}

> **{Role}** · {Org / Team} · {Location}
> 📧 {email} · 💬 {chat handle}
> Reports to: [[]]

## Relationship to me
{Why this person matters / how we work together — the one-liner: "the go-to for X."
Wikilink the workstream or concept.}

## Personal
{Personal details — timezone, background, how they like to work.}

## Notes
{Significant interactions, **newest first**, dated `YYYY-MM-DD`. Wikilink liberally; don't
restate facts that live in a concept note — link to it.}
- {YYYY-MM-DD} — …

## Meeting history
{Very succinct. Link to the `raw/` capture or `00 daily/` note rather than re-typing content.}

## Related
{People + concepts this person connects to — [[reports]], counterparts, [[workstreams]].}

<!--
CONVENTIONS (delete in real notes)
• Filename = "Full Name.md" (Title Case With Spaces) → wikilink as [[Full Name]].
• Put nicknames/first-name short forms in `aliases:` so [[Nickname]] resolves.
  Do NOT alias a bare first name that two people share.
• status: active = currently working with · exec = leadership/skip-level · dormant =
  known but not engaged · departing = leaving · tbc = name only, role unknown.
• Person notes are the SINGLE SOURCE OF TRUTH for per-person detail. 05 concepts/contacts.md
  is the index/usage-context map; org-chart views are kept in separate concept notes.
• Don't duplicate per-person prose into concepts — link to this note instead.
• Businesses/vendors get a `type: org` note in this folder instead — same filename
  convention, this frontmatter (SCHEMA § Relations frontmatter):
      ---
      type: org
      status: active          # active | dormant
      org: {Company name}
      role: {what they do for you — plumber, CPA, dentist …}
      location:
      found-by: "[[Full Name]]"   # who brought the relationship into the household
      tags: [org]
      aliases: []
      ---
  Up-links only: an org never lists its clients; assets point at it via `serviced-by:`.
-->
