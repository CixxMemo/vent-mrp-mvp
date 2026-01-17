"""Application error definitions and FastAPI handlers."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class AppException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, code: str = "error"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Kayıt bulunamadı"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, code="not_found")


class ValidationAppException(AppException):
    def __init__(self, message: str = "Geçersiz veri"):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="validation_error")


def _format_error(detail: str, code: str):
    return {"mesaj": detail, "kod": code}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content=_format_error(exc.message, exc.code))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_format_error("Gönderilen veri doğrulanamadı", "validation_error"),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_format_error("Gönderilen veri doğrulanamadı", "validation_error"),
        )


