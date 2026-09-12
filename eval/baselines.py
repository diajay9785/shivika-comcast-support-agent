"""
Two baselines, per Hiver's requirement to compare against "a trivial one
and a simple one."

TRIVIAL: always predict the most common intent/decision in the golden set.
No logic at all -- the floor any real system must beat.

SIMPLE: keyword-based intent classifier (same style of regex used during
golden-set sampling exploration) + the real decide.py hard-rule logic
(no LLM calls needed for either -- these baselines are free to run).
"""

import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from decide import decide as real_decide  # reuse the actual hard-rule logic

TRIVIAL_INTENT = "service_outage"   # most common in golden_set.csv
TRIVIAL_DECISION = "draft_hold"     # most common in golden_set.csv


def trivial_baseline(text):
    return TRIVIAL_INTENT, TRIVIAL_DECISION


KEYWORD_PATTERNS = {
    "service_outage": r"down|outage|no internet|no service|not working|offline|slow",
    "billing_dispute": r"charge|bill|overage|fee|refund|price|cost|paid|payment",
    "device_malfunction": r"box|modem|router|app|error|remote|equipment|reset|crash",
    "installation_appt": r"appointment|technician|install|schedul|repair",
    "account_general": r"how (do|can)|eta|account|plan|upgrade",
}


def simple_classify(text):
    lower = text.lower()
    for intent, pattern in KEYWORD_PATTERNS.items():
        if re.search(pattern, lower):
            return intent
    return "off_topic"


def simple_baseline(text):
    intent = simple_classify(text)
    decision = real_decide(intent, text)  # reuse real hard-rule logic, free (no LLM)
    return intent, decision
