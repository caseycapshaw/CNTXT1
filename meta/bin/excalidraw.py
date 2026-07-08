#!/usr/bin/env python3
"""Zero-dependency Excalidraw diagram generator for this KB.

Produces Obsidian-Excalidraw `.excalidraw.md` files that open natively in the
Excalidraw plugin (v2.25+) — WITHOUT any external package (no
`@excalidraw/excalidraw`, no esbuild, no browser shim). It reimplements the two
things the official `convertToExcalidrawElements` API does, which are the only
things that matter:

  1. Bind labels to container shapes  (text.containerId + shape.boundElements)
  2. Bind arrows to shapes            (arrow.start/endBinding + boundElements)

…plus the Obsidian plugin's own serializer rules (learned from its `main.js`):

  * File = frontmatter (`excalidraw-plugin: parsed` + `excalidraw` tag), then
    `# Excalidraw Data` / `## Text Elements` / `## Drawing` (```json fence), `%%`.
  * The `## Text Elements` mirror lists each text element as `<text> ^<id>`,
    blank-line separated, first entry flush to the header.
  * Text-element ids MUST be short (Obsidian block refs `^id` break on long ids
    → the whole mirror renders as an overlapping text pile). We generate short
    deterministic ids from the start, so no post-shortening is ever needed.

Text width/height are left 0: the plugin re-measures on open (`autoResize`),
exactly as the official headless converter does — so we need no font metrics.

Usage:
    python3 meta/bin/excalidraw.py --all          # (re)write all KB diagrams
    python3 meta/bin/excalidraw.py "Overview"      # one, by name substring
    python3 meta/bin/excalidraw.py --list          # list defined diagrams

Add a diagram: append a spec dict to DIAGRAMS (see the example below), re-run.
Runbook: Jobs/Create an Excalidraw diagram.md.
"""
import json, os, sys

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "Excalidraw")
UPDATED = 1720400000000

# palette: (fill, stroke)
PAL = {
    "read": ("#a5d8ff", "#1971c2"), "write": ("#b2f2bb", "#2f9e44"),
    "struct": ("#d0bfff", "#6741d9"), "decision": ("#ffec99", "#f08c00"),
    "gate": ("#ffc9c9", "#e03131"), "auto": ("#e9ecef", "#868e96"),
    "session": ("#ced4da", "#495057"), "note": ("#fff3bf", "#f08c00"),
}
GX, GY = 400, 220          # grid cell (px)
OX, OY = 120, 160          # origin offset
BW, BH = 280, 96           # default box size


class Diagram:
    """Builds a valid Excalidraw scene from a compact node/edge spec."""

    def __init__(self, title):
        self.title = title
        self.shapes, self.arrows, self.texts = [], [], []
        self.rect = {}     # key -> (x, y, w, h)
        self._n = 0
        self._text("title", title, OX, 40, 30, "#1e1e1e", "left", "top")

    def _id(self, p):
        self._n += 1
        return f"{p}{self._n:03d}"          # e.g. n001, t001 — always <= 4 chars

    def _common(self, id, typ, x, y, w, h, fill, stroke, dashed=False, roundness=None):
        self._n += 0
        seed = 100000 + len(self.shapes) + len(self.arrows) + len(self.texts) * 3 + self._n * 7
        return {
            "id": id, "type": typ, "x": x, "y": y, "width": w, "height": h, "angle": 0,
            "strokeColor": stroke, "backgroundColor": fill, "fillStyle": "solid",
            "strokeWidth": 2, "strokeStyle": "dashed" if dashed else "solid",
            "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
            "roundness": roundness, "seed": seed, "version": 1, "versionNonce": seed * 3 % 2147483647,
            "isDeleted": False, "boundElements": [], "updated": UPDATED,
            "link": None, "locked": False,
        }

    def _text(self, id, text, x, y, fs, color, align, valign, container=None, w=0):
        lines = text.split("\n")
        h = len(lines) * fs * 1.25
        e = self._common(id, "text", x, y, w, h, "transparent", color)
        e.update({
            "text": text, "fontSize": fs, "fontFamily": 5, "textAlign": align,
            "verticalAlign": valign, "containerId": container, "originalText": text,
            "autoResize": True, "lineHeight": 1.25,
        })
        del e["roundness"]; e["roundness"] = None
        self.texts.append(e)
        return e

    def _xy(self, gx, gy):
        return OX + gx * GX, OY + gy * GY

    def node(self, key, gx, gy, text, kind="read", shape="rectangle", w=BW, h=BH, fs=16):
        x, y = self._xy(gx, gy)
        fill, stroke = PAL[kind]
        self.rect[key] = (x, y, w, h)
        rid = key                      # stable id = key (short)
        r = self._common(rid, shape, x, y, w, h, fill, stroke,
                         roundness=({"type": 3} if shape == "rectangle" else None))
        tid = self._id("t")
        t = self._text(tid, text, x + w / 2, y + (h - len(text.split(chr(10))) * fs * 1.25) / 2,
                       fs, "#1e1e1e", "center", "middle", container=rid)
        r["boundElements"] = [{"type": "text", "id": tid}]
        self.shapes.append(r)
        return r

    def hotspot(self, num, gx, gy, text, to=None, w=300, h=72):
        x, y = self._xy(gx, gy)
        fill, stroke = PAL["note"][0], PAL["gate"][1]
        rid = f"h{num:02d}"
        self.rect[rid] = (x, y, w, h)
        r = self._common(rid, "rectangle", x, y, w, h, fill, stroke, dashed=True,
                         roundness={"type": 3})
        tid = self._id("t")
        label = f"⚠ {num}. {text}"
        t = self._text(tid, label, x + w / 2, y + (h - len(label.split(chr(10))) * 13 * 1.25) / 2,
                       13, "#a51111", "center", "middle", container=rid)
        r["boundElements"] = [{"type": "text", "id": tid}]
        self.shapes.append(r)
        if to and to in self.rect:
            self._arrow(rid, to, color=stroke, dashed=True, head="triangle")

    def _anchor(self, F, T):
        fx, fy, fw, fh = F; tx, ty, tw, th = T
        fc = (fx + fw / 2, fy + fh / 2); tc = (tx + tw / 2, ty + th / 2)
        if tc[1] > fc[1] + 20:   return (fc[0], fy + fh), (tc[0], ty)
        if tc[1] < fc[1] - 20:   return (fc[0], fy),      (tc[0], ty + th)
        if tc[0] > fc[0]:        return (fx + fw, fc[1]),  (tx, tc[1])
        return (fx, fc[1]),      (tx + tw, tc[1])

    def _arrow(self, fkey, tkey, label=None, color="#343a40", dashed=False, head="arrow"):
        s, t = self._anchor(self.rect[fkey], self.rect[tkey])
        aid = self._id("a")
        a = self._common(aid, "arrow", s[0], s[1], abs(t[0] - s[0]), abs(t[1] - s[1]),
                         "transparent", color, dashed=dashed)
        a.update({
            "points": [[0, 0], [t[0] - s[0], t[1] - s[1]]], "lastCommittedPoint": None,
            "startBinding": {"elementId": fkey, "focus": 0, "gap": 4},
            "endBinding": {"elementId": tkey, "focus": 0, "gap": 4},
            "startArrowhead": None, "endArrowhead": head, "elbowed": False,
        })
        a["boundElements"] = None
        self.arrows.append(a)
        # register the arrow on both endpoints
        for k in (fkey, tkey):
            for e in self.shapes:
                if e["id"] == k:
                    e["boundElements"] = (e["boundElements"] or []) + [{"id": aid, "type": "arrow"}]
        if label:
            mx, my = (s[0] + t[0]) / 2, (s[1] + t[1]) / 2
            self._text(self._id("t"), label, mx, my - 9, 13, "#868e96", "center", "middle")

    def edge(self, fkey, tkey, label=None):
        self._arrow(fkey, tkey, label=label)

    def free(self, text, gx, gy, fs=14, color="#343a40", align="left"):
        x, y = self._xy(gx, gy)
        self._text(self._id("t"), text, x, y, fs, color, align, "top")

    def legend(self, gx, gy):
        x, y = self._xy(gx, gy)
        self.free("Legend", gx, gy - 0.14, fs=16, color="#1e1e1e")
        items = [("read", "read / query"), ("write", "capture / write"),
                 ("struct", "People · Jobs · structural"), ("decision", "decision"),
                 ("gate", "⚠ improvement hotspot / gate"), ("auto", "daily automation"),
                 ("session", "always-on (session start)")]
        for i, (k, lab) in enumerate(items):
            yy = y + i * 34
            fill, stroke = PAL[k]
            sid = self._id("n")
            self.shapes.append(self._common(sid, "rectangle", x, yy, 28, 22, fill, stroke,
                                            roundness={"type": 3}))
            self._text(self._id("t"), lab, x + 40, yy + 3, 14, "#343a40", "left", "top")

    # ---- serialize --------------------------------------------------------
    def elements(self):
        # z-order: shapes, then arrows, then text (labels on top). Title built in __init__.
        return self.shapes + self.arrows + self.texts

    def markdown(self):
        els = self.elements()
        scene = {"type": "excalidraw", "version": 2,
                 "source": "https://github.com/zsviczian/obsidian-excalidraw-plugin",
                 "elements": els,
                 "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
                 "files": {}}
        te = "".join(f"{e['text']} ^{e['id']}\n\n"
                     for e in els if e["type"] == "text" and e["text"].strip())
        body = json.dumps(scene, ensure_ascii=False, indent="\t")
        return (
            "---\nexcalidraw-plugin: parsed\ntags: [excalidraw]\n---\n"
            "==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==\n\n"
            "# Excalidraw Data\n\n## Text Elements\n" + te +
            "## Drawing\n```json\n" + body + "\n```\n%%"
        )


# ========================================================================
# Diagram specs — one function per diagram. Grid coords chosen for clear
# spacing. This is a minimal example demonstrating the API against the
# method's own public data flow — replace/extend with your own diagrams.
# ========================================================================
def example():
    d = Diagram("Example — the KB's own data flow  ·  inbox → raw → compile → index → log")
    d.node("inbox", 0, 0, "New note lands at\nvault root = INBOX", "read")
    d.node("raw", 1, 0, "Triage → raw/\nYYYY-MM-DD-topic.md\n(append-only)", "write")
    d.node("concepts", 2, 0, "Compile facts →\nconcepts/\nbump updated: frontmatter", "write")
    d.node("index", 3, 0, "Update index.md\nQuick map", "write")
    d.node("log", 4, 0, "Append meta/log.md\n(one line)", "write")
    for a, b in [("inbox", "raw"), ("raw", "concepts"), ("concepts", "index"), ("index", "log")]:
        d.edge(a, b)
    d.hotspot(1, 0, 1.05, "raw-only vs compile-now is a\njudgment call worth documenting", to="raw")
    d.legend(0, 2)
    return "Example — KB data flow", d


DIAGRAMS = [example]


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    if "--list" in argv:
        for f in DIAGRAMS:
            print(f()[0])
        return
    sel = [a for a in argv if not a.startswith("--")]
    pick = None if ("--all" in argv or not sel) else sel[0].lower()
    for f in DIAGRAMS:
        name, d = f()
        if pick and pick not in name.lower():
            continue
        path = os.path.join(OUT, f"{name}.excalidraw.md")
        with open(path, "w") as fh:
            fh.write(d.markdown())
        print(f"wrote {name} ({len(d.elements())} elements)")


if __name__ == "__main__":
    main(sys.argv[1:])
