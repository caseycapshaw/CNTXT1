#!/usr/bin/env python3
"""CNTXT KB MCP server — points Claude Desktop at the vault deterministically.

Stdlib-only stdio MCP server (newline-delimited JSON-RPC 2.0). Registered in
Claude Desktop's claude_desktop_config.json; Desktop launches it per chat and
injects its `instructions` + tool descriptions into every conversation, so the
"prioritize CNTXT" rule rides in as code, not pasted prose.

Setup: personalize the INSTRUCTIONS block below ({{NAME}}, {{SCOPE}}), then
register in `~/Library/Application Support/Claude/claude_desktop_config.json`:

    {
      "mcpServers": {
        "cntxt": {
          "command": "python3",
          "args": ["/absolute/path/to/your-kb/meta/bin/kb-mcp-server.py"]
        }
      }
    }

Vault root is resolved from this file's location (meta/bin/ → vault), so the
script needs no configuration beyond the INSTRUCTIONS block. Wikilinks resolve
through meta/link-map.md — the same one-lookup table the agents use.

Read path: kb_index / kb_read / kb_search / kb_actions (read-only).
Write path: kb_capture only — new dated file in raw/ + one meta/log.md line.
Nothing else in the vault is writable from here by design (the compile →
index → log pipeline stays in Claude Code, per meta/AGENTS.md).
"""
import datetime
import difflib
import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
LINK_MAP = VAULT / "meta" / "link-map.md"
SKIP_DIRS = {".git", ".obsidian", "attachments", ".stfolder", ".stversions"}
MAX_CHARS = 60_000

INSTRUCTIONS = """CNTXT is {{NAME}}'s personal knowledge base — the single
source of truth for {{SCOPE}}. It outranks your general knowledge and chat
memory; on conflict CNTXT wins — flag the conflict.

Before answering anything about {{NAME}} or the domains this KB covers: call
kb_index first, follow the map with kb_read (wikilinks like
[[karpathy-method]] or [[Full Name]] resolve directly), and ground the answer
in what the notes say, naming the note used. If the KB doesn't cover it, say
so — never guess about {{NAME}}'s life. Dates are YYYY-MM-DD.

Durable new facts from the conversation: capture with kb_capture (lands in the
raw/ inbox for later compilation). Never try to restructure the KB from here —
compiling raw notes into concepts happens in Claude Code."""

TOOLS = [
    {
        "name": "kb_index",
        "description": (
            "Read index.md — the map of the whole CNTXT knowledge base. ALWAYS "
            "call this first for any question about the KB owner or the "
            "domains the KB covers, then follow the map with kb_read. Do not "
            "answer personal questions from memory without checking here."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "kb_read",
        "description": (
            "Read one note from the KB. Accepts a wikilink target exactly as it "
            "appears in other notes ('[[karpathy-method]]', '[[Full Name]]', a "
            "nickname — aliases resolve via the link map) or a vault-relative "
            "path ('concepts/karpathy-method.md', 'daily/2026-01-01.md')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "note": {
                    "type": "string",
                    "description": "Wikilink target, alias, or vault-relative path",
                }
            },
            "required": ["note"],
        },
    },
    {
        "name": "kb_search",
        "description": (
            "Case-insensitive text search across every markdown note in the "
            "vault. Returns matching lines as path:line. Use when the index "
            "doesn't make the destination obvious; prefer kb_index + kb_read "
            "for known topics."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Literal text to find"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "kb_actions",
        "description": (
            "List every open to-do: unchecked '- [ ] … #action' checkboxes "
            "across the vault, with the note each lives in. '#priority' marks "
            "focus items."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "kb_capture",
        "description": (
            "Capture durable new information from this conversation into the "
            "KB inbox: writes a new append-only file raw/YYYY-MM-DD-<topic>.md "
            "and appends one line to meta/log.md. Never overwrites anything. "
            "Use for facts worth keeping (decisions, new people, project "
            "updates) — not for chit-chat. Compilation into concepts happens "
            "later in Claude Code."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Short kebab-case topic for the filename, e.g. 'roof-quote'",
                },
                "content": {
                    "type": "string",
                    "description": (
                        "Markdown body: what was learned, lightly edited, with "
                        "enough context to compile later. Include [[wikilinks]] "
                        "to related notes."
                    ),
                },
            },
            "required": ["topic", "content"],
        },
    },
]

RESOURCES = [
    {
        "uri": "cntxt://index.md",
        "name": "CNTXT index (the map)",
        "description": "index.md — map of every concept, initiative, person, and runbook",
        "mimeType": "text/markdown",
    },
    {
        "uri": "cntxt://meta/AGENTS.md",
        "name": "CNTXT schema (how the KB works)",
        "description": "meta/AGENTS.md — the knowledge base's operating rules",
        "mimeType": "text/markdown",
    },
    {
        "uri": "cntxt://Actions.md",
        "name": "CNTXT actions dashboard",
        "description": "Actions.md — the live aggregated to-do view",
        "mimeType": "text/markdown",
    },
]


def vault_path(rel):
    """Resolve a vault-relative path, refusing anything outside the vault."""
    p = (VAULT / rel).resolve()
    if not str(p).startswith(str(VAULT) + "/") and p != VAULT:
        raise ValueError(f"path escapes the vault: {rel}")
    return p


def md_files():
    for p in sorted(VAULT.rglob("*.md")):
        if not SKIP_DIRS.intersection(p.relative_to(VAULT).parts):
            yield p


def load_link_map():
    links = {}
    if LINK_MAP.exists():
        for m in re.finditer(
            r"^\| `\[\[(.+?)\]\]` \| `(.+?)` \|",
            LINK_MAP.read_text(encoding="utf-8"),
            re.M,
        ):
            links[m.group(1).lower()] = m.group(2)
    return links


def clip(text):
    if len(text) > MAX_CHARS:
        return text[:MAX_CHARS] + f"\n\n[… clipped at {MAX_CHARS} chars]"
    return text


def read_note(rel):
    p = vault_path(rel)
    if not p.is_file():
        raise FileNotFoundError(rel)
    return f"── {rel} ──\n\n" + clip(p.read_text(encoding="utf-8"))


def tool_kb_index(_args):
    return read_note("index.md")


def tool_kb_read(args):
    raw = args["note"].strip().strip("[]").strip()
    # 1. vault-relative path (with or without .md)
    for rel in (raw, raw + ".md"):
        try:
            return read_note(rel)
        except (FileNotFoundError, ValueError):
            pass
    # 2. link map (canonical names + aliases)
    links = load_link_map()
    if raw.lower() in links:
        return read_note(links[raw.lower()])
    # 3. case-insensitive basename match across the vault
    for p in md_files():
        if p.stem.lower() == raw.lower():
            return read_note(str(p.relative_to(VAULT)))
    close = difflib.get_close_matches(raw.lower(), list(links), n=5, cutoff=0.5)
    hint = ("Close wikilinks: " + ", ".join(f"[[{c}]]" for c in close)) if close else \
        "No close wikilink; try kb_search or check kb_index."
    raise FileNotFoundError(f"note not found: {raw!r}. {hint}")


def tool_kb_search(args):
    query = args["query"].strip()
    if not query:
        raise ValueError("empty query")
    needle, hits, capped = query.lower(), [], False
    for p in md_files():
        rel = p.relative_to(VAULT)
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if needle in line.lower():
                hits.append(f"{rel}:{i}: {line.strip()}")
                if len(hits) >= 200:
                    capped = True
                    break
        if capped:
            break
    if not hits:
        return f"No matches for {query!r}."
    out = "\n".join(hits)
    if capped:
        out += "\n\n[capped at 200 matches — narrow the query]"
    return clip(out)


def tool_kb_actions(_args):
    hits = []
    for p in md_files():
        rel = p.relative_to(VAULT)
        if rel.name == "Actions.md" or "TEMPLATE" in rel.name:
            continue  # the dashboard aggregates; templates carry sample actions
        for line in p.read_text(encoding="utf-8").splitlines():
            if "#action" in line and re.match(r"\s*- \[ \]", line):
                hits.append(f"{rel}: {line.strip()}")
    return clip("\n".join(hits)) if hits else "No open actions."


def tool_kb_capture(args):
    topic = re.sub(r"[^a-z0-9]+", "-", args["topic"].lower()).strip("-")
    content = args["content"].strip()
    if not topic:
        raise ValueError("topic is empty after slugifying")
    if not content:
        raise ValueError("content is empty")
    today = datetime.date.today().isoformat()
    dest, n = VAULT / "raw" / f"{today}-{topic}.md", 2
    while dest.exists():
        dest = VAULT / "raw" / f"{today}-{topic}-{n}.md"
        n += 1
    rel = dest.relative_to(VAULT)
    body = (
        f"# {today} — {args['topic'].strip()}\n\n"
        f"> Source: Claude Desktop conversation, captured via the CNTXT MCP "
        f"server (kb_capture). Un-compiled inbox item.\n\n{content}\n"
    )
    dest.write_text(body, encoding="utf-8")
    with (VAULT / "meta" / "log.md").open("a", encoding="utf-8") as f:
        f.write(
            f"- {today} — Captured `{rel}` from a Claude Desktop conversation "
            f"(via kb_capture); awaiting compile in Claude Code.\n"
        )
    return (
        f"Captured to {rel} and logged in meta/log.md. It will be compiled "
        f"into concepts/ from Claude Code later — mention that it's waiting."
    )


TOOL_FNS = {
    "kb_index": tool_kb_index,
    "kb_read": tool_kb_read,
    "kb_search": tool_kb_search,
    "kb_actions": tool_kb_actions,
    "kb_capture": tool_kb_capture,
}


def handle(method, params):
    if method == "initialize":
        return {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": "cntxt-kb", "version": "1.0.0"},
            "instructions": INSTRUCTIONS,
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name = params.get("name")
        if name not in TOOL_FNS:
            raise ValueError(f"unknown tool: {name}")
        try:
            text = TOOL_FNS[name](params.get("arguments") or {})
            return {"content": [{"type": "text", "text": text}], "isError": False}
        except Exception as e:  # tool errors go back as results, not protocol errors
            return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}
    if method == "resources/list":
        return {"resources": RESOURCES}
    if method == "resources/read":
        rel = params.get("uri", "").replace("cntxt://", "", 1)
        return {
            "contents": [
                {
                    "uri": params.get("uri"),
                    "mimeType": "text/markdown",
                    "text": clip(vault_path(rel).read_text(encoding="utf-8")),
                }
            ]
        }
    if method == "prompts/list":
        return {"prompts": []}
    raise KeyError(method)


def main():
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            msg = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if "id" not in msg:  # notification — no response
            continue
        reply = {"jsonrpc": "2.0", "id": msg["id"]}
        try:
            reply["result"] = handle(msg.get("method", ""), msg.get("params") or {})
        except KeyError:
            reply["error"] = {"code": -32601, "message": f"method not found: {msg.get('method')}"}
        except Exception as e:
            reply["error"] = {"code": -32603, "message": str(e)}
        sys.stdout.write(json.dumps(reply) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
