from typing import List, Dict
from ..models import InterviewOutcome
from ..config import settings

class AIInterviewer:
    def __init__(self, role: str = "HR"):
        self.role = role

    def ask_questions(self, resume_text: str) -> List[str]:
        # Very simple script; replace with LLM prompts
        base = [
            "Расскажите кратко о вашем опыте в двух-трех предложениях.",
            "Какими проектами вы особенно гордитесь и почему?",
            "Опишите самый сложный технический вызов, с которым сталкивались.",
            "Какой стек и инструменты предпочитаете сейчас и почему?",
            "Какие ожидания по зарплате и формату работы?"
        ]
        # Add a question based on resume keywords
        if "python" in resume_text.lower():
            base.insert(1, "Расскажите о вашем опыте с Python: библиотеки, проекты, масштаб.")
        return base

    def score_and_decide(self, transcript: List[Dict[str, str]]) -> tuple[str, str]:
        # Naive heuristic: if candidate mentions "не знаю" too often => no_hire
        text = " ".join(turn["text"].lower() for turn in transcript if turn["role"] == "candidate")
        if text.count("не знаю") >= 2:
            return ("no_hire", "Много неуверенности в ответах ('не знаю').")
        # Otherwise hire if length is decent
        if len(text.split()) > 100:
            return ("hire", "Полные и уверенные ответы, релевантный опыт.")
        return ("hold", "Не хватает данных для решения.")

    def run(self, candidate_id: str, resume_text: str, candidate_answers: List[str]) -> InterviewOutcome:
        questions = self.ask_questions(resume_text)
        transcript = []
        for q, a in zip(questions, candidate_answers + [""]*len(questions)):
            transcript.append({"role": "ai", "text": q})
            transcript.append({"role": "candidate", "text": a})
        decision, rationale = self.score_and_decide(transcript)
        return InterviewOutcome(candidate_id=candidate_id, decision=decision, rationale=rationale, transcript=transcript)
