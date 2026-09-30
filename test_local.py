"""Sanity test that needs NO API key: LEGALEASE_MOCK=1 python test_local.py"""
import os
os.environ["LEGALEASE_MOCK"] = "1"
from fastapi.testclient import TestClient
from legalEaseAPI.main import app
from ai_core.generator import format_docx, format_pdf

c = TestClient(app)
assert c.get("/").status_code == 200
r = c.post("/generate", json={"document_type": "Freelance Work Contract",
    "parties": "Jane Doe (Service Provider), TechNova Inc. (Client)",
    "terms": "Work delivered by May 15, 2025; Payment within 7 days; Client owns IP", "dates": "April 15, 2025"})
assert r.status_code == 200, r.text
doc = r.json()["document"]
open("test_output.docx", "wb").write(format_docx(doc, "Freelance Work Contract", "Payment within 7 days; Client owns IP"))
open("test_output.pdf", "wb").write(format_pdf(doc, "Freelance Work Contract", "Payment within 7 days; Client owns IP"))
print("ALL OK - test_output.docx and test_output.pdf created")
