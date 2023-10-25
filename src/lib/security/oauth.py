from fastapi import Request
from fastapi.security import HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param

from src.lib import errors


class OAuth2AccessToken(HTTPBearer):
    # Type ignore because of the overriding return type of __call__ method
    async def __call__(self, request: Request) -> str | None:  # type: ignore
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise errors.UnauthorizedAccessTokenError
            else:
                return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise errors.UnauthorizedRefreshTokenError
            else:
                return None
        return credentials


class OAuth2RefreshToken(HTTPBearer):
    async def __call__(self, request: Request) -> str | None:  # type: ignore
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise errors.UnauthorizedRefreshTokenError
            else:
                return None
        if scheme.lower() != "refresh":
            if self.auto_error:
                raise errors.UnauthorizedRefreshTokenError
            else:
                return None
        return credentials
