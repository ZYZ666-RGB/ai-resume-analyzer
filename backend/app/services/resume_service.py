from __future__ import annotations

import re

from app.schemas.resume import (
    Background,
    BasicInfo,
    Education,
    JobInfo,
    Project,
    StructuredResume,
    WorkExperience,
)
from app.services.ai_service import AIService
from app.utils.regex_utils import extract_contacts
from app.utils.skill_normalizer import extract_known_skills, normalize_skill, normalize_skills


def _match_value(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.I | re.M)
    return match.group(1).strip() if match else None


def _appears_in_source(value: str | None, source: str) -> bool:
    if not value:
        return False
    compact_value = re.sub(r"\s+", "", value).casefold()
    compact_source = re.sub(r"\s+", "", source).casefold()
    return bool(compact_value and compact_value in compact_source)


def _phone_appears_in_source(value: str | None, source: str) -> bool:
    digits = re.sub(r"\D", "", value or "")
    source_digits = re.sub(r"\D", "", source)
    return len(digits) >= 7 and digits in source_digits


def _extract_name(text: str) -> str | None:
    explicit = _match_value(r"^\s*(?:姓名|name)\s*[:：]\s*([^\n|]{2,40})", text)
    if explicit:
        return explicit
    for line in text.splitlines()[:5]:
        line = line.strip()
        if re.fullmatch(r"[\u4e00-\u9fff·]{2,8}", line) and line not in {"个人简历", "简历"}:
            return line
        if re.fullmatch(r"[A-Za-z][A-Za-z .'-]{2,39}", line) and "resume" not in line.casefold():
            return line
    return None


def _extract_education(text: str) -> list[Education]:
    entries: list[Education] = []
    degree_names = ("博士", "硕士", "本科", "学士", "大专", "专科")
    for line in text.splitlines():
        if not re.search(r"大学|学院|University|College", line, flags=re.I):
            continue
        degree = next((item for item in degree_names if item in line), None)
        dates = re.findall(r"(?:19|20)\d{2}(?:[./-]\d{1,2})?", line)
        entries.append(
            Education(
                school=line[:120],
                degree=degree,
                startDate=dates[0] if dates else None,
                endDate=dates[1] if len(dates) > 1 else None,
            )
        )
        if len(entries) >= 5:
            break
    return entries


def _date_range(line: str) -> tuple[str | None, str | None]:
    dates = re.findall(r"(?:19|20)\d{2}(?:[./-]\d{1,2})?", line)
    return (dates[0] if dates else None, dates[1] if len(dates) > 1 else None)


def _extract_work_experiences(text: str) -> list[WorkExperience]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    entries: list[WorkExperience] = []
    company_pattern = re.compile(r"公司|集团|科技|银行|事务所|Company|Corp\.?|Inc\.?|Ltd\.?", re.I)
    for index, line in enumerate(lines):
        if not company_pattern.search(line):
            continue
        start_date, end_date = _date_range(line)
        following = lines[index + 1 : index + 4]
        position = next(
            (
                item
                for item in following
                if len(item) <= 60
                and re.search(r"工程师|开发|经理|主管|实习|顾问|Engineer|Developer|Manager|Intern", item, re.I)
            ),
            None,
        )
        entries.append(
            WorkExperience(
                company=line[:160],
                position=position,
                startDate=start_date,
                endDate=end_date,
                description="；".join(following)[:500] or None,
            )
        )
        if len(entries) >= 8:
            break
    return entries


def _extract_projects(text: str) -> list[Project]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    entries: list[Project] = []
    for index, line in enumerate(lines):
        match = re.match(r"(?:项目(?:名称)?|project(?: name)?)\s*[:：-]?\s*(.+)", line, flags=re.I)
        if not match:
            continue
        following = lines[index + 1 : index + 5]
        description = "；".join(following)[:600]
        entries.append(
            Project(
                name=match.group(1).strip()[:120] or None,
                technologies=extract_known_skills(f"{line} {description}"),
                description=description or None,
            )
        )
        if len(entries) >= 8:
            break
    return entries


def _extract_certificates(text: str) -> list[str]:
    return [
        line.strip()[:160]
        for line in text.splitlines()
        if 2 <= len(line.strip()) <= 160
        and re.search(r"证书|认证|资格|获奖|荣誉|certified|certificate|award", line, re.I)
    ][:12]


def rule_extract_resume(text: str) -> StructuredResume:
    phone, email = extract_contacts(text)
    work_years_raw = _match_value(
        r"(?:工作年限|工作经验|work experience|experience)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:年|years?)",
        text,
    )
    work_years = float(work_years_raw) if work_years_raw else None
    address = _match_value(r"^\s*(?:现居住地|所在地|地址|address)\s*[:：]\s*([^\n|]{2,100})", text)
    intention = _match_value(r"^\s*(?:求职意向|目标岗位)\s*[:：]\s*([^\n|]{2,100})", text)
    salary = _match_value(r"^\s*(?:期望薪资|薪资期望)\s*[:：]\s*([^\n|]{1,80})", text)
    return StructuredResume(
        basicInfo=BasicInfo(
            name=_extract_name(text), phone=phone, email=email, address=address
        ),
        jobInfo=JobInfo(jobIntention=intention, expectedSalary=salary),
        background=Background(
            workYears=work_years,
            education=_extract_education(text),
            workExperiences=_extract_work_experiences(text),
            skills=extract_known_skills(text),
            projects=_extract_projects(text),
            certificates=_extract_certificates(text),
        ),
    )


class ResumeService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def extract(self, text: str) -> StructuredResume:
        rules = rule_extract_resume(text)
        ai_result = await self.ai_service.extract_resume(text)
        if ai_result is None:
            return rules
        phone, email = extract_contacts(text)
        ai_phone, _ = extract_contacts(ai_result.basicInfo.phone or "")
        _, ai_email = extract_contacts(ai_result.basicInfo.email or "")
        ai_result.basicInfo.phone = phone or (
            ai_phone if _phone_appears_in_source(ai_phone, text) else None
        )
        ai_result.basicInfo.email = email or (
            ai_email if _appears_in_source(ai_email, text) else None
        )
        if not _appears_in_source(ai_result.basicInfo.name, text):
            ai_result.basicInfo.name = rules.basicInfo.name
        if not _appears_in_source(ai_result.basicInfo.address, text):
            ai_result.basicInfo.address = rules.basicInfo.address
        if not _appears_in_source(ai_result.jobInfo.jobIntention, text):
            ai_result.jobInfo.jobIntention = rules.jobInfo.jobIntention
        if not _appears_in_source(ai_result.jobInfo.expectedSalary, text):
            ai_result.jobInfo.expectedSalary = rules.jobInfo.expectedSalary
        ai_result.background.workYears = ai_result.background.workYears or rules.background.workYears
        ai_result.background.education = [
            item
            for item in ai_result.background.education
            if _appears_in_source(item.school, text) or _appears_in_source(item.major, text)
        ]
        if not ai_result.background.education:
            ai_result.background.education = rules.background.education
        ai_result.background.workExperiences = [
            item
            for item in ai_result.background.workExperiences
            if _appears_in_source(item.company, text) or _appears_in_source(item.position, text)
        ]
        if not ai_result.background.workExperiences:
            ai_result.background.workExperiences = rules.background.workExperiences
        ai_result.background.projects = [
            item
            for item in ai_result.background.projects
            if _appears_in_source(item.name, text)
        ]
        if not ai_result.background.projects:
            ai_result.background.projects = rules.background.projects
        ai_result.background.certificates = [
            item for item in ai_result.background.certificates if _appears_in_source(item, text)
        ]
        if not ai_result.background.certificates:
            ai_result.background.certificates = rules.background.certificates
        source_skills = set(rules.background.skills)
        grounded_ai_skills = [
            skill
            for skill in ai_result.background.skills
            if normalize_skill(skill) in source_skills or _appears_in_source(skill, text)
        ]
        ai_result.background.skills = normalize_skills(
            [*grounded_ai_skills, *rules.background.skills]
        )
        return ai_result
