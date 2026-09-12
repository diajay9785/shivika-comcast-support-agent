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
    "fraud", "scam",
]
# NOTE (decision_log.md): "fraud"/"scam" are plain literal keywords, kept
# deliberately simple -- unlike the two semantic categories below, a loose
# match here only costs a queue-priority difference (escalate_priority vs
# draft_hold both route to a human either way), so over-triggering is cheap
# and not worth the same rigor as the money-risk categories.

# Three named semantic hard-rule categories (not literal-keyword-only).
# All three route to escalate_priority for the same underlying reason: a
# wrong auto-response on any of these has outsized cost (lost customer,
# legal exposure, reputational damage) -- directly tied to the Aim.
# Discovered iteratively during golden-set labeling: the same gap-class
# (literal keyword missing a plainly-phrased equivalent) surfaced three
# times independently (unauthorized billing, competitor-switch threats,
# explicit cancellation), which is what justified generalizing the fix
# instead of patching individual phrases indefinitely.

NEVER_A_CUSTOMER_PATTERNS = [
    "never been a customer", "never a customer", "not a customer",
    "never used this company", "never signed up",
]

CHURN_THREAT_PATTERNS = [
    "new provider", "find a new provider", "switch to", "switching to",
    "cut the cord", "cancel my service", "i can switch", "going elsewhere",
    "time to find a new",
]

AUTO_SEND_INTENTS = {"account_general"}
# service_outage deliberately excluded from auto-send: Shivika has no live
# outage-status data to verify against, so any outage-related reply risks
# being confidently wrong -- consistent with every outage example in the
# golden set being labeled DRAFT-HOLD (see decision_log.md).

# Even within account_general, most examples in the golden set were NOT
# safe to auto-send -- only genuinely clean, simple questions were (e.g.
# "will the modem be shipped or do I pick it up"). Confused, complaint-
# adjacent, or uncertain account_general messages still need a human.
# Found via eval: the pipeline was wrongly auto-sending on cases like a
# customer confused about a signup email, and even a misclassified billing
# dispute -- exactly the costly error type the Aim exists to prevent.
NOT_CLEAN_ENOUGH_FOR_AUTO = [
    "confused", "confusing", "not sure", "don't understand", "unclear",
    "problem", "issue", "wrong", "mistake", "error", "sketchy", "weird",
    "worried", "concern", "upset", "frustrat",
    "login", "log in", "password", "username", "verify", "security",
    # account-access/credential requests specifically: established during
    # ambiguous-batch golden-set labeling that these need human
    # verification regardless of how the request is phrased (see
    # decision_log.md) -- confirmed necessary again by eval failure #5.
]


def decide(intent, text):
    lower = text.lower()

    # hard rules always win, regardless of intent
    if any(trigger in lower for trigger in HARD_RULE_TRIGGERS):
        return "escalate_priority"

    if any(p in lower for p in NEVER_A_CUSTOMER_PATTERNS):
        return "escalate_priority"

    if any(p in lower for p in CHURN_THREAT_PATTERNS):
        return "escalate_priority"

    if intent == "billing_dispute":
        # never auto-send anything touching money -- hard rule in entity.md
        return "draft_hold"

    if intent in AUTO_SEND_INTENTS:
        if any(signal in lower for signal in NOT_CLEAN_ENOUGH_FOR_AUTO):
            return "draft_hold"
        return "auto_send"

    return "draft_hold"