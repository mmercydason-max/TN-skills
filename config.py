"""Central configuration for LegalEase.

Every setting can be overridden from the .env file in the project root.
Both the FastAPI backend and the Streamlit frontend import this module.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

# --- Gemini -----------------------------------------------------------------
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
# gemini-1.5-* models were retired by Google; 2.5 is the current stable family.
# Use "gemini-2.5-pro" for the highest drafting quality (slower, lower free quota).
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))

# --- Backend / frontend wiring ------------------------------------------------
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "180"))  # seconds

# --- Branding -----------------------------------------------------------------
COMPANY_NAME: str = os.getenv("COMPANY_NAME", "LegalEase")
FOOTER_TEXT: str = os.getenv(
    "FOOTER_TEXT", "LegalEase Inc. | contact@legalease.com | All Rights Reserved."
)
DISCLAIMER: str = (
    "This document was drafted with AI assistance and is provided for general "
    "informational purposes only. It is not legal advice. Have a qualified "
    "lawyer review it before signing."
)
LOGO_PATH: Path = ROOT_DIR / "Image" / "Logo.png"            # dark text, for DOCX/PDF
WEB_LOGO_PATH: Path = ROOT_DIR / "Image" / "inverseLogo.png"  # light text, for dark web UI
