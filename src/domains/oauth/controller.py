from datetime import datetime, timedelta
from functools import partial
from typing import Annotated, Any, Callable, Coroutine

from fastapi import Body, Depends, Request, responses
from redis.asyncio.client import Pipeline as RedisPipeline
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import MainSettings
from src.domains.oauth.repository import OauthCacheRepository, OauthDBRepository
from src.domains.oauth.service import JWTService
from src.domains.user.graph_repository import UserGraphRepository
from src.lib import enums, errors, providers, schemas, security


class OauthController:
    def __init__(
        self,
        db_repo: OauthDBRepository,
        graph_repo: UserGraphRepository,
        cache_repo: OauthCacheRepository,
        oauth_service: JWTService,
    ) -> None:
        self._db_repo = db_repo
        self._graph_repo = graph_repo
        self._cache_repo = cache_repo
        self._oauth_service = oauth_service

    async def rotate_access_and_refresh_token(
        self,
        *,
        username: Annotated[str, Body()],
        password: Annotated[str, Body()],
        settings: providers.MainSettingsRequired,
    ) -> schemas.RotateTokenResponse:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            user: schemas.UserCredentials = await self._db_repo.get_user_credentials(session=session, username=username)
            if not user.password:
                raise errors.IncorrectAuthCredentialsError
            if not self._oauth_service.verify_password(plain_password=password, hashed_password=user.password):
                raise errors.IncorrectAuthCredentialsError

        date_now: datetime = datetime.utcnow()
        access_token_expires_at = date_now + timedelta(settings.security.access_token_expires_minutes)
        refresh_token_expires_at = date_now + timedelta(settings.security.refresh_token_expires_minutes)

        generate_token = partial(
            self._oauth_service.generate_jwt_token,
            user_id=user.id,
            access_token_expires_at=access_token_expires_at,
            refresh_token_expires_at=refresh_token_expires_at,
            secret_key=settings.security.secret_key,
            sign_algorithm=settings.security.sign_algorithm,
        )
        access_token: str = await generate_token()
        refresh_token: str = await generate_token(is_refresh=True)
        session: Redis[Any]
        async with self._cache_repo.create_session() as session:
            pipe: "RedisPipeline[Any]"
            async with self._cache_repo.create_transaction_pipe(session=session) as pipe:
                await self._cache_repo.store_refresh_token(pipe=pipe, user_id=user.id, token=refresh_token)
        return schemas.RotateTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=int(access_token_expires_at.timestamp()),
            refresh_token_expires_at=int(refresh_token_expires_at.timestamp()),
        )

    async def refresh_access_token(
        self,
        *,
        provided_token: Annotated[str, Depends(security.OAuth2RefreshToken())],
        settings: providers.MainSettingsRequired,
    ) -> schemas.RotateTokenResponse:
        """Refresh your access token with refresh token."""
        token_payload: schemas.TokenPayload = await self._oauth_service.decode_jwt_token(
            token=provided_token,
            sign_algorithm=settings.security.sign_algorithm,
            secret_key=settings.security.secret_key,
            is_refresh=True,
        )
        date_now: datetime = datetime.utcnow()
        access_token_expires_at = date_now + timedelta(settings.security.access_token_expires_minutes)
        refresh_token_expires_at = date_now + timedelta(settings.security.refresh_token_expires_minutes)

        generate_token = partial(
            self._oauth_service.generate_jwt_token,
            user_id=token_payload.sub,
            access_token_expires_at=access_token_expires_at,
            refresh_token_expires_at=refresh_token_expires_at,
            secret_key=settings.security.secret_key,
            sign_algorithm=settings.security.sign_algorithm,
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
            access_token_expires_at=int(access_token_expires_at.timestamp()),
            refresh_token_expires_at=int(refresh_token_expires_at.timestamp()),
        )

    async def get_authorized(self, user_id: providers.AuthUserId) -> bool:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            user = await self._db_repo.check_is_user_exists(session=session, item_id=user_id)
            if not user:
                raise errors.AccessTokenProvideNotExistentUserError
        return user is not None

    def get_access_provided(
        self,
        scope: enums.IAMScope,
        access: enums.IAMAccess,
        auto_error: bool = True,
    ) -> Callable[[int], Coroutine[Any, Any, bool]]:
        async def wrapper(user_id: providers.OptionalAuthUserId) -> bool:
            if not user_id:
                return False

            session: Redis[Any]
            async with self._graph_repo.create_session() as session:
                is_granted = await self._graph_repo.is_user_granted_permission(
                    session=session, user_id=user_id, scope=scope, access=access
                )
                if not is_granted and auto_error:
                    raise errors.AccessTokenProvideUserWithNoAccessRightsError
                return is_granted

        return wrapper

    def get_auth_user_id(self, auto_error: bool) -> Callable[[str, MainSettings], Coroutine[Any, Any, int | None]]:
        async def wrapper(
            token: Annotated[str, Depends(security.OAuth2AccessToken(auto_error=auto_error))],
            settings: providers.MainSettingsRequired,
        ) -> int | None:
            if token is None:
                return None
            token_payload: schemas.TokenPayload = await self._oauth_service.decode_jwt_token(
                token=token,
                sign_algorithm=settings.security.sign_algorithm,
                secret_key=settings.security.secret_key,
            )
            return token_payload.sub

        return wrapper

    @staticmethod
    async def google_sso_init(sso: providers.GoogleSSORequired) -> responses.RedirectResponse:
        with sso:
            return await sso.get_login_redirect(params={"prompt": "consent", "access_type": "offline"})

    @staticmethod
    async def google_sso_callback(request: Request, sso: providers.GoogleSSORequired) -> responses.RedirectResponse:
        with sso:
            return await sso.verify_and_process(request=request)

    @staticmethod
    async def github_sso_init(sso: providers.GithubSSORequired) -> responses.RedirectResponse:
        with sso:
            return await sso.get_login_redirect()

    @staticmethod
    async def github_sso_callback(request: Request, sso: providers.GithubSSORequired) -> responses.RedirectResponse:
        with sso:
            return await sso.verify_and_process(request=request)

    @staticmethod
    async def microsoft_sso_init(sso: providers.MicrosoftSSORequired) -> responses.RedirectResponse:
        with sso:
            return await sso.get_login_redirect()

    @staticmethod
    async def microsoft_sso_callback(
        request: Request, sso: providers.MicrosoftSSORequired
    ) -> responses.RedirectResponse:
        with sso:
            return await sso.verify_and_process(request=request)
