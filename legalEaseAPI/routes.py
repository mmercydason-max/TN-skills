"""API routes: POST /generate and GET /health."""
import logging
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

import config
from ai_core.gemini_generator import GeminiDocumentGenerator, GeminiGenerationError

logger = logging.getLogger("legalease.api")
router = APIRouter()


class DocumentRequest(BaseModel):
    document_type: str = Field(..., min_length=2, max_length=200)
    parties: str = Field(..., min_length=2, max_length=3000)
    terms: str = Field(default="", max_length=10000)
    dates: str = Field(..., min_length=2, max_length=100)

    @field_validator("document_type", "parties", "terms", "dates", mode="before")
    @classmethod
    def _strip(cls, value):
        return value.strip() if isinstance(value, str) else value


@lru_cache(maxsize=1)
def get_generator() -> GeminiDocumentGenerator:
    """Created lazily so the API still starts (and /health works) without an API key."""
    return GeminiDocumentGenerator()


@router.get("/health")
def health():
    key = config.GEMINI_API_KEY
    return {
        "status": "ok",
        "model": config.GEMINI_MODEL,
        "api_key_configured": bool(key) and key != "your_gemini_api_key_here",
    }


@router.post("/generate")
def generate_legal_document(request: DocumentRequest):
    try:
        generator = get_generator()
        response = generator.generate_document(
            request.document_type, request.parties, request.terms, request.dates
        )
    except GeminiGenerationError as exc:
        logger.warning("Generation failed: %s", exc)
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    return {"document": response}
