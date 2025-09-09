import asyncio, os, logging, secrets
from typing import Dict
from ..config import settings
from ..scheduling.scheduler import generate_ics, propose_slots
from ..interview.jitsi import make_jitsi_link

# We use python-telegram-bot v21 (asyncio)
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(level=logging.INFO)

ASK_AVAIL = 1

DEEP_LINK_TOKENS: Dict[str, str] = {}  # token -> candidate_id

def build_app():
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    return Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    if args:
        token = args[0]
        cand = DEEP_LINK_TOKENS.get(token)
        if cand:
            context.user_data["candidate_id"] = cand
            await update.message.reply_text(f"Привет! Я AI‑HR бот. Нашли ваше резюме и хотим пригласить на интервью. Уточните доступные слоты.")
            return await ask_availability(update, context)
    await update.message.reply_text("Привет! Я AI‑HR бот. Используйте команду /interview чтобы выбрать время собеседования.")
    return ConversationHandler.END

async def interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await ask_availability(update, context)

async def ask_availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    slots = propose_slots()
    # serialize slots
    text = "Выберите удобный слот (ответьте номером):\n"
    for i, s in enumerate(slots, 1):
        text += f"{i}. {s.start_time:%d.%m %H:%M}–{s.end_time:%H:%M}\n"
    context.user_data["slots"] = slots
    await update.message.reply_text(text)
    return ASK_AVAIL

async def pick_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if not choice.isdigit():
        await update.message.reply_text("Пожалуйста, ответьте номером слота.")
        return ASK_AVAIL
    idx = int(choice) - 1
    slots = context.user_data.get("slots", [])
    if not (0 <= idx < len(slots)):
        await update.message.reply_text("Неверный номер. Попробуйте снова.")
        return ASK_AVAIL
    slot = slots[idx]
    link = make_jitsi_link()
    ics = generate_ics(slot.start_time, slot.end_time, "Собеседование с AI‑HR", link)
    await update.message.reply_text(f"Отлично! Бронирую {slot.start_time:%d.%m %H:%M}. Ссылка на видеозвонок: {link}")
    await update.message.reply_document(document=("invite.ics", ics.encode("utf-8")))
    return ConversationHandler.END

def make_deep_link(candidate_id: str) -> str:
    token = secrets.token_urlsafe(8)
    DEEP_LINK_TOKENS[token] = candidate_id
    if not settings.TELEGRAM_BOT_USERNAME:
        return f"t.me/<your_bot_username>?start={token}"
    return f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={token}"

def run_bot():
    app = build_app()
    conv = ConversationHandler(
        entry_points=[CommandHandler("interview", interview)],
        states={
            ASK_AVAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, pick_slot)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.run_polling()
