from fastapi import APIRouter, File, Form, UploadFile

from app.core.exceptions import BadRequestError
from app.schemas.common import ApiResponse, success
from app.schemas.job import MatchRequest
from app.schemas.match import AnalyzeResponseData, MatchResponseData
from app.schemas.resume import ParsedResumeData
from app.services.container import analysis_service

router = APIRouter(prefix="/resumes", tags=["resumes"])


def _require_single_file(files: list[UploadFile]) -> UploadFile:
    if len(files) != 1:
        raise BadRequestError("每次只能上传一个 PDF 文件")
    return files[0]


@router.post("/parse", response_model=ApiResponse[ParsedResumeData])
async def parse_resume(file: list[UploadFile] = File(...)) -> dict:
    data = await analysis_service.parse(_require_single_file(file))
    return success(data, "简历解析成功")


@router.post("/match", response_model=ApiResponse[MatchResponseData])
async def match_resume(payload: MatchRequest) -> dict:
    data = await analysis_service.match(
        payload.resumeId, payload.jobTitle, payload.jobDescription
    )
    return success(data, "匹配分析成功")


@router.post("/analyze", response_model=ApiResponse[AnalyzeResponseData])
async def analyze_resume(
    file: list[UploadFile] = File(...),
    jobTitle: str = Form(...),
    jobDescription: str = Form(...),
) -> dict:
    data = await analysis_service.analyze(_require_single_file(file), jobTitle, jobDescription)
    return success(data, "分析成功")
