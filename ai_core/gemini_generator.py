"""AI core: turns user inputs into a structured prompt and calls Gemini."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FALLBACK_MODELS, MOCK_MODE  # noqa: E402

SYSTEM_INSTRUCTION = (
    "You are a careful legal drafting assistant. Write formal, well-structured legal "
    "documents with numbered sections and clear clauses. Use plain text with numbered "
    "section headings like '1. Services:'. Do not use markdown symbols such as ** or ##. "
    "Where information is missing, use square-bracket placeholders like [Address]. "
    "Do not add commentary before or after the document."
)


class GeminiDocumentGenerator:
    def __init__(self, model_name: str | None = None):
        self.model_names = [model_name or GEMINI_MODEL] + GEMINI_FALLBACK_MODELS
        self.client = None
        if not MOCK_MODE:
            if not GEMINI_API_KEY:
                raise RuntimeError(
                    "GEMINI_API_KEY is missing. Copy .env.example to .env and paste your key "
                    "from https://aistudio.google.com/apikey"
                )
            from google import genai  # new official SDK (google-genai)

            self.client = genai.Client(api_key=GEMINI_API_KEY)

    @staticmethod
    def build_prompt(document_type: str, parties: str, terms: str, dates: str) -> str:
        term_lines = "\n".join(f"- {t.strip()}" for t in terms.split(";") if t.strip())
        return (
            f"Generate a comprehensive legal document titled '{document_type}'.\n"
            f"Involved parties: {parties}\n"
            f"Effective date: {dates}\n"
            f"Terms and conditions (must all be included as clauses):\n{term_lines}\n\n"
            "Ensure formal legal structure with multiple numbered sections, recitals, "
            "governing law, termination, confidentiality where relevant, and a signature block."
        )

    def generate_document(self, document_type, parties, terms, dates) -> str:
        if MOCK_MODE:
            return _mock_document(document_type, parties, terms, dates)

        from google.genai import types

        prompt = self.build_prompt(document_type, parties, terms, dates)
        last_error = None
        for name in self.model_names:
            try:
                response = self.client.models.generate_content(
                    model=name,
                    contents=prompt,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
                )
                if response.text:
                    return response.text
                last_error = RuntimeError("Model returned an empty response")
            except Exception as exc:  # try the next model only for "model gone" errors
                last_error = exc
                msg = str(exc).lower()
                if not any(k in msg for k in ("not found", "no longer available", "404", "not supported")):
                    raise
        raise RuntimeError(f"All models failed. Last error: {last_error}")


def _mock_document(document_type, parties, terms, dates) -> str:
    clauses = [t.strip() for t in terms.split(";") if t.strip()]
    body = "\n".join(f"{i}. Clause {i}: {c}." for i, c in enumerate(clauses, start=1))
    return (
        f"{document_type}\n\n"
        f"This Agreement is made effective on {dates}.\n\n"
        f"Between:\n{parties}\n\n"
        "WITNESSETH:\n\n"
        "WHEREAS, the parties wish to record the terms of their arrangement;\n\n"
        "NOW, THEREFORE, the parties agree as follows:\n\n"
        "1. Terms and Conditions:\n"
        f"{body}\n\n"
        "2. Governing Law:\n"
        "This Agreement shall be governed by the laws of [State/Country].\n\n"
        "3. Entire Agreement:\n"
        "This Agreement is the entire understanding of the parties.\n\n"
        "IN WITNESS WHEREOF, the parties have executed this Agreement as of the Effective Date.\n\n"
        "______________________\n[Party 1 Signature]\n\n______________________\n[Party 2 Signature]"
    )
