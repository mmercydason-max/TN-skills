"""Live end-to-end check against the RUNNING backend with several input combinations.

    1) start the backend:  uvicorn legalEaseAPI.main:app --reload
    2) run:                python scripts/smoke_test.py
"""
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402
from ai_core.generator import format_docx, format_pdf  # noqa: E402

cases = json.loads((ROOT / "docs" / "sample_inputs.json").read_text(encoding="utf-8"))
health = requests.get(f"{config.BACKEND_URL}/health", timeout=5).json()
print("Health:", health)
if not health.get("api_key_configured"):
    sys.exit("Set GEMINI_API_KEY in .env and restart the backend first.")

failures = 0
for i, case in enumerate(cases, 1):
    print(f"\n[{i}/{len(cases)}] {case['document_type']}")
    try:
        r = requests.post(f"{config.BACKEND_URL}/generate", json=case, timeout=config.REQUEST_TIMEOUT)
        r.raise_for_status()
        text = r.json()["document"]
        docx_bytes = format_docx(text, case["document_type"], case["terms"])
        pdf_bytes = format_pdf(text, case["document_type"], case["terms"])
        assert len(text) > 500, "document suspiciously short"
        print(f"  OK  chars={len(text)}  docx={len(docx_bytes)}B  pdf={len(pdf_bytes)}B")
    except Exception as exc:
        failures += 1
        print("  FAIL", exc)

print("\nAll checks passed." if not failures else f"\n{failures} case(s) failed.")
sys.exit(1 if failures else 0)
