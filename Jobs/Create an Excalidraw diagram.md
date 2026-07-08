---
type: job
domain: kb-meta
trigger: need a diagram / flowchart / visual map in the vault
frequency: ad-hoc
tools: Excalidraw (Obsidian plugin), mermaid, node/npm, "@excalidraw/excalidraw", esbuild
owner: {{NAME}}
status: active
tags: [job]
aliases: [Create Excalidraw, Make an Excalidraw diagram, Excalidraw diagram]
---

# Job — Create an Excalidraw diagram

> **When:** you need a visual (flowchart, architecture, reasoning map) as a native `.excalidraw.md` in the vault · **Frequency:** ad-hoc · **Tools:** Obsidian Excalidraw plugin (v2.25+), mermaid, node, `@excalidraw/excalidraw`, esbuild
> **Outcome:** a file in `Excalidraw/` that opens in **Excalidraw view** as real shapes + arrows (not raw text, no duplicated text pile), labels centred in boxes, arrows that re-route when a box is dragged.

## When to run this
You want a diagram stored in the KB. **Pick the route first** — the reputable practice is *never* hand-author full Excalidraw JSON; use an intermediate layer that handles layout/binding for you:

- **Route A — `meta/bin/excalidraw.py` (RECOMMENDED, self-contained).** A **zero-dependency** Python generator that lives in the KB: you describe the diagram as a compact node/edge spec, it emits a correct `.excalidraw.md` (auto-binds labels→containers and arrows→shapes, short ids, exact plugin format). No npm, no `@excalidraw/excalidraw`, no network — just the Python stdlib. Best for agent-generated / data-driven / KB diagrams.
- **Route B — Mermaid → Excalidraw (by hand).** LLM writes compact **Mermaid**; the *installed* plugin converts it (no external service). Best when a human will keep tweaking it and you'd rather sketch than script. Sources: [Atomic Object](https://spin.atomicobject.com/diagrams-mermaid-excalidraw/), [smcleod.net](https://smcleod.net/2024/10/generating-diagrams-with-with-ai-/-llms/).

## Steps

### Route A — `meta/bin/excalidraw.py` (self-contained, no external deps)
1. **Describe the diagram as a spec** in `meta/bin/excalidraw.py`. Add a function returning `(name, Diagram)` and append it to `DIAGRAMS`. The builder API:
   - `d = Diagram("Title …")`
   - `d.node(key, gx, gy, "label\ntext", kind, shape="rectangle"|"diamond", w, h)` — `kind` ∈ `read/write/struct/decision/gate/auto/session` (the palette); `gx,gy` are grid cells.
   - `d.edge(from_key, to_key, label=None)` — arrows auto-bind to both boxes and re-route on drag.
   - `d.hotspot(num, gx, gy, "text", to=key)` — amber ⚠ callout linked to a node.
   - `d.free("text", gx, gy)` / `d.legend(gx, gy)` — standalone label / the legend.
2. **Generate:** `python3 meta/bin/excalidraw.py --all` (or `python3 meta/bin/excalidraw.py "Overview"` for one; `--list` to list). Files land in `Excalidraw/`.
3. **Open in Excalidraw view** (⋯ → *Switch to Excalidraw view*) to verify. The plugin re-measures text and recompresses to `compressed-json` on first save — expected.
4. **Refine by hand** in the canvas if needed (drag boxes; Excalidraw's sketchy style is forgiving). If you want the change to survive a regenerate, edit the spec instead.

The script auto-handles the two things that make hand-authored Excalidraw fail: label/arrow **binding**, and **short block-ref ids** (see Gotchas). It needs nothing but Python 3 — no npm, no bundle, no network.

### Route B — Mermaid → Excalidraw (by hand, uses the installed plugin)
1. Draft the diagram as **Mermaid** (`flowchart TD`/`LR`), compact — LLMs are strong at this. One node per concept, edges for flow, `subgraph` for lanes.
2. Validate syntax at [mermaid.live](https://mermaid.live) (a syntax error → the import silently produces nothing).
3. In Obsidian: Command palette → **"Excalidraw: Create new drawing"**. In the drawing, open the tools menu → **"Mermaid to Excalidraw"** (or **"Insert mermaid diagram"**), paste, insert.
4. **Hand-refine** and save into `Excalidraw/`. The AI gives the first draft; you do the layout pass.

## Gotchas / rules
- **Short block-ref ids are mandatory** — the one thing that breaks hand-authored attempts. The `## Text Elements` mirror lists each text element as `<text> ^<id>`; Obsidian block refs need **short ids (≤8 chars)**. Long ids (21-char nanoids) break the parse and dump every label as an overlapping text pile on the canvas. `excalidraw.py` generates short ids (`t001`, `n001`) from the start, so this is handled — but if you ever hand-edit the JSON, keep text ids short and keep the first mirror entry flush against the header (a blank line there corrupts entry #1).
- **Never hand-author full element JSON** with manual arrow `points` + a hand-written mirror. That path mis-binds and overlaps. Use `excalidraw.py` (auto-binds) or Mermaid (auto-layout).
- **Text width/height are left `0` on purpose.** The plugin re-measures every text element on open (`autoResize:true`) — so we need no font metrics, and container-bound labels self-centre. (This is also exactly what the official headless converter emits.)
- **`compress:true`** is the plugin default: it recompresses your uncompressed `## Drawing` to `compressed-json` the first time you open+save in Excalidraw view. Expected — the script writes uncompressed for diffable history; let the plugin compress. (A file showing `compressed-json` just means it's been opened.)
- **`Excalidraw/` is a registered structural folder** (`meta/bin/lint.sh` + `meta/AGENTS.md` + `CLAUDE.md`) — new drawings there don't trip the inbox lint. Reference them with plain links, not `[[wikilinks]]` (the lint resolver only knows concepts/Initiatives/People/Jobs).
- **This is an optional extension** (see `meta/AGENTS.md` § Optional extensions) — nothing else in the KB depends on it. Skip it entirely if you don't need visual diagrams.

## Done when
- [ ] File opens in **Excalidraw view** as shapes + arrows — **no** raw JSON, **no** duplicated/overlapping text pile.
- [ ] Labels are centred inside their boxes; arrows connect the right nodes and re-route when a box is dragged.
- [ ] File lives in `Excalidraw/`; `meta/bin/lint.sh` is green.

## Provenance — how the schema was derived (one-time, not needed for normal use)
`excalidraw.py` is a from-scratch reimplementation of what Excalidraw's official [`convertToExcalidrawElements`](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api/excalidraw-element-skeleton) + the plugin's serializer produce. The exact element schema + binding rules were captured once by running the official converter headless (bundle `@excalidraw/excalidraw` with esbuild, patch roughjs `exports` for `./bin/*`, minimal DOM shim, set `window.EXCALIDRAW_ASSET_PATH="http://localhost/"`), and by reading the plugin's `main.js` serializer. **You don't need any of that to make diagrams** — it's only how the dependency-free script's output was validated to match. Re-derive only if a future plugin version changes the format.

## Related
`meta/AGENTS.md` (KB file-format rules, § Optional extensions) · the generator `meta/bin/excalidraw.py` · the visual maps in [`Excalidraw/`](../Excalidraw). Sources: [Excalidraw skeleton API](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api/excalidraw-element-skeleton) · [mermaid-to-excalidraw](https://github.com/excalidraw/mermaid-to-excalidraw) · [plugin file format (DeepWiki)](https://deepwiki.com/zsviczian/obsidian-excalidraw-plugin/3.1-file-formats-and-conversion).
