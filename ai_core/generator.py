"""Formatting helpers: clean text, then build .docx, .pdf and an HTML preview."""
import html
import io
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from fpdf import FPDF

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "Image" / "inverseLogo.png"  # dark text, for white pages
WEB_LOGO_PATH = BASE_DIR / "Image" / "Logo.png"  # light text, for the dark web UI
FOOTER_TEXT = "LegalEase Inc. | contact@legalease.com | All Rights Reserved."
DISCLAIMER = "AI-generated draft. Review with a qualified lawyer before signing."

_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u2022": "-", "\u00a0": " ",
}


def sanitize_text(text: str) -> str:
    """Replace typographic quotes/dashes so every export format renders cleanly."""
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    text = text.replace("\r\n", "\n")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _strip_inline(line: str) -> str:
    return re.sub(r"(\*\*|`)", "", line).strip()


def parse_blocks(text: str):
    """Turn raw AI text into [(kind, text)] where kind is title/heading/bullet/para/space."""
    blocks, seen_title = [], False
    for raw in text.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            blocks.append(("space", ""))
            continue
        stripped = line.strip()
        if stripped.startswith("#"):
            content = _strip_inline(stripped.lstrip("#"))
            kind = "title" if not seen_title else "heading"
            seen_title = True
            blocks.append((kind, content))
        elif re.fullmatch(r"\*\*.+\*\*:?", stripped) or re.fullmatch(r"\d+\.\s+[^.]{2,60}:", stripped) \
                or stripped.upper() in ("WITNESSETH:", "BETWEEN:", "AND:") or stripped.rstrip(":").lower() in ("between", "and"):
            blocks.append(("heading", _strip_inline(stripped)))
        elif re.match(r"^([-*]|\d+\)|[a-z]\))\s+", stripped):
            blocks.append(("bullet", _strip_inline(re.sub(r"^([-*])\s+", "", stripped))))
        else:
            blocks.append(("para", _strip_inline(stripped)))
    return blocks


def split_terms(terms: str):
    return [t.strip() for t in (terms or "").split(";") if t.strip()]


# ---------------------------------------------------------------- HTML preview
def format_html_preview(text: str) -> str:
    out = []
    for kind, content in parse_blocks(sanitize_text(text)):
        c = html.escape(content)
        if kind == "title":
            out.append(f"<h2 style='text-align:center;margin:0 0 12px'>{c}</h2>")
        elif kind == "heading":
            out.append(f"<h4 style='margin:16px 0 4px'>{c}</h4>")
        elif kind == "bullet":
            out.append(f"<p style='margin:2px 0 2px 18px'>&bull; {c}</p>")
        elif kind == "para":
            out.append(f"<p style='margin:4px 0;line-height:1.55'>{c}</p>")
    return "".join(out)


# ------------------------------------------------------------------------ DOCX
def format_docx(text: str, doc_type: str, terms: str = "") -> bytes:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)

    if LOGO_PATH.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(LOGO_PATH), width=Inches(2.2))

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(sanitize_text(doc_type).upper())
    run.bold, run.font.size = True, Pt(16)

    term_list = split_terms(terms)
    if term_list:
        doc.add_paragraph().add_run("Summary of Key Terms").bold = True
        table = doc.add_table(rows=1, cols=2)
        table.style = "Table Grid"
        table.rows[0].cells[0].text, table.rows[0].cells[1].text = "No.", "Term"
        for cell in table.rows[0].cells:
            for r in cell.paragraphs[0].runs:
                r.bold = True
        for i, t in enumerate(term_list, start=1):
            row = table.add_row().cells
            row[0].text, row[1].text = str(i), sanitize_text(t)
        doc.add_paragraph()

    first_title_skipped = False
    for kind, content in parse_blocks(sanitize_text(text)):
        if kind == "space":
            continue
        if kind == "title" and not first_title_skipped:
            first_title_skipped = True  # title already printed above
            continue
        if kind in ("title", "heading"):
            doc.add_paragraph().add_run(content).bold = True
        elif kind == "bullet":
            doc.add_paragraph(content, style="List Bullet")
        else:
            doc.add_paragraph(content)

    footer = doc.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = footer.add_run(f"{FOOTER_TEXT}\n{DISCLAIMER}")
    fr.italic, fr.font.size = True, Pt(9)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ------------------------------------------------------------------------- PDF
class _LegalPDF(FPDF):
    def header(self):
        if LOGO_PATH.exists():
            self.image(str(LOGO_PATH), x=(self.w - 45) / 2, y=8, w=45)
        self.ln(22)

    def footer(self):
        self.set_y(-18)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 4, FOOTER_TEXT, align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 4, f"{DISCLAIMER}  Page {self.page_no()}", align="C")


def _latin(s: str) -> str:
    """Built-in PDF fonts only support latin-1; drop anything else safely."""
    return s.encode("latin-1", "replace").decode("latin-1")


def format_pdf(text: str, doc_type: str, terms: str = "") -> bytes:
    pdf = _LegalPDF()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.set_margins(20, 20, 20)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 15)
    pdf.multi_cell(0, 8, _latin(sanitize_text(doc_type)), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    first_title_skipped = False
    for kind, content in parse_blocks(sanitize_text(text)):
        content = _latin(content)
        if kind == "space":
            pdf.ln(2)
        elif kind == "title" and not first_title_skipped:
            first_title_skipped = True
        elif kind in ("title", "heading"):
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 6, content, new_x="LMARGIN", new_y="NEXT")
        elif kind == "bullet":
            pdf.set_font("Helvetica", "", 11)
            pdf.set_x(26)
            pdf.multi_cell(0, 6, f"-  {content}", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, content, align="J", new_x="LMARGIN", new_y="NEXT")

    term_list = split_terms(terms)
    if term_list:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, "Summary of Key Terms", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for t in term_list:
            pdf.set_x(26)
            pdf.multi_cell(0, 6, _latin(f"-  {sanitize_text(t)}"), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
