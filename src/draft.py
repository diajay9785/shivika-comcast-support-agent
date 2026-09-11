from llm_client import call_llm


def draft_reply(text, examples):
    context = "\n".join(
        f"Customer: {e.get('text', '')}\nReply: {e.get('response', '')}"
        for e in examples
    )

    prompt = f"""
Draft a ComcastCares reply to this customer message.

Customer message:
{text}

Historical examples:
{context}

Use the historical examples to match the existing ComcastCares tone.
Do not invent refunds, credits, or specific promises.
Return only the reply.
"""
    result = call_llm(prompt)
    return result["text"].strip(), result["model"]