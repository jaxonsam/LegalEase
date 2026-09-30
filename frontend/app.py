import re
import sys
from pathlib import Path

import requests
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))

from ai_core.generator import (  # noqa: E402
    DISCLAIMER, WEB_LOGO_PATH, format_docx, format_html_preview, format_pdf, sanitize_text,
)
from config import BACKEND_URL  # noqa: E402

st.set_page_config(page_title="LegalEase", layout="centered")

# ---- Header -----------------------------------------------------------------
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.image(str(WEB_LOGO_PATH), width="stretch")
st.markdown("<h2 style='text-align: center;'>AI Legal Document Generator</h2>", unsafe_allow_html=True)

# ---- Session state ----------------------------------------------------------
for key, default in {"doc_text": "", "doc_type": "", "terms": "", "show_edit": False}.items():
    st.session_state.setdefault(key, default)

# ---- Inputs -----------------------------------------------------------------
document_type = st.text_input("Document Type (Ex: Agreement, Contract, NDA)")
parties = st.text_area("Parties Involved")
terms = st.text_area("Terms & Conditions (Use semicolons for bullet points)")
dates = st.text_input("Effective Date")

if st.button("Generate Document"):
    if not document_type.strip() or not parties.strip():
        st.warning("Please fill in at least the Document Type and Parties Involved.")
    else:
        with st.spinner("Drafting your document with Gemini..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/generate",
                    json={"document_type": document_type, "parties": parties, "terms": terms, "dates": dates},
                    timeout=180,
                )
                if resp.ok:
                    st.session_state.doc_text = sanitize_text(resp.json()["document"])
                    st.session_state.doc_type = document_type
                    st.session_state.terms = terms
                    st.session_state.show_edit = False
                    st.session_state.pop("editor", None)  # reset the edit box
                    st.success("Document Generated Successfully!")
                else:
                    detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text
                    st.error(f"Backend error ({resp.status_code}): {detail}")
            except requests.exceptions.ConnectionError:
                st.error(f"Cannot reach the backend at {BACKEND_URL}. Start it with: uvicorn legalEaseAPI.main:app --reload")
            except requests.exceptions.Timeout:
                st.error("The AI took too long to respond. Please try again.")

if not st.session_state.doc_text:
    st.info("Click 'Generate Document' to start")
    st.stop()

# ---- Preview ----------------------------------------------------------------
styled_html = format_html_preview(st.session_state.doc_text)
st.markdown(
    "<div style='background:#0f1626;border:1px solid #223;border-radius:10px;padding:20px;"
    f"max-height:420px;overflow-y:auto;color:#e6e6e6'>{styled_html}</div>",
    unsafe_allow_html=True,
)
st.caption(DISCLAIMER)

# ---- Edit -------------------------------------------------------------------
if st.button("✏️ Click to Edit Document"):
    st.session_state.show_edit = not st.session_state.show_edit

if st.session_state.show_edit:
    edited = st.text_area("Edit Document Below:", value=st.session_state.doc_text, height=300, key="editor")
    st.session_state.doc_text = edited

# ---- Downloads --------------------------------------------------------------
text, dtype, saved_terms = st.session_state.doc_text, st.session_state.doc_type, st.session_state.terms
fname = re.sub(r"[^a-z0-9_]+", "", dtype.strip().replace(" ", "_").lower()) or "legal_document"

st.download_button("📄 Download as .TXT", data=text, file_name=f"{fname}.txt", mime="text/plain")
st.download_button(
    "📝 Download as .DOCX", data=format_docx(text, dtype, saved_terms), file_name=f"{fname}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)
st.download_button(
    "📕 Download as .PDF", data=format_pdf(text, dtype, saved_terms), file_name=f"{fname}.pdf", mime="application/pdf",
)
