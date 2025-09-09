import os
from pdfminer.high_level import extract_text
import docx2txt
from striprtf.striprtf import rtf_to_text

def read_pdf(path: str) -> str:
    return extract_text(path) or ""

def read_docx(path: str) -> str:
    return docx2txt.process(path) or ""

def read_rtf(path: str) -> str:
    with open(path, "r", errors="ignore") as f:
        data = f.read()
    return rtf_to_text(data) or ""
