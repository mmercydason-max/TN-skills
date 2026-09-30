"""Gemini integration: builds the drafting prompt and calls the model."""
import logging
import time
from typing import Optional

from google import genai
from google.genai import errors, types

import config
from ai_core.text_utils import sanitize_text, split_terms

logger = logging.getLogger("legalease.gemini")

MAX_ATTEMPTS = 3
RETRYABLE_CODES = {429, 500, 503, 504}

SYSTEM_INSTRUCTION = """\
You are a senior legal drafter who prepares clear, professional, well-structured legal documents.

OUTPUT FORMAT (strict):
- Plain text only. No markdown bold/italics, no code fences, no tables, no preamble, no closing commentary.
- First line: "# <Document Title>".
- Each section heading on its own line, starting with "## " and numbered, e.g. "## 1. Definitions".
- Clauses are normal paragraphs under their heading. Sub-clauses start on new lines with "(a)", "(b)", ...
- Simple lists use lines starting with "- ".

DRAFTING RULES:
- Use the parties, effective date and terms exactly as supplied. Never invent names, amounts, dates or addresses.
- Where information is missing (addresses, amounts, governing law, notice periods), insert a square-bracket placeholder such as [Client Address] or [Governing Law / Jurisdiction].
- Turn EVERY user-supplied term into a proper, enforceable-sounding clause.
- Include the standard clauses suited to the document type (for example: recitals/purpose, definitions, term and termination, payment or consideration, confidentiality, intellectual property, liability, dispute resolution, governing law, notices, amendments, entire agreement, severability).
- Use formal but plain legal English.
- Finish with an "IN WITNESS WHEREOF" statement and a signature block (name, title, signature line, date) for each party.
"""


class GeminiGenerationError(Exception):
    """Raised for any failure while generating a document."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class GeminiDocumentGenerator:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = (api_key or config.GEMINI_API_KEY).strip()
        self.model_name = (model_name or config.GEMINI_MODEL).strip()
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise GeminiGenerationError(
                "GEMINI_API_KEY is not set. Add your key to the .env file and restart the backend.",
                503,
            )
        self.client = genai.Client(api_key=self.api_key)
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=config.GEMINI_TEMPERATURE,
        )

    @staticmethod
    def build_prompt(document_type: str, parties: str, terms: str, dates: str) -> str:
        term_lines = split_terms(terms)
        terms_block = "\n".join(f"- {t}" for t in term_lines) if term_lines else "- (none supplied; use sensible standard terms)"
        return (
            f"Draft a complete legal document titled '{document_type.strip()}'.\n\n"
            f"Involved parties:\n{parties.strip()}\n\n"
            f"Effective date: {dates.strip()}\n\n"
            f"Terms and conditions that MUST each appear as a clause:\n{terms_block}\n\n"
            "Ensure formal legal structure with multiple numbered sections and legal clauses."
        )

    def generate_document(self, document_type: str, parties: str, terms: str, dates: str) -> str:
        prompt = self.build_prompt(document_type, parties, terms, dates)
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name, contents=prompt, config=self._config
                )
                text = sanitize_text(response.text or "")
                if not text:
                    raise GeminiGenerationError(
                        "Gemini returned an empty response (possibly blocked by safety filters). "
                        "Try rewording the inputs.",
                        502,
                    )
                return text
            except errors.APIError as exc:
                code = getattr(exc, "code", None) or 502
                if code in RETRYABLE_CODES and attempt < MAX_ATTEMPTS:
                    wait = 2 ** attempt
                    logger.warning("Gemini error %s (attempt %d/%d); retrying in %ss", code, attempt, MAX_ATTEMPTS, wait)
                    time.sleep(wait)
                    continue
                raise GeminiGenerationError(self._friendly_error(code, exc), 429 if code == 429 else 502) from exc
            except GeminiGenerationError:
                raise
            except Exception as exc:  # network problems, SDK errors, etc.
                logger.exception("Unexpected Gemini failure")
                raise GeminiGenerationError(f"Could not reach Gemini: {exc}", 502) from exc
        raise GeminiGenerationError("Gemini did not return a result.", 502)  # pragma: no cover

    def _friendly_error(self, code: int, exc: Exception) -> str:
        detail = getattr(exc, "message", None) or str(exc)
        low = detail.lower()
        if "api key" in low or code in (401, 403):
            return "Gemini rejected the API key. Check GEMINI_API_KEY in your .env file."
        if code == 404:
            return (f"Model '{self.model_name}' was not found. Set GEMINI_MODEL in .env to an "
                    "available model such as gemini-2.5-flash or gemini-2.5-pro.")
        if code == 429:
            return "Gemini rate limit or quota reached. Wait a minute and try again, or use a different model."
        return f"Gemini API error ({code}): {detail}"
