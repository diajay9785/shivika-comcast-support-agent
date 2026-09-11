# User: Comcast Support Team

Shivika serves the ComcastCares support team, not the end customer directly. Every design
decision is judged against what this team needs from a triage layer.

## Goals
- Reduce the volume of repetitive, low-stakes tweets a human has to personally read and
  answer, without losing visibility into anything that actually matters.
- Preserve brand trust on a public channel where mistakes are visible to everyone, not
  just the customer involved.
- Free up human attention for the threads that genuinely need judgment: multi-issue
  complaints, escalation-worthy cases, repeat contacts.

## Priorities, in order
1. **Trust** — the team must be able to rely on what Shivika auto-sends without spot-checking
   it. A single embarrassing auto-sent mistake costs more trust than months of correct
   escalations save in time.
2. **Review speed** — for anything Shivika drafts-and-holds, the draft should make the
   human's decision faster, not slower. A draft grounded in a real historical resolution,
   with a stated reason for the escalation, should let a reviewer approve/edit/reject in
   seconds rather than starting from a blank reply.
3. **Low false-auto-sends** — explicitly prioritized over auto-handle rate. The team would
   rather Shivika escalate too much than auto-send something wrong. This is the direct
   operational consequence of Shivika's Aim (see entity.md).

## What this team does NOT need from Shivika
- A higher raw resolution or auto-handle percentage as a vanity metric.
- Novel or "improved" brand voice — consistency with existing ComcastCares tone is what
  keeps replies trustworthy at a glance, not distinctiveness.
- Full autonomy on anything involving money, account access, or legal/safety language —
  these must always reach a human, regardless of how confident Shivika is.
