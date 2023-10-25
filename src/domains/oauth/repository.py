from typing import Any

from redis import asyncio as aioredis
from redis.asyncio.client import Pipeline as RedisPipeline
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.base.repository import (
    BaseAsyncDBRepository,
    BaseRedisRepository,
)
from src.lib import errors, models, schemas


class OauthDBRepository(BaseAsyncDBRepository):
    @staticmethod
    async def check_is_user_exists(*, session: AsyncSession, item_id: int) -> bool:
        result = await session.execute(select(exists(models.User)).where(models.User.id == item_id))
        return result.scalars().first() is not None

    @staticmethod
    async def get_user_credentials(
        *, session: AsyncSession, item_id: int | None = None, username: str | None = None
    ) -> schemas.UserCredentials:
        if username and not item_id:
            result = await session.execute(
                select(models.User.id, models.User.username, models.User.hashed_password.label("password")).where(
                    models.User.username == username
                )
            )
            user = result.fetchone()
            if not user:
                raise errors.UserNotFoundByUsernameError
            return schemas.UserCredentials.model_validate(user)
        raise errors.UserNotFoundByUsernameError


class OauthCacheRepository(BaseRedisRepository):
    @staticmethod
    async def store_refresh_token(pipe: "RedisPipeline[Any]", user_id: int, token: str) -> None:
        await pipe.sadd(str(user_id), token).execute()

    @staticmethod
    async def check_refresh_token(session: "aioredis.Redis[Any]", user_id: int, refresh_token: str) -> bool:
        return await session.sismember(name=str(user_id), value=refresh_token)

    @staticmethod
    async def delete_refresh_token(pipe: "RedisPipeline[Any]", user_id: int, refresh_token: str) -> None:
        await pipe.srem(str(user_id), refresh_token).execute()
