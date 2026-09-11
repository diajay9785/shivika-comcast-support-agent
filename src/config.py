import os
from dotenv import load_dotenv

load_dotenv()  # reads the local .env file, never commit that file

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not found. Copy .env.example to .env and fill in your key."
    )
