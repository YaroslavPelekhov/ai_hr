import re
import phonenumbers

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
TELEGRAM_RE = re.compile(r"(?:t\.me/|@)([A-Za-z0-9_]{4,})")
URL_RE = re.compile(r"(https?://\S+)", re.I)

def extract_contacts_basic(text: str):
    emails = list(sorted(set(EMAIL_RE.findall(text))))
    urls = list(sorted(set(URL_RE.findall(text))))
    telegrams = list(sorted(set(TELEGRAM_RE.findall(text))))
    # Phones (parse many formats, assume RU/LT defaults)
    phones = []
    for m in re.findall(r"[+()\d\-\s]{7,}", text):
        for region in ("RU", "LT", "BY", "UA", "KZ"):
            try:
                pn = phonenumbers.parse(m, region)
                if phonenumbers.is_possible_number(pn) and phonenumbers.is_valid_number(pn):
                    e164 = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
                    phones.append(e164)
                    break
            except:
                continue
    phones = sorted(set(phones))
    return {"emails": emails, "phones": phones, "telegrams": telegrams, "links": urls}
