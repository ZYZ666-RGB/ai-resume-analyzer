from __future__ import annotations

import httpx
import pytest

from app.core.config import Settings
from app.services.analysis_service import AnalysisService
from app.services.ai_service import AIService
from app.services.cache_service import CacheService
from app.services.job_service import JobService
from app.services.matching_service import clamp_score, recommendation_level
from app.services.pdf_service import PDFService


class BrokenRedis:
    async def get(self, _: str):
        raise ConnectionError("redis unavailable")

    async def set(self, *args, **kwargs):
        raise ConnectionError("redis unavailable")


class CachedResumeStore:
    def __init__(self, resume_hash: str) -> None:
        self.resume_hash = resume_hash

    async def get_json(self, key: str):
        if key != f"resume:parse:{self.resume_hash}":
            return None
        return {
            "resumeId": f"res_{self.resume_hash}",
            "resumeHash": self.resume_hash,
            "pageCount": 2,
            "cleanedText": "Python FastAPI",
            "resume": {
                "basicInfo": {},
                "jobInfo": {},
                "background": {},
            },
            "cacheHit": False,
        }


@pytest.mark.asyncio
async def test_redis_unavailable_degrades_to_cache_miss() -> None:
    cache = CacheService(Settings(redis_enabled=True), client=BrokenRedis())
    assert await cache.get_json("key") is None
    assert await cache.set_json("key", {"ok": True}) is False


@pytest.mark.asyncio
async def test_resume_record_recovers_from_redis_after_fc_cold_start() -> None:
    resume_hash = "a" * 64
    service = AnalysisService(
        settings=Settings(),
        pdf_service=None,  # type: ignore[arg-type]
        resume_service=None,  # type: ignore[arg-type]
        job_service=None,  # type: ignore[arg-type]
        matching_service=None,  # type: ignore[arg-type]
        cache_service=CachedResumeStore(resume_hash),  # type: ignore[arg-type]
    )

    record = await service.get_record(f"res_{resume_hash}")

    assert record.resume_hash == resume_hash
    assert record.page_count == 2
    assert record.resume.background.skills == []


@pytest.mark.asyncio
async def test_invalid_ai_json_returns_none_without_real_network_call() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not-json"}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = AIService(Settings(dashscope_api_key="mock-key"), client=client)
    assert await service.extract_resume("张三 Python 开发") is None
    await client.aclose()


def test_scoring_boundaries_and_recommendation_levels() -> None:
    assert clamp_score(-10) == 0
    assert clamp_score(110) == 100
    assert recommendation_level(85) == "高度匹配"
    assert recommendation_level(70) == "较为匹配"
    assert recommendation_level(50) == "一般匹配"
    assert recommendation_level(49.9) == "匹配度较低"


def test_empty_job_description_is_rejected() -> None:
    with pytest.raises(Exception) as error:
        JobService.validate("Python 开发", " 太短 ")
    assert "至少需要 10 个字符" in str(error.value)


def test_pdf_service_extracts_multiple_pages(make_pdf) -> None:
    result = PDFService(Settings()).extract_text(make_pdf(["Page one Python", "Page two Redis"]))
    assert result.page_count == 2
    assert "Page one Python" in result.cleaned_text
    assert "Page two Redis" in result.cleaned_text
