import os, re, subprocess, tempfile
from typing import List
from . import readers
from ..models import ResumeParsed
from ..contacts.extractor import extract_contacts_basic
from ..utils.text import normalize_whitespace

SUPPORTED_EXTS = {".pdf", ".docx", ".rtf", ".txt"}

def read_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return readers.read_pdf(path)
    elif ext == ".docx":
        return readers.read_docx(path)
    elif ext == ".rtf":
        return readers.read_rtf(path)
    elif ext == ".txt":
        with open(path, "r", errors="ignore") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file: {path}")

def parse_resume(path: str) -> ResumeParsed:
    raw = read_file(path)
    raw = normalize_whitespace(raw)
    contact = extract_contacts_basic(raw)
    skills = extract_skills(raw)
    exp_years = estimate_experience_years(raw)
    name = guess_name(raw)
    location = guess_location(raw)
    langs = guess_langs(raw)
    return ResumeParsed(
        candidate_id=os.path.basename(path),
        raw_text=raw,
        name=name,
        emails=contact.get("emails", []),
        phones=contact.get("phones", []),
        telegrams=contact.get("telegrams", []),
        links=contact.get("links", []),
        skills=skills,
        experience_years=exp_years,
        location=location,
        langs=langs,
    )

# Very naive skill extraction; replace with spaCy / KeyBERT in production
def extract_skills(text: str) -> List[str]:
    # A small dictionary to get started
    keywords = [
        "python","java","c++","c#","go","golang","rust","sql","nosql","postgres",
        "mysql","mongodb","redis","kafka","spark","hadoop","linux","docker","kubernetes",
        "aws","gcp","azure","bash","git","ci/cd","ml","machine learning","nlp","cv",
        "react","vue","angular","typescript","js","node","django","flask","fastapi",
        "pandas","numpy","pytorch","tensorflow","scikit","airflow","jira","confluence",
        "business analysis","uml","bpmn","requirements","api","rest","grpc","microservices"
    ]
    found = set()
    low = text.lower()
    for k in keywords:
        if k in low:
            found.add(k)
    # also capture capitalized acronyms
    acr = set(re.findall(r"\b([A-Z]{2,5})\b", text))
    return sorted(found.union(acr))

def estimate_experience_years(text: str):
    m = re.findall(r"(\d+)[\+\-]?\s*(?:years|year|лет|года|год|yrs|y\.)", text, flags=re.I)
    if m:
        try:
            nums = [int(x) for x in m]
            return max(nums)
        except:
            return None
    return None

def guess_name(text: str):
    # Try to capture Russian style "Фамилия Имя" or "Имя Фамилия"
    m = re.search(r"\b([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+)\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b", text)
    return m.group(1) if m else None

def guess_location(text: str):
    m = re.search(r"(Москва|Санкт[- ]Петербург|Новосибирск|Екатеринбург|Казань|Минск|Алматы|Вильнюс|Рига|Тбилиси)", text, re.I)
    return m.group(1) if m else None

def guess_langs(text: str):
    langs = []
    if re.search(r"англ(ийский)?\s*(?:[A-C][12]|intermediate|upper|advanced|b2|c1|c2)", text, re.I):
        langs.append("EN")
    if re.search(r"рус(ский)?", text, re.I):
        langs.append("RU")
    if re.search(r"литов(ский)?", text, re.I):
        langs.append("LT")
    return langs or []

def parse_dir(folder: str) -> List[ResumeParsed]:
    out = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in SUPPORTED_EXTS:
                try:
                    out.append(parse_resume(os.path.join(root, f)))
                except Exception as e:
                    print("Failed to parse", f, e)
    return out
