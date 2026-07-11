from __future__ import annotations

from pydantic import BaseModel, Field


class BasicInfo(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class JobInfo(BaseModel):
    jobIntention: str | None = None
    expectedSalary: str | None = None


class Education(BaseModel):
    school: str | None = None
    major: str | None = None
    degree: str | None = None
    startDate: str | None = None
    endDate: str | None = None


class WorkExperience(BaseModel):
    company: str | None = None
    position: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    description: str | None = None


class Project(BaseModel):
    name: str | None = None
    role: str | None = None
    technologies: list[str] = Field(default_factory=list)
    description: str | None = None


class Background(BaseModel):
    workYears: float | None = None
    education: list[Education] = Field(default_factory=list)
    workExperiences: list[WorkExperience] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)


class StructuredResume(BaseModel):
    basicInfo: BasicInfo = Field(default_factory=BasicInfo)
    jobInfo: JobInfo = Field(default_factory=JobInfo)
    background: Background = Field(default_factory=Background)


class ParsedResumeData(BaseModel):
    resumeId: str
    resumeHash: str
    pageCount: int
    cleanedText: str | None = None
    resume: StructuredResume
    cacheHit: bool = False

