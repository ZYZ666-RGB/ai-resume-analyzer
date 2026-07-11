from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import NotFoundError
from app.schemas.job import JobAnalysis
from app.schemas.resume import StructuredResume
from app.services.cache_service import CacheService
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.services.pdf_service import PDFService
from app.services.resume_service import ResumeService
from app.utils.hash_utils import sha256_bytes, sha256_text

logger = logging.getLogger(__name__)


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

    def _record_from_cached(self, value: dict) -> ResumeRecord:
        return ResumeRecord(
            resume_id=str(value["resumeId"]),
            resume_hash=str(value["resumeHash"]),
            page_count=int(value["pageCount"]),
            cleaned_text=str(value.get("cleanedText") or ""),
            resume=StructuredResume.model_validate(value["resume"]),
        )

    async def parse(self, file: UploadFile) -> dict:
        content = await self.pdf_service.read_and_validate(file)
        resume_hash = sha256_bytes(content)
        cache_key = f"resume:parse:{resume_hash}"
        cached = await self.cache_service.get_json(cache_key)
        if cached:
            try:
                record = self._record_from_cached(cached)
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
            cached = await self.cache_service.get_json(f"resume:parse:{resume_hash}")
            if cached:
                try:
                    record = self._record_from_cached(cached)
                    if record.resume_id == resume_id:
                        self._records[resume_id] = record
                        return record
                except (KeyError, TypeError, ValueError):
                    logger.warning("resume_cache_invalid hash_prefix=%s", resume_hash[:8])
        raise NotFoundError("简历不存在或已过期，请重新上传")

    async def match(self, resume_id: str, job_title: str, job_description: str) -> dict:
        job_title, job_description = self.job_service.validate(job_title, job_description)
        record = await self.get_record(resume_id)
        jd_hash = sha256_text(f"{job_title}{job_description}")
        cache_key = f"resume:match:{record.resume_hash}:{jd_hash}"
        cached = await self.cache_service.get_json(cache_key)
        if cached and isinstance(cached.get("job"), dict) and isinstance(cached.get("match"), dict):
            return {
                "resumeId": resume_id,
                "job": cached["job"],
                "match": cached["match"],
                "cacheHit": True,
            }
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
