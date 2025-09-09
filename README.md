# AI-HR — Автоматизация рекрутинга

##  Описание проекта
**AI-HR** — это интеллектуальная система для автоматизации рекрутинга.  
Она умеет:
- анализировать резюме в разных форматах,
- извлекать контакты кандидатов и отправлять приглашения,
- назначать интервью и подключаться к голосовому каналу (Discord),
- вести собеседование в реальном времени (Speech-to-Text + GPT + Text-to-Speech),
- формировать подробный отчет о кандидате с рекомендацией.

Проект создан в рамках хакатона **MORE.Tech**.

---

##  Архитектура
- **Backend (Python, FastAPI, uvicorn)**  
  Оркестрирует процесс, принимает аудио для распознавания, управляет логикой интервью, генерирует отчеты.  

- **Discord-бот (Node.js, discord.js, prism-media)**  
  Подключается к голосовому каналу, слушает кандидата, отправляет аудио в backend для распознавания, озвучивает вопросы.  

- **Speech-to-Text (Whisper / Realtime API)**  
  Транскрибирует речь кандидата.  

- **Text-to-Speech (gTTS / TTS API)**  
  Задаёт вопросы голосом.  

---

##  Установка и запуск

### 1. Клонирование проекта
```bash
git clone https://github.com/<your-org>/ai-hr.git
cd ai-hr
```

### 2. Установка backend
```bash
cd ai-hr
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Запуск backend
```bash
uvicorn app.interview.realtime:app --host 127.0.0.1 --port 8000 --reload
```
Проверка:
```bash
curl http://127.0.0.1:8000/health
# {"ok": true}
```

### 4. Установка и запуск Discord-бота
```bash
cd voice_bridge_node
npm install
node index.js
```

---

##  Конфигурация

Создайте файл `.env` в папке `voice_bridge_node`:

```env
DISCORD_BOT_TOKEN=<токен вашего Discord-бота>
PY_API_BASE=http://127.0.0.1:8000
MODEL=4o-mini
BUDGET_USD=0.90
MINUTES_LIMIT_IN=60
MINUTES_LIMIT_OUT=30
```
