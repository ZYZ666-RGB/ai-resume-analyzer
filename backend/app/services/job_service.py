from __future__ import annotations

import re

from app.core.exceptions import BadRequestError
from app.schemas.job import (
    JOB_DESCRIPTION_MAX_LENGTH,
    JOB_DESCRIPTION_MIN_LENGTH,
    JOB_TITLE_MAX_LENGTH,
    JOB_TITLE_MIN_LENGTH,
    JobAnalysis,
)
from app.services.ai_service import AIService
from app.utils.skill_normalizer import extract_known_skills, normalize_skill, normalize_skills


def _skill_appears(skill: str, description: str, known: set[str]) -> bool:
    if normalize_skill(skill) in known:
        return True
    compact_skill = re.sub(r"[\s._-]+", "", skill).casefold()
    compact_description = re.sub(r"[\s._-]+", "", description).casefold()
    return bool(compact_skill and compact_skill in compact_description)


def _degree_requirement(description: str) -> str | None:
    for degree in ("博士", "硕士", "本科", "大专", "专科", "高中"):
        if degree in description:
            return degree
    match = re.search(r"(PhD|Master'?s?|Bachelor'?s?)\s+degree", description, flags=re.I)
    return match.group(0) if match else None


def _years_requirement(description: str) -> float | None:
    match = re.search(
        r"(\d+(?:\.\d+)?)(?:\s*[-~至到]\s*\d+(?:\.\d+)?)?\s*"
        r"(?:年以上|年及以上|年经验|年|\+\s*years?|years?)",
        description,
        flags=re.I,
    )
    return float(match.group(1)) if match else None


def rule_analyze_job(title: str, description: str) -> JobAnalysis:
    all_skills = extract_known_skills(description)
    bonus_text = "\n".join(
        line for line in description.splitlines() if re.search(r"加分|优先|bonus|preferred", line, flags=re.I)
    )
    bonus = set(extract_known_skills(bonus_text))
    core = [skill for skill in all_skills if skill not in bonus]
    lines = [re.sub(r"^[\s\-•*\d.、()（）]+", "", line).strip() for line in description.splitlines()]
    responsibilities = [
        line for line in lines if len(line) >= 6 and re.search(r"负责|参与|设计|开发|维护|build|develop|design", line, flags=re.I)
    ][:10]
    other_requirements = [
        line
        for line in lines
        if len(line) >= 6
        and re.search(r"沟通|协作|抗压|出差|英语|自驱|学历|经验|communication|teamwork", line, flags=re.I)
        and line not in responsibilities
    ][:10]
    industry = next(
        (
            label
            for keyword, label in (
                ("金融", "金融"),
                ("电商", "电子商务"),
                ("医疗", "医疗健康"),
                ("教育", "教育"),
                ("游戏", "游戏"),
                ("互联网", "互联网"),
                ("制造", "制造业"),
            )
            if keyword in description
        ),
        None,
    )
    return JobAnalysis(
        jobTitle=title.strip(),
        coreSkills=core,
        bonusSkills=sorted(bonus),
        educationRequirement=_degree_requirement(description),
        workYearsRequirement=_years_requirement(description),
        responsibilities=responsibilities,
        industry=industry,
        otherRequirements=other_requirements,
    )


class JobService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    @staticmethod
    def validate(title: str, description: str) -> tuple[str, str]:
        title = title.strip()
        description = description.strip()
        if len(title) < JOB_TITLE_MIN_LENGTH:
            raise BadRequestError("岗位名称不能为空")
        if len(title) > JOB_TITLE_MAX_LENGTH:
            raise BadRequestError(f"岗位名称不能超过 {JOB_TITLE_MAX_LENGTH} 个字符")
        if len(description) < JOB_DESCRIPTION_MIN_LENGTH:
            raise BadRequestError(
                f"岗位描述不能为空且至少需要 {JOB_DESCRIPTION_MIN_LENGTH} 个字符"
            )
        if len(description) > JOB_DESCRIPTION_MAX_LENGTH:
            raise BadRequestError(
                f"岗位描述不能超过 {JOB_DESCRIPTION_MAX_LENGTH} 个字符"
            )
        return title, description

    async def analyze(self, title: str, description: str) -> JobAnalysis:
        title, description = self.validate(title, description)
        rules = rule_analyze_job(title, description)
        ai_result = await self.ai_service.analyze_job(title, description)
        if ai_result is None:
            return rules
        ai_result.jobTitle = title
        known = set([*rules.coreSkills, *rules.bonusSkills])
        grounded_core = [
            skill for skill in ai_result.coreSkills if _skill_appears(skill, description, known)
        ]
        grounded_bonus = [
            skill for skill in ai_result.bonusSkills if _skill_appears(skill, description, known)
        ]
        ai_result.coreSkills = normalize_skills([*grounded_core, *rules.coreSkills])
        ai_result.bonusSkills = [
            skill
            for skill in normalize_skills([*grounded_bonus, *rules.bonusSkills])
            if skill not in ai_result.coreSkills
        ]
        ai_result.educationRequirement = ai_result.educationRequirement or rules.educationRequirement
        ai_result.workYearsRequirement = ai_result.workYearsRequirement or rules.workYearsRequirement
        ai_result.responsibilities = ai_result.responsibilities or rules.responsibilities
        ai_result.industry = ai_result.industry or rules.industry
        ai_result.otherRequirements = ai_result.otherRequirements or rules.otherRequirements
        return ai_result
