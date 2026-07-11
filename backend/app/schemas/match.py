from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.job import JobAnalysis
from app.schemas.resume import StructuredResume


class AIMatchEvaluation(BaseModel):
    aiScore: float = 50
    advantages: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    summary: str = ""

    @field_validator("aiScore")
    @classmethod
    def clamp_score(cls, value: float) -> float:
        return max(0.0, min(100.0, float(value)))


class MatchResult(BaseModel):
    overallScore: float
    skillScore: float
    experienceScore: float
    projectScore: float
    educationScore: float
    aiScore: float
    matchedKeywords: list[str] = Field(default_factory=list)
    missingKeywords: list[str] = Field(default_factory=list)
    advantages: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    summary: str
    recommendationLevel: str

    @field_validator(
        "overallScore",
        "skillScore",
        "experienceScore",
        "projectScore",
        "educationScore",
        "aiScore",
    )
    @classmethod
    def clamp_scores(cls, value: float) -> float:
        return round(max(0.0, min(100.0, float(value))), 1)


class MatchResponseData(BaseModel):
    resumeId: str
    job: JobAnalysis
    match: MatchResult
    cacheHit: bool = False


class AnalyzeResponseData(BaseModel):
    resumeId: str
    pageCount: int
    resumeHash: str
    cleanedText: str | None = None
    resume: StructuredResume
    job: JobAnalysis
    match: MatchResult
    cacheHit: bool = False
