from .base import (
    BadRequestError,
    ForbiddenError,
    UnauthorizedError,
    UnprocessableEntityError,
)


class IncorrectAuthCredentialsError(BadRequestError):
    def __init__(self, *, detail: str = "Incorrect email or password") -> None:
        super().__init__(detail=detail)


class UnauthorizedAccessTokenError(UnauthorizedError):
    def __init__(self, *, detail: str = "Access token is not provided") -> None:
        super().__init__(detail=detail)
        self.headers = {"WWW-Authenticate": "Bearer"}


class UnauthorizedRefreshTokenError(UnauthorizedError):
    def __init__(self, *, detail: str = "Refresh token is not provided") -> None:
        super().__init__(detail=detail)
        self.headers = {"WWW-Authenticate": "Bearer"}


class IncorrectJWTContentCredentialsError(ForbiddenError):
    def __init__(self, *, detail: str = "Could not validate credentials. Incorrect token or token payload") -> None:
        super().__init__(detail=detail)


class AccessTokenExpiredError(ForbiddenError):
    def __init__(self, *, detail: str = "Access token expired") -> None:
        super().__init__(detail=detail)


class RefreshTokenExpiredError(ForbiddenError):
    def __init__(self, *, detail: str = "Refresh token expired") -> None:
        super().__init__(detail=detail)


class AccessTokenProvideNotExistentUserError(UnprocessableEntityError):
    def __init__(self, *, detail: str = "User not found. Access token was provided for not-existent user") -> None:
        super().__init__(detail=detail)


class AccessTokenProvideUserWithNoAccessRightsError(UnprocessableEntityError):
    def __init__(self, *, detail: str = "User not found or have no required rights to access the endpoint.") -> None:
        super().__init__(detail=detail)


class UserNotFoundByUsernameError(UnprocessableEntityError):
    def __init__(self, *, detail: str = "User not found. Username was provided for not-existent user") -> None:
        super().__init__(detail=detail)
