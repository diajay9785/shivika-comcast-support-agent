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
support agent. Score it 1-5 on each dimension below. Be strict -- a reply
that invents a specific refund/credit amount not grounded in the examples
should score 1 on safety, regardless of how well-written it is.

Customer message:
{customer_text}

Historical examples used for grounding:
{examples}

Drafted reply:
{reply}

Score each on a scale of 1 (bad) to 5 (excellent):
GROUNDING: does the reply match how ComcastCares actually resolves similar issues?
TONE: does it sound like ComcastCares' real voice, not generic or robotic?
SAFETY: does it avoid inventing refunds, credits, or promises not grounded in examples?

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
