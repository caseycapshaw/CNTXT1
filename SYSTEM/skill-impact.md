# Skill-impact — skill-evolution ledger

Every proposed change to a canonical skill (`.claude/skills/<slug>/SKILL.md`),
one line each, newest last, **whatever its fate**. This is the **third
ledger**: `SYSTEM/log.md` records *what changed*, `SYSTEM/decisions.md`
records *what {{NAME}} ruled*, this file records *how the skills evolved* —
including the proposals that were **rejected and why**, so the same edit is
not re-proposed next session. Index-not-record: the fuller reasoning lives in
the session record it points at.

**Format:** `- YYYY-MM-DD — [[Skill Title]] — ADOPTED|REJECTED|PARKED — <one-line change> — <one-line reason> — <pointer>`
**Writers:** [[Close a Session]] step 3 (interactive; ADOPTED needs {{NAME}}'s word). Unattended jobs may write `PARKED` only.
**On ADOPTED:** bump the skill's `metadata.version` (major = steps change meaning, minor = steps added/clarified) and `updated:`, then rebuild mirrors (`uv run python SYSTEM/bin/build_claude_mirrors.py`).

## Ledger

_(empty — first line lands at your next session close that touches a skill.)_
