from datetime import datetime

import jose
from jose import jwt as jose_jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from src.domains.base.service import BaseService
from src.lib import errors, schemas


class JWTService(BaseService):
    def __init__(self, pwd_context: CryptContext) -> None:
        super().__init__()
        self.pwd_context = pwd_context

    @staticmethod
    async def generate_jwt_token(
        *,
        user_id: int,
        secret_key: str,
        sign_algorithm: str,
        access_token_expires_at: datetime,
        refresh_token_expires_at: datetime,
        is_refresh: bool = False,
    ) -> str:
        expire_date: datetime = refresh_token_expires_at if is_refresh else access_token_expires_at
        to_encode: dict[str, datetime | str | int] = {"exp": expire_date, "sub": str(user_id)}
        if is_refresh:
            to_encode.update({"irt": True})

        encoded_jwt: str = jose_jwt.encode(
            claims=to_encode,
            key=secret_key,
            algorithm=sign_algorithm,
        )
        return encoded_jwt

    @staticmethod
    async def decode_jwt_token(
        *,
        token: str,
        secret_key: str,
        sign_algorithm: str,
        is_refresh: bool = False,
    ) -> schemas.TokenPayload:
        try:
            payload: dict[str, str | int] = jose_jwt.decode(
                token=token,
                key=secret_key,
                algorithms=[sign_algorithm],
            )
        except jose.ExpiredSignatureError:
            if is_refresh:
                raise errors.RefreshTokenExpiredError
            raise errors.AccessTokenExpiredError
        except (jose.JWTError, ValidationError):
            raise errors.IncorrectJWTContentCredentialsError

        exp_str = payload.get("exp")
        if not exp_str:
            raise errors.IncorrectJWTContentCredentialsError

        sub_str = payload.get("sub")
        if not sub_str:
            raise errors.IncorrectJWTContentCredentialsError
        sub = int(sub_str)

        if is_refresh and not payload.get("irt"):
            raise errors.IncorrectJWTContentCredentialsError

        return schemas.TokenPayload(exp=int(exp_str), sub=sub, irt=is_refresh)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        result: bool = self.pwd_context.verify(plain_password, hashed_password)
        return result

    def get_password_hash(self, password: str) -> str:
        result: str = self.pwd_context.hash(password)
        return result
