import uuid
from ..config import settings

def make_jitsi_link() -> str:
    room = "AIHR-" + uuid.uuid4().hex[:10]
    base = settings.JITSI_BASE.rstrip("/")
    return f"{base}/{room}"
