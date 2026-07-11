from __future__ import annotations

from pydantic import BaseModel, Field


class JobAnalysis(BaseModel):
    jobTitle: str
    coreSkills: list[str] = Field(default_factory=list)
    bonusSkills: list[str] = Field(default_factory=list)
    educationRequirement: str | None = None
    workYearsRequirement: float | None = None
    responsibilities: list[str] = Field(default_factory=list)
    industry: str | None = None
    otherRequirements: list[str] = Field(default_factory=list)


class MatchRequest(BaseModel):
    resumeId: str = Field(min_length=1, max_length=128)
    jobTitle: str = Field(min_length=1, max_length=200)
    jobDescription: str

