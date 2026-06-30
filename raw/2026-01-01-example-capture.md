# Example capture — what a raw note looks like

> ⚠️ **This is an EXAMPLE file.** It exists to show the format. Delete it once
> you've written your own first capture (`setup.md` Phase 4 offers to do this).

_Source: kb-starter example, 2026-01-01._

Raw notes live in `raw/`, are named `YYYY-MM-DD-topic.md`, and are **append-only**
— never rewritten or deleted. They start with a one-line provenance header (where
the material came from) so every compiled fact can be traced back. This is the
"source code" the LLM compiles into `concepts/`.

## What goes here
- Lightly-edited dumps of a meeting, a document, a conversation, an article, slides.
- Whatever you'd otherwise lose. Messy is fine — this is the source, not the polished page.

## Example facts (the kind of thing you'd capture)
- The knowledge base is built on the [[karpathy-method]] — note the `[[wikilink]]`, which connects this note to a concept article.
- Durable facts from this note get **compiled** into `concepts/`, then the new concept is added to `index.md` and a line is appended to `meta/log.md`.

## Actions surface inline, next to their context
- [ ] Delete this example file after writing my first real capture #action
- [ ] Read `concepts/karpathy-method.md` to understand why this works #action #priority

That's the whole format: provenance header, facts, wikilinks, and any `#action`
checkboxes written right where they come up.
