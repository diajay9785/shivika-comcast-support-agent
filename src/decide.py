"""
Decision logic. Matches identity/entity.md exactly:

- AUTO: only clearly low-stakes intents (account_general -- general info,
  status-type questions). Everything else drafts for human review.
- Hard rules override intent-based logic entirely: any mention of
  cancellation, legal action, or safety always escalates, regardless of
  intent or confidence.
- venting / off_topic are NOT run through normal auto/draft logic -- see
  pipeline.py, which routes them differently before this function is
  even called for the "reply" path.
"""

HARD_RULE_TRIGGERS = [
    "cancel", "cancellation", "cancelling", "canceling",
    "legal", "lawyer", "sue", "lawsuit",
    "safety", "danger", "unsafe", "fire hazard",
]

AUTO_SEND_INTENTS = {"account_general"}
# service_outage deliberately excluded from auto-send: Shivika has no live
# outage-status data to verify against, so any outage-related reply risks
# being confidently wrong -- consistent with every outage example in the
# golden set being labeled DRAFT-HOLD (see decision_log.md).


def decide(intent, text):
    lower = text.lower()

    # hard rules always win, regardless of intent
    if any(trigger in lower for trigger in HARD_RULE_TRIGGERS):
        return "escalate_priority"

    if intent == "billing_dispute":
        # never auto-send anything touching money -- hard rule in entity.md
        return "draft_hold"

    if intent in AUTO_SEND_INTENTS:
        return "auto_send"

    return "draft_hold"