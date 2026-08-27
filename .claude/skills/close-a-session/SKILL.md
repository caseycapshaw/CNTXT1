---
name: close-a-session
description: The single-door session close — one feedback question, then record (log, decisions, digests), then review (route learnings by scope). Use when {{NAME}} says "close", "close session", "wrap up", or an equivalent end signal.
metadata:
  title: Close a Session
  type: do
  domain: kb-meta
  trigger: "{{NAME}} says \"close\", \"close session\", \"wrap up\", or an equivalent end signal"
  frequency: ad-hoc
  tools: [SYSTEM/log.md, SYSTEM/decisions.md, SYSTEM/bin/cap_check.py, git]
  owner: "{{NAME}}"
  status: active
  tags: [do, kb-meta]
  aliases: [Close a Session, close-a-session, close ritual]
  summary: The single-door session close — one feedback question, then record (log, decisions, digests), then review (route learnings by scope).
---


# Skill — Close a Session

> **When:** {{NAME}} signals the end of a working session · **Frequency:** every substantive session
> **Outcome:** the session's state is in the vault (log line, decisions captured, digests current) and its learnings are routed — any surface could pick up tomorrow

## When to run this

{{NAME}}'s end-phrases — "close", "close session", "wrap up", "done for now" — or any equivalent end signal. This is the **single door**: the whole ritual runs in one fixed order, no conditional branches. Casual Q&A sessions that wrote nothing can close with step 2's log line alone — say so and stop.

## Steps

1. **Threshold feedback pause — before anything else.** Ask {{NAME}} **one** open question: *"Any feedback on this session — friction, misses, keepers — or 'nothing'?"* Never a questionnaire. The close proceeds in full regardless of the answer; the answer is recorded in step 2 and is the highest-signal input to step 3. (Unattended closes skip this — nobody to ask.)

2. **Record — never skippable, runs first.**
   a. One line in `SYSTEM/log.md` for the session's work (if not already logged).
   b. **The ledger question: did {{NAME}} rule anything this session?** Each ruling they triggered with an explicit ruling-verb ("decided", "adopted", "that's a decision"…), or that they confirm now, appends one line to `SYSTEM/decisions.md` — index-not-record (date + title + 1–2 sentences + pointer). When unsure whether something was a ruling, ask — their confirmation counts; your inference alone does not.
   c. If a role session: refresh that role's digest per its KB-sync contract, then run `python3 SYSTEM/bin/cap_check.py` — over cap means compact now (rewrite the state from what is still true) or declare a dated `cap_exception:`.
   d. If an initiative session: update its "Now & next" + `updated:`; append a `## Trail` line if the note keeps one.
   e. {{NAME}}'s step-1 feedback, verbatim, goes wherever the session's record lives (log line suffix, session note, or journal).

3. **Review — route learnings by scope.** From the session (corrections {{NAME}} made rank highest, then step-1 feedback, then observed friction): a learning that binds *one role* → propose an edit to that `Knowledge/Agents/<role>.md` (show the diff; bump its version on adoption). One that binds *a skill* → same, in the skill. One that binds *the system* (`SYSTEM/SCHEMA.md`, templates, `CLAUDE.md`) → **draft, never apply** — present for {{NAME}}'s yes or park it in the relevant note's Open questions. "No friction = no findings" — the door costs nothing extra.

4. **Sweep what the session's edits made stale.** If the session amended a rule surface (AGENTS.md, a template, a RULE skill): grep for prose restating the amended text and fix companions **now** — staleness is generated at write time. If it renamed anything: link-map regen.

5. **End clean.** Report what was recorded and stop. **Nothing needing {{NAME}}'s word may first surface during or after this close** — if step 2–4 revealed a leftover needing their input, that's a "Need from you now:" *before* declaring the close complete.

## Gotchas / rules

- **One door.** Don't run a partial close ("I'll just log it") when {{NAME}} gave an end signal — the fixed order exists because ad-hoc closes skip the ledger question and the review.
- The 6pm `daily-summary.sh` is the **backstop** for sessions that die without a close (it logs and lints); it never asks the feedback question or appends to `decisions.md` — those are interactive-only.
- An unattended session that thinks it spotted a ruling files it as a proposal (Open questions / pending note), never a `decisions.md` line.

## Done when

- [ ] Log line appended; decisions ledger checked (and appended only on {{NAME}}'s word).
- [ ] Digest/initiative state current; cap check green or exception declared.
- [ ] Learnings routed (or "no findings" stated); nothing needing {{NAME}}'s word left unsurfaced.

## Related

[[SCHEMA]] · [[Run the KB Health Check]] · [[Keep Machinery Vendor-Portable]] · `SYSTEM/decisions.md`.
