---
type: area
description: <one-line summary of the responsibility — single-sources the index one-liner>
status: current       # areas are never done — an area that ends gets its durable facts distilled and the note archived to raw/ (rare)
updated: YYYY-MM-DD   # bump on every meaningful rewrite (same rule as concepts)
review: monthly       # weekly | monthly | quarterly — audited by SYSTEM/bin/audit-area-reviews.sh
reviewed: YYYY-MM-DD  # bumped by [[Review an Area]] each pass
area: "[[<parent>]]"  # SUB-AREAS ONLY (e.g. 02 Areas/Assets/ children up-link "[[assets]]") — delete for top areas
serves: "[[<goal-slug>]]"   # optional — a type: goal note (or a horizon). Does not replace area: on children.
owner: {{NAME}}       # ASSET SUB-AREAS — {{NAME}} | household | "[[Full Name]]" (primary owner) — delete otherwise
serviced-by: "[[<org>]]"  # optional — the type: org vendor that maintains this asset
tags: [area, <domain>]
---

# Area — {Title}

_The compiled truth about this responsibility lives here (facts trace to
`raw/` captures, same as concepts). Projects serving this area up-link it via
`area:` frontmatter — the Projects view below renders them live (Dataview);
never hand-maintain a project list._

## Standard
_What "maintained" means for this area — the bar a review checks against.
Reviewing an area is where its projects get created and retired._

## Projects (generated — live view)

_Every non-done project whose `area:` up-links this note. Rendered by
Dataview from frontmatter; never hand-edit a project list here._

```dataview
TABLE WITHOUT ID file.link AS Project, status AS Status, updated AS Updated
FROM "03 Projects"
WHERE contains(area, this.file.link) AND status != "done"
SORT status ASC, updated DESC
```

## Actions
_Standing/small actions live inline, same as anywhere — they aggregate to
`Actions.md`. An outcome needing 3+ actions becomes a project up-linking
this area._

- [ ] _(first action, if any)_ #action

## Related
_[[concepts]], [[People]], sibling areas, and `raw/` captures this draws on._
