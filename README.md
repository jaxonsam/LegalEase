# LegalEase - AI Legal Document Generator

FastAPI (backend) + Streamlit (frontend) + Google Gemini (AI). Exports .txt / .docx / .pdf.

## 1. What you need
- Python 3.10+  (check: `python --version`)
- VS Code (or any editor) + a browser
- A free Gemini API key: https://aistudio.google.com/apikey  -> sign in -> "Create API key"
- Internet connection

## 2. Setup (Windows PowerShell)
```
cd LegalEase
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then open .env and paste your key
```
(Mac/Linux: `source venv/bin/activate` and `cp .env.example .env`)

## 3. Run
Two terminals, both with the venv activated:
```
uvicorn legalEaseAPI.main:app --reload        # terminal 1 -> http://127.0.0.1:8000/docs
streamlit run frontend/app.py                 # terminal 2 -> http://localhost:8501
```
Or just run `run.bat` (Windows) / `./run.sh` (Mac/Linux).

## 4. Test without an API key
`set LEGALEASE_MOCK=1` (Windows) / `export LEGALEASE_MOCK=1`, then `python test_local.py`.

## 5. Common problems
- **404 / "model no longer available"**: Google retires models. Change `GEMINI_MODEL` in `.env`
  (see https://ai.google.dev/gemini-api/docs/models). The brief's `gemini-1.5-pro` no longer works.
- **429 quota error**: free tier limit hit. Wait a minute and retry.
- **"Cannot reach the backend"**: terminal 1 isn't running.
- **`.env` not read**: run commands from the `LegalEase` folder; file must be named exactly `.env`.
- **Never upload `.env` to GitHub** (`.gitignore` already blocks it).

## 6. Deploy (optional)
- Backend: Render/Railway -> start command in `Procfile`; add env var `GEMINI_API_KEY`.
- Frontend: Streamlit Community Cloud -> main file `frontend/app.py`; add secret/env `BACKEND_URL` = your backend URL.

## Project layout
```
ai_core/gemini_generator.py   prompt + Gemini call (with model fallback)
ai_core/generator.py          sanitize_text, format_docx, format_pdf, format_html_preview
legalEaseAPI/main.py, routes.py   FastAPI app, POST /generate
frontend/app.py               Streamlit UI
config.py  .env  requirements.txt  run.sh / run.bat
```
