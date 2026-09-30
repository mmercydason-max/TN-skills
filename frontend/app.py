"""LegalEase Streamlit frontend.  Run from the project root:

    streamlit run frontend/app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:          # so "import config" / "import ai_core" work
    sys.path.insert(0, str(ROOT))

import requests
import streamlit as st

import config
from ai_core.generator import format_docx, format_html_preview, format_pdf, sanitize_text
from ai_core.text_utils import slugify

st.set_page_config(page_title="LegalEase", page_icon="⚖️", layout="centered")

# ------------------------------------------------------------------ helpers
@st.cache_data(show_spinner=False)
def build_docx(text: str, doc_type: str, terms: str) -> bytes:
    return format_docx(text, doc_type, terms)


@st.cache_data(show_spinner=False)
def build_pdf(text: str, doc_type: str, terms: str) -> bytes:
    return format_pdf(text, doc_type, terms)


def backend_status():
    try:
        r = requests.get(f"{config.BACKEND_URL}/health", timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def call_backend(payload: dict) -> str:
    try:
        resp = requests.post(f"{config.BACKEND_URL}/generate", json=payload, timeout=config.REQUEST_TIMEOUT)
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot reach the backend at {config.BACKEND_URL}. Start it with: "
            "uvicorn legalEaseAPI.main:app --reload"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("The request timed out. Please try again.")
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except ValueError:
            detail = resp.text
        if isinstance(detail, list):  # FastAPI validation errors
            detail = "; ".join(f"{'.'.join(map(str, d.get('loc', [])[1:]))}: {d.get('msg')}" for d in detail)
        raise RuntimeError(str(detail))
    return sanitize_text(resp.json()["document"])


ss = st.session_state
ss.setdefault("generated_text", "")
ss.setdefault("doc_type", "")
ss.setdefault("terms", "")
ss.setdefault("show_edit", False)

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.subheader("Backend status")
    status = backend_status()
    if status is None:
        st.error("Backend not reachable")
        st.caption(f"Expected at {config.BACKEND_URL}")
    else:
        st.success("Backend online")
        st.caption(f"Model: {status.get('model')}")
        if not status.get("api_key_configured"):
            st.warning("GEMINI_API_KEY is not set in .env")
    st.button("Refresh")

# ------------------------------------------------------------------ header
_, mid, _ = st.columns([1, 2, 1])
with mid:
    if config.WEB_LOGO_PATH.exists():
        st.image(str(config.WEB_LOGO_PATH), width=340)
st.markdown("<h2 style='text-align: center;'>AI Legal Document Generator</h2>", unsafe_allow_html=True)

# ------------------------------------------------------------------ inputs
document_type = st.text_input("Document Type (Ex: Agreement, Contract, NDA)", placeholder="Freelance Work Contract")
parties = st.text_area("Parties Involved", placeholder="Jane Doe (Service Provider), TechNova Inc. (Client)")
terms = st.text_area(
    "Terms & Conditions (Use semicolons for bullet points)",
    placeholder="Work must be delivered by May 15, 2025; Payment within 7 days of invoice; The client retains intellectual property rights",
)
dates = st.text_input("Effective Date", placeholder="April 15, 2025")

if st.button("Generate Document", type="primary"):
    if not (document_type.strip() and parties.strip() and dates.strip()):
        st.warning("Please fill in Document Type, Parties Involved and Effective Date.")
    else:
        with st.spinner("Drafting your document with Gemini... this can take up to a minute."):
            try:
                text = call_backend({
                    "document_type": document_type, "parties": parties,
                    "terms": terms, "dates": dates,
                })
            except RuntimeError as exc:
                st.error(f"❌ {exc}")
            else:
                ss.generated_text = text
                ss.doc_type = document_type.strip()
                ss.terms = terms
                ss.show_edit = False
                ss["editor"] = text          # reset the editor to the new draft
                st.success("✅ Document Generated Successfully!")

# ------------------------------------------------------------------ preview / edit / download
if ss.generated_text:
    if ss.show_edit and "editor" in ss:      # apply edits before rendering the preview
        ss.generated_text = ss["editor"]

    styled_html = format_html_preview(ss.generated_text)
    st.markdown(
        "<div style='background:#0f1626;border:1px solid #26314d;border-radius:10px;padding:20px 24px;"
        "max-height:480px;overflow-y:auto;font-family:Georgia,serif;font-size:15px;color:#e8ecf5;'>"
        f"{styled_html}</div>",
        unsafe_allow_html=True,
    )

    if st.button("✏️ Click to Edit Document"):
        ss.show_edit = not ss.show_edit
        st.rerun()

    if ss.show_edit:
        ss.setdefault("editor", ss.generated_text)
        st.text_area("Edit Document Below:", height=400, key="editor")
        ss.generated_text = ss["editor"]
        st.caption("Press Ctrl+Enter (or click outside the box) to apply your edits to the preview and downloads.")

    base = slugify(ss.doc_type)
    text, dtype, tms = ss.generated_text, ss.doc_type, ss.terms

    st.download_button("📄 Download as .TXT", data=text, file_name=f"{base}.txt", mime="text/plain")
    try:
        st.download_button(
            "📝 Download as .DOCX", data=build_docx(text, dtype, tms), file_name=f"{base}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        st.download_button(
            "📕 Download as .PDF", data=build_pdf(text, dtype, tms), file_name=f"{base}.pdf",
            mime="application/pdf",
        )
    except Exception as exc:  # keep the app usable if an export fails
        st.error(f"Could not build the DOCX/PDF export: {exc}")

    st.caption(config.DISCLAIMER)
else:
    st.info("Click 'Generate Document' to start")
