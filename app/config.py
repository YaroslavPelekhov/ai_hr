from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_BOT_USERNAME: str | None = os.getenv("TELEGRAM_BOT_USERNAME")
    SMTP_HOST: str | None = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str | None = os.getenv("SMTP_USER")
    SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")
    SMTP_FROM: str | None = os.getenv("SMTP_FROM")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    DISCORD_BOT_TOKEN: str | None = os.getenv("DISCORD_BOT_TOKEN")
    DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "Europe/Moscow")
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "AI-HR Inc.")
    ROLE_NAME: str = os.getenv("ROLE_NAME", "Engineer")
    MIN_MATCH_SCORE: float = float(os.getenv("MIN_MATCH_SCORE", "0.5"))
    JITSI_BASE: str = os.getenv("JITSI_BASE", "https://meet.jit.si")

settings = Settings()
