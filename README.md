# LegalEase - AI-Powered Legal Document Generator

Streamlit UI -> FastAPI backend -> Google Gemini -> formatted `.txt` / `.docx` / `.pdf`.

```
LegalEase/
├── ai_core/
│   ├── gemini_generator.py   # Gemini prompt + API call (retries, friendly errors)
│   ├── generator.py          # format_docx / format_pdf / format_html_preview
│   └── text_utils.py         # sanitize_text, split_terms, parse_blocks
├── legalEaseAPI/
│   ├── main.py               # FastAPI app, GET /
│   └── routes.py             # POST /generate, GET /health, DocumentRequest
├── frontend/app.py           # Streamlit UI
├── Image/                    # Logo.png (docs) and inverseLogo.png (dark web UI)
├── docs/sample_inputs.json   # inputs used by the smoke test
├── scripts/                  # make_logos.py, smoke_test.py
├── tests/                    # pytest suite (no API key needed)
├── .streamlit/config.toml    # dark theme
├── .vscode/launch.json       # F5 debug configs
├── config.py  .env  requirements.txt  run.sh  run.bat
```

## 1. Setup in VS Code

1. Install **Python 3.10+** and **VS Code** (with the *Python* extension).
2. `File > Open Folder...` and open the `LegalEase` folder.
3. Open a terminal (`Ctrl+``) and create a virtual environment:

   **Windows (PowerShell)**
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```
   If activation is blocked: `Set-ExecutionPolicy -Scope Process Bypass`

   **macOS / Linux**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. `Ctrl+Shift+P` -> **Python: Select Interpreter** -> choose the one inside `venv`.
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Get a free Gemini key at https://aistudio.google.com/app/apikey and put it in `.env`:
   ```
   GEMINI_API_KEY=AIza...your-key...
   ```

## 2. Run

**Fastest:** `run.bat` (Windows) or `./run.sh` (macOS/Linux) starts both servers.

**Manually - two terminals (venv activated in each):**
```bash
# Terminal 1 - backend  (http://localhost:8000, docs at /docs)
uvicorn legalEaseAPI.main:app --reload

# Terminal 2 - frontend (http://localhost:8501)
streamlit run frontend/app.py
```

**Or with F5:** Run and Debug panel -> *LegalEase: Run everything*.

Always run commands from the project root (the folder containing `config.py`).

## 3. Use it

1. Fill in Document Type, Parties, Terms (separate with `;`) and Effective Date.
2. Click **Generate Document**.
3. Review the preview, click **Click to Edit Document** to change the wording
   (press Ctrl+Enter to apply).
4. Download as `.TXT`, `.DOCX` (logo, terms table, footer) or `.PDF` (logo + footer on every page).

Example: `Freelance Work Contract` / `Jane Doe (Service Provider), TechNova Inc. (Client)` /
`Work must be delivered by May 15, 2025; Payment within 7 days of invoice; The client retains intellectual property rights` / `April 15, 2025`.

## 4. Test

```bash
pip install -r requirements-dev.txt
pytest                       # offline tests: formatters + API (Gemini mocked)

# Live end-to-end test with 5 different inputs (backend must be running, key set):
python scripts/smoke_test.py
```
Quick manual checks: http://localhost:8000/ (welcome), http://localhost:8000/health (shows model and whether the key is set), http://localhost:8000/docs (try `POST /generate`).

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| "Backend not reachable" in sidebar | Start uvicorn (Terminal 1); check `BACKEND_URL` in `.env` |
| "GEMINI_API_KEY is not set" / "rejected the API key" | Edit `.env`, then **restart** uvicorn |
| "Model ... was not found" | Set `GEMINI_MODEL=gemini-2.5-flash` (or `gemini-2.5-pro`) in `.env` |
| 429 / quota message | Free-tier limit; wait a minute or switch model |
| `ModuleNotFoundError` | venv not active / not run from project root / `pip install -r requirements.txt` |
| `fpdf` errors | `pip uninstall fpdf fpdf2 -y` then `pip install fpdf2` (never both) |
| Port already in use | Change `--port` and `BACKEND_URL` / `API_PORT` in `.env` |

## Notes

- The PDF uses built-in Latin-1 fonts, so characters outside Latin-1 (e.g. Tamil/Hindi text) are replaced with `?`; `₹` is written as `Rs.`. DOCX and TXT keep full Unicode.
- Replace `Image/Logo.png` and `Image/inverseLogo.png` with your own branding (or re-run `python scripts/make_logos.py`).
- AI drafts are not legal advice; every export carries a disclaimer.
