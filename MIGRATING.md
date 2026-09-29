# MIGRATING — from the `Knowledge/` layout to the numbered GTD layout

The kit now ships a numbered, [GTD](https://gettingthingsdone.com)-shaped layout
instead of everything under `Knowledge/`. If you started from the old kit, this is
the step-by-step move. New users can ignore this file.

**Why:** the numbers make Obsidian's file explorer sort by altitude, and the folders
now carry the GTD stack — `03 Projects/` (finite workstreams), `02 Areas/` (ongoing
responsibilities), `01 Horizons/` (goals → vision → purpose) — chained by frontmatter
up-links, with `Initiative` renamed `Project` and the endpoint test as the rule
that decides which is which. See `SYSTEM/SCHEMA.md` § Conventions and
`05 concepts/gtd.md`.

## 1. The map

| Old | New |
| :-- | :-- |
| `Knowledge/Concepts/` | `05 concepts/` |
| `Knowledge/Initiatives/` (+ `archive/`, `trails/`) | `03 Projects/` (+ `archive/`, `trails/`) |
| `Knowledge/Initiatives/Initiative TEMPLATE.md` | `03 Projects/Project TEMPLATE.md` |
| `Knowledge/People/` | `04 People/` |
| `Knowledge/Skills/` (generated mirrors) | `Skills/` |
| `Knowledge/Agents/` (generated mirrors) | `Agents/` |
| `Knowledge/raw/` | `raw/` |
| `Knowledge/Excalidraw/` | `excalidraw/` |
| `Knowledge/Actions.md` | `Actions.md` (root anchor) |
| `daily/` | `00 daily/` |
| *(new)* | `01 Horizons/` (`Goals/`, `vision.md`, `purpose-principles.md`), `02 Areas/` (`Assets/`, `Area TEMPLATE.md`) |
| `Writing/<Outlet>/` | a graduated area folder, `02 Areas/<slug>/` beside `02 Areas/<slug>.md` (optional) |
| `.claude/skills/run-an-initiative` · `delegate-an-initiative-to-a-cmux-workspace` | `run-a-project` · `delegate-a-project-to-a-cmux-workspace` (old names stay as alias stubs) |
| `.claude/agents/initiative-worker.md` | `.claude/agents/project-worker.md` |
| `SYSTEM/bin/*-initiatives.sh`, `audit-initiative-next-actions.sh` | `active-projects.sh`, `stale-projects.sh`, `audit-project-next-actions.sh` (+ new `audit-area-reviews.sh`) |

Folder names are defined once, in `SYSTEM/bin/kb-folders.json` (mirrored for shell in
`kb-folders.sh`); every script reads them from there.

## 2. Frontmatter changes

| Note | Change |
| :-- | :-- |
| Every initiative note | `type: initiative` → `type: project`; `tags: [initiative, …]` → `[project, …]` |
| Live projects | **new required `area:`** up-link — `area: "[[<slug>]]"` naming the `02 Areas/` note the project serves (`status: done` is exempt) |
| Projects | `status:` gains `pending` (= Someday/Maybe: opened, waiting on a trigger). Optional `serves: "[[goal]]"` |
| Concepts | `description:` (one stable sentence) is now **required** |
| Person notes | optional `relation:` (your relationship to them); vendors are `type: org` notes in `04 People/` |
| Skills | optional `metadata.version` (quoted string), bumped when the skill-impact ledger ADOPTs a change |
| Areas *(new)* | `type: area` · `review: weekly\|monthly\|quarterly` · `reviewed: YYYY-MM-DD` · `## Standard` section |

## 3. Do the move

Back up first (`git status` clean, or copy the folder). Then pick your mode.

### Clone mode (you use the kit repo directly; your notes are untracked)

1. `git pull` on the new branch/release. The shipped scaffolding lands in the new
   folders; the old shipped skeleton under `Knowledge/` is removed. **Your own notes
   in `Knowledge/` are untracked and stay put.** (If git objects to a file you
   edited, e.g. `Knowledge/Concepts/contacts.md`: copy your version aside, accept
   the kit's, and merge your edits back after step 2.)
2. From the vault root: `SYSTEM/bin/migrate-to-numbered-layout.sh` (dry run — prints
   the plan), then `SYSTEM/bin/migrate-to-numbered-layout.sh --apply`. It moves
   every remaining file from the old folders into the new ones (never overwriting —
   collisions are listed for you), rewrites old path prefixes and Initiative →
   Project wording in your markdown, flips `type: initiative` → `type: project`, and
   prints each live project still missing `area:`.

### Instance-repo mode (your own private history, kit as fetch-only `upstream`)

1. In your instance: `SYSTEM/bin/migrate-to-numbered-layout.sh --apply` **first**
   (it uses `git mv`, so history follows), review `git status`, commit
   (`refactor: numbered GTD layout`).
2. Then adopt the kit: `git fetch upstream` and follow
   `Skills/DO/Pull Framework Updates from CNTXT1.md`. Path-divergent files
   (`SYSTEM/SCHEMA.md`, `AGENTS.md`, templates, `SYSTEM/bin/lint.sh`) will conflict
   by design — take the kit's version, then re-apply your populated bits
   (placeholders, `index.md` groups, your `{{NAME}}` values).

## 4. Finish

1. **Areas.** For each live project's `area:`, create the area note:
   `02 Areas/<slug>.md` from `02 Areas/Area TEMPLATE.md` (fill `## Standard`, set
   `review:` + `reviewed:`). Apply the endpoint test to your old initiatives: anything
   that can never be "done" is really an **area** — `git mv` it into `02 Areas/` and
   swap the frontmatter (wikilinks are basename-based, so links don't break).
2. **Horizons** (optional): fill the `01 Horizons/` stubs, or leave the placeholders.
3. **Index.** `index.md` gains marker pairs for generated sections — copy them from
   the kit's `index.md` (`<!-- projects:auto:start/end -->`, `areas:`, `concepts:`);
   the generators fill them.
4. **Contacts.** Add `<!-- generated -->` below the hand-written part of
   `05 concepts/contacts.md` (the vendor/service directory generates there).
5. **Regenerate and lint:**
   ```
   SYSTEM/bin/build-link-map.sh
   SYSTEM/bin/regen-all.sh
   SYSTEM/bin/lint.sh              # exit 0 = green
   LINT_STRICT=1 SYSTEM/bin/lint.sh
   ```
6. **Sweep for stale prose** (SCHEMA § Rename/convention-change hygiene):
   `rg -i 'Knowledge/|initiative' -g '!SYSTEM/log.md'` and fix any hit — keep
   historical log/raw text as it was.
7. **Obsidian:** reopen the vault; the old `Knowledge/` folder is gone, so re-pin any
   bookmarks. If you used the optional automation from `~/.claude/hooks/`, re-copy
   the updated scripts from `SYSTEM/optional/automation/` (they now write to
   `00 daily/`).

## What did not change

`raw/` stays append-only; the inbox is still the vault root; skills and roles are
still canonical in `.claude/` with generated mirrors (now at `Skills/` and
`Agents/`); the privacy rule is untouched.
