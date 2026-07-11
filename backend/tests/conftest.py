from __future__ import annotations

import os
from collections.abc import Callable

import fitz
import pytest
from fastapi.testclient import TestClient

os.environ["REDIS_ENABLED"] = "false"
os.environ.pop("DASHSCOPE_API_KEY", None)

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_pdf() -> Callable[[list[str]], bytes]:
    def factory(pages: list[str]) -> bytes:
        document = fitz.open()
        for text in pages:
            page = document.new_page()
            page.insert_text((72, 72), text, fontsize=11)
        value = document.tobytes()
        document.close()
        return value

    return factory

