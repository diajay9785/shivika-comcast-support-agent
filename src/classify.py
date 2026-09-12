from llm_client import call_llm

# Matches identity/entity.md exactly -- do not edit without updating that file too
INTENTS = [
    "service_outage",       # Service Outage / Connectivity Issue
    "billing_dispute",      # Billing / Charge Dispute
    "device_malfunction",   # Equipment / Device Malfunction
    "installation_appt",    # Installation / Appointment Scheduling
    "account_general",      # Account / General Inquiry
    "venting",               # Venting / Non-Actionable Complaint
    "off_topic",             # Off-Topic / Not a Support Request
]


def classify(text):
    prompt = f"""
Classify this tweet directed at ComcastCares into exactly one category.

Categories:
- service_outage: internet/cable/phone service is down or degraded
- billing_dispute: charges, fees, refunds, pricing complaints
- device_malfunction: equipment/box/modem/app not working properly (not a full outage)
- installation_appt: technician visits, installation, repair scheduling
- account_general: account questions, plan info, how-to questions, general info requests
- venting: frustration or anger with NO specific, actionable issue underneath
- off_topic: not actually a ComcastCares support request at all

CRITICAL RULE for venting: angry, sarcastic, or profane tone alone does NOT
make something venting. If there is a real, fixable issue underneath the
anger (an outage, a broken device, a billing dispute), classify it as that
issue -- NOT venting. Venting is ONLY for messages with no specific
actionable request at all (pure complaints like "your service sucks" with
no fixable detail given).

Examples:
- "internet down again, so sick of this garbage company!!" -> service_outage
  (angry tone, but there's a real outage being reported)
- "you guys are the worst, nothing ever works" -> venting
  (no specific fixable detail, just a general complaint)
- "box keeps freezing, this is ridiculous" -> device_malfunction
  (angry, but names a specific broken device)

Message:
{text}

Return only the category name, exactly as written above, nothing else.
"""
    result = call_llm(prompt)
    label = result["text"].strip().lower()
    # guard against the model returning something slightly off-format
    for intent in INTENTS:
        if intent in label:
            return intent, result["model"]
    return "off_topic", result["model"]  # safe default if nothing matches