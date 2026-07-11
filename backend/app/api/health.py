from fastapi import APIRouter

from app.schemas.common import ApiResponse, success

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[dict[str, str]])
async def health_check() -> dict:
    return success({"status": "ok", "service": "ai-resume-analyzer"})
