from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_core.gemini_generator import GeminiDocumentGenerator

router = APIRouter()
_generator = None


def get_generator() -> GeminiDocumentGenerator:
    """Created lazily so a missing API key gives a clear error, not a crash at import."""
    global _generator
    if _generator is None:
        _generator = GeminiDocumentGenerator()
    return _generator


class DocumentRequest(BaseModel):
    document_type: str = Field(min_length=2)
    parties: str = Field(min_length=2)
    terms: str = ""
    dates: str = ""


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/generate")
def generate_legal_document(request: DocumentRequest):
    try:
        response = get_generator().generate_document(
            request.document_type, request.parties, request.terms, request.dates
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI service error: {exc}")
    return {"document": response}
