# AI-HR Realtime Add-on (Discord + Whisper STT)

## Что входит
- `app/interview/realtime.py` — FastAPI сервис: STT (OpenAI Whisper) + TTS (gTTS) + управление сценарием.
- `voice_bridge_node/` — Discord-бот (Node.js), умеет принимать голос, отправлять аудио на STT и воспроизводить TTS.

## Установка
1) Установите FFmpeg (macOS: `brew install ffmpeg`).
2) В корне основного проекта: добавьте зависимости в `requirements.txt`: `openai` и `gTTS`.
3) Запустите Python сервис:
```bash
uvicorn app.interview.realtime:app --reload --port 8000
```
4) Настройте и запустите Node бота:
```bash
cd voice_bridge_node
cp .env.example .env   # пропишите DISCORD_BOT_TOKEN
npm install
node index.js
```
5) В Discord зайдите в голосовой канал и напишите в текстовом: `!join`.
6) Говорите — транскрипт будет в текстовом канале, бот будет задавать вопросы и озвучивать их. `!finish` — завершение + отчёт.

> Для STT нужен `OPENAI_API_KEY` в окружении Python сервиса (`.env` корня проекта). Если не задан, будет пустая транскрипция.
