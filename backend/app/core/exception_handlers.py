from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


def _error_response(status_code: int, message: str, code: int | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code or status_code, "message": message, "data": None},
    )


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return _error_response(exc.status_code, exc.message, exc.code)


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    logger.info("request_validation_failed error_count=%s", len(exc.errors()))
    return _error_response(422, "请求数据校验失败")


async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "请求处理失败"
    return _error_response(exc.status_code, message)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_error path=%s error_type=%s", request.url.path, type(exc).__name__
    )
    return _error_response(500, "服务内部错误，请稍后重试")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

