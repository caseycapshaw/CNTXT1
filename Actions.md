# ✅ Actions — the single to-do view

The one place to see every outstanding **action** (thing to do) in the KB.

Actions are Markdown checkboxes tagged `#action`, written **inline in whatever
note they belong to** (next to their context). This note doesn't store them — it
**gathers** them. Check an item off in its home note (or right here) and it drops
off the list. Convention is defined in [`AGENTS.md`](meta/AGENTS.md).

> **Requires the [Tasks](https://publish.obsidian.md/tasks/) community plugin.**
> Obsidian → Settings → Community plugins → Browse → search **"Tasks"** (by Clare
> Macrae) → Install → Enable. Until it's enabled, the blocks below show as plain
> code instead of a live list. (The `#action` convention still works as plain
> text without it — the plugin just renders the dashboard.)

## 🔺 Priority

Tag any `#action` with `#priority` to flag it as a focus item.

```tasks
not done
tags include #action
tags include #priority
sort by due
```

## All open actions — grouped by source note

```tasks
not done
tags include #action
sort by description
group by filename
```

## Recently completed

```tasks
done
tags include #action
sort by done reverse
limit 15
```

---

### How to add an action
Anywhere, in any note, write a checkbox with the tag (a `📅 YYYY-MM-DD` due date
is optional):

```
- [ ] Email procurement re. handoff #action 📅 2026-01-15
```

Add **`#priority`** to flag it as a focus item:

```
- [ ] Decide on team offsite venue #action #priority
```

It shows up here automatically — no need to edit this dashboard. Keep **actions**
(things *you* do) distinct from **open questions** (unknowns to resolve); if a
question's answer is a task you perform, write it as an `#action`.
