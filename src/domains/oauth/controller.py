from functools import partial
from typing import Any, Callable, Coroutine

from fastapi import Body, Depends
from redis.asyncio.client import Pipeline as RedisPipeline
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.oauth.repository import (
    BaseOauthCacheRepository,
    BaseOauthDBRepository,
)
from src.domains.oauth.service import BaseJWTService
from src.domains.user.graph_repository import BaseUserGraphRepository
from src.lib import errors, providers, schemas, security
from src.lib.enums import IAMAccess, IAMScope
from src.lib.schemas import JwtTokenGenerationInfo


class OauthController:
    def __init__(
        self,
        db_repo: BaseOauthDBRepository,
        graph_repo: BaseUserGraphRepository,
        cache_repo: BaseOauthCacheRepository,
        oauth_service: BaseJWTService,
    ) -> None:
        self._db_repo = db_repo
        self._graph_repo = graph_repo
        self._cache_repo = cache_repo
        self._oauth_service = oauth_service

    async def rotate_access_and_refresh_token(
        self,
        *,
        username: str = Body(),
        password: str = Body(),
        jwt_token_generation_info: schemas.JwtTokenGenerationInfo = Depends(providers.get_jwt_token_generation_info),
    ) -> schemas.RotateTokenResponse:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            user: schemas.UserCredentials = await self._db_repo.get_user_credentials(session=session, username=username)
            if not user.password:
                raise errors.IncorrectAuthCredentialsError
            if not self._oauth_service.verify_password(plain_password=password, hashed_password=user.password):
                raise errors.IncorrectAuthCredentialsError

        generate_token = partial(
            self._oauth_service.generate_jwt_token,
            user_id=user.id,
            access_token_expires_minutes=jwt_token_generation_info.access_token_expires_minutes,
            refresh_token_expires_minutes=jwt_token_generation_info.refresh_token_expires_minutes,
            secret_key=jwt_token_generation_info.secret_key,
            sign_algorithm=jwt_token_generation_info.sign_algorithm,
        )
        access_token: str = await generate_token()
        refresh_token: str = await generate_token(is_refresh=True)
        session: Redis[Any]
        async with self._cache_repo.create_session() as session:
            pipe: "RedisPipeline[Any]"
            async with self._cache_repo.create_transaction_pipe(session=session) as pipe:
                await self._cache_repo.store_refresh_token(pipe=pipe, user_id=user.id, token=refresh_token)
        return schemas.RotateTokenResponse(
            refresh_token=refresh_token,
            access_token=access_token,
        )

    async def refresh_access_token(
        self,
        *,
        provided_token: str = Depends(security.OAuth2RefreshToken()),
        jwt_token_generation_info: schemas.JwtTokenGenerationInfo = Depends(providers.get_jwt_token_generation_info),
    ) -> schemas.RotateTokenResponse:
        """Refresh your access token with refresh token."""
        token_payload: schemas.TokenPayload = await self._oauth_service.decode_jwt_token(
            token=provided_token,
            sign_algorithm=jwt_token_generation_info.sign_algorithm,
            secret_key=jwt_token_generation_info.secret_key,
            is_refresh=True,
        )
        generate_token = partial(
            self._oauth_service.generate_jwt_token,
            user_id=token_payload.sub,
            access_token_expires_minutes=jwt_token_generation_info.access_token_expires_minutes,
            refresh_token_expires_minutes=jwt_token_generation_info.refresh_token_expires_minutes,
            secret_key=jwt_token_generation_info.secret_key,
            sign_algorithm=jwt_token_generation_info.sign_algorithm,
        )
        access_token: str = await generate_token()
        refresh_token: str = await generate_token(is_refresh=True)
        session: Redis[Any]
        async with self._cache_repo.create_session() as session:
            token_is_valid: bool = await self._cache_repo.check_refresh_token(
                session=session, user_id=token_payload.sub, refresh_token=provided_token
            )
            if not token_is_valid:
                raise errors.IncorrectJWTContentCredentialsError
            pipe: "RedisPipeline[Any]"
            async with self._cache_repo.create_transaction_pipe(session=session) as pipe:
                await self._cache_repo.delete_refresh_token(
                    pipe=pipe, user_id=token_payload.sub, refresh_token=provided_token
                )
                await self._cache_repo.store_refresh_token(pipe=pipe, user_id=token_payload.sub, token=refresh_token)

        return schemas.RotateTokenResponse(
            refresh_token=refresh_token,
            access_token=access_token,
        )

    async def get_authorized(
        self,
        token: str = Depends(security.OAuth2AccessToken()),
        jwt_token_generation_info: schemas.JwtTokenGenerationInfo = Depends(providers.get_jwt_token_generation_info),
    ) -> bool:
        token_payload: schemas.TokenPayload = await self._oauth_service.decode_jwt_token(
            token=token,
            sign_algorithm=jwt_token_generation_info.sign_algorithm,
            secret_key=jwt_token_generation_info.secret_key,
        )
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            user = await self._db_repo.check_is_user_exists(session=session, item_id=token_payload.sub)
            if not user:
                raise errors.AccessTokenProvideNotExistentUserError
        return user is not None

    def get_access_provided(
        self,
        scope: IAMScope,
        access: IAMAccess,
    ) -> Callable[[str, JwtTokenGenerationInfo], Coroutine[Any, Any, bool]]:
        async def wrapper(
            token: str = Depends(security.OAuth2AccessToken()),
            jwt_token_generation_info: schemas.JwtTokenGenerationInfo = Depends(
                providers.get_jwt_token_generation_info
            ),
        ) -> bool:
            token_payload: schemas.TokenPayload = await self._oauth_service.decode_jwt_token(
                token=token,
                sign_algorithm=jwt_token_generation_info.sign_algorithm,
                secret_key=jwt_token_generation_info.secret_key,
            )

            session: Redis[Any]
            async with self._graph_repo.create_session() as session:
                is_granted = await self._graph_repo.is_user_granted_permission(
                    session=session, user_id=token_payload.sub, scope=scope, access=access
                )
                if not is_granted:
                    raise errors.AccessTokenProvideUserWithNoAccessRightsError
                return is_granted

        return wrapper

    async def get_auth_user_id(
        self,
        token: str = Depends(security.OAuth2AccessToken()),
        jwt_token_generation_info: schemas.JwtTokenGenerationInfo = Depends(providers.get_jwt_token_generation_info),
    ) -> int:
        token_payload: schemas.TokenPayload = await self._oauth_service.decode_jwt_token(
            token=token,
            sign_algorithm=jwt_token_generation_info.sign_algorithm,
            secret_key=jwt_token_generation_info.secret_key,
        )
        return token_payload.sub
