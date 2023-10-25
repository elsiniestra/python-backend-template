from dataclasses import dataclass

from passlib.context import CryptContext
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domains.oauth.service import JWTService

from .controller import UserController
from .graph_repository import UserGraphRepository
from .repository import UserDBRepository


@dataclass(frozen=True)
class UserDomain:
    controller: UserController


def create_user_domain(
    *,
    pg_session_manager: async_sessionmaker[AsyncSession],
    redis_connection_pool: aioredis.ConnectionPool,
    iam_graph_name: str,
    pwd_context: CryptContext,
) -> UserDomain:
    db_repo = UserDBRepository.create_instance(session_manager=pg_session_manager)
    graph_repo = UserGraphRepository.create_instance(connection_pool=redis_connection_pool, graph_name=iam_graph_name)
    oauth_service = JWTService(pwd_context=pwd_context)
    controller = UserController(db_repo=db_repo, graph_repo=graph_repo, oauth_service=oauth_service)
    return UserDomain(controller=controller)
