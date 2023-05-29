import abc
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from src.domains.base.service import BaseService
from src.lib import errors, schemas


class BaseJWTService(BaseService):
    def __init__(self, pwd_context: CryptContext) -> None:
        super().__init__()
        self.pwd_context = pwd_context

    @abc.abstractmethod
    async def generate_jwt_token(
        self,
        *,
        user_id: int,
        secret_key: str,
        sign_algorithm: str,
        access_token_expires_minutes: int,
        refresh_token_expires_minutes: int,
        is_refresh: bool = False,
    ) -> str:
        pass

    @abc.abstractmethod
    async def decode_jwt_token(
        self, *, token: str, secret_key: str, sign_algorithm: str, is_refresh: bool = False
    ) -> schemas.TokenPayload:
        pass

    @abc.abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        pass

    @abc.abstractmethod
    def get_password_hash(self, password: str) -> str:
        pass


class JWTService(BaseJWTService):
    async def generate_jwt_token(
        self,
        *,
        user_id: int,
        secret_key: str,
        sign_algorithm: str,
        access_token_expires_minutes: int,
        refresh_token_expires_minutes: int,
        is_refresh: bool = False,
    ) -> str:
        date_now: datetime = datetime.utcnow()
        expires: int = refresh_token_expires_minutes if is_refresh else access_token_expires_minutes
        expire_date: datetime = date_now + timedelta(expires)
        to_encode: dict[str, datetime | str | int] = {"exp": expire_date, "sub": str(user_id)}
        if is_refresh:
            to_encode.update({"irt": True})

        encoded_jwt: str = jwt.encode(
            claims=to_encode,
            key=secret_key,
            algorithm=sign_algorithm,
        )
        return encoded_jwt

    async def decode_jwt_token(
        self,
        *,
        token: str,
        secret_key: str,
        sign_algorithm: str,
        is_refresh: bool = False,
    ) -> schemas.TokenPayload:
        try:
            payload: dict[str, str | int] = jwt.decode(
                token=token,
                key=secret_key,
                algorithms=[sign_algorithm],
            )
        except (jwt.JWTError, ValidationError):
            raise errors.IncorrectJWTContentCredentialsError

        exp_str = payload.get("exp")
        if not exp_str:
            raise errors.IncorrectJWTContentCredentialsError
        exp = int(exp_str)
        if exp <= datetime.utcnow().timestamp():
            if is_refresh:
                raise errors.RefreshTokenExpiredError
            raise errors.AccessTokenExpiredError

        sub_str = payload.get("sub")
        if not sub_str:
            raise errors.IncorrectJWTContentCredentialsError
        sub = int(sub_str)

        if is_refresh and not payload.get("irt"):
            raise errors.IncorrectJWTContentCredentialsError

        return schemas.TokenPayload(exp=exp, sub=sub, irt=is_refresh)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        result: bool = self.pwd_context.verify(plain_password, hashed_password)
        return result

    def get_password_hash(self, password: str) -> str:
        result: str = self.pwd_context.hash(password)
        return result
