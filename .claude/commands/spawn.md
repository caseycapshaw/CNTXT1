---
description: Launch a CMUX pane worker under a named agent role
argument-hint: <role> <task>
---

Parse `$ARGUMENTS` as `<role> <task…>`. Read the role definition
`.claude/agents/<role>.md` (visible mirror: `Knowledge/Agents/<role>.md`), then
follow the canonical runbook
`.claude/skills/spawn-subagent-panes-in-a-cmux-workspace/SKILL.md` to launch and
drive a worker for the task, using the role fragment as its system-prompt append
(absolute path — the worker's cwd may not be this vault).
