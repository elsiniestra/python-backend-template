from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.lib import errors


class OAuth2AccessToken(HTTPBearer):
    # Type ignore because of the overriding return type of __call__ method
    async def __call__(self, request: Request) -> str | None:  # type: ignore
        authorization: HTTPAuthorizationCredentials | None = await super().__call__(request)
        if not authorization:
            raise errors.UnauthorizedAccessTokenError

        if authorization.scheme != "Bearer":
            raise errors.UnauthorizedAccessTokenError
        return authorization.credentials


class OAuth2RefreshToken(HTTPBearer):
    async def __call__(self, request: Request) -> str | None:  # type: ignore
        authorization: HTTPAuthorizationCredentials | None = await super().__call__(request)
        if not authorization:
            raise errors.UnauthorizedRefreshTokenError

        if authorization.scheme != "Bearer":
            raise errors.UnauthorizedRefreshTokenError
        return authorization.credentials
