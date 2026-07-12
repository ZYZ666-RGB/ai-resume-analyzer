from __future__ import annotations

import pytest

from app.core.config import Settings
from app.schemas.job import JobAnalysis
from app.schemas.resume import StructuredResume
from app.services.ai_service import AIService
from app.services.matching_service import MatchingService


@pytest.mark.asyncio
async def test_full_weighted_formula_uses_all_rule_dimensions_and_fallback_score() -> None:
    resume = StructuredResume.model_validate(
        {
            "background": {
                "workYears": 2,
                "skills": ["Python", "Redis"],
                "education": [{"degree": "本科"}],
                "projects": [
                    {
                        "name": "API Platform",
                        "technologies": ["Python"],
                        "description": "Built a Python service",
                    }
                ],
            }
        }
    )
    job = JobAnalysis(
        jobTitle="Backend Engineer",
        coreSkills=["Python", "Redis"],
        workYearsRequirement=4,
        educationRequirement="本科及以上",
    )

    result = await MatchingService(AIService(Settings(dashscope_api_key=None))).match(
        resume, job
    )

    assert result.skillScore == 100.0
    assert result.experienceScore == 50.0
    assert result.projectScore == 50.0
    assert result.educationScore == 100.0
    assert result.aiScore == 77.5
    assert result.overallScore == 77.8
    assert result.aiUsed is False
    assert result.analysisMode == "rules"
