from __future__ import annotations

from dataclasses import dataclass

import fitz
from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import BadRequestError, FileTooLargeError
from app.utils.text_utils import clean_text


@dataclass(slots=True)
class PDFText:
    page_count: int
    cleaned_text: str


class PDFService:
    ALLOWED_MIME_TYPES = {"application/pdf", "application/x-pdf"}

    def __init__(self, settings: Settings):
        self.settings = settings

    async def read_and_validate(self, file: UploadFile) -> bytes:
        filename = (file.filename or "").strip()
        if not filename.lower().endswith(".pdf"):
            raise BadRequestError("仅支持 PDF 格式文件")
        if (file.content_type or "").lower() not in self.ALLOWED_MIME_TYPES:
            raise BadRequestError("文件 MIME 类型必须为 application/pdf")
        content = await file.read(self.settings.max_upload_size_bytes + 1)
        if len(content) > self.settings.max_upload_size_bytes:
            raise FileTooLargeError(
                f"上传文件不能超过 {self.settings.max_upload_size_mb}MB"
            )
        if not content:
            raise BadRequestError("上传的 PDF 文件为空")
        if not content.startswith(b"%PDF-"):
            raise BadRequestError("文件内容不是有效的 PDF")
        return content

    def extract_text(self, content: bytes) -> PDFText:
        try:
            document = fitz.open(stream=content, filetype="pdf")
        except (fitz.FileDataError, RuntimeError, ValueError) as exc:
            raise BadRequestError("PDF 文件已损坏或无法解析") from exc
        try:
            if document.page_count <= 0:
                raise BadRequestError("PDF 中没有可解析的页面")
            pages = [document.load_page(index).get_text("text") for index in range(document.page_count)]
            page_count = document.page_count
        except (RuntimeError, ValueError) as exc:
            raise BadRequestError("PDF 文件已损坏或无法解析") from exc
        finally:
            document.close()
        text = clean_text("\n\n".join(pages))
        if not text:
            raise BadRequestError("PDF 中没有可提取文本，请上传文本型 PDF")
        return PDFText(page_count=page_count, cleaned_text=text)

