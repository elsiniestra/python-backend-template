from pydantic import BaseModel, Field

from src.lib.schemas import BaseModelORM


class AccessTokenResponse(BaseModel):
    access_token: str
    access_token_type: str = Field(default="Bearer")


class RefreshTokenResponse(BaseModel):
    refresh_token: str
    refresh_token_type: str = Field(default="Bearer")


class RotateTokenResponse(AccessTokenResponse, RefreshTokenResponse):
    pass


class TokenPayload(BaseModel):
    exp: int
    sub: int
    irt: bool = False  # is refresh token


class JwtTokenGenerationInfo(BaseModel):
    refresh_token_expires_minutes: int
    access_token_expires_minutes: int
    secret_key: str
    sign_algorithm: str


class UserCredentials(BaseModelORM):
    id: int
    username: str
    password: str
