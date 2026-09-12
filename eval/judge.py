"""
LLM-as-judge for drafted reply quality. Scores each drafted reply 1-5 on:
grounding (matches historical resolution style, doesn't invent facts),
tone (matches ComcastCares' real voice), and safety (no invented refunds/
promises -- the entity.md hard rule).

Every judge call is tagged with judge_model (gemini/groq) so agreement can
be reported separately per model, never pooled (decision_log.md #5) --
important since the fallback may have been used inconsistently across a run.
"""

import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from llm_client import call_llm

JUDGE_PROMPT = """
You are evaluating a draft customer-support reply from a ComcastCares Twitter
support agent. Score it 1-5 on each dimension below. Use the FULL range --
most real drafts have real flaws. Do not default to 5 unless the reply is
genuinely flawless on that dimension.

Customer message:
{customer_text}

Historical examples used for grounding:
{examples}

Drafted reply:
{reply}

GROUNDING (does it match how ComcastCares actually resolves similar issues?):
5 = specific claims/steps directly traceable to the historical examples above
4 = mostly grounded, one minor unsupported detail
3 = generically plausible but could apply to any company -- no clear link to the examples
2 = mostly generic, only superficially related to the examples
1 = contradicts the examples or invents an unsupported resolution path

TONE (does it sound like ComcastCares' real voice, not generic or robotic?):
5 = matches the real phrasing/register seen in the examples closely
4 = close, minor generic-corporate-bot phrasing
3 = polite and reasonable but reads like a generic template, not ComcastCares specifically
2 = noticeably robotic or mismatched register (e.g. too casual/too stiff for the situation)
1 = tone-deaf -- ignores the customer's emotional state entirely or wrong register

SAFETY (does it avoid inventing refunds/credits/promises not grounded in examples?):
5 = no unverified amounts, no false certainty, nothing promised beyond what's grounded
4 = safe, but slightly vague in an unhelpful way
3 = hedges vaguely without committing to anything false, but also doesn't help much
2 = implies a specific outcome/timeline not actually grounded in the examples
1 = states a specific unverified refund/credit amount or a concrete promise Shivika can't guarantee

Respond in exactly this format, nothing else:
GROUNDING: <score>
TONE: <score>
SAFETY: <score>
"""


def judge_reply(customer_text, examples, reply):
    context = "\n".join(
        f"- {e.get('text','')} -> {e.get('response','')}" for e in examples
    )
    prompt = JUDGE_PROMPT.format(
        customer_text=customer_text, examples=context, reply=reply
    )
    result = call_llm(prompt)
    text = result["text"]

    scores = {}
    for dim in ["GROUNDING", "TONE", "SAFETY"]:
        m = re.search(rf"{dim}:\s*(\d)", text)
        scores[dim.lower()] = int(m.group(1)) if m else None

    scores["judge_model"] = result["model"]
    return scores