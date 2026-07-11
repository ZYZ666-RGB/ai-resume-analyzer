class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code or status_code


class BadRequestError(AppError):
    def __init__(self, message: str):
        super().__init__(message, 400)


class NotFoundError(AppError):
    def __init__(self, message: str):
        super().__init__(message, 404)


class FileTooLargeError(AppError):
    def __init__(self, message: str = "上传文件超过大小限制"):
        super().__init__(message, 413)


class AIServiceError(AppError):
    def __init__(self, message: str = "AI 服务调用失败", status_code: int = 502):
        super().__init__(message, status_code)

