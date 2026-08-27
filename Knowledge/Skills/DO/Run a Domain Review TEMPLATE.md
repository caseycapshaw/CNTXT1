---
type: do
domain: "{{domain}}"
trigger: "{{NAME}} asks for a {{domain}} review, or the cadence comes due"
frequency: on request / periodic
tools: ["{{connectors/CLIs used}}", "Read", "Write", "Edit", "Bash"]
owner: "{{NAME}}"
status: active
tags: [do, "{{domain}}"]
aliases: ["Run a {{domain}} review", "{{Domain}} review", "{{Domain}} check-in"]
summary: "One sentence: what the {{domain}} review does + when to use it."
---

# Skill — Run a {{domain}} review

<!-- TEMPLATE — copy to Knowledge/Skills/DO/Run a {{Domain}} Review.md and fill every
     {{placeholder}}. Pairs with a role file built from
     `Knowledge/Agents/domain-advisor TEMPLATE.md`: the role carries the
     stance (sources, caveats, checklist, sync contract); this skill carries
     the steps. -->

> **When:** on request, or the periodic pass · **Tools:** {{sources}} · vault ·
> **Outcome:** fresh {{domain}} state with anomalies flagged and the KB synced
> per the advisor's contract.

## When to run this

{{NAME}} asks for a {{domain}} review or a "where are we" check, or the
cadence comes due.

## Steps

1. **Load the role:** read `Knowledge/Agents/{{domain}}-advisor.md` —
   guardrail, source caveats, anomaly checklist, KB-sync contract all live
   there.
2. **Pull sources:** work through the role's source playbook, applying its
   caveats and canonical-figure rules.
3. **Anomaly sweep:** run the role's checklist against the pull; chase
   anything odd back to its source.
4. **KB sync:** execute the role's KB-sync contract (Knowledge/raw/ capture → home-note
   state update → index one-liner → log line). Commit.
5. **Report to {{NAME}}:** current state vs. last pull, anomalies (or
   "none"), and any `#action` lines added.

## Gotchas / rules

- **Read-only guardrail** — see the role file; no external writes or
  outbound sends without explicit approval.
- {{source-specific gotchas — broken endpoints, interactive-only connectors}}

## Done when

- [ ] Fresh state reported with anomalies flagged (or "none")
- [ ] KB-sync contract executed for a substantive pull (Knowledge/raw/, home note, index, log)

## Related

`{{home note}}` · `Knowledge/Agents/{{domain}}-advisor.md` (the role) · [[skills]] · [[SCHEMA]]
