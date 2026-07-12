from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import NotFoundError
from app.schemas.job import JobAnalysis
from app.schemas.match import MatchResponseData
from app.schemas.resume import ParsedResumeData, StructuredResume
from app.services.cache_service import CacheService
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.services.pdf_service import PDFService
from app.services.resume_service import ResumeService
from app.utils.hash_utils import sha256_bytes, sha256_job_description

logger = logging.getLogger(__name__)

CACHE_KEY_VERSION = "v1"
PARSE_CACHE_NAMESPACE = f"resume:parse:{CACHE_KEY_VERSION}"
MATCH_CACHE_NAMESPACE = f"resume:match:{CACHE_KEY_VERSION}"
# Kept read-only during the version transition so resume IDs issued by an older
# running FC instance can still be resolved after a rolling deployment.
LEGACY_PARSE_CACHE_NAMESPACE = "resume:parse"


@dataclass(slots=True)
class ResumeRecord:
    resume_id: str
    resume_hash: str
    page_count: int
    cleaned_text: str
    resume: StructuredResume


class AnalysisService:
    def __init__(
        self,
        settings: Settings,
        pdf_service: PDFService,
        resume_service: ResumeService,
        job_service: JobService,
        matching_service: MatchingService,
        cache_service: CacheService,
    ):
        self.settings = settings
        self.pdf_service = pdf_service
        self.resume_service = resume_service
        self.job_service = job_service
        self.matching_service = matching_service
        self.cache_service = cache_service
        self._records: dict[str, ResumeRecord] = {}

    def _public_parse(self, record: ResumeRecord, cache_hit: bool) -> dict:
        return {
            "resumeId": record.resume_id,
            "resumeHash": record.resume_hash,
            "pageCount": record.page_count,
            "cleanedText": record.cleaned_text if self.settings.return_cleaned_text else None,
            "resume": record.resume.model_dump(),
            "cacheHit": cache_hit,
        }

    def _record_from_cached(
        self, value: dict, expected_resume_hash: str | None = None
    ) -> ResumeRecord:
        parsed = ParsedResumeData.model_validate(value, strict=True)
        if (
            len(parsed.resumeHash) != 64
            or any(char not in "0123456789abcdef" for char in parsed.resumeHash)
            or parsed.resumeId != f"res_{parsed.resumeHash}"
            or (
                expected_resume_hash is not None
                and parsed.resumeHash != expected_resume_hash
            )
            or parsed.pageCount < 1
            or not isinstance(parsed.cleanedText, str)
        ):
            raise ValueError("invalid cached resume metadata")
        return ResumeRecord(
            resume_id=parsed.resumeId,
            resume_hash=parsed.resumeHash,
            page_count=parsed.pageCount,
            cleaned_text=parsed.cleanedText,
            resume=parsed.resume,
        )

    @staticmethod
    def _parse_cache_key(resume_hash: str) -> str:
        return f"{PARSE_CACHE_NAMESPACE}:{resume_hash}"

    @staticmethod
    def _match_cache_key(resume_hash: str, jd_hash: str) -> str:
        return f"{MATCH_CACHE_NAMESPACE}:{resume_hash}:{jd_hash}"

    @staticmethod
    def _public_match_from_cached(
        value: dict, resume_id: str, expected_job_title: str
    ) -> dict:
        # The stored payload intentionally contains only job/match. Build the
        # complete response model here so all nested fields are validated before
        # a cache hit can reach FastAPI's response serialization boundary.
        validated = MatchResponseData.model_validate(
            {
                "resumeId": resume_id,
                "job": value["job"],
                "match": value["match"],
                "cacheHit": True,
            },
            strict=True,
        )
        if validated.job.jobTitle != expected_job_title:
            raise ValueError("cached job title does not match its cache key")
        return validated.model_dump()

    async def parse(self, file: UploadFile) -> dict:
        content = await self.pdf_service.read_and_validate(file)
        resume_hash = sha256_bytes(content)
        cache_key = self._parse_cache_key(resume_hash)
        cached = await self.cache_service.get_json(cache_key)
        if cached is not None:
            try:
                record = self._record_from_cached(cached, resume_hash)
                self._records[record.resume_id] = record
                logger.info("resume_parse cache_hit=true page_count=%s", record.page_count)
                return self._public_parse(record, True)
            except (KeyError, TypeError, ValueError):
                logger.warning("resume_cache_invalid hash_prefix=%s", resume_hash[:8])

        pdf = self.pdf_service.extract_text(content)
        structured = await self.resume_service.extract(pdf.cleaned_text)
        record = ResumeRecord(
            # The full hash keeps the identifier reversible so a stateless FC
            # instance can recover the required Redis parse key after a cold start.
            resume_id=f"res_{resume_hash}",
            resume_hash=resume_hash,
            page_count=pdf.page_count,
            cleaned_text=pdf.cleaned_text,
            resume=structured,
        )
        self._records[record.resume_id] = record
        cached_value = self._public_parse(record, False)
        cached_value["cleanedText"] = record.cleaned_text
        await self.cache_service.set_json(cache_key, cached_value)
        logger.info("resume_parse cache_hit=false page_count=%s", record.page_count)
        return self._public_parse(record, False)

    async def get_record(self, resume_id: str) -> ResumeRecord:
        record = self._records.get(resume_id)
        if record is not None:
            return record
        resume_hash = resume_id.removeprefix("res_")
        if len(resume_hash) == 64 and all(char in "0123456789abcdef" for char in resume_hash):
            cached = await self.cache_service.get_json(self._parse_cache_key(resume_hash))
            if cached is not None:
                try:
                    record = self._record_from_cached(cached, resume_hash)
                    if record.resume_id == resume_id:
                        self._records[resume_id] = record
                        return record
                except (KeyError, TypeError, ValueError):
                    logger.warning("resume_cache_invalid hash_prefix=%s", resume_hash[:8])
            else:
                # Transitional read compatibility only. New writes always use
                # the versioned namespace above, so schema/prompt changes cannot
                # collide with legacy entries.
                legacy = await self.cache_service.get_json(
                    f"{LEGACY_PARSE_CACHE_NAMESPACE}:{resume_hash}"
                )
                if legacy is not None:
                    try:
                        record = self._record_from_cached(legacy, resume_hash)
                        if record.resume_id == resume_id:
                            self._records[resume_id] = record
                            return record
                    except (KeyError, TypeError, ValueError):
                        logger.warning(
                            "resume_legacy_cache_invalid hash_prefix=%s", resume_hash[:8]
                        )
        raise NotFoundError("简历不存在或已过期，请重新上传")

    async def match(self, resume_id: str, job_title: str, job_description: str) -> dict:
        job_title, job_description = self.job_service.validate(job_title, job_description)
        record = await self.get_record(resume_id)
        jd_hash = sha256_job_description(job_title, job_description)
        cache_key = self._match_cache_key(record.resume_hash, jd_hash)
        cached = await self.cache_service.get_json(cache_key)
        if cached is not None:
            try:
                return self._public_match_from_cached(cached, resume_id, job_title)
            except (KeyError, TypeError, ValueError):
                logger.warning(
                    "resume_match_cache_invalid resume_hash_prefix=%s jd_hash_prefix=%s",
                    record.resume_hash[:8],
                    jd_hash[:8],
                )
        job = await self.job_service.analyze(job_title, job_description)
        match = await self.matching_service.match(record.resume, job)
        value = {"job": job.model_dump(), "match": match.model_dump()}
        await self.cache_service.set_json(cache_key, value)
        return {"resumeId": resume_id, **value, "cacheHit": False}

    async def analyze(self, file: UploadFile, job_title: str, job_description: str) -> dict:
        parsed = await self.parse(file)
        matched = await self.match(parsed["resumeId"], job_title, job_description)
        return {
            "resumeId": parsed["resumeId"],
            "pageCount": parsed["pageCount"],
            "resumeHash": parsed["resumeHash"],
            "cleanedText": parsed["cleanedText"],
            "resume": parsed["resume"],
            "job": matched["job"],
            "match": matched["match"],
            "cacheHit": bool(matched["cacheHit"]),
        }
