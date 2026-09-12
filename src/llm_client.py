"""
Single entry point for all LLM calls in the pipeline.
Primary: Gemini (free tier, google-genai SDK). Fallback: Groq, on Gemini
failure. Gemini's free tier is rate-limited to roughly 10-15 requests per
minute -- calls are throttled here to stay under that, since a 2-second
retry (the old behavior) is nowhere near long enough to clear a per-minute
rate-limit window and was causing near-constant, unnecessary fallback to
Groq (which then burned through Groq's daily quota instead). See
decision_log.md for the full story -- this was found and fixed after the
full-sample run hit a Groq daily cap by row 334.
"""

import time
from google import genai
from groq import Groq

from config import GEMINI_API_KEY, GROQ_API_KEY

_gemini_client = genai.Client(api_key=GEMINI_API_KEY)
_groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

GEMINI_MODEL = "gemini-3.6-flash"
GROQ_MODEL = "openai/gpt-oss-120b"

# Stay comfortably under Gemini free tier's ~10-15 RPM. 5s between calls
# = 12 calls/min, safely under the ceiling with margin for jitter.
MIN_SECONDS_BETWEEN_GEMINI_CALLS = 5.0
_last_gemini_call_time = 0.0


def _throttle_gemini():
    global _last_gemini_call_time
    elapsed = time.time() - _last_gemini_call_time
    wait = MIN_SECONDS_BETWEEN_GEMINI_CALLS - elapsed
    if wait > 0:
        time.sleep(wait)
    _last_gemini_call_time = time.time()


def call_llm(prompt: str) -> dict:
    """
    Returns: {"text": <model output>, "model": "gemini" | "groq"}
    Retries Gemini up to 3 times (with real backoff on rate-limit errors)
    before ever touching Groq -- Groq's free tier has proven unreliable
    under real load, so leaning on Gemini harder is the safer default.
    """
    last_gemini_error = None
    for attempt in range(3):
        _throttle_gemini()
        try:
            response = _gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return {"text": response.text, "model": "gemini"}
        except Exception as e:
            last_gemini_error = e
            err = str(e).lower()
            is_rate_limit = "429" in err or "rate" in err or "quota" in err
            print(f"  [Gemini attempt {attempt+1} failed: {type(e).__name__}: {str(e)[:150]}]")
            if attempt < 2:
                time.sleep(65 if is_rate_limit else 3)
                continue

    # all 3 Gemini attempts failed -- try Groq once as last resort
    if _groq_client is not None:
        try:
            completion = _groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            return {"text": completion.choices[0].message.content, "model": "groq"}
        except Exception as groq_error:
            print(f"  [Groq also failed: {type(groq_error).__name__}: {str(groq_error)[:150]}]")

    # last resort: one more Gemini attempt after a longer cooldown, rather
    # than crashing the whole run outright
    print("  [Both providers failed -- waiting 90s for one final Gemini attempt]")
    time.sleep(90)
    _throttle_gemini()
    response = _gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return {"text": response.text, "model": "gemini"}