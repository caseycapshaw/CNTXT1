---
type: job
domain: "{{domain}}"
trigger: "{{NAME}} asks for a {{domain}} review/check-in, or the periodic cadence comes due"
frequency: ad-hoc (natural cadence ~{{monthly/quarterly}})
tools: "{{connectors/CLIs used}}, Read, Write, Edit, Bash"
owner: {{NAME}}
status: active
tags: [job]
aliases: [{{Domain}} review, {{Domain}} check-in]
---

# Job — Run a {{domain}} review

<!-- TEMPLATE — copy to Jobs/Run a <domain> review.md and fill every
     {{placeholder}}. Pairs with a role file built from
     `meta/agent-roles/domain-advisor TEMPLATE.md`: the role carries the
     stance (sources, caveats, checklist, sync contract); this job carries
     the steps. -->

> **When:** on request, or the periodic pass · **Tools:** {{sources}} · vault ·
> **Outcome:** fresh {{domain}} state with anomalies flagged and the KB synced
> per the advisor's contract.

## When to run this

{{NAME}} asks for a {{domain}} review or a "where are we" check, or the
cadence comes due.

## Steps

1. **Load the role:** read `meta/agent-roles/{{domain}}-advisor.md` —
   guardrail, source caveats, anomaly checklist, KB-sync contract all live
   there.
2. **Pull sources:** work through the role's source playbook, applying its
   caveats and canonical-figure rules.
3. **Anomaly sweep:** run the role's checklist against the pull; chase
   anything odd back to its source.
4. **KB sync:** execute the role's KB-sync contract (raw/ capture → home-note
   state update → index one-liner → log line). Commit.
5. **Report to {{NAME}}:** current state vs. last pull, anomalies (or
   "none"), and any `#action` lines added.

## Gotchas / rules

- **Read-only guardrail** — see the role file; no external writes or
  outbound sends without explicit approval.
- {{source-specific gotchas — broken endpoints, interactive-only connectors}}

## Done when

- [ ] Fresh state reported with anomalies flagged (or "none")
- [ ] KB-sync contract executed for a substantive pull (raw/, home note, index, log)

## Related

`{{home note}}` · `meta/agent-roles/{{domain}}-advisor.md` (the role) · [[jobs]] · [[AGENTS]]
