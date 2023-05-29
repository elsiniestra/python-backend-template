from dataclasses import dataclass

from passlib.context import CryptContext
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.domains.oauth.controller import OauthController
from src.domains.oauth.repository import OauthCacheRepository, OauthDBRepository
from src.domains.oauth.service import JWTService
from src.domains.user.graph_repository import UserGraphRepository


@dataclass(frozen=True)
class OauthDomain:
    controller: OauthController


def create_oauth_domain(
    *,
    pg_session_manager: "sessionmaker[AsyncSession]",
    redis_connection_pool: aioredis.ConnectionPool,
    iam_graph_name: str,
    pwd_context: CryptContext,
) -> OauthDomain:
    db_repo = OauthDBRepository(session_manager=pg_session_manager)
    cache_repo = OauthCacheRepository(connection_pool=redis_connection_pool)
    graph_repo = UserGraphRepository(connection_pool=redis_connection_pool, graph_name=iam_graph_name)
    oauth_service = JWTService(pwd_context=pwd_context)
    controller = OauthController(
        db_repo=db_repo, cache_repo=cache_repo, graph_repo=graph_repo, oauth_service=oauth_service
    )
    return OauthDomain(controller=controller)
