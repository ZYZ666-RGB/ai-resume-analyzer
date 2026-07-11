from __future__ import annotations

from app.core.config import get_settings
from app.services.ai_service import AIService
from app.services.analysis_service import AnalysisService
from app.services.cache_service import CacheService
from app.services.job_service import JobService
from app.services.matching_service import MatchingService
from app.services.pdf_service import PDFService
from app.services.resume_service import ResumeService

settings = get_settings()
ai_service = AIService(settings)
cache_service = CacheService(settings)
pdf_service = PDFService(settings)
resume_service = ResumeService(ai_service)
job_service = JobService(ai_service)
matching_service = MatchingService(ai_service)
analysis_service = AnalysisService(
    settings=settings,
    pdf_service=pdf_service,
    resume_service=resume_service,
    job_service=job_service,
    matching_service=matching_service,
    cache_service=cache_service,
)


async def close_services() -> None:
    await ai_service.close()
    await cache_service.close()

