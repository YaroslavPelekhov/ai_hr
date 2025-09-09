from datetime import datetime, timedelta, timezone
from ..models import InterviewSlot
from ..config import settings
import uuid

def propose_slots(n: int = 5):
    now = datetime.now().astimezone()
    slots = []
    start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)
    for i in range(n):
        s = start + timedelta(hours=i*2)
        slots.append(InterviewSlot(start_time=s, end_time=s+timedelta(minutes=45), link=""))
    return slots

def generate_ics(start: datetime, end: datetime, summary: str, url: str) -> str:
    # Naive ICS string
    dtfmt = "%Y%m%dT%H%M%S"
    uid = str(uuid.uuid4())
    tz = "UTC" if not start.tzinfo else start.tzname() or "UTC"
    s = start.astimezone(timezone.utc).strftime(dtfmt) + "Z"
    e = end.astimezone(timezone.utc).strftime(dtfmt) + "Z"
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI-HR//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{s}
DTSTART:{s}
DTEND:{e}
SUMMARY:{summary}
DESCRIPTION:Join: {url}
URL:{url}
END:VEVENT
END:VCALENDAR
"""
    return ics
