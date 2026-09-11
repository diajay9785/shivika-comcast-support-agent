"""
Single entry point for all LLM calls in the pipeline.
Primary: Gemini (free tier, google-genai SDK). Fallback: Groq, on ANY
Gemini failure (rate limit, dropped connection, timeout, etc) -- not just
rate-limit-shaped errors, since network drops don't look like quota errors.
Retries Gemini once before falling back, since transient drops often
succeed on retry alone.
"""

import time
from google import genai
from groq import Groq

from config import GEMINI_API_KEY, GROQ_API_KEY

_gemini_client = genai.Client(api_key=GEMINI_API_KEY)
_groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

GEMINI_MODEL = "gemini-3.6-flash"
GROQ_MODEL = "openai/gpt-oss-120b"


def call_llm(prompt: str) -> dict:
    """
    Returns: {"text": <model output>, "model": "gemini" | "groq"}
    """
    for attempt in range(2):  # try Gemini twice before falling back
        try:
            response = _gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return {"text": response.text, "model": "gemini"}
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
                continue
            # both Gemini attempts failed -- fall back to Groq
            if _groq_client is None:
                raise
            completion = _groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            return {"text": completion.choices[0].message.content, "model": "groq"}