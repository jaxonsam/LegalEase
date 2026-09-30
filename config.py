"""Central configuration. Values come from the .env file (never commit .env!)."""
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Model names change often. If one is retired, just edit GEMINI_MODEL in .env.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
# Tried in order if the main model returns "not found / no longer available".
GEMINI_FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.1-flash-lite,gemini-3.8-flash").split(",")
    if m.strip()
]
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
# Set LEGALEASE_MOCK=1 to run without an API key (returns a sample contract).
MOCK_MODE = os.getenv("LEGALEASE_MOCK", "0") == "1"
