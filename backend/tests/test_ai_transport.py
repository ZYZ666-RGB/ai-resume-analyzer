from __future__ import annotations

import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import AIServiceError
from app.services.ai_service import AIService


def _service(handler) -> tuple[AIService, httpx.AsyncClient]:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return AIService(Settings(dashscope_api_key="mock-key"), client=client), client


@pytest.mark.parametrize("status_code", [401, 429, 500])
@pytest.mark.asyncio
async def test_ai_http_errors_map_to_safe_502(status_code: int) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "upstream detail must stay private"})

    service, client = _service(handler)
    try:
        with pytest.raises(AIServiceError) as raised:
            await service.extract_resume("safe test resume")
    finally:
        await client.aclose()

    assert raised.value.status_code == 502
    assert "upstream detail" not in raised.value.message


@pytest.mark.asyncio
async def test_ai_timeout_maps_to_504() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("upstream timed out", request=request)

    service, client = _service(handler)
    try:
        with pytest.raises(AIServiceError) as raised:
            await service.extract_resume("safe test resume")
    finally:
        await client.aclose()

    assert raised.value.status_code == 504
    assert raised.value.message == "AI 服务调用超时"


@pytest.mark.asyncio
async def test_ai_network_error_and_invalid_envelope_map_to_502() -> None:
    def network_error(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    network_service, network_client = _service(network_error)
    try:
        with pytest.raises(AIServiceError) as network_raised:
            await network_service.extract_resume("safe test resume")
    finally:
        await network_client.aclose()
    assert network_raised.value.status_code == 502

    def invalid_envelope(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": []})

    envelope_service, envelope_client = _service(invalid_envelope)
    try:
        with pytest.raises(AIServiceError) as envelope_raised:
            await envelope_service.extract_resume("safe test resume")
    finally:
        await envelope_client.aclose()
    assert envelope_raised.value.status_code == 502
    assert envelope_raised.value.message == "AI 服务返回格式异常"
