from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.resume import router as resume_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import configure_logging, request_logging_middleware
from app.services.container import close_services

settings = get_settings()
configure_logging(settings.debug)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_services()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-assisted resume parsing and explainable job matching API",
    debug=settings.debug,
    lifespan=lifespan,
)
app.middleware("http")(request_logging_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(resume_router, prefix=settings.api_prefix)

