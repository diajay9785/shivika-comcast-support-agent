"""
Single entry point for all LLM calls in the pipeline.
Primary: Gemini (free tier). Fallback: Groq, only on rate-limit errors.
Every call result is tagged with which model actually answered, so eval
can report agreement/quality per judge_model separately (never pooled).
"""

import time
import google.generativeai as genai
from groq import Groq

from config import GEMINI_API_KEY, GROQ_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
_gemini_model = genai.GenerativeModel("gemini-1.5-flash")
_groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def call_llm(prompt: str, max_retries: int = 2) -> dict:
    """
    Returns: {"text": <model output>, "model": "gemini" | "groq"}
    Tries Gemini first. Falls back to Groq only on a rate-limit style error.
    """
    try:
        response = _gemini_model.generate_content(prompt)
        return {"text": response.text, "model": "gemini"}
    except Exception as e:
        err = str(e).lower()
        is_rate_limit = "quota" in err or "rate" in err or "429" in err
        if is_rate_limit and _groq_client is not None:
            completion = _groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
            )
            return {"text": completion.choices[0].message.content, "model": "groq"}
        raise
