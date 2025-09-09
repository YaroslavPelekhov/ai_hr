import argparse, json, os
from pathlib import Path
from typing import List
from .config import settings
from .models import Requirement, ResumeParsed, MatchResult, OutreachTask
from .ingestion.parser import parse_dir
from .screening.matcher import compute_match
from .messaging.telegram_bot import make_deep_link
from .scheduling.scheduler import generate_ics, propose_slots
from .interview.jitsi import make_jitsi_link
from .interview.ai_interviewer import AIInterviewer
from .reporting.report_builder import render_report

def load_requirements(req_dir: str) -> Requirement:
    # Simple loader: aggregate text files into keywords (must-have / nice-to-have)
    must = []
    nice = []
    role = os.getenv("ROLE_NAME", settings.ROLE_NAME)
    for p in Path(req_dir).glob("*"):
        if p.suffix.lower() in [".txt",".docx",".rtf",".pdf"]:
            from .ingestion.parser import read_file
            text = read_file(str(p)).lower()
            # naive split by keywords
            for kw in ["python","sql","docker","kubernetes","ml","nlp","pandas","fastapi","django","react","business analysis","bpmn","uml","requirements","jira"]:
                if kw in text and kw not in must:
                    must.append(kw)
    return Requirement(role=role, must_have=must, nice_to_have=nice, locations=["Москва","Вильнюс"], langs=["RU","EN"])

def screen_and_outreach(resume_dir: str, req_dir: str, out_dir: str):
    resumes: List[ResumeParsed] = parse_dir(resume_dir)
    req = load_requirements(req_dir)
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    picked: List[tuple[ResumeParsed, MatchResult]] = []
    for r in resumes:
        mr = compute_match(r, req)
        if mr.score >= settings.MIN_MATCH_SCORE:
            picked.append((r, mr))

    tasks: List[OutreachTask] = []
    for r, mr in picked:
        channel = "none"
        addr = None
        deep = None
        if r.telegrams:
            channel = "telegram"
            # We don't know the user ID, so deep-link via bot username
            deep = make_deep_link(r.candidate_id)
            addr = f"@{r.telegrams[0]}"
            msg = f"Привет, {r.name or ''}! Это AI‑HR из {settings.COMPANY_NAME}. Нашли ваше резюме на роль {settings.ROLE_NAME}. Хотим пригласить на интервью. Перейдите по ссылке, чтобы выбрать время: {deep}"
        elif r.emails:
            channel = "email"
            addr = r.emails[0]
            link = make_jitsi_link()
            slots = propose_slots(3)
            body = f"""Здравствуйте! Мы из {settings.COMPANY_NAME}. Рассматриваем вас на роль {settings.ROLE_NAME}.
Предлагаем выбрать слот для интервью, ответив на это письмо номером слота:
{os.linesep.join(f"{i+1}. {s.start_time:%d.%m %H:%M}" for i,s in enumerate(slots))}
Ссылка на видеозвонок будет отправлена после подтверждения.
С уважением, AI‑HR
"""
            ics = generate_ics(slots[0].start_time, slots[0].end_time, "Собеседование с AI‑HR", link)
            msg = body  # For storage; actual sending via SMTP
        else:
            msg = "Контактов не найдено."
        tasks.append(OutreachTask(candidate_id=r.candidate_id, channel=channel, address=addr, message=msg, deep_link=deep))

    # Save tasks as JSON
    Path(out_dir, "outreach_tasks.json").write_text(json.dumps([t.model_dump() for t in tasks], ensure_ascii=False, indent=2), encoding="utf-8")
    # Produce dummy interview + report for each picked
    ai = AIInterviewer()
    for r, mr in picked:
        outcome = ai.run(r.candidate_id, r.raw_text, candidate_answers=[
            "У меня 5 лет опыта, делал проекты в FinTech.",
            "Python, FastAPI, PostgreSQL, Docker, Kubernetes.",
            "Миграция монолита на микросервисы, оптимизация производительности.",
            "Сейчас предпочитаю Python/PyTorch, инфраструктура на K8s.",
            "Ожидания по рынку, гибридный формат."
        ])
        html_path = render_report(os.path.join(out_dir, "..", "reports"), r, mr, outcome)
        print("Report saved:", html_path)

def main():
    ap = argparse.ArgumentParser(description="AI‑HR Pipeline")
    ap.add_argument("--run", action="store_true", help="Run end-to-end: ingest, screen, outreach (draft) and build reports")
    ap.add_argument("--resume_dir", default="input/resumes")
    ap.add_argument("--req_dir", default="input/requirements")
    ap.add_argument("--out_dir", default="data")
    args = ap.parse_args()

    if args.run:
        screen_and_outreach(args.resume_dir, args.req_dir, args.out_dir)
        print("Done. See data/outreach_tasks.json and reports/*.html")

if __name__ == "__main__":
    main()
