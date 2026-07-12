from __future__ import annotations

from typing import Any

import pytest

from app.core.config import Settings
from app.schemas.job import JobAnalysis
from app.schemas.match import MatchResult
from app.schemas.resume import StructuredResume
from app.services.analysis_service import (
    MATCH_CACHE_NAMESPACE,
    PARSE_CACHE_NAMESPACE,
    AnalysisService,
    ResumeRecord,
)
from app.services.cache_service import CacheService
from app.services.pdf_service import PDFText
from app.utils.hash_utils import (
    sha256_bytes,
    sha256_canonical_json,
    sha256_job_description,
)


class MemoryCache:
    def __init__(self, values: dict[str, dict[str, Any]] | None = None) -> None:
        self.values = values or {}
        self.get_keys: list[str] = []
        self.set_calls: list[tuple[str, dict[str, Any]]] = []

    async def get_json(self, key: str) -> dict[str, Any] | None:
        self.get_keys.append(key)
        return self.values.get(key)

    async def set_json(self, key: str, value: dict[str, Any]) -> bool:
        self.set_calls.append((key, value))
        self.values[key] = value
        return True


class FakePDFService:
    def __init__(self, content: bytes = b"%PDF-cache-test") -> None:
        self.content = content
        self.extract_calls = 0

    async def read_and_validate(self, _file: object) -> bytes:
        return self.content

    def extract_text(self, _content: bytes) -> PDFText:
        self.extract_calls += 1
        return PDFText(page_count=2, cleaned_text="Python FastAPI Redis")


class FakeResumeService:
    def __init__(self) -> None:
        self.calls = 0

    async def extract(self, _text: str) -> StructuredResume:
        self.calls += 1
        return StructuredResume.model_validate(
            {"background": {"skills": ["python", "fastapi", "redis"]}}
        )


class FakeJobService:
    def __init__(self, fail_analyze: bool = False) -> None:
        self.analyze_calls = 0
        self.fail_analyze = fail_analyze

    @staticmethod
    def validate(title: str, description: str) -> tuple[str, str]:
        return title.strip(), description.strip()

    async def analyze(self, title: str, _description: str) -> JobAnalysis:
        self.analyze_calls += 1
        if self.fail_analyze:
            raise AssertionError("valid match cache should skip job analysis")
        return JobAnalysis(jobTitle=title, coreSkills=["python", "fastapi"])


class FakeMatchingService:
    def __init__(self, fail_match: bool = False) -> None:
        self.calls = 0
        self.fail_match = fail_match

    async def match(
        self, _resume: StructuredResume, _job: JobAnalysis
    ) -> MatchResult:
        self.calls += 1
        if self.fail_match:
            raise AssertionError("valid match cache should skip score calculation")
        return _match_result()


class RecordingRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int | None]] = []

    async def set(self, key: str, payload: str, ex: int | None = None) -> None:
        self.calls.append((key, payload, ex))


def _job() -> JobAnalysis:
    return JobAnalysis(jobTitle="Python Engineer", coreSkills=["python", "fastapi"])


def _match_result() -> MatchResult:
    return MatchResult(
        overallScore=88.0,
        skillScore=100.0,
        experienceScore=80.0,
        projectScore=75.0,
        educationScore=80.0,
        aiScore=85.0,
        matchedKeywords=["python", "fastapi"],
        missingKeywords=[],
        advantages=["skills"],
        risks=["verify depth"],
        summary="good fit",
        recommendationLevel="high",
    )


def _cached_resume(resume_hash: str) -> dict[str, Any]:
    return {
        "resumeId": f"res_{resume_hash}",
        "resumeHash": resume_hash,
        "pageCount": 2,
        "cleanedText": "Python FastAPI Redis",
        "resume": StructuredResume.model_validate(
            {"background": {"skills": ["python", "fastapi", "redis"]}}
        ).model_dump(),
        "cacheHit": False,
    }


def _service(
    cache: MemoryCache,
    *,
    pdf: FakePDFService | None = None,
    resume: FakeResumeService | None = None,
    job: FakeJobService | None = None,
    matching: FakeMatchingService | None = None,
) -> AnalysisService:
    return AnalysisService(
        settings=Settings(redis_enabled=True),
        pdf_service=pdf or FakePDFService(),  # type: ignore[arg-type]
        resume_service=resume or FakeResumeService(),  # type: ignore[arg-type]
        job_service=job or FakeJobService(),  # type: ignore[arg-type]
        matching_service=matching or FakeMatchingService(),  # type: ignore[arg-type]
        cache_service=cache,  # type: ignore[arg-type]
    )


def test_canonical_job_hash_is_order_stable_and_preserves_field_boundaries() -> None:
    assert sha256_canonical_json({"b": 2, "a": 1}) == sha256_canonical_json(
        {"a": 1, "b": 2}
    )
    assert sha256_job_description("ab", "c") != sha256_job_description("a", "bc")


@pytest.mark.asyncio
async def test_parse_and_match_use_versioned_cache_namespaces() -> None:
    content = b"%PDF-versioned-cache"
    cache = MemoryCache()
    service = _service(cache, pdf=FakePDFService(content))

    parsed = await service.parse(object())  # type: ignore[arg-type]
    await service.match(
        parsed["resumeId"],
        "Python Engineer",
        "Build Python and FastAPI backend services",
    )

    resume_hash = sha256_bytes(content)
    jd_hash = sha256_job_description(
        "Python Engineer", "Build Python and FastAPI backend services"
    )
    assert cache.get_keys == [
        f"{PARSE_CACHE_NAMESPACE}:{resume_hash}",
        f"{MATCH_CACHE_NAMESPACE}:{resume_hash}:{jd_hash}",
    ]
    assert [key for key, _ in cache.set_calls] == cache.get_keys


@pytest.mark.asyncio
async def test_cache_service_passes_configured_ttl_to_redis() -> None:
    redis = RecordingRedis()
    cache = CacheService(
        Settings(redis_enabled=True, redis_ttl=321), client=redis
    )

    assert await cache.set_json("resume:parse:v1:test", {"ok": True}) is True
    assert redis.calls == [("resume:parse:v1:test", '{"ok":true}', 321)]


@pytest.mark.asyncio
async def test_corrupt_parse_cache_is_a_miss_and_is_recomputed() -> None:
    content = b"%PDF-corrupt-parse-cache"
    resume_hash = sha256_bytes(content)
    key = f"{PARSE_CACHE_NAMESPACE}:{resume_hash}"
    corrupt = _cached_resume(resume_hash)
    corrupt["resume"] = "not-an-object"
    cache = MemoryCache({key: corrupt})
    pdf = FakePDFService(content)
    resume = FakeResumeService()
    service = _service(cache, pdf=pdf, resume=resume)

    result = await service.parse(object())  # type: ignore[arg-type]

    assert result["cacheHit"] is False
    assert pdf.extract_calls == 1
    assert resume.calls == 1
    assert cache.set_calls[0][0] == key


@pytest.mark.asyncio
async def test_valid_parse_cache_is_validated_and_returns_cache_hit() -> None:
    content = b"%PDF-valid-parse-cache"
    resume_hash = sha256_bytes(content)
    key = f"{PARSE_CACHE_NAMESPACE}:{resume_hash}"
    cache = MemoryCache({key: _cached_resume(resume_hash)})
    pdf = FakePDFService(content)
    resume = FakeResumeService()
    service = _service(cache, pdf=pdf, resume=resume)

    result = await service.parse(object())  # type: ignore[arg-type]

    assert result["cacheHit"] is True
    assert result["resumeHash"] == resume_hash
    assert pdf.extract_calls == 0
    assert resume.calls == 0
    assert cache.set_calls == []


@pytest.mark.asyncio
async def test_unversioned_parse_value_is_ignored_and_recomputed() -> None:
    content = b"%PDF-old-parse-cache"
    resume_hash = sha256_bytes(content)
    old_key = f"resume:parse:{resume_hash}"
    new_key = f"{PARSE_CACHE_NAMESPACE}:{resume_hash}"
    cache = MemoryCache({old_key: _cached_resume(resume_hash)})
    pdf = FakePDFService(content)
    resume = FakeResumeService()
    service = _service(cache, pdf=pdf, resume=resume)

    result = await service.parse(object())  # type: ignore[arg-type]

    assert result["cacheHit"] is False
    assert cache.get_keys == [new_key]
    assert cache.set_calls[0][0] == new_key
    assert pdf.extract_calls == 1
    assert resume.calls == 1


@pytest.mark.asyncio
async def test_corrupt_match_cache_is_a_miss_and_is_recomputed() -> None:
    resume_hash = "b" * 64
    title = "Python Engineer"
    description = "Build Python and FastAPI backend services"
    key = (
        f"{MATCH_CACHE_NAMESPACE}:{resume_hash}:"
        f"{sha256_job_description(title, description)}"
    )
    cache = MemoryCache(
        {key: {"job": _job().model_dump(), "match": {"overallScore": "bad"}}}
    )
    job = FakeJobService()
    matching = FakeMatchingService()
    service = _service(cache, job=job, matching=matching)
    resume_id = f"res_{resume_hash}"
    service._records[resume_id] = ResumeRecord(
        resume_id=resume_id,
        resume_hash=resume_hash,
        page_count=1,
        cleaned_text="Python FastAPI",
        resume=StructuredResume.model_validate(
            {"background": {"skills": ["python", "fastapi"]}}
        ),
    )

    result = await service.match(resume_id, title, description)

    assert result["cacheHit"] is False
    assert job.analyze_calls == 1
    assert matching.calls == 1
    assert cache.set_calls[0][0] == key


@pytest.mark.asyncio
async def test_valid_match_cache_is_fully_validated_and_returns_cache_hit() -> None:
    resume_hash = "c" * 64
    title = "Python Engineer"
    description = "Build Python and FastAPI backend services"
    key = (
        f"{MATCH_CACHE_NAMESPACE}:{resume_hash}:"
        f"{sha256_job_description(title, description)}"
    )
    cache = MemoryCache(
        {
            key: {
                "job": _job().model_dump(),
                "match": _match_result().model_dump(),
            }
        }
    )
    job = FakeJobService(fail_analyze=True)
    matching = FakeMatchingService(fail_match=True)
    service = _service(cache, job=job, matching=matching)
    resume_id = f"res_{resume_hash}"
    service._records[resume_id] = ResumeRecord(
        resume_id=resume_id,
        resume_hash=resume_hash,
        page_count=1,
        cleaned_text="Python FastAPI",
        resume=StructuredResume(),
    )

    result = await service.match(resume_id, title, description)

    assert result["cacheHit"] is True
    assert result["job"]["jobTitle"] == title
    assert result["match"]["overallScore"] == 88.0
    assert job.analyze_calls == 0
    assert matching.calls == 0
    assert cache.set_calls == []


@pytest.mark.asyncio
async def test_fc_cold_start_recovers_resume_from_versioned_cache() -> None:
    resume_hash = "d" * 64
    key = f"{PARSE_CACHE_NAMESPACE}:{resume_hash}"
    cache = MemoryCache({key: _cached_resume(resume_hash)})
    restarted_service = _service(cache)

    record = await restarted_service.get_record(f"res_{resume_hash}")

    assert record.resume_hash == resume_hash
    assert record.page_count == 2
    assert record.resume.background.skills == ["python", "fastapi", "redis"]
    assert cache.get_keys == [key]
