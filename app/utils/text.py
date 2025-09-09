import re

def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"\t", " ", text)
    text = re.sub(r"[\u00A0\u2007\u202F]", " ", text)  # non-breaking spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def to_lower(text: str) -> str:
    return text.lower()
