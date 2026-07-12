from __future__ import annotations

from pydantic import BaseModel, Field


JOB_TITLE_MIN_LENGTH = 1
JOB_TITLE_MAX_LENGTH = 120
JOB_DESCRIPTION_MIN_LENGTH = 10
JOB_DESCRIPTION_MAX_LENGTH = 5000


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
    jobTitle: str = Field(
        min_length=JOB_TITLE_MIN_LENGTH,
        max_length=JOB_TITLE_MAX_LENGTH,
    )
    jobDescription: str = Field(
        min_length=JOB_DESCRIPTION_MIN_LENGTH,
        max_length=JOB_DESCRIPTION_MAX_LENGTH,
    )
