from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class Requirement(BaseModel):
    role: str
    must_have: List[str] = Field(default_factory=list)
    nice_to_have: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    langs: List[str] = Field(default_factory=list)
    seniority: Optional[str] = None

class ResumeParsed(BaseModel):
    candidate_id: str
    raw_text: str
    name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    telegrams: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[float] = None
    location: Optional[str] = None
    langs: List[str] = Field(default_factory=list)

class MatchResult(BaseModel):
    candidate_id: str
    score: float
    reasons: List[str] = Field(default_factory=list)
    matched_must: List[str] = Field(default_factory=list)
    matched_nice: List[str] = Field(default_factory=list)

class OutreachTask(BaseModel):
    candidate_id: str
    channel: str  # telegram | email | none
    address: str | None = None
    message: str | None = None
    deep_link: str | None = None

class InterviewSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    link: str

class InterviewOutcome(BaseModel):
    candidate_id: str
    decision: str  # hire | no_hire | hold
    rationale: str
    transcript: List[Dict[str, str]] = Field(default_factory=list)  # {role: "ai|candidate", "text": ""}
