from ..models import Requirement, ResumeParsed, MatchResult
from typing import List, Tuple

def compute_match(resume: ResumeParsed, req: Requirement) -> MatchResult:
    low_skills = set([s.lower() for s in resume.skills])
    must = [m.lower() for m in req.must_have]
    nice = [n.lower() for n in req.nice_to_have]
    matched_must = [m for m in must if m in low_skills]
    matched_nice = [n for n in nice if n in low_skills]

    must_ratio = len(matched_must) / max(1, len(must))
    nice_ratio = len(matched_nice) / max(1, len(nice))

    exp_bonus = 0.0
    if resume.experience_years:
        if resume.experience_years >= 5: exp_bonus = 0.1
        elif resume.experience_years >= 3: exp_bonus = 0.05

    score = 0.7 * must_ratio + 0.2 * nice_ratio + exp_bonus

    reasons = []
    if must_ratio < 1.0:
        missing = [m for m in must if m not in matched_must]
        if missing:
            reasons.append("Missing must-have: " + ", ".join(missing))
    if matched_nice:
        reasons.append("Nice-to-have matched: " + ", ".join(matched_nice))
    if resume.location and req.locations:
        if any(loc.lower() in resume.location.lower() for loc in req.locations):
            score += 0.05
            reasons.append(f"Location match: {resume.location}")
    if resume.langs and req.langs:
        if any(l in resume.langs for l in req.langs):
            score += 0.05
            reasons.append(f"Language match: {','.join(resume.langs)}")

    score = min(score, 1.0)
    return MatchResult(
        candidate_id=resume.candidate_id,
        score=score,
        reasons=reasons,
        matched_must=matched_must,
        matched_nice=matched_nice
    )
