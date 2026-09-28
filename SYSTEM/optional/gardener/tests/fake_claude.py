#!/usr/bin/env python3
"""Fake `claude` CLI for tests (GARDENER_CLAUDE_CMD=.../fake_claude.py). Reads
FAKE_CLAUDE_ACTION from the environment:
  noop        — does nothing, exits 0 (default)
  write_file  — writes FAKE_CLAUDE_WRITE_PATH with FAKE_CLAUDE_WRITE_TEXT,
                relative to cwd (simulates a well-behaved edit)
  touch_raw   — writes a new file under raw/ (simulates a guardrail violation
                the enforcement layer must catch and revert)
"""
import os
import sys
from pathlib import Path

action = os.environ.get("FAKE_CLAUDE_ACTION", "noop")

if action == "write_file":
    rel = os.environ["FAKE_CLAUDE_WRITE_PATH"]
    text = os.environ.get("FAKE_CLAUDE_WRITE_TEXT", "fake content\n")
    p = Path.cwd() / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
elif action == "touch_raw":
    p = Path.cwd() / "raw" / "2026-09-28-llm-violation.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("an LLM tried to add a new raw file\n", encoding="utf-8")

print("fake claude ok")
sys.exit(0)
