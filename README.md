# AI‑HR Starter Kit (MoreTech VTB – AI‑HR)

Готовый минимально‑живой проект под хакатон: автоматический **предварительный скрининг резюме → контакт кандидата (приоритет: Telegram) → назначение слота → ссылка на видео (Jitsi/Discord) → авто‑интервью AI‑HR → итоговый отчет**.

## Что уже умеет
- Парсит PDF/DOCX/RTF резюме из `input/resumes` (в репо есть образцы из вашего архива).
- Грубый скоринг по must‑have/ nice‑to‑have (из `input/requirements`).
- Извлекает контакты (email, телефон, Telegram @handle, ссылки).
- Формирует задачи на аутрич: если есть TG — **генерит deep‑link** для бота; иначе готовит **email‑черновик** + `.ics` для календаря.
- Генерит HTML‑отчеты по каждому кандидату (скор, причины, транскрипт, решение hire/hold/no hire).
- Готовый Telegram‑бот для выбора слота и автоматической отправки `.ics` + ссылки на видеозвонок (**Jitsi** по умолчанию).

> Discord‑вариант можно включить отдельно (см. `app/interview/discord_integration.py`). Для MVP проще Jitsi: не требует учеток, создаем уникальную комнату.

## Быстрый старт (локально)
1. **Python 3.11+**. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Скопируйте `.env.example` → `.env` и заполните как минимум `TELEGRAM_BOT_TOKEN` и `TELEGRAM_BOT_USERNAME` (или настройте SMTP для fallback email).

3. В папках уже лежат примеры: `input/resumes` и `input/requirements` (взято из вашего архива).

4. Запустите **конвейер** (ингест → скоринг → аутрич → отчеты):
   ```bash
   python -m app.main --run
   ```
   Результаты:
   - `data/outreach_tasks.json` — кого и как контактируем (TG deep‑link или email‑черновик).
   - `reports/*.html` — готовые отчеты.

5. Запустите **Telegram‑бота** (после настройки токена):
   ```bash
   python -c "from app.messaging.telegram_bot import run_bot; run_bot()"
   ```
   Бот предлагает слоты и отправляет `.ics` + ссылку на звонок.

## Структура
```
app/
  ingestion/reader.py        # PDF/DOCX/RTF → текст
  ingestion/parser.py        # извлечение контактов, навыков, ФИО, языка, города
  screening/matcher.py       # скоринг резюме vs требования
  contacts/extractor.py      # email/телефон/TG/URL
  messaging/telegram_bot.py  # deep‑link, выбор слота, ICS
  messaging/emailer.py       # SMTP fallback
  scheduling/scheduler.py    # генерация слотов и .ics
  interview/jitsi.py         # Jitsi ссылочный генератор
  interview/ai_interviewer.py# простой логический интервьюер
  reporting/report_builder.py# отчет HTML через Jinja2
  utils/text.py
input/
  resumes/                   # исходные резюме (PDF/DOCX/RTF/TXT)
  requirements/              # текст описаний вакансий (агрегируются в must-have)
templates/
  report.html.j2             # шаблон отчета
```

## Как это «крутится» в прод‑режиме
- **Ingest/Screening** гоняется по расписанию (cron/k8s job), пишет кандидатов в БД и создает аутрич‑таски.
- **Outreach**: TG deep‑link (`https://t.me/<bot>?start=<token>`). Если TG нет — отправляем email (см. `messaging/emailer.py`).
- **Scheduling**: бот предлагает N слотов (конфиг в `scheduling/scheduler.py`), высылает `.ics` и ссылку (Jitsi/Discord).
- **Interview**: для MVP — текстовый (в TG/Discord). Реал‑тайм голос/видео — опционально, можно прикрутить [discord.py] бота + WebRTC.
- **Reporting**: по окончании собеседования формируется отчет (HTML). При желании легко добавить PDF (WeasyPrint) и загрузку в S3.

## Улучшения за вечер
- ML‑матчинг: Embeddings + ANN (например, sentence‑transformers) вместо простых ключей.
- Нормализация навыков: словарь → синонимы → кластеризация.
- Антиспам‑аутрич: очереди (Redis) и backoff.
- «Лайв» интервью: TTS/STT (Whisper/vosk) + LLM‑скрипт с контекстом резюме.
- Админ‑панель на FastAPI (таблица кандидатов, статусы, ручные правки).

## Примечания
- TG‑бот сможет написать кандидату, **только если кандидат стартовал бота**. Поэтому deep‑link обязателен (мы отправляем ссылку TG, email или через соцсети/LinkedIn).
- Для RTF использован `striprtf`, для DOCX — `docx2txt`, для PDF — `pdfminer.six`. OCR (сканы) не включен; при необходимости добавьте `pytesseract`.

Удачи на хакатоне 🚀
