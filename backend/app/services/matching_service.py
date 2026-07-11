from __future__ import annotations

from app.schemas.job import JobAnalysis
from app.schemas.match import MatchResult
from app.schemas.resume import StructuredResume
from app.services.ai_service import AIService
from app.utils.skill_normalizer import extract_known_skills, skill_match


def clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 1)


def recommendation_level(score: float) -> str:
    if score >= 85:
        return "高度匹配"
    if score >= 70:
        return "较为匹配"
    if score >= 50:
        return "一般匹配"
    return "匹配度较低"


def _experience_score(resume: StructuredResume, job: JobAnalysis) -> float:
    required = job.workYearsRequirement
    actual = resume.background.workYears
    if required is None:
        return 80.0 if resume.background.workExperiences else (65.0 if actual else 55.0)
    if required <= 0:
        return 100.0
    if actual is None:
        return 25.0
    return clamp_score(actual / required * 100)


def _project_score(resume: StructuredResume, job: JobAnalysis) -> float:
    if not resume.background.projects:
        return 30.0 if job.coreSkills else 50.0
    project_text = " ".join(
        " ".join(
            [
                project.name or "",
                project.role or "",
                " ".join(project.technologies),
                project.description or "",
            ]
        )
        for project in resume.background.projects
    )
    project_skills = extract_known_skills(project_text)
    if not job.coreSkills:
        return 75.0
    _, _, score = skill_match(job.coreSkills, project_skills)
    return score


def _education_score(resume: StructuredResume, job: JobAnalysis) -> float:
    requirement = (job.educationRequirement or "").casefold()
    if not requirement:
        return 80.0
    level_map = {
        "高中": 1,
        "专科": 2,
        "大专": 2,
        "本科": 3,
        "bachelor": 3,
        "硕士": 4,
        "master": 4,
        "博士": 5,
        "phd": 5,
    }
    required_level = max((level for key, level in level_map.items() if key in requirement), default=0)
    actual_level = 0
    for item in resume.background.education:
        text = f"{item.degree or ''} {item.school or ''}".casefold()
        actual_level = max(actual_level, *(level for key, level in level_map.items() if key in text), 0)
    if actual_level == 0:
        return 30.0
    if required_level == 0:
        return 70.0
    return 100.0 if actual_level >= required_level else clamp_score(actual_level / required_level * 70)


class MatchingService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def match(self, resume: StructuredResume, job: JobAnalysis) -> MatchResult:
        matched, missing, skill_score = skill_match(job.coreSkills, resume.background.skills)
        if not job.coreSkills:
            skill_score = 60.0
        experience_score = _experience_score(resume, job)
        project_score = _project_score(resume, job)
        education_score = _education_score(resume, job)
        rule_composite = clamp_score(
            skill_score * 0.45
            + experience_score * 0.25
            + project_score * 0.20
            + education_score * 0.10
        )
        ai_evaluation = await self.ai_service.evaluate_match(resume, job)
        ai_score = clamp_score(ai_evaluation.aiScore if ai_evaluation else rule_composite)
        overall = clamp_score(
            skill_score * 0.40
            + experience_score * 0.20
            + project_score * 0.20
            + education_score * 0.10
            + ai_score * 0.10
        )

        advantages = list(ai_evaluation.advantages) if ai_evaluation else []
        risks = list(ai_evaluation.risks) if ai_evaluation else []
        if matched:
            advantages.insert(0, f"已匹配 {len(matched)} 项核心技能：{', '.join(matched[:6])}")
        if resume.background.workYears is not None:
            advantages.append(f"简历显示约 {resume.background.workYears:g} 年工作经验")
        if missing:
            risks.insert(0, f"尚未在简历中发现核心技能：{', '.join(missing[:6])}")
        if job.workYearsRequirement and resume.background.workYears is None:
            risks.append("简历未明确说明工作年限，需进一步核实")
        if not advantages:
            advantages.append("简历具备可进一步评估的基础信息")
        if not risks:
            risks.append("建议面试中进一步核实经历深度与成果")
        summary = (
            ai_evaluation.summary.strip()
            if ai_evaluation and ai_evaluation.summary.strip()
            else f"规则评估综合得分 {overall:.1f}，核心技能匹配 {len(matched)}/{len(job.coreSkills)} 项。"
        )
        return MatchResult(
            overallScore=overall,
            skillScore=skill_score,
            experienceScore=experience_score,
            projectScore=project_score,
            educationScore=education_score,
            aiScore=ai_score,
            matchedKeywords=matched,
            missingKeywords=missing,
            advantages=advantages,
            risks=risks,
            summary=summary,
            recommendationLevel=recommendation_level(overall),
        )

