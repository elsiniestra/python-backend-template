from abc import ABCMeta

from fastapi import status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorModel(BaseModel):
    ok: bool = False
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error: str = "Internal Server Error"
    detail: str | None = None


class AbstractError(Exception, metaclass=ABCMeta):
    def __init__(
        self,
        *,
        status_code: int,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.detail = detail
        self.status_code = status_code
        self.headers = headers


class BadRequestError(AbstractError):
    def __init__(self, *, detail: str = "Bad Request") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnprocessableEntityError(AbstractError):
    def __init__(self, *, detail: str = "Unprocessable Entity") -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class UnauthorizedError(AbstractError):
    def __init__(self, *, detail: str = "Unauthorized") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(AbstractError):
    def __init__(self, *, detail: str = "Forbidden") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class InternalServerError(AbstractError):
    def __init__(self, *, detail: str = "Internal Server Error") -> None:
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class NotFoundError(AbstractError):
    def __init__(self, *, detail: str = "Resource Not Found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


async def global_exception_handler(request: Request, exc: AbstractError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorModel(
            error=exc.__class__.__name__,
            detail=exc.detail,
            status_code=exc.status_code,
        ).model_dump(),
    )
