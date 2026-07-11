from __future__ import annotations

import logging
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.core.exceptions import AIServiceError
from app.prompts.job_analysis import build_job_prompt
from app.prompts.resume_extraction import build_resume_prompt
from app.prompts.resume_matching import build_match_prompt
from app.schemas.job import JobAnalysis
from app.schemas.match import AIMatchEvaluation
from app.schemas.resume import StructuredResume
from app.utils.json_utils import parse_json_object

ModelT = TypeVar("ModelT", bound=BaseModel)
logger = logging.getLogger(__name__)


class AIService:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self.settings = settings
        self._client = client
        self._owns_client = client is None

    @property
    def enabled(self) -> bool:
        return bool(self.settings.dashscope_api_key)

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.settings.dashscope_timeout)
        return self._client

    async def _request_json(self, prompt: str) -> dict:
        if not self.enabled:
            return {}
        payload = {
            "model": self.settings.dashscope_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You return only strict JSON grounded in the supplied text.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.dashscope_api_key}",
            "Content-Type": "application/json",
        }
        started = time.perf_counter()
        try:
            response = await self._get_client().post(
                self.settings.dashscope_base_url, json=payload, headers=headers
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.warning("ai_request_timeout elapsed_ms=%.2f", (time.perf_counter() - started) * 1000)
            raise AIServiceError("AI 服务调用超时", 504) from exc
        except httpx.HTTPStatusError as exc:
            logger.warning("ai_request_http_error status=%s", exc.response.status_code)
            raise AIServiceError("AI 服务调用失败", 502) from exc
        except httpx.RequestError as exc:
            logger.warning("ai_request_network_error type=%s", type(exc).__name__)
            raise AIServiceError("AI 服务暂时不可用", 502) from exc
        logger.info("ai_request_completed elapsed_ms=%.2f", (time.perf_counter() - started) * 1000)
        try:
            body = response.json()
            raw = body["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AIServiceError("AI 服务返回格式异常", 502) from exc
        return parse_json_object(raw)

    async def _validated(self, prompt: str, model: type[ModelT]) -> ModelT | None:
        if not self.enabled:
            return None
        try:
            data = await self._request_json(prompt)
            return model.model_validate(data)
        except (ValueError, ValidationError) as exc:
            logger.warning("ai_output_validation_failed model=%s type=%s", model.__name__, type(exc).__name__)
            return None

    async def extract_resume(self, text: str) -> StructuredResume | None:
        return await self._validated(build_resume_prompt(text), StructuredResume)

    async def analyze_job(self, title: str, description: str) -> JobAnalysis | None:
        return await self._validated(build_job_prompt(title, description), JobAnalysis)

    async def evaluate_match(
        self, resume: StructuredResume, job: JobAnalysis
    ) -> AIMatchEvaluation | None:
        return await self._validated(build_match_prompt(resume, job), AIMatchEvaluation)

    async def close(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()

